import random
import string
from datetime import datetime

from django.db.models import Q
from django.views.decorators.http import require_http_methods

from .models import Visitor, Room, Owner, OwnerRoom
from .utils import (ok, error, parse_body, login_required, role_required, page_result,
                    to_int, now, current_owner)

ADMIN = ['ADMIN', 'STAFF']


def _gen_code():
    for _ in range(20):
        code = 'V' + now().strftime('%Y%m%d') + ''.join(random.choices(string.digits, k=4))
        if not Visitor.objects.filter(visit_code=code).exists():
            return code
    return 'V' + now().strftime('%Y%m%d%H%M%S')


def _parse_dt(v):
    if not v:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    return None


@login_required
def visitor_page(request):
    qs = Visitor.objects.filter(deleted=0)
    if request.role == 'OWNER':
        owner = current_owner(request)
        qs = qs.filter(owner_id=owner.id) if owner else qs.none()
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    kw = (request.GET.get('keyword') or '').strip()
    if kw:
        qs = qs.filter(Q(visitor_name__contains=kw) | Q(phone__contains=kw) |
                       Q(visit_code__contains=kw) | Q(car_no__contains=kw))
    return page_result(request, qs.order_by('-visit_time'), lambda o: o.to_dict())


@role_required(['OWNER', 'ADMIN'])
@require_http_methods(['POST'])
def visitor_create(request):
    """业主预约访客"""
    b = parse_body(request)
    name = (b.get('visitorName') or '').strip()
    phone = (b.get('phone') or '').strip()
    visit_time = _parse_dt(b.get('visitTime'))
    if not name or not phone or not visit_time:
        return error('访客姓名、联系电话和到访时间为必填项')
    if not (phone.isdigit() and len(phone) == 11):
        return error('请输入 11 位有效手机号')
    if request.role == 'OWNER':
        owner = current_owner(request)
        if not owner:
            return error('当前账号未关联业主档案，无法预约访客')
        owner_id = owner.id
    else:
        owner_id = to_int(b.get('ownerId'))
        if not owner_id:
            return error('请选择被访业主')
    room_id = to_int(b.get('roomId'))
    if room_id:
        if not OwnerRoom.objects.filter(owner_id=owner_id, room_id=room_id, deleted=0, status='有效').exists():
            return error('该房屋不属于所选业主，请重新选择')
    else:
        bind = OwnerRoom.objects.filter(owner_id=owner_id, deleted=0, status='有效', is_primary=1).first()
        room_id = bind.room_id if bind else None
    obj = Visitor.objects.create(
        visitor_name=name, phone=phone, owner_id=owner_id, room_id=room_id,
        visit_time=visit_time, visit_code=_gen_code(), purpose=b.get('purpose'),
        car_no=b.get('carNo'), status='待到访', remark=b.get('remark'))
    return ok(obj.to_dict(), msg=f'访客预约成功，访客码 {obj.visit_code}')


@role_required(ADMIN)
@require_http_methods(['PUT', 'POST'])
def visitor_update(request, pk):
    obj = Visitor.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('访客记录不存在')
    if obj.status in ('已离开',):
        return error('访客已离开，记录不可修改')
    b = parse_body(request)
    if b.get('visitorName'):
        obj.visitor_name = b['visitorName'].strip()
    if b.get('phone'):
        phone = b['phone'].strip()
        if not (phone.isdigit() and len(phone) == 11):
            return error('请输入 11 位有效手机号')
        obj.phone = phone
    vt = _parse_dt(b.get('visitTime'))
    if vt:
        obj.visit_time = vt
    obj.purpose = b.get('purpose')
    obj.car_no = b.get('carNo')
    obj.remark = b.get('remark')
    obj.save()
    return ok(obj.to_dict(), msg='修改成功')


@role_required(ADMIN)
@require_http_methods(['POST'])
def visitor_checkin(request, pk):
    obj = Visitor.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('访客记录不存在')
    if obj.status != '待到访':
        return error(f'当前状态为「{obj.status}」，只有「待到访」的访客可以登记进入')
    obj.status = '已到访'
    obj.save()
    return ok(obj.to_dict(), msg='访客已登记进入小区')


@role_required(ADMIN)
@require_http_methods(['POST'])
def visitor_checkout(request, pk):
    obj = Visitor.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('访客记录不存在')
    if obj.status != '已到访':
        return error(f'当前状态为「{obj.status}」，只有「已到访」的访客可以登记离开')
    obj.status = '已离开'
    obj.leave_time = now()
    obj.save()
    return ok(obj.to_dict(), msg='访客已登记离开')


@login_required
@require_http_methods(['POST'])
def visitor_cancel(request, pk):
    obj = Visitor.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('访客记录不存在')
    if request.role == 'OWNER':
        owner = current_owner(request)
        if not owner or obj.owner_id != owner.id:
            return error('只能取消本人预约的访客', 403)
    elif request.role == 'STAFF':
        return error('物业员工无权取消访客预约', 403)
    if obj.status != '待到访':
        return error(f'当前状态为「{obj.status}」，只有「待到访」的预约可以取消')
    obj.status = '已取消'
    obj.save()
    return ok(obj.to_dict(), msg='预约已取消')


@role_required(ADMIN)
@require_http_methods(['DELETE', 'POST'])
def visitor_delete(request, pk):
    obj = Visitor.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('访客记录不存在')
    obj.deleted = 1
    obj.save(update_fields=['deleted', 'update_time'])
    return ok(msg='删除成功')
