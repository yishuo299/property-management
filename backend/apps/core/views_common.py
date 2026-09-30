import os
import uuid
from io import BytesIO
from urllib.parse import quote

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from .models import RepairOrder, FeeBill, Owner
from .utils import ok, error, login_required, role_required, to_int, current_owner, calc_late_fee, dec

ADMIN = ['ADMIN']
STAFF_ROLES = ['ADMIN', 'STAFF']

# 文件头魔数，用于校验上传内容确为对应格式图片
_IMAGE_MAGIC = {
    '.jpg': [b'\xff\xd8\xff'],
    '.jpeg': [b'\xff\xd8\xff'],
    '.png': [b'\x89PNG\r\n\x1a\n'],
    '.gif': [b'GIF87a', b'GIF89a'],
    '.webp': [b'RIFF'],
}


def _looks_like(ext, head):
    if ext == '.webp':
        return head[:4] == b'RIFF' and head[8:12] == b'WEBP'
    return any(head.startswith(m) for m in _IMAGE_MAGIC.get(ext, []))


@login_required
@require_http_methods(['POST'])
def upload(request):
    file = request.FILES.get('file')
    if not file:
        return error('请选择要上传的文件')
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in _IMAGE_MAGIC:
        return error('仅支持 jpg/png/gif/webp 图片格式')
    head = file.read(12)
    file.seek(0)
    if not _looks_like(ext, head):
        return error('文件内容与图片格式不符，请上传真实图片')
    if file.size > 5 * 1024 * 1024:
        return error('图片大小不能超过 5MB')
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(upload_dir, name), 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)
    return ok({'url': f"{settings.MEDIA_URL}uploads/{name}"}, msg='上传成功')


# ---------------------------------------------------------------
# Excel 导出
# ---------------------------------------------------------------
HEAD_FILL = PatternFill('solid', fgColor='EA580C')
HEAD_FONT = Font(color='FFFFFF', bold=True, size=11)


def _xlsx_response(filename, title, headers, rows, widths=None):
    wb = Workbook()
    ws = wb.active
    ws.title = title
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
        cell.alignment = Alignment(horizontal='center', vertical='center')
    for r in rows:
        ws.append(r)
    for i in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(i)].width = (widths[i - 1] if widths else 16)
    ws.freeze_panes = 'A2'
    buf = BytesIO()
    wb.save(buf)
    resp = HttpResponse(
        buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    return resp


@role_required(STAFF_ROLES)
def export_repairs(request):
    qs = RepairOrder.objects.filter(deleted=0).select_related('room', 'room__building', 'room__unit')
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    rtype = request.GET.get('repairType')
    if rtype:
        qs = qs.filter(repair_type=rtype)
    kw = (request.GET.get('keyword') or '').strip()
    if kw:
        qs = qs.filter(Q(order_no__contains=kw) | Q(title__contains=kw))
    headers = ['工单号', '房屋', '报修类型', '报修标题', '紧急程度', '状态', '处理人',
               '提交时间', '受理时间', '完成时间', '是否超时', '评分']
    rows = []
    for o in qs.order_by('-submit_time'):
        d = o.to_dict()
        rows.append([d['orderNo'], d['roomName'], d['repairType'], d['title'], d['urgency'],
                     d['status'], d['handlerName'], d['submitTime'], d['acceptTime'] or '',
                     d['finishTime'] or '', '是' if d['timeout'] else '否', d['score'] or ''])
    return _xlsx_response('报修工单明细.xlsx', '报修工单', headers, rows,
                          [22, 24, 10, 26, 10, 10, 10, 20, 20, 20, 9, 7])


@role_required(STAFF_ROLES)
def export_bills(request):
    qs = FeeBill.objects.filter(deleted=0).select_related('room', 'room__building', 'room__unit')
    period = request.GET.get('period')
    if period:
        qs = qs.filter(period=period)
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    bid = to_int(request.GET.get('buildingId'))
    if bid:
        qs = qs.filter(room__building_id=bid)
    headers = ['账单号', '房屋', '业主', '费用类型', '账期', '单价', '月数', '应缴金额',
               '已缴金额', '滞纳金', '欠费金额', '状态', '缴费截止日']
    rows = []
    from decimal import Decimal
    for b in qs.order_by('-period', 'room_id'):
        d = b.to_dict()
        # 欠费 = 应缴 + 滞纳金 - 已缴
        remaining = dec(d['amount']) + dec(d['lateFee']) - dec(d['paidAmount'])
        rows.append([d['billNo'], d['roomName'], d['ownerName'], d['feeType'], d['period'],
                     d['unitPrice'], d['months'], d['amount'], d['paidAmount'], d['lateFee'],
                     float(max(Decimal('0'), remaining)), d['status'], d['dueDate']])
    return _xlsx_response('物业费账单明细.xlsx', '物业费账单', headers, rows,
                          [24, 24, 10, 10, 10, 9, 7, 12, 12, 10, 12, 10, 14])


@role_required(ADMIN)
def export_owners(request):
    qs = Owner.objects.filter(deleted=0).order_by('id')
    headers = ['姓名', '性别', '联系电话', '身份证号', '业主类型', '名下房屋', '房屋数量', '备注']
    rows = []
    for o in qs:
        d = o.to_dict()
        rows.append([d['name'], d['gender'], d['phone'], d['idCard'] or '', d['ownerType'],
                     '、'.join(d['roomNames']), d['roomCount'], d['remark'] or ''])
    return _xlsx_response('业主信息.xlsx', '业主信息', headers, rows,
                          [10, 7, 14, 22, 10, 46, 10, 24])
