from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Avg, Q, Sum
from django.views.decorators.http import require_http_methods

from .models import (RepairOrder, RepairEvaluation, FeeBill, Room, Building, Owner,
                     ParkingSpot, Visitor, Notice, SysUser)
from .utils import (ok, login_required, role_required, now, money, calc_late_fee,
                    days_overdue, current_owner, refresh_timeout_flags, to_int,
                    INTERNAL_ROLES)

ADMIN = ['ADMIN']
STAFF_ROLES = ['ADMIN', 'STAFF']
REPAIR_TYPES = ['水电', '门窗', '家电', '公共设施', '其他']


def _rate(paid, total):
    if not total or float(total) == 0:
        return 0.0
    return round(float(paid) / float(total) * 100, 2)


# ============================ 总览 ============================
@role_required(INTERNAL_ROLES)
def overview(request):
    """物业管理端首页总览（小区全局数据，仅内部人员可见）"""
    refresh_timeout_flags()
    total_orders = RepairOrder.objects.filter(deleted=0).count()
    pending = RepairOrder.objects.filter(deleted=0, status='待受理').count()
    processing = RepairOrder.objects.filter(deleted=0, status__in=['已派单', '处理中']).count()
    finished = RepairOrder.objects.filter(deleted=0, status__in=['已完成', '已评价']).count()
    timeout = RepairOrder.objects.filter(deleted=0, status='待受理', timeout_flag=1).count()

    bills = FeeBill.objects.filter(deleted=0)
    total_bills = bills.count()
    unpaid_bills = bills.filter(status__in=['未缴', '部分缴纳']).count()
    receivable = Decimal('0')
    received = Decimal('0')
    for b in bills.values('amount', 'paid_amount'):
        receivable += Decimal(str(b['amount']))
        received += min(Decimal(str(b['paid_amount'])), Decimal(str(b['amount'])))

    ev = RepairEvaluation.objects.filter(deleted=0)
    avg_score = ev.aggregate(v=Avg('score'))['v']

    return ok({
        'roomCount': Room.objects.filter(deleted=0).count(),
        'buildingCount': Building.objects.filter(deleted=0).count(),
        'ownerCount': Owner.objects.filter(deleted=0).count(),
        'parkingCount': ParkingSpot.objects.filter(deleted=0).count(),
        'parkingFree': ParkingSpot.objects.filter(deleted=0, status='空闲').count(),
        'visitorToday': Visitor.objects.filter(deleted=0,
                                               visit_time__date=now().date()).count(),
        'noticeCount': Notice.objects.filter(deleted=0, status='已发布').count(),
        'totalOrders': total_orders,
        'pendingOrders': pending,
        'processingOrders': processing,
        'finishedOrders': finished,
        'timeoutOrders': timeout,
        'avgScore': round(float(avg_score), 2) if avg_score else None,
        'totalBills': total_bills,
        'unpaidBills': unpaid_bills,
        'receivable': money(receivable),
        'received': money(received),
        'collectRate': _rate(received, receivable),
        'totalLateFee': money(sum(Decimal(str(calc_late_fee(b)))
                                  for b in FeeBill.objects.filter(deleted=0, status__in=['未缴', '部分缴纳']))),
    })


def _owner_overview(request):
    owner = current_owner(request)
    if not owner:
        return ok({})
    my_orders = RepairOrder.objects.filter(deleted=0, owner_id=owner.id)
    my_bills = FeeBill.objects.filter(deleted=0, owner_id=owner.id)
    unpaid = Decimal('0')
    for b in my_bills.filter(status__in=['未缴', '部分缴纳']):
        unpaid += Decimal(str(b.amount)) - Decimal(str(b.paid_amount)) + Decimal(str(calc_late_fee(b)))
    from .models import NoticeRead
    read_ids = list(NoticeRead.objects.filter(user_id=request.user_id, deleted=0)
                    .values_list('notice_id', flat=True))
    unread = Notice.objects.filter(deleted=0, status='已发布').filter(
        Q(expire_time__isnull=True) | Q(expire_time__gte=now())).exclude(id__in=read_ids).count()
    return ok({
        'myOrders': my_orders.count(),
        'myPending': my_orders.filter(status__in=['待受理', '已派单', '处理中']).count(),
        'myFinished': my_orders.filter(status__in=['已完成', '已评价']).count(),
        'myRooms': owner.to_dict()['roomCount'],
        'myBills': my_bills.count(),
        'myUnpaidBills': my_bills.filter(status__in=['未缴', '部分缴纳']).count(),
        'myUnpaidAmount': money(unpaid),
        'myParking': ParkingSpot.objects.filter(deleted=0, owner_id=owner.id).count(),
        'myVisitors': Visitor.objects.filter(deleted=0, owner_id=owner.id, status='待到访').count(),
        'unreadNotice': unread,
    })


