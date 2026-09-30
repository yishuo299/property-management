from datetime import datetime
from decimal import Decimal
import uuid

from django.db import IntegrityError
from django.db.models import Q, Sum
from django.views.decorators.http import require_http_methods

from .models import FeeBill, PaymentRecord, Room, Building, OwnerRoom, SysUser, Owner
from .utils import (ok, error, parse_body, login_required, role_required, page_result,
                    to_int, to_decimal, now, money, dec, calc_late_fee, days_overdue,
                    period_due_date, valid_period, DEFAULT_UNIT_PRICE, current_owner,
                    LATE_FEE_RATE)

ADMIN = ['ADMIN']


def _total_due(bill):
    return dec(bill.amount) + dec(calc_late_fee(bill))


def _enrich(d):
    d['totalDue'] = float(dec(d['amount']) + dec(d['lateFee']))
    d['remaining'] = float(max(Decimal('0'), dec(d['totalDue']) - dec(d['paidAmount'])))
    return d


def _primary_owner_map(room_ids):
    """房屋 -> 主产权人 映射"""
    m = {}
    for b in OwnerRoom.objects.filter(room_id__in=room_ids, is_primary=1, deleted=0, status='有效'):
        m.setdefault(b.room_id, b.owner_id)
    return m


def _scope(request, qs):
    if request.role == 'OWNER':
        owner = current_owner(request)
        return qs.filter(owner_id=owner.id) if owner else qs.none()
    return qs


# ============================ 账单查询 ============================
@login_required
def bill_page(request):
    qs = FeeBill.objects.filter(deleted=0)
    qs = _scope(request, qs)
    period = request.GET.get('period')
    if period:
        qs = qs.filter(period=period)
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    fee_type = request.GET.get('feeType')
    if fee_type:
        qs = qs.filter(fee_type=fee_type)
    bid = to_int(request.GET.get('buildingId'))
    if bid:
        qs = qs.filter(room__building_id=bid)
    kw = (request.GET.get('keyword') or '').strip()
    if kw:
        qs = qs.filter(Q(bill_no__contains=kw) | Q(room__room_no__contains=kw))
    return page_result(request, qs.select_related('room', 'room__building', 'room__unit')
                       .order_by('-period', 'room_id'),
                       lambda o: _enrich(o.to_dict()))


@login_required
def bill_mine(request):
    """业主「我的账单」"""
    owner = current_owner(request)
    if not owner:
        return ok({'records': [], 'total': 0, 'current': 1, 'size': 10})
    qs = FeeBill.objects.filter(deleted=0, owner_id=owner.id)
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    return page_result(request, qs.select_related('room', 'room__building', 'room__unit')
                       .order_by('-period', 'room_id'), lambda o: _enrich(o.to_dict()))


@login_required
def bill_detail(request, pk):
    bill = FeeBill.objects.filter(id=pk, deleted=0).first()
    if not bill:
        return error('账单不存在')
    if request.role == 'OWNER':
        owner = current_owner(request)
        if not owner or bill.owner_id != owner.id:
            return error('无权限查看该账单', 403)
    data = _enrich(bill.to_dict())
    data['lateFeeRate'] = float(LATE_FEE_RATE)
    data['lateFeeFormula'] = (
        f'滞纳金 = 逾期天数({days_overdue(bill)}) × 日滞纳金率({float(LATE_FEE_RATE)}) '
        f'× 欠费金额({money(Decimal(str(bill.amount)) - Decimal(str(bill.paid_amount)))}) '
        f'= {calc_late_fee(bill)} 元')
    data['payments'] = [p.to_dict() for p in
                        PaymentRecord.objects.filter(bill_id=pk, deleted=0).order_by('-pay_time')]
    return ok(data)


