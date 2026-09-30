from datetime import datetime

from django.db.models import Q
from django.views.decorators.http import require_http_methods

from .models import Notice, NoticeRead
from .utils import ok, error, parse_body, login_required, role_required, page_result, to_int, now

ADMIN = ['ADMIN']
NOTICE_TYPES = ['通知', '提醒', '活动', '紧急']


def _active(qs):
    """业主可见：已发布且未过期"""
    return qs.filter(status='已发布').filter(Q(expire_time__isnull=True) | Q(expire_time__gte=now()))


@login_required
def notice_page(request):
    """管理员分页管理公告；业主/员工只看已发布且在有效期内的"""
    qs = Notice.objects.filter(deleted=0)
    if request.role != 'ADMIN':
        qs = _active(qs)
    ntype = request.GET.get('noticeType')
    if ntype:
        qs = qs.filter(notice_type=ntype)
    status = request.GET.get('status')
    if status and request.role == 'ADMIN':
        qs = qs.filter(status=status)
    if request.GET.get('unreadOnly') in ('1', 'true'):
        read_ids = list(NoticeRead.objects.filter(user_id=request.user_id, deleted=0)
                        .values_list('notice_id', flat=True))
        qs = qs.exclude(id__in=read_ids)
    kw = (request.GET.get('keyword') or '').strip()
    if kw:
        qs = qs.filter(Q(title__contains=kw) | Q(content__contains=kw))
    return page_result(request, qs.order_by('-is_top', '-publish_time'),
                       lambda o: o.to_dict(request.user_id))


@login_required
def notice_list(request):
    """业主首页公告列表"""
    qs = _active(Notice.objects.filter(deleted=0)).order_by('-is_top', '-publish_time')[:20]
    return ok([n.to_dict(request.user_id) for n in qs])


@login_required
def notice_detail(request, pk):
    n = Notice.objects.filter(id=pk, deleted=0).first()
    if not n:
        return error('公告不存在')
    if request.role != 'ADMIN' and n.status != '已发布':
        return error('该公告不可见', 403)
    # 阅读即标记已读
    if not NoticeRead.objects.filter(notice_id=pk, user_id=request.user_id, deleted=0).exists():
        NoticeRead.objects.create(notice_id=pk, user_id=request.user_id, read_time=now())
    return ok(n.to_dict(request.user_id))


@login_required
def notice_read(request, pk):
    n = Notice.objects.filter(id=pk, deleted=0).first()
    if not n:
        return error('公告不存在')
    if not NoticeRead.objects.filter(notice_id=pk, user_id=request.user_id, deleted=0).exists():
        NoticeRead.objects.create(notice_id=pk, user_id=request.user_id, read_time=now())
    return ok(msg='已标记为已读')


@login_required
def notice_unread_count(request):
    ids = list(NoticeRead.objects.filter(user_id=request.user_id, deleted=0).values_list('notice_id', flat=True))
    count = _active(Notice.objects.filter(deleted=0)).exclude(id__in=ids).count()
    return ok({'unread': count})


@role_required(ADMIN)
@require_http_methods(['POST'])
def notice_create(request):
    b = parse_body(request)
    title = (b.get('title') or '').strip()
    content = (b.get('content') or '').strip()
    if not title or not content:
        return error('公告标题和内容为必填项')
    ntype = b.get('noticeType') or '通知'
    if ntype not in NOTICE_TYPES:
        return error('公告类型不合法')
    obj = Notice.objects.create(
        title=title, content=content, notice_type=ntype,
        is_top=to_int(b.get('isTop'), 0), publisher_id=request.user_id,
        publish_time=now(), expire_time=None, status=b.get('status') or '已发布',
        remark=b.get('remark'))
    return ok(obj.to_dict(request.user_id), msg='发布成功')


@role_required(ADMIN)
@require_http_methods(['PUT', 'POST'])
def notice_update(request, pk):
    obj = Notice.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('公告不存在')
    b = parse_body(request)
    if b.get('title'):
        obj.title = b['title'].strip()
    if b.get('content'):
        obj.content = b['content'].strip()
    if b.get('noticeType'):
        if b['noticeType'] not in NOTICE_TYPES:
            return error('公告类型不合法')
        obj.notice_type = b['noticeType']
    obj.is_top = to_int(b.get('isTop'), obj.is_top)
    if b.get('status'):
        obj.status = b['status']
    obj.remark = b.get('remark')
    obj.save()
    return ok(obj.to_dict(request.user_id), msg='修改成功')


@role_required(ADMIN)
@require_http_methods(['DELETE', 'POST'])
def notice_delete(request, pk):
    obj = Notice.objects.filter(id=pk, deleted=0).first()
    if not obj:
        return error('公告不存在')
    obj.deleted = 1
    obj.save(update_fields=['deleted', 'update_time'])
    return ok(msg='删除成功')
