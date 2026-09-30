from datetime import datetime

from django.db.models import Q
from django.views.decorators.http import require_http_methods

from .models import Building, Unit, Room, Owner, OwnerRoom, SysUser
from .utils import (ok, error, parse_body, login_required, role_required, page_result,
                    to_int, to_decimal, now, INTERNAL_ROLES, mask_owner_dict, mask_phone,
                    current_owner)

ADMIN = ['ADMIN']


# ============================ 楼栋 ============================
@role_required(INTERNAL_ROLES)
def building_list(request):
    qs = Building.objects.filter(deleted=0).order_by('building_code')
    return ok([b.to_dict() for b in qs])


@role_required(INTERNAL_ROLES)
def building_page(request):
    qs = Building.objects.filter(deleted=0)
    kw = (request.GET.get('keyword') or '').strip()
    if kw:
        qs = qs.filter(Q(building_name__contains=kw) | Q(building_code__contains=kw))
    btype = request.GET.get('buildingType')
    if btype:
        qs = qs.filter(building_type=btype)
    return page_result(request, qs.order_by('building_code'), lambda o: o.to_dict())


@role_required(ADMIN)
@require_http_methods(['POST'])
def building_create(request):
    b = parse_body(request)
    name = (b.get('buildingName') or '').strip()
    code = (b.get('buildingCode') or '').strip()
    if not name or not code:
        return error('楼栋编号和名称为必填项')
    if Building.objects.filter(building_code=code, deleted=0).exists():
        return error('楼栋编号已存在')
    obj = Building.objects.create(
        building_code=code, building_name=name,
        unit_count=to_int(b.get('unitCount'), 1), floor_count=to_int(b.get('floorCount'), 6),
        building_type=b.get('buildingType') or '住宅',
        build_year=to_int(b.get('buildYear')), address=b.get('address'), remark=b.get('remark'))
    return ok(obj.to_dict(), msg='新增成功')


@role_required(ADMIN)
@require_http_methods(['PUT', 'POST'])
def building_update(request, pk):
    obj = Building.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('楼栋不存在')
    b = parse_body(request)
    name = (b.get('buildingName') or '').strip()
    if not name:
        return error('楼栋名称不能为空')
    obj.building_name = name
    obj.unit_count = to_int(b.get('unitCount'), obj.unit_count)
    obj.floor_count = to_int(b.get('floorCount'), obj.floor_count)
    obj.building_type = b.get('buildingType') or obj.building_type
    obj.build_year = to_int(b.get('buildYear'), obj.build_year)
    obj.address = b.get('address')
    obj.remark = b.get('remark')
    obj.save()
    return ok(obj.to_dict(), msg='修改成功')


@role_required(ADMIN)
@require_http_methods(['DELETE', 'POST'])
def building_delete(request, pk):
    obj = Building.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('楼栋不存在')
    if Room.objects.filter(building_id=pk, deleted=0).exists():
        return error('该楼栋下仍有房屋，无法删除')
    obj.deleted = 1
    obj.save(update_fields=['deleted', 'update_time'])
    return ok(msg='删除成功')


# ============================ 单元 ============================
@role_required(INTERNAL_ROLES)
def unit_list(request):
    qs = Unit.objects.filter(deleted=0)
    bid = to_int(request.GET.get('buildingId'))
    if bid:
        qs = qs.filter(building_id=bid)
    return ok([u.to_dict() for u in qs.select_related('building').order_by('unit_no')])


@role_required(INTERNAL_ROLES)
def unit_page(request):
    qs = Unit.objects.filter(deleted=0)
    bid = to_int(request.GET.get('buildingId'))
    if bid:
        qs = qs.filter(building_id=bid)
    kw = (request.GET.get('keyword') or '').strip()
    if kw:
        qs = qs.filter(Q(unit_name__contains=kw) | Q(unit_no__contains=kw))
    return page_result(request, qs.select_related('building').order_by('unit_no'), lambda o: o.to_dict())