# ============================ 批量生成 ============================
@role_required(ADMIN)
def bill_preview(request):
    """批量生成预览：选楼栋 + 账期 -> 列出将生成/已存在的账单"""
    bid = to_int(request.GET.get('buildingId'))
    period = (request.GET.get('period') or '').strip()
    if not bid:
        return error('请选择楼栋')
    if not valid_period(period):
        return error('账期格式不正确，应为 YYYY-MM')
    building = Building.objects.filter(id=bid, deleted=0).first()
    if not building:
        return error('楼栋不存在')
    price = to_decimal(request.GET.get('unitPrice'), DEFAULT_UNIT_PRICE)
    months = to_int(request.GET.get('months'), 1)
    if price <= 0:
        return error('单价必须大于 0')
    if months < 1 or months > 24:
        return error('计费月数应在 1-24 之间')

    rooms = list(Room.objects.filter(building_id=bid, deleted=0).order_by('unit_id', 'room_no'))
    owner_map = _primary_owner_map([r.id for r in rooms])
    existing = set(FeeBill.objects.filter(room_id__in=[r.id for r in rooms], fee_type='物业费',
                                          period=period, deleted=0).values_list('room_id', flat=True))
    rows, new_count, exist_count, total = [], 0, 0, Decimal('0')
    for r in rooms:
        amount = dec(dec(r.area) * price * months)
        is_new = r.id not in existing
        if is_new:
            new_count += 1
            total += amount
        else:
            exist_count += 1
        rows.append({
            'roomId': r.id, 'roomName': r.full_name(), 'area': float(r.area),
            'amount': float(amount), 'exists': not is_new,
            'ownerId': owner_map.get(r.id),
            'ownerName': Owner.objects.filter(id=owner_map.get(r.id)).first().name if owner_map.get(r.id) else '',
        })
    return ok({
        'buildingId': bid, 'buildingName': building.building_name, 'period': period,
        'unitPrice': float(price), 'months': months, 'dueDate': period_due_date(period).strftime('%Y-%m-%d'),
        'totalRooms': len(rooms), 'newCount': new_count, 'existCount': exist_count,
        'newAmount': float(total), 'rows': rows,
    })


@role_required(ADMIN)
@require_http_methods(['POST'])
def bill_generate(request):
    """批量生成物业费账单（已存在的不重复生成）"""
    b = parse_body(request)
    bid = to_int(b.get('buildingId'))
    period = (b.get('period') or '').strip()
    if not bid:
        return error('请选择楼栋')
    if not valid_period(period):
        return error('账期格式不正确，应为 YYYY-MM')
    building = Building.objects.filter(id=bid, deleted=0).first()
    if not building:
        return error('楼栋不存在')
    price = to_decimal(b.get('unitPrice'), DEFAULT_UNIT_PRICE)
    months = to_int(b.get('months'), 1)
    if price <= 0:
        return error('单价必须大于 0')
    if months < 1 or months > 24:
        return error('计费月数应在 1-24 之间')

    rooms = list(Room.objects.filter(building_id=bid, deleted=0).order_by('unit_id', 'room_no'))
    if not rooms:
        return error('该楼栋下暂无房屋，无法生成账单')
    room_ids = [r.id for r in rooms]
    owner_map = _primary_owner_map(room_ids)
    existing = set(FeeBill.objects.filter(room_id__in=room_ids, fee_type='物业费',
                                          period=period, deleted=0).values_list('room_id', flat=True))
    # 批次号：秒级时间戳 + 毫秒 + 4 位随机串，保证同一秒内多次调用也不重复
    ts = now()
    batch_no = (f"BATCH-{period}-{building.building_code}-"
                f"{ts.strftime('%Y%m%d%H%M%S')}{ts.microsecond // 1000:03d}-{uuid.uuid4().hex[:4]}")
    due = period_due_date(period)
    created, skipped, total_amount = 0, 0, Decimal('0')
    for r in rooms:
        if r.id in existing:
            skipped += 1
            continue
        amount = dec(dec(r.area) * price * months)
        try:
            FeeBill.objects.create(
                bill_no=f"WY{period.replace('-', '')}{r.id:05d}", room_id=r.id,
                owner_id=owner_map.get(r.id), fee_type='物业费', period=period,
                unit_price=price, months=months, amount=amount, paid_amount=0,
                late_fee=0, status='未缴', due_date=due, generate_batch=batch_no,
                remark=f'{building.building_name}批量生成')
            created += 1
            total_amount += amount
        except IntegrityError:
            # 唯一键 uk_bill_room_period 兜底，保证不重复生成
            skipped += 1
    return ok({
        'batchNo': batch_no, 'buildingName': building.building_name, 'period': period,
        'created': created, 'skipped': skipped, 'totalRooms': len(rooms),
        'totalAmount': float(total_amount),
    }, msg=f'批量生成完成：新增 {created} 条，跳过已存在 {skipped} 条')