@role_required(['OWNER'])
def my_overview(request):
    """业主端首页总览（只含本人数据）"""
    return _owner_overview(request)


# ============================ 报修类型分布（饼图） ============================
@login_required
def repair_type(request):
    qs = RepairOrder.objects.filter(deleted=0)
    if request.role == 'OWNER':
        owner = current_owner(request)
        qs = qs.filter(owner_id=owner.id) if owner else qs.none()
    counts = {r['repair_type']: r['c'] for r in qs.values('repair_type').annotate(c=Count('id'))}
    data = [{'name': t, 'value': counts.get(t, 0)} for t in REPAIR_TYPES]
    return ok([d for d in data if d['value'] > 0] or data)


# ============================ 报修趋势（折线图，近 14 天） ============================
@login_required
def repair_trend(request):
    qs = RepairOrder.objects.filter(deleted=0)
    if request.role == 'OWNER':
        owner = current_owner(request)
        qs = qs.filter(owner_id=owner.id) if owner else qs.none()
    days = to_int(request.GET.get('days'), 14)
    if days < 7 or days > 90:
        days = 14
    start = (now() - timedelta(days=days - 1)).date()
    buckets = {}
    for i in range(days):
        d = start + timedelta(days=i)
        buckets[d.strftime('%m-%d')] = {'new': 0, 'finished': 0}
    for o in qs.filter(Q(submit_time__gte=start) | Q(finish_time__gte=start)) \
            .values('submit_time', 'finish_time', 'status'):
        if o['submit_time']:
            k = o['submit_time'].strftime('%m-%d')
            if k in buckets:
                buckets[k]['new'] += 1
        if o['finish_time']:
            k = o['finish_time'].strftime('%m-%d')
            if k in buckets:
                buckets[k]['finished'] += 1
    return ok({
        'dates': list(buckets.keys()),
        'newOrders': [v['new'] for v in buckets.values()],
        'finishedOrders': [v['finished'] for v in buckets.values()],
    })


# ============================ 工单处理时效（柱状图） ============================
@require_http_methods(['GET'])
@login_required
def repair_efficiency(request):
    qs = RepairOrder.objects.filter(deleted=0)
    if request.role == 'OWNER':
        owner = current_owner(request)
        qs = qs.filter(owner_id=owner.id) if owner else qs.none()
    accept_map, finish_map, counts = {}, {}, {}
    within24, between24_48, over48 = 0, 0, 0
    for o in qs.values('repair_type', 'submit_time', 'accept_time', 'finish_time', 'status'):
        t = o['repair_type']
        counts[t] = counts.get(t, 0) + 1
        if o['accept_time']:
            h = (o['accept_time'] - o['submit_time']).total_seconds() / 3600
            accept_map.setdefault(t, []).append(h)
        if o['finish_time']:
            h = (o['finish_time'] - o['submit_time']).total_seconds() / 3600
            finish_map.setdefault(t, []).append(h)
            if h <= 24:
                within24 += 1
            elif h <= 48:
                between24_48 += 1
            else:
                over48 += 1
    types = [t for t in REPAIR_TYPES if counts.get(t)]
    return ok({
        'types': types,
        'orderCounts': [counts.get(t, 0) for t in types],
        'avgAcceptHours': [round(sum(accept_map.get(t, [0])) / len(accept_map[t]), 1)
                           if accept_map.get(t) else 0 for t in types],
        'avgFinishHours': [round(sum(finish_map.get(t, [0])) / len(finish_map[t]), 1)
                           if finish_map.get(t) else 0 for t in types],
        'durationBuckets': [
            {'name': '24小时内完成', 'value': within24},
            {'name': '24-48小时完成', 'value': between24_48},
            {'name': '48小时以上完成', 'value': over48},
        ],
    })