@role_required(ADMIN)
@require_http_methods(['POST'])
def unit_create(request):
    b = parse_body(request)
    bid = to_int(b.get('buildingId'))
    name = (b.get('unitName') or '').strip()
    if not bid or not name:
        return error('所属楼栋和单元名称为必填项')
    building = Building.objects.filter(id=bid, deleted=0).first()
    if not building:
        return error('所属楼栋不存在')
    if Unit.objects.filter(building_id=bid, unit_name=name, deleted=0).exists():
        return error('该楼栋下已存在同名单元')
    seq = Unit.objects.filter(building_id=bid, deleted=0).count() + 1
    obj = Unit.objects.create(
        unit_no=f'{building.building_code}-{seq}', unit_name=name, building_id=bid,
        floor_count=to_int(b.get('floorCount'), building.floor_count),
        has_elevator=to_int(b.get('hasElevator'), 1), remark=b.get('remark'))
    return ok(obj.to_dict(), msg='新增成功')


@role_required(ADMIN)
@require_http_methods(['PUT', 'POST'])
def unit_update(request, pk):
    obj = Unit.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('单元不存在')
    b = parse_body(request)
    if b.get('unitName'):
        obj.unit_name = b['unitName'].strip()
    obj.floor_count = to_int(b.get('floorCount'), obj.floor_count)
    obj.has_elevator = to_int(b.get('hasElevator'), obj.has_elevator)
    obj.remark = b.get('remark')
    obj.save()
    return ok(obj.to_dict(), msg='修改成功')


@role_required(ADMIN)
@require_http_methods(['DELETE', 'POST'])
def unit_delete(request, pk):
    obj = Unit.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('单元不存在')
    if Room.objects.filter(unit_id=pk, deleted=0).exists():
        return error('该单元下仍有房屋，无法删除')
    obj.deleted = 1
    obj.save(update_fields=['deleted', 'update_time'])
    return ok(msg='删除成功')


# ============================ 房屋 ============================
@role_required(INTERNAL_ROLES)
def room_list(request):
    qs = Room.objects.filter(deleted=0)
    bid = to_int(request.GET.get('buildingId'))
    if bid:
        qs = qs.filter(building_id=bid)
    uid = to_int(request.GET.get('unitId'))
    if uid:
        qs = qs.filter(unit_id=uid)
    return ok([r.to_dict() for r in qs.select_related('building', 'unit').order_by('id')[:2000]])


@role_required(INTERNAL_ROLES)
def room_page(request):
    qs = Room.objects.filter(deleted=0)
    bid = to_int(request.GET.get('buildingId'))
    if bid:
        qs = qs.filter(building_id=bid)
    uid = to_int(request.GET.get('unitId'))
    if uid:
        qs = qs.filter(unit_id=uid)
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    layout = request.GET.get('layout')
    if layout:
        qs = qs.filter(layout=layout)
    kw = (request.GET.get('keyword') or '').strip()
    if kw:
        qs = qs.filter(room_no__contains=kw)
    return page_result(request, qs.select_related('building', 'unit').order_by('building_id', 'unit_id', 'room_no'),
                       lambda o: o.to_dict())


@role_required(ADMIN)
@require_http_methods(['POST'])
def room_create(request):
    b = parse_body(request)
    uid = to_int(b.get('unitId'))
    room_no = (b.get('roomNo') or '').strip()
    area = to_decimal(b.get('area'))
    if not uid or not room_no or area is None:
        return error('单元、房号和建筑面积为必填项')
    unit = Unit.objects.filter(id=uid, deleted=0).first()
    if not unit:
        return error('所属单元不存在')
    if area <= 0:
        return error('建筑面积必须大于 0')
    if Room.objects.filter(unit_id=uid, room_no=room_no, deleted=0).exists():
        return error('该单元下房号已存在')
    obj = Room.objects.create(
        room_no=room_no, building_id=unit.building_id, unit_id=uid,
        floor_no=to_int(b.get('floorNo'), int(room_no[0]) if room_no[0].isdigit() else 1),
        area=area, layout=b.get('layout') or '2室1厅',
        orientation=b.get('orientation'), status=b.get('status') or '自住', remark=b.get('remark'))
    return ok(obj.to_dict(), msg='新增成功')


@role_required(ADMIN)
@require_http_methods(['PUT', 'POST'])
def room_update(request, pk):
    obj = Room.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('房屋不存在')
    b = parse_body(request)
    area = to_decimal(b.get('area'), obj.area)
    if area is None or area <= 0:
        return error('建筑面积必须大于 0')
    obj.area = area
    obj.floor_no = to_int(b.get('floorNo'), obj.floor_no)
    obj.layout = b.get('layout') or obj.layout
    obj.orientation = b.get('orientation')
    obj.status = b.get('status') or obj.status
    obj.remark = b.get('remark')
    obj.save()
    return ok(obj.to_dict(), msg='修改成功')


