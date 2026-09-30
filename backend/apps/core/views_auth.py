from django.views.decorators.http import require_http_methods

from .models import SysUser, Owner
from .utils import ok, error, parse_body, md5, gen_token, login_required


def build_user_info(user):
    info = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'realName': user.real_name,
        'avatar': user.avatar or '',
        'phone': user.phone or '',
        'email': user.email or '',
    }
    if user.role == 'OWNER':
        owner = Owner.objects.filter(user_id=user.id, deleted=0).first()
        if owner:
            info['ownerId'] = owner.id
            info['ownerType'] = owner.owner_type
    return info


@require_http_methods(['POST'])
def login(request):
    body = parse_body(request)
    username = (body.get('username') or '').strip()
    password = body.get('password') or ''
    if not username or not password:
        return error('请输入用户名和密码', 401)
    user = SysUser.objects.filter(username=username, deleted=0).first()
    # 认证失败统一返回 401，避免泄露账号是否存在
    if not user or user.status != 1 or user.password != md5(password):
        return error('用户名或密码错误', 401)
    token = gen_token(user.id, user.role, user.username)
    return ok({'token': token, 'userInfo': build_user_info(user)})


@login_required
def info(request):
    user = SysUser.objects.filter(id=request.user_id, deleted=0).first()
    if not user:
        return error('用户不存在', 401)
    return ok(build_user_info(user))


@login_required
def change_password(request):
    body = parse_body(request)
    old_password = body.get('oldPassword') or ''
    new_password = body.get('newPassword') or ''
    if not new_password or len(new_password) < 6:
        return error('新密码长度不能少于6位')
    user = SysUser.objects.filter(id=request.user_id, deleted=0).first()
    if not user:
        return error('用户不存在', 401)
    if user.password != md5(old_password):
        return error('原密码错误')
    user.password = md5(new_password)
    user.save(update_fields=['password', 'update_time'])
    return ok(msg='密码修改成功')


@login_required
def logout(request):
    return ok(msg='已退出登录')


@login_required
def profile_update(request):
    body = parse_body(request)
    user = SysUser.objects.filter(id=request.user_id, deleted=0).first()
    if not user:
        return error('用户不存在', 401)
    user.avatar = body.get('avatar') or user.avatar
    user.phone = body.get('phone') or user.phone
    user.email = body.get('email') or user.email
    user.save(update_fields=['avatar', 'phone', 'email', 'update_time'])
    return ok(build_user_info(user), msg='个人信息已更新')


@login_required
def staff_list(request):
    """物业员工列表（派单用）"""
    if request.role not in ('ADMIN', 'STAFF'):
        return error('无权限访问该接口', 403)
    users = SysUser.objects.filter(role='STAFF', deleted=0, status=1).order_by('id')
    return ok([{'id': u.id, 'realName': u.real_name, 'phone': u.phone} for u in users])
