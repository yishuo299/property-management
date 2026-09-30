from datetime import datetime

from django.db.models import Q
from django.views.decorators.http import require_http_methods

from .models import ParkingSpot, Owner, Room
from .utils import (ok, error, parse_body, login_required, role_required, page_result,
                    to_int, to_decimal, now, INTERNAL_ROLES)

ADMIN = ['ADMIN']
SPOT_TYPES = ['地上', '地下', '固定', '临时']
SPOT_STATUS = ['空闲', '已租', '停用']


@role_required(INTERNAL_ROLES)
def parking_page(request):
    qs = ParkingSpot.objects.filter(deleted=0)
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    stype = request.GET.get('spotType')
    if stype:
        qs = qs.filter(spot_type=stype)
    kw = (request.GET.get('keyword') or '').strip()
    if kw:
        qs = qs.filter(Q(spot_no__contains=kw) | Q(area__contains=kw))
    return page_result(request, qs.order_by('spot_no'), lambda o: o.to_dict())


@role_required(INTERNAL_ROLES)
def parking_list(request):
    qs = ParkingSpot.objects.filter(deleted=0).order_by('spot_no')
    return ok([p.to_dict() for p in qs])


@login_required
def parking_mine(request):
    """业主「我的车位」"""
    from .utils import current_owner
    owner = current_owner(request)
    if not owner:
        return ok([])
    qs = ParkingSpot.objects.filter(deleted=0, owner_id=owner.id).order_by('spot_no')
    return ok([p.to_dict() for p in qs])


@role_required(ADMIN)
@require_http_methods(['POST'])
def parking_create(request):
    b = parse_body(request)
    spot_no = (b.get('spotNo') or '').strip()
    if not spot_no:
        return error('车位编号为必填项')
    if ParkingSpot.objects.filter(spot_no=spot_no, deleted=0).exists():
        return error('车位编号已存在')
    stype = b.get('spotType') or '地上'
    if stype not in SPOT_TYPES:
        return error('车位类型不合法')
    obj = ParkingSpot.objects.create(
        spot_no=spot_no, spot_type=stype, area=b.get('area'),
        fee=to_decimal(b.get('fee'), 0), status='空闲', remark=b.get('remark'))
    return ok(obj.to_dict(), msg='新增成功')


@role_required(ADMIN)
@require_http_methods(['PUT', 'POST'])
def parking_update(request, pk):
    obj = ParkingSpot.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('车位不存在')
    b = parse_body(request)
    if b.get('spotType') and b['spotType'] not in SPOT_TYPES:
        return error('车位类型不合法')
    obj.spot_type = b.get('spotType') or obj.spot_type
    obj.area = b.get('area')
    obj.fee = to_decimal(b.get('fee'), obj.fee)
    if b.get('status'):
        if b['status'] not in SPOT_STATUS:
            return error('车位状态不合法')
        obj.status = b['status']
    obj.remark = b.get('remark')
    obj.save()
    return ok(obj.to_dict(), msg='修改成功')


@role_required(ADMIN)
@require_http_methods(['POST'])
def parking_bind(request, pk):
    """车位绑定业主"""
    obj = ParkingSpot.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('车位不存在')
    if obj.status == '已租':
        return error('该车位已绑定业主，请先释放')
    b = parse_body(request)
    owner_id = to_int(b.get('ownerId'))
    if not owner_id:
        return error('请选择要绑定的业主')
    owner = Owner.objects.filter(id=owner_id, deleted=0).first()
    if not owner:
        return error('业主不存在')
    room_id = to_int(b.get('roomId'))
    if room_id and not Room.objects.filter(id=room_id, deleted=0).exists():
        return error('房屋不存在')
    start = b.get('startDate')
    end = b.get('endDate')
    obj.owner_id = owner_id
    obj.room_id = room_id or None
    obj.status = '已租'
    obj.start_date = datetime.strptime(start, '%Y-%m-%d').date() if start else now().date()
    obj.end_date = datetime.strptime(end, '%Y-%m-%d').date() if end else None
    obj.save()
    return ok(obj.to_dict(), msg=f'车位已绑定给业主 {owner.name}')


@role_required(ADMIN)
@require_http_methods(['POST'])
def parking_release(request, pk):
    obj = ParkingSpot.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('车位不存在')
    if obj.status != '已租':
        return error('该车位当前未绑定业主')
    obj.owner_id = None
    obj.room_id = None
    obj.status = '空闲'
    obj.start_date = None
    obj.end_date = None
    obj.save()
    return ok(obj.to_dict(), msg='车位已释放')


@role_required(ADMIN)
@require_http_methods(['DELETE', 'POST'])
def parking_delete(request, pk):
    obj = ParkingSpot.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('车位不存在')
    if obj.status == '已租':
        return error('已绑定业主的车位不允许删除，请先释放')
    obj.deleted = 1
    obj.save(update_fields=['deleted', 'update_time'])
    return ok(msg='删除成功')