@role_required(ADMIN)
@require_http_methods(['DELETE', 'POST'])
def room_delete(request, pk):
    obj = Room.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('房屋不存在')
    obj.deleted = 1
    obj.save(update_fields=['deleted', 'update_time'])
    return ok(msg='删除成功')


# ============================ 业主 ============================
@role_required(ADMIN)
def owner_list(request):
    """业主下拉列表（含身份证号等敏感信息，仅管理员可用）"""
    qs = Owner.objects.filter(deleted=0).order_by('id')
    kw = (request.GET.get('keyword') or '').strip()
    if kw:
        qs = qs.filter(Q(name__contains=kw) | Q(phone__contains=kw))
    return ok([o.to_dict() for o in qs])


@role_required(ADMIN)
def owner_page(request):
    """业主档案分页（含身份证号等敏感信息，仅管理员可用）"""
    qs = Owner.objects.filter(deleted=0)
    kw = (request.GET.get('keyword') or '').strip()
    if kw:
        qs = qs.filter(Q(name__contains=kw) | Q(phone__contains=kw) | Q(id_card__contains=kw))
    otype = request.GET.get('ownerType')
    if otype:
        qs = qs.filter(owner_type=otype)
    return page_result(request, qs.order_by('id'), lambda o: o.to_dict())


@login_required
def owner_detail(request, pk):
    """管理员可查看任意业主档案；业主仅能查看本人档案（身份证/手机号脱敏）"""
    obj = Owner.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('业主不存在')
    if request.role == 'ADMIN':
        mask = False
    elif request.role == 'OWNER':
        me = current_owner(request)
        if not me or me.id != obj.id:
            return error('只能查看本人的业主档案', 403)
        mask = True
    else:
        return error('无权限访问该接口', 403)
    data = obj.to_dict(mask=mask)
    binds = OwnerRoom.objects.filter(owner_id=pk, deleted=0).select_related(
        'room', 'room__building', 'room__unit')
    bindings = []
    for b in binds:
        bd = b.to_dict()
        if mask and bd.get('ownerPhone'):
            bd['ownerPhone'] = mask_phone(bd['ownerPhone'])
        bindings.append(bd)
    data['bindings'] = bindings
    return ok(data)


@role_required(ADMIN)
@require_http_methods(['POST'])
def owner_create(request):
    b = parse_body(request)
    name = (b.get('name') or '').strip()
    phone = (b.get('phone') or '').strip()
    if not name or not phone:
        return error('姓名和联系电话为必填项')
    if not (phone.isdigit() and len(phone) == 11):
        return error('请输入 11 位有效手机号')
    if Owner.objects.filter(phone=phone, deleted=0).exists():
        return error('该手机号已登记为业主')
    username = (b.get('username') or '').strip()
    user_id = None
    if username:
        if SysUser.objects.filter(username=username, deleted=0).exists():
            return error('登录账号已存在')
        from .utils import md5
        u = SysUser.objects.create(username=username, password=md5(b.get('password') or '123456'),
                                   role='OWNER', real_name=name, phone=phone)
        user_id = u.id
    obj = Owner.objects.create(
        user_id=user_id, name=name, gender=b.get('gender') or '男', phone=phone,
        id_card=b.get('idCard'), owner_type=b.get('ownerType') or '业主', remark=b.get('remark'))
    return ok(obj.to_dict(), msg='新增成功')


@role_required(ADMIN)
@require_http_methods(['PUT', 'POST'])
def owner_update(request, pk):
    obj = Owner.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('业主不存在')
    b = parse_body(request)
    if b.get('name'):
        obj.name = b['name'].strip()
    if b.get('phone'):
        phone = b['phone'].strip()
        if not (phone.isdigit() and len(phone) == 11):
            return error('请输入 11 位有效手机号')
        if Owner.objects.filter(phone=phone, deleted=0).exclude(id=pk).exists():
            return error('该手机号已被其他业主使用')
        obj.phone = phone
    obj.gender = b.get('gender') or obj.gender
    obj.id_card = b.get('idCard')
    obj.owner_type = b.get('ownerType') or obj.owner_type
    obj.remark = b.get('remark')
    obj.save()
    return ok(obj.to_dict(), msg='修改成功')


