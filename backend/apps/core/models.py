from django.db import models


def _d(v):
    """Decimal -> float，便于 JSON 序列化"""
    return float(v) if v is not None else None


def _dt(v):
    return v.strftime('%Y-%m-%d %H:%M:%S') if v else None


def _date(v):
    return v.strftime('%Y-%m-%d') if v else None


class SysUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=20)
    real_name = models.CharField(max_length=50, null=True)
    phone = models.CharField(max_length=20, null=True)
    email = models.CharField(max_length=100, null=True)
    avatar = models.CharField(max_length=255, null=True)
    status = models.IntegerField(default=1)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'sys_user'

    def to_dict(self):
        return {
            'id': self.id, 'username': self.username, 'role': self.role,
            'realName': self.real_name, 'phone': self.phone, 'email': self.email,
            'avatar': self.avatar, 'status': self.status,
            'createTime': _dt(self.create_time),
        }


class Building(models.Model):
    id = models.BigAutoField(primary_key=True)
    building_code = models.CharField(max_length=20, unique=True)
    building_name = models.CharField(max_length=50)
    unit_count = models.IntegerField(default=1)
    floor_count = models.IntegerField(default=6)
    building_type = models.CharField(max_length=20, default='住宅')
    build_year = models.IntegerField(null=True)
    address = models.CharField(max_length=200, null=True)
    remark = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'building'

    def to_dict(self):
        return {
            'id': self.id, 'buildingCode': self.building_code, 'buildingName': self.building_name,
            'unitCount': self.unit_count, 'floorCount': self.floor_count,
            'buildingType': self.building_type, 'buildYear': self.build_year,
            'address': self.address, 'remark': self.remark,
        }


class Unit(models.Model):
    id = models.BigAutoField(primary_key=True)
    unit_no = models.CharField(max_length=30, unique=True)
    unit_name = models.CharField(max_length=30)
    building = models.ForeignKey(Building, db_constraint=False, on_delete=models.DO_NOTHING,
                                 db_column='building_id', related_name='units')
    floor_count = models.IntegerField(default=6)
    has_elevator = models.IntegerField(default=1)
    remark = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'unit'

    def to_dict(self):
        return {
            'id': self.id, 'unitNo': self.unit_no, 'unitName': self.unit_name,
            'buildingId': self.building_id,
            'buildingName': self.building.building_name if self.building_id else '',
            'floorCount': self.floor_count, 'hasElevator': self.has_elevator,
            'remark': self.remark,
        }


class Room(models.Model):
    id = models.BigAutoField(primary_key=True)
    room_no = models.CharField(max_length=20)
    building = models.ForeignKey(Building, db_constraint=False, on_delete=models.DO_NOTHING,
                                 db_column='building_id', related_name='rooms')
    unit = models.ForeignKey(Unit, db_constraint=False, on_delete=models.DO_NOTHING,
                             db_column='unit_id', related_name='rooms')
    floor_no = models.IntegerField()
    area = models.DecimalField(max_digits=8, decimal_places=2)
    layout = models.CharField(max_length=20, default='2室1厅')
    orientation = models.CharField(max_length=20, null=True)
    status = models.CharField(max_length=20, default='自住')
    remark = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'room'

    def to_dict(self):
        return {
            'id': self.id, 'roomNo': self.room_no,
            'buildingId': self.building_id,
            'buildingName': self.building.building_name if self.building_id else '',
            'unitId': self.unit_id,
            'unitName': self.unit.unit_name if self.unit_id else '',
            'floorNo': self.floor_no, 'area': _d(self.area), 'layout': self.layout,
            'orientation': self.orientation, 'status': self.status, 'remark': self.remark,
        }

    def full_name(self):
        b = self.building.building_name if self.building_id else ''
        u = self.unit.unit_name if self.unit_id else ''
        return f'{b}{u}{self.room_no}'


