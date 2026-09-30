import hashlib
import json
import time
from datetime import datetime, date
from decimal import Decimal
from functools import wraps

import jwt
from django.conf import settings
from django.http import JsonResponse


# ---------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------
def now():
    return datetime.now()


def md5(text):
    return hashlib.md5(str(text).encode('utf-8')).hexdigest()


def ok(data=None, msg='success'):
    return JsonResponse({'code': 200, 'msg': msg, 'data': data})


def error(msg, code=500):
    # 401/403 使用对应 HTTP 状态码；业务异常(code=500)返回 HTTP 200
    status = code if code in (401, 403) else 200
    return JsonResponse({'code': code, 'msg': msg, 'data': None}, status=status)


def parse_body(request):
    try:
        if request.body:
            return json.loads(request.body.decode('utf-8'))
    except Exception:
        pass
    return {}


def to_int(v, default=None):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def to_decimal(v, default=None):
    try:
        return Decimal(str(v))
    except Exception:
        return default


def dec(v):
    """转成保留两位小数的 Decimal（用于金额累加运算）"""
    return Decimal(str(v if v is not None else 0)).quantize(Decimal('0.01'))


def money(v):
    """转成 float（用于 JSON 返回）"""
    return float(dec(v))


# ---------------------------------------------------------------
# JWT 鉴权
# ---------------------------------------------------------------
def gen_token(user_id, role, username):
    payload = {
        'user_id': user_id,
        'role': role,
        'username': username,
        'exp': time.time() + settings.JWT_EXPIRE_HOURS * 3600,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


def decode_token(token):
    return jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])


def get_token(request):
    auth = request.headers.get('Authorization', '') or request.META.get('HTTP_AUTHORIZATION', '')
    if auth.startswith('Bearer '):
        return auth[7:].strip()
    return None


def login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        token = get_token(request)
        if not token:
            return error('未登录或登录已过期', 401)
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return error('登录已过期，请重新登录', 401)
        except Exception:
            return error('无效的登录凭证', 401)
        request.user_id = payload.get('user_id')
        request.role = payload.get('role')
        request.username = payload.get('username')
        return view(request, *args, **kwargs)
    return wrapper