@role_required(ADMIN)
@require_http_methods(['DELETE', 'POST'])
def owner_delete(request, pk):
    obj = Owner.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('业主不存在')
    if OwnerRoom.objects.filter(owner_id=pk, deleted=0, status='有效').exists():
        return error('该业主仍绑定有房屋，请先解除绑定')
    obj.deleted = 1
    obj.save(update_fields=['deleted', 'update_time'])
    return ok(msg='删除成功')


@role_required(INTERNAL_ROLES)
def owner_room_bindings(request):
    """房屋维度的绑定关系（供物业管理端查询房屋归属）"""
    rid = to_int(request.GET.get('roomId'))
    if not rid:
        return error('缺少房屋参数')
    qs = OwnerRoom.objects.filter(room_id=rid, deleted=0).select_related('owner', 'room')
    return ok([b.to_dict() for b in qs.order_by('-is_primary', 'id')])


@role_required(ADMIN)
@require_http_methods(['POST'])
def owner_bind(request):
    """业主绑定房屋（支持一户多业主）"""
    b = parse_body(request)
    owner_id = to_int(b.get('ownerId'))
    room_id = to_int(b.get('roomId'))
    if not owner_id or not room_id:
        return error('请选择业主和房屋')
    if not Owner.objects.filter(id=owner_id, deleted=0).exists():
        return error('业主不存在')
    if not Room.objects.filter(id=room_id, deleted=0).exists():
        return error('房屋不存在')
    if OwnerRoom.objects.filter(owner_id=owner_id, room_id=room_id, deleted=0, status='有效').exists():
        return error('该业主已绑定此房屋，请勿重复绑定')
    is_primary = to_int(b.get('isPrimary'), 0)
    if is_primary:
        OwnerRoom.objects.filter(room_id=room_id, deleted=0, is_primary=1).update(is_primary=0)
    start = b.get('startDate')
    obj = OwnerRoom.objects.create(
        owner_id=owner_id, room_id=room_id, relation=b.get('relation') or '产权人',
        is_primary=is_primary,
        start_date=datetime.strptime(start, '%Y-%m-%d').date() if start else now().date(),
        status='有效', remark=b.get('remark'))
    return ok(obj.to_dict(), msg='绑定成功')


@role_required(ADMIN)
@require_http_methods(['POST'])
def owner_unbind(request, pk):
    b = parse_body(request)
    obj = OwnerRoom.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('绑定关系不存在')
    if obj.is_primary == 1:
        return error('主产权人关系不能直接解除，请先办理过户或指定新的主产权人')
    obj.status = '已退租'
    obj.end_date = now().date()
    obj.remark = b.get('remark') or '解除绑定'
    obj.save()
    return ok(msg='已解除绑定')


@role_required(ADMIN)
@require_http_methods(['POST'])
def owner_transfer(request):
    """房屋过户：原业主关系置为已过户，新业主成为主产权人"""
    b = parse_body(request)
    room_id = to_int(b.get('roomId'))
    new_owner_id = to_int(b.get('newOwnerId'))
    transfer_date = b.get('transferDate')
    if not room_id or not new_owner_id:
        return error('请选择房屋和新业主')
    room = Room.objects.filter(id=room_id, deleted=0).first()
    if not room:
        return error('房屋不存在')
    new_owner = Owner.objects.filter(id=new_owner_id, deleted=0).first()
    if not new_owner:
        return error('新业主不存在')
    old = OwnerRoom.objects.filter(room_id=room_id, deleted=0, is_primary=1).first()
    if old and old.owner_id == new_owner_id:
        return error('新业主已是该房屋的产权人，无需过户')
    if OwnerRoom.objects.filter(room_id=room_id, owner_id=new_owner_id, deleted=0, status='有效').exists():
        return error('新业主已绑定该房屋，请直接指定为主产权人')
    tdate = datetime.strptime(transfer_date, '%Y-%m-%d').date() if transfer_date else now().date()
    old_name = ''
    if old:
        old_name = old.owner.name
        old.status = '已过户'
        old.is_primary = 0
        old.end_date = tdate
        old.remark = f'房屋已过户给{new_owner.name}'
        old.save()
    obj = OwnerRoom.objects.create(
        owner_id=new_owner_id, room_id=room_id, relation='产权人', is_primary=1,
        start_date=tdate, status='有效',
        remark=f'过户自{old_name}' if old_name else '初始登记')
    return ok(obj.to_dict(), msg=f'过户成功，{room.full_name()} 产权人已变更为 {new_owner.name}')