class Owner(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField(null=True)
    name = models.CharField(max_length=50)
    gender = models.CharField(max_length=4, default='男')
    phone = models.CharField(max_length=20)
    id_card = models.CharField(max_length=30, null=True)
    owner_type = models.CharField(max_length=20, default='业主')
    remark = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'owner'

    def to_dict(self, mask=False):
        """mask=True 时对身份证号 / 手机号脱敏（用于非管理员视角）"""
        from .utils import mask_owner_dict
        rooms = list(OwnerRoom.objects.filter(owner_id=self.id, deleted=0, status='有效'))
        data = {
            'id': self.id, 'userId': self.user_id, 'name': self.name, 'gender': self.gender,
            'phone': self.phone, 'idCard': self.id_card, 'ownerType': self.owner_type,
            'remark': self.remark, 'createTime': _dt(self.create_time),
            'roomCount': len(rooms),
            'roomNames': [r.room.full_name() for r in rooms if r.room_id],
        }
        return mask_owner_dict(data, mask)


class OwnerRoom(models.Model):
    id = models.BigAutoField(primary_key=True)
    owner = models.ForeignKey(Owner, db_constraint=False, on_delete=models.DO_NOTHING,
                              db_column='owner_id', related_name='bindings')
    room = models.ForeignKey(Room, db_constraint=False, on_delete=models.DO_NOTHING,
                             db_column='room_id', related_name='bindings')
    relation = models.CharField(max_length=20, default='产权人')
    is_primary = models.IntegerField(default=0)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    status = models.CharField(max_length=20, default='有效')
    remark = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'owner_room'

    def to_dict(self):
        return {
            'id': self.id, 'ownerId': self.owner_id,
            'ownerName': self.owner.name if self.owner_id else '',
            'ownerPhone': self.owner.phone if self.owner_id else '',
            'roomId': self.room_id,
            'roomName': self.room.full_name() if self.room_id else '',
            'relation': self.relation, 'isPrimary': self.is_primary,
            'startDate': _date(self.start_date), 'endDate': _date(self.end_date),
            'status': self.status, 'remark': self.remark,
        }


class RepairOrder(models.Model):
    id = models.BigAutoField(primary_key=True)
    order_no = models.CharField(max_length=40, unique=True)
    room = models.ForeignKey(Room, db_constraint=False, on_delete=models.DO_NOTHING,
                             db_column='room_id', related_name='repairs')
    owner_id = models.BigIntegerField(null=True)
    repair_type = models.CharField(max_length=20)
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=500, null=True)
    urgency = models.CharField(max_length=10, default='一般')
    images = models.CharField(max_length=500, null=True)
    status = models.CharField(max_length=20, default='待受理')
    handler_id = models.BigIntegerField(null=True)
    submit_time = models.DateTimeField()
    accept_time = models.DateTimeField(null=True)
    assign_time = models.DateTimeField(null=True)
    finish_time = models.DateTimeField(null=True)
    evaluate_time = models.DateTimeField(null=True)
    timeout_flag = models.IntegerField(default=0)
    remark = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'repair_order'

    def to_dict(self):
        handler = SysUser.objects.filter(id=self.handler_id, deleted=0).first() if self.handler_id else None
        owner = Owner.objects.filter(id=self.owner_id, deleted=0).first() if self.owner_id else None
        ev = RepairEvaluation.objects.filter(order_id=self.id, deleted=0).first()
        # 待受理工单实时判断是否超时（>24 小时未受理）
        timeout = self.timeout_flag
        if self.status == '待受理' and self.submit_time:
            from .utils import now
            timeout = 1 if (now() - self.submit_time).total_seconds() >= 24 * 3600 else 0
        return {
            'id': self.id, 'orderNo': self.order_no,
            'roomId': self.room_id,
            'roomName': self.room.full_name() if self.room_id else '',
            'area': _d(self.room.area) if self.room_id else None,
            'ownerId': self.owner_id,
            'ownerName': owner.name if owner else '',
            'ownerPhone': owner.phone if owner else '',
            'repairType': self.repair_type, 'title': self.title, 'content': self.content,
            'urgency': self.urgency,
            'images': [i for i in (self.images or '').split(',') if i],
            'status': self.status,
            'handlerId': self.handler_id,
            'handlerName': handler.real_name if handler else '',
            'submitTime': _dt(self.submit_time), 'acceptTime': _dt(self.accept_time),
            'assignTime': _dt(self.assign_time), 'finishTime': _dt(self.finish_time),
            'evaluateTime': _dt(self.evaluate_time),
            'timeout': bool(timeout), 'remark': self.remark,
            'score': ev.score if ev else None,
        }


class RepairRecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    order_id = models.BigIntegerField()
    operator_id = models.BigIntegerField(null=True)
    operator_name = models.CharField(max_length=50, null=True)
    action = models.CharField(max_length=30)
    content = models.CharField(max_length=500, null=True)
    images = models.CharField(max_length=500, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'repair_record'

    def to_dict(self):
        return {
            'id': self.id, 'orderId': self.order_id, 'operatorName': self.operator_name,
            'action': self.action, 'content': self.content,
            'images': [i for i in (self.images or '').split(',') if i],
            'createTime': _dt(self.create_time),
        }


class RepairEvaluation(models.Model):
    id = models.BigAutoField(primary_key=True)
    order_id = models.BigIntegerField(unique=True)
    owner_id = models.BigIntegerField(null=True)
    score = models.IntegerField()
    attitude_score = models.IntegerField(null=True)
    speed_score = models.IntegerField(null=True)
    content = models.CharField(max_length=500, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'repair_evaluation'

    def to_dict(self):
        return {
            'id': self.id, 'orderId': self.order_id, 'ownerId': self.owner_id,
            'score': self.score, 'attitudeScore': self.attitude_score,
            'speedScore': self.speed_score, 'content': self.content,
            'createTime': _dt(self.create_time),
        }


class FeeBill(models.Model):
    id = models.BigAutoField(primary_key=True)
    bill_no = models.CharField(max_length=50, unique=True)
    room = models.ForeignKey(Room, db_constraint=False, on_delete=models.DO_NOTHING,
                             db_column='room_id', related_name='bills')
    owner_id = models.BigIntegerField(null=True)
    fee_type = models.CharField(max_length=20, default='物业费')
    period = models.CharField(max_length=7)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    months = models.IntegerField(default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    late_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='未缴')
    due_date = models.DateField()
    generate_batch = models.CharField(max_length=50, null=True)
    pay_time = models.DateTimeField(null=True)
    remark = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'fee_bill'

    def to_dict(self):
        owner = Owner.objects.filter(id=self.owner_id, deleted=0).first() if self.owner_id else None
        from .utils import calc_late_fee, days_overdue
        due_days = days_overdue(self)
        return {
            'id': self.id, 'billNo': self.bill_no,
            'roomId': self.room_id,
            'roomName': self.room.full_name() if self.room_id else '',
            'area': _d(self.room.area) if self.room_id else None,
            'ownerId': self.owner_id, 'ownerName': owner.name if owner else '',
            'ownerPhone': owner.phone if owner else '',
            'feeType': self.fee_type, 'period': self.period,
            'unitPrice': _d(self.unit_price), 'months': self.months,
            'amount': _d(self.amount), 'paidAmount': _d(self.paid_amount),
            'lateFee': calc_late_fee(self), 'lateFeeStored': _d(self.late_fee),
            'overdueDays': due_days,
            'status': self.status, 'dueDate': _date(self.due_date),
            'generateBatch': self.generate_batch, 'payTime': _dt(self.pay_time),
            'remark': self.remark, 'createTime': _dt(self.create_time),
        }


class PaymentRecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    bill_id = models.BigIntegerField()
    room_id = models.BigIntegerField()
    owner_id = models.BigIntegerField(null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    pay_method = models.CharField(max_length=20, default='微信')
    trade_no = models.CharField(max_length=60, null=True)
    pay_time = models.DateTimeField()
    operator = models.CharField(max_length=50, null=True)
    remark = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'payment_record'

    def to_dict(self):
        return {
            'id': self.id, 'billId': self.bill_id, 'amount': _d(self.amount),
            'payMethod': self.pay_method, 'tradeNo': self.trade_no,
            'payTime': _dt(self.pay_time), 'operator': self.operator, 'remark': self.remark,
        }


class ParkingSpot(models.Model):
    id = models.BigAutoField(primary_key=True)
    spot_no = models.CharField(max_length=30, unique=True)
    spot_type = models.CharField(max_length=20, default='地上')
    area = models.CharField(max_length=50, null=True)
    owner_id = models.BigIntegerField(null=True)
    room_id = models.BigIntegerField(null=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='空闲')
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    remark = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'parking_spot'

    def to_dict(self):
        owner = Owner.objects.filter(id=self.owner_id, deleted=0).first() if self.owner_id else None
        room = Room.objects.filter(id=self.room_id, deleted=0).first() if self.room_id else None
        return {
            'id': self.id, 'spotNo': self.spot_no, 'spotType': self.spot_type,
            'area': self.area, 'ownerId': self.owner_id,
            'ownerName': owner.name if owner else '',
            'ownerPhone': owner.phone if owner else '',
            'roomId': self.room_id, 'roomName': room.full_name() if room else '',
            'fee': _d(self.fee), 'status': self.status,
            'startDate': _date(self.start_date), 'endDate': _date(self.end_date),
            'remark': self.remark,
        }


class Notice(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    notice_type = models.CharField(max_length=20, default='通知')
    is_top = models.IntegerField(default=0)
    publisher_id = models.BigIntegerField(null=True)
    publish_time = models.DateTimeField()
    expire_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=20, default='已发布')
    remark = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'notice'

    def to_dict(self, user_id=None):
        read = False
        if user_id:
            read = NoticeRead.objects.filter(notice_id=self.id, user_id=user_id, deleted=0).exists()
        pub = SysUser.objects.filter(id=self.publisher_id, deleted=0).first() if self.publisher_id else None
        return {
            'id': self.id, 'title': self.title, 'content': self.content,
            'noticeType': self.notice_type, 'isTop': self.is_top,
            'publisherId': self.publisher_id,
            'publisherName': pub.real_name if pub else '物业服务中心',
            'publishTime': _dt(self.publish_time), 'expireTime': _dt(self.expire_time),
            'status': self.status, 'read': read,
        }


class NoticeRead(models.Model):
    id = models.BigAutoField(primary_key=True)
    notice_id = models.BigIntegerField()
    user_id = models.BigIntegerField()
    read_time = models.DateTimeField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'notice_read'


class Visitor(models.Model):
    id = models.BigAutoField(primary_key=True)
    visitor_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    owner_id = models.BigIntegerField(null=True)
    room_id = models.BigIntegerField(null=True)
    visit_time = models.DateTimeField()
    leave_time = models.DateTimeField(null=True)
    visit_code = models.CharField(max_length=30, unique=True)
    purpose = models.CharField(max_length=100, null=True)
    car_no = models.CharField(max_length=20, null=True)
    status = models.CharField(max_length=20, default='待到访')
    remark = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'visitor'

    def to_dict(self):
        owner = Owner.objects.filter(id=self.owner_id, deleted=0).first() if self.owner_id else None
        room = Room.objects.filter(id=self.room_id, deleted=0).first() if self.room_id else None
        return {
            'id': self.id, 'visitorName': self.visitor_name, 'phone': self.phone,
            'ownerId': self.owner_id, 'ownerName': owner.name if owner else '',
            'roomId': self.room_id, 'roomName': room.full_name() if room else '',
            'visitTime': _dt(self.visit_time), 'leaveTime': _dt(self.leave_time),
            'visitCode': self.visit_code, 'purpose': self.purpose,
            'carNo': self.car_no, 'status': self.status, 'remark': self.remark,
            'createTime': _dt(self.create_time),
        }
