from datetime import datetime

from django.db.models import Q
from django.views.decorators.http import require_http_methods

from .models import (RepairOrder, RepairRecord, RepairEvaluation, Room, Owner, SysUser, OwnerRoom)
from .utils import (ok, error, parse_body, login_required, role_required, page_result,
                    to_int, now, can_transition, refresh_timeout_flags, current_owner)

REPAIR_TYPES = ['水电', '门窗', '家电', '公共设施', '其他']
URGENCY = ['一般', '紧急', '非常紧急']
ADMIN = ['ADMIN']
STAFF_ROLES = ['ADMIN', 'STAFF']


def _imgs(v):
    """接受数组或逗号分隔字符串，统一存为逗号分隔"""
    if not v:
        return ''
    if isinstance(v, list):
        return ','.join([str(i) for i in v if i])
    return str(v)


def _add_record(order_id, operator_id, operator_name, action, content, images=''):
    RepairRecord.objects.create(
        order_id=order_id, operator_id=operator_id, operator_name=operator_name,
        action=action, content=content, images=images)


def _gen_order_no():
    prefix = 'BX' + now().strftime('%Y%m%d')
    seq = RepairOrder.objects.filter(order_no__startswith=prefix).count() + 1
    while True:
        no = f'{prefix}{seq:04d}'
        if not RepairOrder.objects.filter(order_no=no).exists():
            return no
        seq += 1


def _scope(request, qs):
    """业主只能看自己的工单；员工只能看指派给自己的（管理员看全部）"""
    if request.role == 'OWNER':
        owner = current_owner(request)
        return qs.filter(owner_id=owner.id) if owner else qs.none()
    return qs


# ============================ 查询 ============================
@login_required
def repair_page(request):
    refresh_timeout_flags()
    qs = RepairOrder.objects.filter(deleted=0)
    qs = _scope(request, qs)
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    rtype = request.GET.get('repairType')
    if rtype:
        qs = qs.filter(repair_type=rtype)
    urgency = request.GET.get('urgency')
    if urgency:
        qs = qs.filter(urgency=urgency)
    if request.GET.get('timeoutOnly') in ('1', 'true'):
        qs = qs.filter(timeout_flag=1, status='待受理')
    handler_id = to_int(request.GET.get('handlerId'))
    if handler_id:
        qs = qs.filter(handler_id=handler_id)
    bid = to_int(request.GET.get('buildingId'))
    if bid:
        qs = qs.filter(room__building_id=bid)
    kw = (request.GET.get('keyword') or '').strip()
    if kw:
        qs = qs.filter(Q(order_no__contains=kw) | Q(title__contains=kw) | Q(content__contains=kw))
    # 员工默认只看指派给自己的工单
    if request.role == 'STAFF' and request.GET.get('mine') in ('1', 'true'):
        qs = qs.filter(handler_id=request.user_id)
    return page_result(request, qs.select_related('room', 'room__building', 'room__unit').order_by('-submit_time'),
                       lambda o: o.to_dict())


@login_required
def repair_mine(request):
    """员工「我的工单」/ 业主「我的报修」"""
    refresh_timeout_flags()
    if request.role == 'OWNER':
        owner = current_owner(request)
        if not owner:
            return ok({'records': [], 'total': 0, 'current': 1, 'size': 10})
        qs = RepairOrder.objects.filter(deleted=0, owner_id=owner.id)
    else:
        qs = RepairOrder.objects.filter(deleted=0, handler_id=request.user_id)
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    return page_result(request, qs.select_related('room', 'room__building', 'room__unit').order_by('-submit_time'),
                       lambda o: o.to_dict())


@login_required
def repair_detail(request, pk):
    order = RepairOrder.objects.filter(id=pk, deleted=0).first()
    if not order:
        return error('工单不存在')
    if request.role == 'OWNER':
        owner = current_owner(request)
        if not owner or order.owner_id != owner.id:
            return error('无权限查看该工单', 403)
    data = order.to_dict()
    data['records'] = [r.to_dict() for r in
                       RepairRecord.objects.filter(order_id=pk, deleted=0).order_by('create_time', 'id')]
    ev = RepairEvaluation.objects.filter(order_id=pk, deleted=0).first()
    data['evaluation'] = ev.to_dict() if ev else None
    data['allowedNext'] = [
        {'status': s, 'action': a}
        for s, a in {'待受理': {'已派单': '派单', '已驳回': '驳回', '已取消': '取消'},
                     '已派单': {'处理中': '开始处理', '已取消': '取消'},
                     '处理中': {'已完成': '完成维修'},
                     '已完成': {'已评价': '业主评价'}}.get(order.status, {}).items()
    ]
    return ok(data)