def role_required(roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.role not in roles:
                return error('无权限访问该接口', 403)
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def paginate(request, queryset):
    page = to_int(request.GET.get('current'), 1)
    size = to_int(request.GET.get('size'), 10)
    if page < 1:
        page = 1
    if size < 1 or size > 500:
        size = 10
    total = queryset.count()
    records = list(queryset[(page - 1) * size: page * size])
    return {'records': records, 'total': total, 'current': page, 'size': size}


def page_result(request, queryset, serializer=None):
    """分页 + 序列化，serializer 接收单个对象返回 dict"""
    data = paginate(request, queryset)
    if serializer:
        data['records'] = [serializer(o) for o in data['records']]
    return ok(data)


def current_owner(request):
    """当前登录用户对应的业主档案（业主角色专用）"""
    from .models import Owner
    return Owner.objects.filter(user_id=request.user_id, deleted=0).first()


# ---------------------------------------------------------------
# 隐私字段脱敏
# ---------------------------------------------------------------
# 物业管理端内部角色（可访问管理类接口）
INTERNAL_ROLES = ['ADMIN', 'STAFF']


def mask_id_card(value):
    """身份证号脱敏：保留前 6 位与后 4 位"""
    if not value:
        return value
    s = str(value).strip()
    if len(s) <= 10:
        return '*' * len(s)
    return s[:6] + '*' * (len(s) - 10) + s[-4:]


def mask_phone(value):
    """手机号脱敏：保留前 3 位与后 4 位"""
    if not value:
        return value
    s = str(value).strip()
    if len(s) != 11:
        return s
    return s[:3] + '****' + s[-4:]


def is_admin(request):
    return getattr(request, 'role', None) == 'ADMIN'


def mask_owner_dict(data, mask):
    """按需对业主字典中的身份证号 / 手机号脱敏（mask=True 时生效）"""
    if not mask or not isinstance(data, dict):
        return data
    if data.get('idCard'):
        data['idCard'] = mask_id_card(data['idCard'])
    if data.get('phone'):
        data['phone'] = mask_phone(data['phone'])
    return data


# ---------------------------------------------------------------
# 报修工单状态机
# ---------------------------------------------------------------
ORDER_STATUS = ['待受理', '已派单', '处理中', '已完成', '已评价', '已驳回', '已取消']

# 合法的状态流转：key 当前状态 -> {目标状态: 动作名}
TRANSITIONS = {
    '待受理': {'已派单': '派单', '已驳回': '驳回', '已取消': '取消'},
    '已派单': {'处理中': '开始处理', '已取消': '取消'},
    '处理中': {'已完成': '完成维修'},
    '已完成': {'已评价': '业主评价'},
    '已评价': {},
    '已驳回': {},
    '已取消': {},
}

# 终态
FINAL_STATUS = ['已评价', '已驳回', '已取消']

TIMEOUT_HOURS = 24


def can_transition(cur, nxt):
    """校验状态流转是否合法，返回 (是否允许, 提示语)"""
    if cur not in TRANSITIONS:
        return False, f'未知的工单状态「{cur}」'
    if nxt not in ORDER_STATUS:
        return False, f'未知的目标状态「{nxt}」'
    if nxt == cur:
        return False, f'工单已经处于「{cur}」状态，无需重复操作'
    allowed = TRANSITIONS[cur]
    if nxt not in allowed:
        if cur in FINAL_STATUS:
            return False, f'工单已处于终态「{cur}」，不能再变更为「{nxt}」'
        tips = '、'.join(allowed.keys()) if allowed else '无'
        return False, f'非法状态流转：工单当前为「{cur}」，不能直接变更为「{nxt}」，当前允许的流转为：{tips}'
    return True, ''


def refresh_timeout_flags():
    """把超过 24 小时仍未受理的工单标记为超时"""
    from .models import RepairOrder
    from django.db.models import Q
    from datetime import timedelta
    deadline = now() - timedelta(hours=TIMEOUT_HOURS)
    RepairOrder.objects.filter(status='待受理', deleted=0, submit_time__lt=deadline) \
        .filter(Q(timeout_flag=0)).update(timeout_flag=1)
    RepairOrder.objects.filter(status='待受理', deleted=0, submit_time__gte=deadline) \
        .filter(timeout_flag=1).update(timeout_flag=0)


# ---------------------------------------------------------------
# 物业费 / 滞纳金
# ---------------------------------------------------------------
LATE_FEE_RATE = Decimal('0.0005')  # 日滞纳金率 0.05%


def days_overdue(bill):
    """逾期天数（未结清且已过缴费截止日）"""
    if bill.status == '已缴':
        return 0
    due = bill.due_date
    if not due:
        return 0
    if isinstance(due, datetime):
        due = due.date()
    delta = (date.today() - due).days
    return delta if delta > 0 else 0


def calc_late_fee(bill):
    """滞纳金 = 逾期天数 × 日滞纳金率 × 欠费金额"""
    days = days_overdue(bill)
    if days <= 0:
        return 0.0
    unpaid = Decimal(str(bill.amount)) - Decimal(str(bill.paid_amount))
    if unpaid <= 0:
        return 0.0
    return money(unpaid * LATE_FEE_RATE * days)


def period_due_date(period):
    """账期 -> 缴费截止日（当月最后一天）"""
    y, m = int(period[:4]), int(period[5:7])
    if m == 12:
        nxt = date(y + 1, 1, 1)
    else:
        nxt = date(y, m + 1, 1)
    from datetime import timedelta
    return nxt - timedelta(days=1)


def valid_period(period):
    if not period or len(period) != 7 or period[4] != '-':
        return False
    try:
        y, m = int(period[:4]), int(period[5:7])
        return 2000 <= y <= 2100 and 1 <= m <= 12
    except ValueError:
        return False


DEFAULT_UNIT_PRICE = Decimal('2.50')  # 元/㎡/月