# ============================ 缴费 ============================
@role_required(ADMIN)
@require_http_methods(['POST'])
def bill_pay(request, pk):
    bill = FeeBill.objects.filter(id=pk, deleted=0).first()
    if not bill:
        return error('账单不存在')
    if bill.status == '已缴':
        return error('该账单已结清，无需重复缴费')
    b = parse_body(request)
    amount = to_decimal(b.get('amount'))
    if amount is None or amount <= 0:
        return error('缴费金额必须大于 0')
    late = calc_late_fee(bill)
    total_due = money(Decimal(str(bill.amount)) + Decimal(str(late)))
    paid = dec(bill.paid_amount)
    remaining = max(Decimal('0'), dec(total_due) - paid)
    amount = dec(amount)
    if amount > remaining + Decimal('0.01'):
        return error(f'缴费金额不能超过应缴金额 {float(remaining)} 元')
    pay_method = b.get('payMethod') or '微信'
    if pay_method not in ('微信', '支付宝', '银行卡', '现金'):
        return error('缴费方式不合法')
    trade_no = f"PAY{now().strftime('%Y%m%d%H%M%S')}{bill.id:04d}"
    PaymentRecord.objects.create(
        bill_id=bill.id, room_id=bill.room_id, owner_id=bill.owner_id, amount=amount,
        pay_method=pay_method, trade_no=trade_no, pay_time=now(),
        operator=b.get('operator') or '物业收费员', remark=b.get('remark'))
    new_paid = paid + amount
    bill.paid_amount = new_paid
    bill.late_fee = dec(late)
    if new_paid + Decimal('0.01') >= dec(total_due):
        bill.status = '已缴'
        bill.pay_time = now()
    else:
        bill.status = '部分缴纳'
    bill.save()
    data = _enrich(bill.to_dict())
    data['tradeNo'] = trade_no
    data['thisPay'] = float(amount)
    return ok(data, msg=f'缴费成功，本次缴纳 {float(amount)} 元')


@login_required
def bill_payments(request, pk):
    bill = FeeBill.objects.filter(id=pk, deleted=0).first()
    if not bill:
        return error('账单不存在')
    if request.role == 'OWNER':
        owner = current_owner(request)
        if not owner or bill.owner_id != owner.id:
            return error('无权限查看该账单', 403)
    qs = PaymentRecord.objects.filter(bill_id=pk, deleted=0).order_by('-pay_time')
    return ok([p.to_dict() for p in qs])


# ============================ 欠费统计 ============================
@login_required
def bill_arrears(request):
    """欠费统计（按楼栋汇总），并同步滞纳金"""
    if request.role == 'OWNER':
        owner = current_owner(request)
        qs = FeeBill.objects.filter(deleted=0, status__in=['未缴', '部分缴纳'], owner_id=owner.id if owner else 0)
    else:
        qs = FeeBill.objects.filter(deleted=0, status__in=['未缴', '部分缴纳'])
    rows, total_unpaid, total_late = {}, Decimal('0'), Decimal('0')
    for bill in qs.select_related('room', 'room__building'):
        late = calc_late_fee(bill)
        # 同步滞纳金到数据库
        if abs(float(bill.late_fee) - late) > 0.001:
            FeeBill.objects.filter(id=bill.id).update(late_fee=late)
        unpaid = dec(bill.amount) - dec(bill.paid_amount) + dec(late)
        bname = bill.room.building.building_name if bill.room_id and bill.room.building_id else '未知'
        row = rows.setdefault(bname, {'buildingName': bname, 'billCount': 0, 'unpaidAmount': Decimal('0'),
                                      'lateFee': Decimal('0'), 'overdueCount': 0})
        row['billCount'] += 1
        row['unpaidAmount'] += unpaid
        row['lateFee'] += dec(late)
        if days_overdue(bill) > 0:
            row['overdueCount'] += 1
        total_unpaid += unpaid
        total_late += dec(late)
    result = []
    for r in sorted(rows.values(), key=lambda x: -x['unpaidAmount']):
        result.append({
            'buildingName': r['buildingName'], 'billCount': r['billCount'],
            'unpaidAmount': float(r['unpaidAmount']), 'lateFee': float(r['lateFee']),
            'overdueCount': r['overdueCount'],
        })
    return ok({'list': result, 'totalUnpaid': float(total_unpaid), 'totalLateFee': float(total_late),
               'totalBills': qs.count(), 'lateFeeRate': float(LATE_FEE_RATE)})


@role_required(ADMIN)
@require_http_methods(['POST'])
def bill_delete(request, pk):
    bill = FeeBill.objects.filter(id=pk, deleted=0).first()
    if not bill:
        return error('账单不存在')
    if bill.status == '已缴':
        return error('已缴清的账单不允许删除')
    bill.deleted = 1
    bill.save(update_fields=['deleted', 'update_time'])
    return ok(msg='删除成功')