# ============================ 业主提交报修 ============================
@role_required(['OWNER', 'ADMIN'])
@require_http_methods(['POST'])
def repair_create(request):
    b = parse_body(request)
    room_id = to_int(b.get('roomId'))
    rtype = b.get('repairType')
    title = (b.get('title') or '').strip()
    if not room_id or not rtype or not title:
        return error('报修房屋、报修类型和标题为必填项')
    if rtype not in REPAIR_TYPES:
        return error('报修类型不合法')
    urgency = b.get('urgency') or '一般'
    if urgency not in URGENCY:
        return error('紧急程度不合法')
    room = Room.objects.filter(id=room_id, deleted=0).first()
    if not room:
        return error('报修房屋不存在')
    # 业主只能给自己的房屋报修
    if request.role == 'OWNER':
        owner = current_owner(request)
        if not owner:
            return error('当前账号未关联业主档案，无法报修')
        if not OwnerRoom.objects.filter(owner_id=owner.id, room_id=room_id, deleted=0, status='有效').exists():
            return error('只能对本人名下房屋提交报修', 403)
        owner_id = owner.id
    else:
        owner_id = to_int(b.get('ownerId'))
        if not owner_id:
            bind = OwnerRoom.objects.filter(room_id=room_id, deleted=0, is_primary=1).first()
            owner_id = bind.owner_id if bind else None
    obj = RepairOrder.objects.create(
        order_no=_gen_order_no(), room_id=room_id, owner_id=owner_id, repair_type=rtype,
        title=title, content=b.get('content'), urgency=urgency,
        images=_imgs(b.get('images')), status='待受理', submit_time=now())
    operator = SysUser.objects.filter(id=request.user_id).first()
    _add_record(obj.id, request.user_id, operator.real_name if operator else '业主', '提交报修',
                f'业主提交报修：{title}（{rtype} / 紧急程度：{urgency}）', obj.images)
    return ok(obj.to_dict(), msg='报修提交成功，物业将尽快受理')


# ============================ 工单流转 ============================
def _transition(request, order, target, action_name, allow_roles, extra_save=None, content='', images=''):
    """统一的合法流转入口：先校验角色，再校验状态机"""
    if request.role not in allow_roles:
        return error('无权限执行该操作', 403)
    allowed, msg = can_transition(order.status, target)
    if not allowed:
        return error(msg)
    if extra_save:
        extra_save(order)
    order.status = target
    order.save()
    operator = SysUser.objects.filter(id=request.user_id).first()
    _add_record(order.id, request.user_id, operator.real_name if operator else '物业员工',
                action_name, content, images)
    return ok(order.to_dict(), msg=f'操作成功，工单已变更为「{target}」')


@role_required(STAFF_ROLES)
@require_http_methods(['POST'])
def repair_assign(request, pk):
    """派单：待受理 -> 已派单，指派给具体物业员工"""
    order = RepairOrder.objects.filter(id=pk, deleted=0).first()
    if not order:
        return error('工单不存在')
    b = parse_body(request)
    handler_id = to_int(b.get('handlerId'))
    if not handler_id:
        return error('请选择要指派的物业员工')
    staff = SysUser.objects.filter(id=handler_id, role='STAFF', deleted=0, status=1).first()
    if not staff:
        return error('指定的物业员工不存在或已停用')

    def _set(o):
        o.handler_id = handler_id
        o.accept_time = now()
        o.assign_time = now()
        o.timeout_flag = 0
        o.remark = b.get('remark') or o.remark

    # 先确认流转合法，再补写「受理工单」记录，保证时间线为 提交→受理→派单（与历史数据一致）
    allowed, msg = can_transition(order.status, '已派单')
    if not allowed:
        return error(msg)
    operator = SysUser.objects.filter(id=request.user_id).first()
    _add_record(order.id, request.user_id, operator.real_name if operator else '物业员工',
                '受理工单', '物业服务中心已受理该报修，正在安排维修人员。')
    return _transition(request, order, '已派单', '派单',
                       ['ADMIN', 'STAFF'], _set,
                       content=f'工单已指派给维修工 {staff.real_name}（{staff.phone}）上门处理。')