# ============================ 物业费收缴率（按账期） ============================
@role_required(STAFF_ROLES)
def fee_rate(request):
    rows = {}
    qs = FeeBill.objects.filter(deleted=0)
    bid = to_int(request.GET.get('buildingId'))
    if bid:
        qs = qs.filter(room__building_id=bid)
    for b in qs.values('period', 'fee_type', 'amount', 'paid_amount'):
        key = b['period']
        r = rows.setdefault(key, {'period': key, 'receivable': Decimal('0'), 'received': Decimal('0'),
                                  'billCount': 0, 'paidCount': 0, 'unpaidCount': 0})
        amt = Decimal(str(b['amount']))
        paid = min(Decimal(str(b['paid_amount'])), amt)
        r['receivable'] += amt
        r['received'] += paid
        r['billCount'] += 1
        if paid >= amt:
            r['paidCount'] += 1
        else:
            r['unpaidCount'] += 1
    periods = sorted(rows.keys())
    return ok({
        'periods': periods,
        'receivable': [money(rows[p]['receivable']) for p in periods],
        'received': [money(rows[p]['received']) for p in periods],
        'rate': [_rate(rows[p]['received'], rows[p]['receivable']) for p in periods],
        'billCount': [rows[p]['billCount'] for p in periods],
        'paidCount': [rows[p]['paidCount'] for p in periods],
        'unpaidCount': [rows[p]['unpaidCount'] for p in periods],
    })


# ============================ 楼栋缴费对比（柱状图） ============================
@role_required(STAFF_ROLES)
def building_fee(request):
    period = request.GET.get('period')
    qs = FeeBill.objects.filter(deleted=0)
    if period:
        qs = qs.filter(period=period)
    rows = {}
    for b in qs.values('room__building__building_name', 'amount', 'paid_amount'):
        name = b['room__building__building_name'] or '未知'
        r = rows.setdefault(name, {'receivable': Decimal('0'), 'received': Decimal('0'),
                                   'billCount': 0, 'unpaidCount': 0})
        amt = Decimal(str(b['amount']))
        paid = min(Decimal(str(b['paid_amount'])), amt)
        r['receivable'] += amt
        r['received'] += paid
        r['billCount'] += 1
        if paid < amt:
            r['unpaidCount'] += 1
    names = sorted(rows.keys(), key=lambda n: int(''.join(filter(str.isdigit, n)) or 0))
    return ok({
        'buildings': names,
        'receivable': [money(rows[n]['receivable']) for n in names],
        'received': [money(rows[n]['received']) for n in names],
        'rate': [_rate(rows[n]['received'], rows[n]['receivable']) for n in names],
        'unpaidCount': [rows[n]['unpaidCount'] for n in names],
    })


# ============================ 员工工作量与满意度 ============================
@role_required(STAFF_ROLES)
def staff_workload(request):
    staffs = SysUser.objects.filter(role='STAFF', deleted=0).order_by('id')
    data = []
    for s in staffs:
        orders = RepairOrder.objects.filter(deleted=0, handler_id=s.id)
        evs = RepairEvaluation.objects.filter(deleted=0,
                                              order_id__in=list(orders.values_list('id', flat=True)))
        avg = evs.aggregate(v=Avg('score'))['v']
        data.append({
            'staffId': s.id, 'staffName': s.real_name,
            'total': orders.count(),
            'processing': orders.filter(status__in=['已派单', '处理中']).count(),
            'finished': orders.filter(status__in=['已完成', '已评价']).count(),
            'avgScore': round(float(avg), 2) if avg else None,
        })
    return ok({'list': data,
               'names': [d['staffName'] for d in data],
               'totals': [d['total'] for d in data],
               'finished': [d['finished'] for d in data]})


# ============================ 费用构成 ============================
@role_required(STAFF_ROLES)
def fee_composition(request):
    rows = []
    for ft in ['物业费', '车位费']:
        qs = FeeBill.objects.filter(deleted=0, fee_type=ft)
        rec = Decimal('0')
        got = Decimal('0')
        for b in qs.values('amount', 'paid_amount'):
            amt = Decimal(str(b['amount']))
            rec += amt
            got += min(Decimal(str(b['paid_amount'])), amt)
        rows.append({'name': ft, 'value': money(rec), 'received': money(got), 'rate': _rate(got, rec)})
    return ok(rows)