@role_required(STAFF_ROLES)
@require_http_methods(['POST'])
def repair_process(request, pk):
    """已派单 -> 处理中"""
    order = RepairOrder.objects.filter(id=pk, deleted=0).first()
    if not order:
        return error('工单不存在')
    if request.role == 'STAFF' and order.handler_id != request.user_id:
        return error('该工单未指派给你，无法处理', 403)
    b = parse_body(request)

    def _set(o):
        if not o.assign_time:
            o.assign_time = now()
        if not o.handler_id:
            o.handler_id = request.user_id

    return _transition(request, order, '处理中', '处理中', STAFF_ROLES, _set,
                       content=b.get('content') or '维修人员已上门查看，正在准备材料进行维修。',
                       images=_imgs(b.get('images')))


@role_required(STAFF_ROLES)
@require_http_methods(['POST'])
def repair_finish(request, pk):
    """处理中 -> 已完成"""
    order = RepairOrder.objects.filter(id=pk, deleted=0).first()
    if not order:
        return error('工单不存在')
    if request.role == 'STAFF' and order.handler_id != request.user_id:
        return error('该工单未指派给你，无法处理', 403)
    b = parse_body(request)

    def _set(o):
        o.finish_time = now()

    return _transition(request, order, '已完成', '完成', STAFF_ROLES, _set,
                       content=b.get('content') or '维修已完成，已通知业主验收。',
                       images=_imgs(b.get('images')))


@role_required(['OWNER'])
@require_http_methods(['POST'])
def repair_evaluate(request, pk):
    """已完成 -> 已评价（仅报修业主本人）"""
    order = RepairOrder.objects.filter(id=pk, deleted=0).first()
    if not order:
        return error('工单不存在')
    owner = current_owner(request)
    if not owner or order.owner_id != owner.id:
        return error('只能评价本人提交的报修工单', 403)
    b = parse_body(request)
    score = to_int(b.get('score'))
    if score is None or score < 1 or score > 5:
        return error('请给出 1-5 星的评分')
    allowed, msg = can_transition(order.status, '已评价')
    if not allowed:
        return error(msg)
    evaluated_at = now()
    order.status = '已评价'
    order.evaluate_time = evaluated_at
    order.save()
    ev = RepairEvaluation.objects.create(
        order_id=pk, owner_id=owner.id, score=score,
        attitude_score=to_int(b.get('attitudeScore'), score),
        speed_score=to_int(b.get('speedScore'), score),
        content=b.get('content'))
    RepairEvaluation.objects.filter(id=ev.id).update(create_time=evaluated_at)
    _add_record(pk, request.user_id, owner.name, '评价',
                f'业主已确认完成并评价，综合评分 {score} 星。{b.get("content") or ""}')
    return ok(order.to_dict(), msg='感谢您的评价')


@role_required(ADMIN)
@require_http_methods(['POST'])
def repair_reject(request, pk):
    """待受理 -> 已驳回"""
    order = RepairOrder.objects.filter(id=pk, deleted=0).first()
    if not order:
        return error('工单不存在')
    b = parse_body(request)
    reason = (b.get('reason') or '').strip()
    if not reason:
        return error('请填写驳回原因')

    def _set(o):
        o.remark = reason

    return _transition(request, order, '已驳回', '驳回', ADMIN, _set, content=f'驳回原因：{reason}')


@require_http_methods(['POST'])
@login_required
def repair_cancel(request, pk):
    """待受理/已派单 -> 已取消（业主本人或管理员）"""
    order = RepairOrder.objects.filter(id=pk, deleted=0).first()
    if not order:
        return error('工单不存在')
    if request.role == 'OWNER':
        owner = current_owner(request)
        if not owner or order.owner_id != owner.id:
            return error('只能取消本人提交的报修工单', 403)
    elif request.role == 'STAFF':
        return error('物业员工无权取消工单', 403)
    b = parse_body(request)
    reason = (b.get('reason') or '').strip() or '业主主动取消该工单'

    def _set(o):
        o.remark = reason

    return _transition(request, order, '已取消', '取消', ['OWNER', 'ADMIN'], _set,
                       content=f'取消原因：{reason}')
