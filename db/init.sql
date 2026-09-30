-- =============================================================
--  社区物业管理与报修系统  property_management
--  数据库初始化脚本（可重复执行）
--  MySQL 8.0+ / 9.x   引擎 InnoDB  字符集 utf8mb4
-- =============================================================

DROP DATABASE IF EXISTS property_management;
CREATE DATABASE property_management DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE property_management;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -------------------------------------------------------------
-- 1. 用户表（管理员 ADMIN / 物业员工 STAFF / 业主 OWNER）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS sys_user;
CREATE TABLE sys_user (
  id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
  username    VARCHAR(50)  NOT NULL COMMENT '登录账号',
  password    VARCHAR(100) NOT NULL COMMENT '密码(MD5)',
  role        VARCHAR(20)  NOT NULL COMMENT '角色 ADMIN/STAFF/OWNER',
  real_name   VARCHAR(50)           DEFAULT NULL COMMENT '姓名',
  phone       VARCHAR(20)           DEFAULT NULL COMMENT '手机号',
  email       VARCHAR(100)          DEFAULT NULL COMMENT '邮箱',
  avatar      VARCHAR(255)          DEFAULT NULL COMMENT '头像',
  status      TINYINT      NOT NULL DEFAULT 1 COMMENT '状态 1正常 0停用',
  create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted     TINYINT      NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='系统用户表';

-- -------------------------------------------------------------
-- 2. 楼栋表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS building;
CREATE TABLE building (
  id            BIGINT      NOT NULL AUTO_INCREMENT,
  building_code VARCHAR(20) NOT NULL COMMENT '楼栋编号',
  building_name VARCHAR(50) NOT NULL COMMENT '楼栋名称',
  unit_count    INT         NOT NULL DEFAULT 1 COMMENT '单元数',
  floor_count   INT         NOT NULL DEFAULT 6 COMMENT '总层数',
  building_type VARCHAR(20) NOT NULL DEFAULT '住宅' COMMENT '楼栋类型',
  build_year    INT                  DEFAULT NULL COMMENT '建成年份',
  address       VARCHAR(200)         DEFAULT NULL COMMENT '坐落位置',
  remark        VARCHAR(255)         DEFAULT NULL,
  create_time   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted       TINYINT     NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_building_code (building_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='楼栋表';

-- -------------------------------------------------------------
-- 3. 单元表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS unit;
CREATE TABLE unit (
  id          BIGINT      NOT NULL AUTO_INCREMENT,
  unit_no     VARCHAR(30) NOT NULL COMMENT '单元编号',
  unit_name   VARCHAR(30) NOT NULL COMMENT '单元名称',
  building_id BIGINT      NOT NULL COMMENT '所属楼栋',
  floor_count INT         NOT NULL DEFAULT 6 COMMENT '层数',
  has_elevator TINYINT    NOT NULL DEFAULT 1 COMMENT '是否有电梯',
  remark      VARCHAR(255)         DEFAULT NULL,
  create_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted     TINYINT     NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_unit_no (unit_no),
  KEY idx_unit_building (building_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='单元表';

-- -------------------------------------------------------------
-- 4. 房屋表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS room;
CREATE TABLE room (
  id          BIGINT       NOT NULL AUTO_INCREMENT,
  room_no     VARCHAR(20)  NOT NULL COMMENT '房号',
  building_id BIGINT       NOT NULL COMMENT '所属楼栋',
  unit_id     BIGINT       NOT NULL COMMENT '所属单元',
  floor_no    INT          NOT NULL COMMENT '所在楼层',
  area        DECIMAL(8,2) NOT NULL COMMENT '建筑面积(㎡)',
  layout      VARCHAR(20)  NOT NULL DEFAULT '2室1厅' COMMENT '户型',
  orientation VARCHAR(20)           DEFAULT NULL COMMENT '朝向',
  status      VARCHAR(20)  NOT NULL DEFAULT '自住' COMMENT '自住/出租/空置',
  remark      VARCHAR(255)          DEFAULT NULL,
  create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted     TINYINT      NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_room (unit_id, room_no),
  KEY idx_room_building (building_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='房屋表';

-- -------------------------------------------------------------
-- 5. 业主表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS owner;
CREATE TABLE owner (
  id          BIGINT      NOT NULL AUTO_INCREMENT,
  user_id     BIGINT               DEFAULT NULL COMMENT '关联登录账号(家属可无)',
  name        VARCHAR(50) NOT NULL COMMENT '姓名',
  gender      VARCHAR(4)  NOT NULL DEFAULT '男' COMMENT '性别',
  phone       VARCHAR(20) NOT NULL COMMENT '联系电话',
  id_card     VARCHAR(30)          DEFAULT NULL COMMENT '身份证号',
  owner_type  VARCHAR(20) NOT NULL DEFAULT '业主' COMMENT '业主/家属/租户',
  remark      VARCHAR(255)         DEFAULT NULL,
  create_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted     TINYINT     NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_owner_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='业主表';

-- -------------------------------------------------------------
-- 6. 房屋-业主绑定关系表（支持一户多业主、过户历史）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS owner_room;
CREATE TABLE owner_room (
  id          BIGINT      NOT NULL AUTO_INCREMENT,
  owner_id    BIGINT      NOT NULL COMMENT '业主',
  room_id     BIGINT      NOT NULL COMMENT '房屋',
  relation    VARCHAR(20) NOT NULL DEFAULT '产权人' COMMENT '产权人/配偶/子女/父母/租客',
  is_primary  TINYINT     NOT NULL DEFAULT 0 COMMENT '是否第一业主',
  start_date  DATE                 DEFAULT NULL COMMENT '建立关系日期',
  end_date    DATE                 DEFAULT NULL COMMENT '关系结束日期(过户)',
  status      VARCHAR(20) NOT NULL DEFAULT '有效' COMMENT '有效/已过户/已退租',
  remark      VARCHAR(255)         DEFAULT NULL,
  create_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted     TINYINT     NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_or_owner (owner_id),
  KEY idx_or_room (room_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='房屋业主绑定关系表';

-- -------------------------------------------------------------
-- 7. 报修工单表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS repair_order;
CREATE TABLE repair_order (
  id            BIGINT       NOT NULL AUTO_INCREMENT,
  order_no      VARCHAR(40)  NOT NULL COMMENT '工单号',
  room_id       BIGINT       NOT NULL COMMENT '报修房屋',
  owner_id      BIGINT                DEFAULT NULL COMMENT '报修业主',
  repair_type   VARCHAR(20)  NOT NULL COMMENT '水电/门窗/家电/公共设施/其他',
  title         VARCHAR(100) NOT NULL COMMENT '报修标题',
  content       VARCHAR(500)          DEFAULT NULL COMMENT '问题描述',
  urgency       VARCHAR(10)  NOT NULL DEFAULT '一般' COMMENT '一般/紧急/非常紧急',
  images        VARCHAR(500)          DEFAULT NULL COMMENT '现场照片,逗号分隔',
  status        VARCHAR(20)  NOT NULL DEFAULT '待受理' COMMENT '待受理/已派单/处理中/已完成/已评价/已驳回/已取消',
  handler_id    BIGINT                DEFAULT NULL COMMENT '处理人(物业员工)',
  submit_time   DATETIME     NOT NULL COMMENT '提交时间',
  accept_time   DATETIME              DEFAULT NULL COMMENT '受理时间',
  assign_time   DATETIME              DEFAULT NULL COMMENT '派单时间',
  finish_time   DATETIME              DEFAULT NULL COMMENT '完成时间',
  evaluate_time DATETIME              DEFAULT NULL COMMENT '评价时间',
  timeout_flag  TINYINT      NOT NULL DEFAULT 0 COMMENT '超时(>24h未受理)',
  remark        VARCHAR(255)          DEFAULT NULL,
  create_time   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted       TINYINT      NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_order_no (order_no),
  KEY idx_ro_status (status),
  KEY idx_ro_owner (owner_id),
  KEY idx_ro_handler (handler_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='报修工单表';

-- -------------------------------------------------------------
-- 8. 工单处理记录表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS repair_record;
CREATE TABLE repair_record (
  id            BIGINT       NOT NULL AUTO_INCREMENT,
  order_id      BIGINT       NOT NULL COMMENT '工单',
  operator_id   BIGINT                DEFAULT NULL COMMENT '操作人',
  operator_name VARCHAR(50)           DEFAULT NULL COMMENT '操作人姓名',
  action        VARCHAR(30)  NOT NULL COMMENT '提交报修/受理工单/派单/处理中/完成/评价/驳回/取消',
  content       VARCHAR(500)          DEFAULT NULL COMMENT '处理说明',
  images        VARCHAR(500)          DEFAULT NULL COMMENT '处理照片',
  create_time   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted       TINYINT      NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_rr_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='工单处理记录表';

-- -------------------------------------------------------------
-- 9. 工单评价表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS repair_evaluation;
CREATE TABLE repair_evaluation (
  id             BIGINT      NOT NULL AUTO_INCREMENT,
  order_id       BIGINT      NOT NULL COMMENT '工单',
  owner_id       BIGINT               DEFAULT NULL COMMENT '评价业主',
  score          TINYINT     NOT NULL COMMENT '综合评分1-5',
  attitude_score TINYINT              DEFAULT NULL COMMENT '服务态度分',
  speed_score    TINYINT              DEFAULT NULL COMMENT '处理速度分',
  content        VARCHAR(500)         DEFAULT NULL COMMENT '评价内容',
  create_time    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted        TINYINT     NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_re_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='工单评价表';

-- -------------------------------------------------------------
-- 10. 物业费账单表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS fee_bill;
CREATE TABLE fee_bill (
  id             BIGINT        NOT NULL AUTO_INCREMENT,
  bill_no        VARCHAR(50)   NOT NULL COMMENT '账单号',
  room_id        BIGINT        NOT NULL COMMENT '房屋',
  owner_id       BIGINT                 DEFAULT NULL COMMENT '业主',
  fee_type       VARCHAR(20)   NOT NULL DEFAULT '物业费' COMMENT '物业费/车位费',
  period         VARCHAR(7)    NOT NULL COMMENT '账期 YYYY-MM',
  unit_price     DECIMAL(10,2) NOT NULL COMMENT '单价(元/㎡/月 或 元/月)',
  months         INT           NOT NULL DEFAULT 1 COMMENT '计费月数',
  amount         DECIMAL(12,2) NOT NULL COMMENT '应缴金额',
  paid_amount    DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '已缴金额',
  late_fee       DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '滞纳金',
  status         VARCHAR(20)   NOT NULL DEFAULT '未缴' COMMENT '未缴/部分缴纳/已缴',
  due_date       DATE          NOT NULL COMMENT '缴费截止日',
  generate_batch VARCHAR(50)            DEFAULT NULL COMMENT '批量生成批次号',
  pay_time       DATETIME               DEFAULT NULL COMMENT '结清时间',
  remark         VARCHAR(255)           DEFAULT NULL,
  create_time    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted        TINYINT       NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_bill_no (bill_no),
  UNIQUE KEY uk_bill_room_period (room_id, fee_type, period),
  KEY idx_fb_status (status),
  KEY idx_fb_owner (owner_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='物业费账单表';

-- -------------------------------------------------------------
-- 11. 缴费记录表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS payment_record;
CREATE TABLE payment_record (
  id          BIGINT        NOT NULL AUTO_INCREMENT,
  bill_id     BIGINT        NOT NULL COMMENT '账单',
  room_id     BIGINT        NOT NULL COMMENT '房屋',
  owner_id    BIGINT                 DEFAULT NULL COMMENT '业主',
  amount      DECIMAL(12,2) NOT NULL COMMENT '缴费金额',
  pay_method  VARCHAR(20)   NOT NULL DEFAULT '微信' COMMENT '微信/支付宝/银行卡/现金',
  trade_no    VARCHAR(60)            DEFAULT NULL COMMENT '交易流水号',
  pay_time    DATETIME      NOT NULL COMMENT '缴费时间',
  operator    VARCHAR(50)            DEFAULT NULL COMMENT '经办人',
  remark      VARCHAR(255)           DEFAULT NULL,
  create_time DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted     TINYINT       NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_pr_bill (bill_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='缴费记录表';

-- -------------------------------------------------------------
-- 12. 停车位表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS parking_spot;
CREATE TABLE parking_spot (
  id          BIGINT        NOT NULL AUTO_INCREMENT,
  spot_no     VARCHAR(30)   NOT NULL COMMENT '车位编号',
  spot_type   VARCHAR(20)   NOT NULL DEFAULT '地上' COMMENT '地上/地下/固定/临时',
  area        VARCHAR(50)            DEFAULT NULL COMMENT '所在区域',
  owner_id    BIGINT                 DEFAULT NULL COMMENT '绑定业主',
  room_id     BIGINT                 DEFAULT NULL COMMENT '绑定房屋',
  fee         DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '车位费(元/月)',
  status      VARCHAR(20)   NOT NULL DEFAULT '空闲' COMMENT '空闲/已租/停用',
  start_date  DATE                   DEFAULT NULL COMMENT '租用开始',
  end_date    DATE                   DEFAULT NULL COMMENT '租用结束',
  remark      VARCHAR(255)           DEFAULT NULL,
  create_time DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted     TINYINT       NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_spot_no (spot_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='停车位表';

-- -------------------------------------------------------------
-- 13. 公告表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS notice;
CREATE TABLE notice (
  id           BIGINT       NOT NULL AUTO_INCREMENT,
  title        VARCHAR(200) NOT NULL COMMENT '公告标题',
  content      TEXT         NOT NULL COMMENT '公告内容',
  notice_type  VARCHAR(20)  NOT NULL DEFAULT '通知' COMMENT '通知/提醒/活动/紧急',
  is_top       TINYINT      NOT NULL DEFAULT 0 COMMENT '是否置顶',
  publisher_id BIGINT                DEFAULT NULL COMMENT '发布人',
  publish_time DATETIME     NOT NULL COMMENT '发布时间',
  expire_time  DATETIME              DEFAULT NULL COMMENT '有效期截止',
  status       VARCHAR(20)  NOT NULL DEFAULT '已发布' COMMENT '草稿/已发布/已下线',
  remark       VARCHAR(255)          DEFAULT NULL,
  create_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted      TINYINT      NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_notice_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='公告表';

-- -------------------------------------------------------------
-- 14. 公告已读表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS notice_read;
CREATE TABLE notice_read (
  id          BIGINT   NOT NULL AUTO_INCREMENT,
  notice_id   BIGINT   NOT NULL COMMENT '公告',
  user_id     BIGINT   NOT NULL COMMENT '阅读用户',
  read_time   DATETIME NOT NULL COMMENT '阅读时间',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted     TINYINT  NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_notice_user (notice_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='公告已读表';

-- -------------------------------------------------------------
-- 15. 访客登记表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS visitor;
CREATE TABLE visitor (
  id           BIGINT      NOT NULL AUTO_INCREMENT,
  visitor_name VARCHAR(50) NOT NULL COMMENT '访客姓名',
  phone        VARCHAR(20) NOT NULL COMMENT '访客电话',
  owner_id     BIGINT               DEFAULT NULL COMMENT '被访业主',
  room_id      BIGINT               DEFAULT NULL COMMENT '到访房屋',
  visit_time   DATETIME    NOT NULL COMMENT '预约到访时间',
  leave_time   DATETIME             DEFAULT NULL COMMENT '实际离开时间',
  visit_code   VARCHAR(30) NOT NULL COMMENT '访客码',
  purpose      VARCHAR(100)         DEFAULT NULL COMMENT '来访事由',
  car_no       VARCHAR(20)          DEFAULT NULL COMMENT '车牌号',
  status       VARCHAR(20) NOT NULL DEFAULT '待到访' COMMENT '待到访/已到访/已离开/已取消',
  remark       VARCHAR(255)         DEFAULT NULL,
  create_time  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted      TINYINT     NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_visit_code (visit_code),
  KEY idx_visitor_owner (owner_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='访客登记表';

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================
--  初始化数据
-- =============================================================

-- ---------- 1. 用户（密码统一 123456，MD5 = e10adc3949ba59abbe56e057f20f883e） ----------
INSERT INTO sys_user (id, username, password, role, real_name, phone, email, status) VALUES
 (1,  'admin',   'e10adc3949ba59abbe56e057f20f883e', 'ADMIN', '张明华', '13800000001', 'admin@xingfu-community.cn', 1),
 (2,  'staff01', 'e10adc3949ba59abbe56e057f20f883e', 'STAFF', '王建军', '13800000002', 'wangjj@xingfu-community.cn', 1),
 (3,  'staff02', 'e10adc3949ba59abbe56e057f20f883e', 'STAFF', '李国强', '13800000003', 'ligq@xingfu-community.cn', 1),
 (4,  'staff03', 'e10adc3949ba59abbe56e057f20f883e', 'STAFF', '刘海涛', '13800000004', 'liuht@xingfu-community.cn', 1),
 (5,  'owner01', 'e10adc3949ba59abbe56e057f20f883e', 'OWNER', '张伟民', '13910000001', 'zhangwm@163.com', 1),
 (6,  'owner02', 'e10adc3949ba59abbe56e057f20f883e', 'OWNER', '李秀兰', '13910000002', 'lixl@163.com', 1),
 (7,  'owner03', 'e10adc3949ba59abbe56e057f20f883e', 'OWNER', '王建国', '13910000003', 'wangjg@163.com', 1),
 (8,  'owner04', 'e10adc3949ba59abbe56e057f20f883e', 'OWNER', '刘桂芳', '13910000004', 'liugf@163.com', 1),
 (9,  'owner05', 'e10adc3949ba59abbe56e057f20f883e', 'OWNER', '陈志强', '13910000005', 'chenzq@163.com', 1),
 (10, 'owner06', 'e10adc3949ba59abbe56e057f20f883e', 'OWNER', '赵晓梅', '13910000006', 'zhaoxm@163.com', 1),
 (11, 'owner07', 'e10adc3949ba59abbe56e057f20f883e', 'OWNER', '孙德海', '13910000007', 'sundh@163.com', 1),
 (12, 'owner08', 'e10adc3949ba59abbe56e057f20f883e', 'OWNER', '周文静', '13910000008', 'zhouwj@163.com', 1),
 (13, 'owner09', 'e10adc3949ba59abbe56e057f20f883e', 'OWNER', '吴国庆', '13910000009', 'wugq@163.com', 1),
 (14, 'owner10', 'e10adc3949ba59abbe56e057f20f883e', 'OWNER', '郑丽华', '13910000010', 'zhenglh@163.com', 1);

-- ---------- 2. 楼栋（15 栋） ----------
INSERT INTO building (building_code, building_name, unit_count, floor_count, building_type, build_year, address, remark) VALUES
 ('B01','1号楼', 2, 6, '住宅', 2012, '幸福家园小区东区', '临近小区东门'),
 ('B02','2号楼', 2, 6, '住宅', 2012, '幸福家园小区东区', NULL),
 ('B03','3号楼', 2, 6, '住宅', 2013, '幸福家园小区东区', NULL),
 ('B04','4号楼', 2, 6, '住宅', 2013, '幸福家园小区东区', '底层为沿街商铺'),
 ('B05','5号楼', 2, 6, '住宅', 2014, '幸福家园小区西区', NULL),
 ('B06','6号楼', 2, 6, '住宅', 2014, '幸福家园小区西区', NULL),
 ('B07','7号楼', 2, 6, '住宅', 2015, '幸福家园小区西区', '临近中心花园'),
 ('B08','8号楼', 2, 6, '住宅', 2015, '幸福家园小区西区', NULL),
 ('B09','9号楼', 2, 6, '住宅', 2016, '幸福家园小区南区', NULL),
 ('B10','10号楼',2, 6, '住宅', 2016, '幸福家园小区南区', NULL),
 ('B11','11号楼',2, 6, '住宅', 2017, '幸福家园小区南区', '小区最大楼栋'),
 ('B12','12号楼',2, 6, '住宅', 2018, '幸福家园小区北区', NULL),
 ('B13','13号楼',2, 6, '公寓', 2019, '幸福家园小区北区', '小户型公寓'),
 ('B14','14号楼',2, 6, '公寓', 2020, '幸福家园小区北区', '小户型公寓'),
 ('B15','15号楼',2, 6, '住宅', 2021, '幸福家园小区北区', '最新交付楼栋');

-- ---------- 3. 单元（每栋 2 个单元，共 30 个） ----------
INSERT INTO unit (unit_no, unit_name, building_id, floor_count, has_elevator, remark)
SELECT CONCAT(b.building_code, '-', n.n), CONCAT(n.n, '单元'), b.id, 6,
       CASE WHEN b.building_type = '公寓' THEN 1 ELSE 0 END, NULL
FROM building b
CROSS JOIN (SELECT 1 AS n UNION ALL SELECT 2) n;

-- ---------- 4. 房屋（每单元 6 层 × 2 户 = 12 户，共 360 户） ----------
INSERT INTO room (room_no, building_id, unit_id, floor_no, area, layout, orientation, status, remark)
SELECT CONCAT(f.n + 1, LPAD(r.n + 1, 2, '0')),
       u.building_id, u.id, f.n + 1,
       CASE ((f.n + r.n) % 4) WHEN 0 THEN 89.50 WHEN 1 THEN 105.00 WHEN 2 THEN 76.80 ELSE 128.60 END,
       CASE ((f.n + r.n) % 4) WHEN 0 THEN '2室1厅' WHEN 1 THEN '3室2厅' WHEN 2 THEN '1室1厅' ELSE '4室2厅' END,
       CASE ((f.n + r.n) % 2) WHEN 0 THEN '南' ELSE '南北通透' END,
       CASE ((u.id + f.n + r.n) % 5) WHEN 0 THEN '空置' WHEN 1 THEN '出租' ELSE '自住' END,
       NULL
FROM unit u
CROSS JOIN (SELECT 0 AS n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5) f
CROSS JOIN (SELECT 0 AS n UNION ALL SELECT 1) r;

-- ---------- 5. 业主（20 位，前 10 位有登录账号） ----------
INSERT INTO owner (id, user_id, name, gender, phone, id_card, owner_type, remark) VALUES
 (1,  5,    '张伟民', '男', '13910000001', '110101197803124519', '业主', '1号楼老住户'),
 (2,  6,    '李秀兰', '女', '13910000002', '110101198105063328', '业主', NULL),
 (3,  7,    '王建国', '男', '13910000003', '110101197511208814', '业主', '业委会成员'),
 (4,  8,    '刘桂芳', '女', '13910000004', '110101198309172146', '业主', NULL),
 (5,  9,    '陈志强', '男', '13910000005', '110101198012255537', '业主', NULL),
 (6,  10,   '赵晓梅', '女', '13910000006', '110101198607118823', '业主', NULL),
 (7,  11,   '孙德海', '男', '13910000007', '110101197409034415', '业主', NULL),
 (8,  12,   '周文静', '女', '13910000008', '110101199002216650', '业主', NULL),
 (9,  13,   '吴国庆', '男', '13910000009', '110101197710011132', '业主', NULL),
 (10, 14,   '郑丽华', '女', '13910000010', '110101198812304428', '业主', NULL),
 (11, NULL, '冯建军', '男', '13911000011', '110101198203157719', '业主', '未注册线上账号'),
 (12, NULL, '蒋淑珍', '女', '13911000012', '110101196905224462', '业主', NULL),
 (13, NULL, '韩明远', '男', '13911000013', '110101199104188831', '业主', NULL),
 (14, NULL, '曹玉琴', '女', '13911000014', '110101197608302215', '业主', NULL),
 (15, NULL, '邓伟东', '男', '13911000015', '110101198511119903', '业主', NULL),
 (16, NULL, '许静怡', '女', '13911000016', '110101199307065548', '业主', NULL),
 (17, NULL, '沈国安', '男', '13911000017', '110101196702142271', '业主', '退休教师'),
 (18, NULL, '谢文娟', '女', '13911000018', '110101198909277784', '业主', NULL),
 (19, NULL, '罗建华', '男', '13911000019', '110101198001093316', '业主', NULL),
 (20, NULL, '梁秀英', '女', '13911000020', '110101197504036625', '业主', NULL);

-- ---------- 6. 房屋-业主绑定 ----------
-- 1~3 号楼（房屋 id 1-72）绑定业主 1-10，便于业主账号演示
INSERT INTO owner_room (owner_id, room_id, relation, is_primary, start_date, end_date, status, remark)
SELECT ((r.id - 1) % 10) + 1, r.id, '产权人', 1,
       DATE_SUB('2024-06-01', INTERVAL (r.id % 40) MONTH), NULL, '有效', NULL
FROM room r
JOIN building b ON b.id = r.building_id
WHERE b.building_code IN ('B01','B02','B03');

-- 4~15 号楼绑定业主 11-20
INSERT INTO owner_room (owner_id, room_id, relation, is_primary, start_date, end_date, status, remark)
SELECT 11 + ((r.id - 73) % 10), r.id, '产权人', 1,
       DATE_SUB('2024-06-01', INTERVAL (r.id % 30) MONTH), NULL, '有效', NULL
FROM room r
JOIN building b ON b.id = r.building_id
WHERE b.building_code NOT IN ('B01','B02','B03');

-- 一户多业主（配偶/子女共同持有）
INSERT INTO owner_room (owner_id, room_id, relation, is_primary, start_date, end_date, status, remark)
SELECT m.owner_id, r.id, m.relation, 0, m.start_date, NULL, '有效', m.remark
FROM (
  SELECT  2 AS owner_id, 'B01' AS bcode, '1单元' AS uname, '101' AS rno, '配偶' AS relation, '2021-05-20' AS start_date, '张伟民与李秀兰为夫妻共同持有' AS remark
  UNION ALL SELECT  4, 'B01', '1单元', '102', '配偶', '2022-03-11', '共同持有'
  UNION ALL SELECT  5, 'B01', '1单元', '201', '子女', '2023-01-09', '房产证登记为父子共有'
  UNION ALL SELECT 10, 'B01', '1单元', '502', '配偶', '2020-11-02', '共同持有'
  UNION ALL SELECT 13, 'B02', '1单元', '101', '配偶', '2019-09-18', '共同持有'
  UNION ALL SELECT 16, 'B03', '1单元', '201', '子女', '2023-06-25', '共同持有'
  UNION ALL SELECT 19, 'B04', '1单元', '301', '配偶', '2018-04-14', '共同持有'
) m
JOIN building b ON b.building_code = m.bcode
JOIN unit u ON u.building_id = b.id AND u.unit_name = m.uname
JOIN room r ON r.unit_id = u.id AND r.room_no = m.rno;

-- 过户历史（原业主关系结束，新业主为当前产权人）
INSERT INTO owner_room (owner_id, room_id, relation, is_primary, start_date, end_date, status, remark)
SELECT m.owner_id, r.id, '产权人', 0, m.start_date, m.end_date, '已过户', m.remark
FROM (
  SELECT 11 AS owner_id, 'B01' AS bcode, '1单元' AS uname, '102' AS rno, '2016-08-01' AS start_date, '2022-03-11' AS end_date, '原业主冯建军于2022年3月过户给刘桂芳' AS remark
  UNION ALL SELECT 12, 'B01', '1单元', '201', '2015-06-20', '2023-01-09', '原业主蒋淑珍于2023年1月过户给陈志强'
) m
JOIN building b ON b.building_code = m.bcode
JOIN unit u ON u.building_id = b.id AND u.unit_name = m.uname
JOIN room r ON r.unit_id = u.id AND r.room_no = m.rno;

-- ---------- 7. 报修工单（35 条，覆盖全部状态） ----------
INSERT INTO repair_order (order_no, room_id, owner_id, repair_type, title, content, urgency, images, status,
                          handler_id, submit_time, accept_time, assign_time, finish_time, evaluate_time,
                          timeout_flag, remark)
SELECT
  CONCAT('BX', DATE_FORMAT(DATE_SUB(NOW(), INTERVAL m.submit_h HOUR), '%Y%m%d'), LPAD(m.seq, 4, '0')),
  r.id,
  orr.owner_id,
  m.repair_type, m.title, m.content, m.urgency,
  CASE m.repair_type WHEN '水电' THEN '/media/uploads/repair_water.jpg'
                     WHEN '门窗' THEN '/media/uploads/repair_door.jpg'
                     WHEN '家电' THEN '/media/uploads/repair_appliance.jpg'
                     WHEN '公共设施' THEN '/media/uploads/repair_public.jpg'
                     ELSE '/media/uploads/repair_other.jpg' END,
  m.status, m.handler_id,
  DATE_SUB(NOW(), INTERVAL m.submit_h HOUR),
  CASE WHEN m.status IN ('已派单','处理中','已完成','已评价') THEN DATE_SUB(NOW(), INTERVAL m.submit_h - 2 HOUR) END,
  CASE WHEN m.status IN ('已派单','处理中','已完成','已评价') THEN DATE_SUB(NOW(), INTERVAL m.submit_h - 3 HOUR) END,
  CASE WHEN m.status IN ('已完成','已评价') THEN DATE_SUB(NOW(), INTERVAL m.submit_h - 20 HOUR) END,
  CASE WHEN m.status = '已评价' THEN DATE_SUB(NOW(), INTERVAL m.submit_h - 22 HOUR) END,
  m.timeout_flag, m.remark
FROM (
  -- 待受理（其中 3 条超时：submit > 24 小时）
            SELECT  1 AS seq, 'B01' AS bcode, '1单元' AS uname, '101' AS rno, '水电' AS repair_type, '厨房水管漏水' AS title, '厨房水槽下方水管接口处持续渗水，地面已经积水，希望尽快上门维修。' AS content, '紧急' AS urgency, '待受理' AS status, NULL AS handler_id, 30 AS submit_h, 1 AS timeout_flag, '已超24小时未受理，系统自动标记超时' AS remark
  UNION ALL SELECT  2, 'B01', '1单元', '101', '门窗', '卧室窗户把手松动', '卧室窗户把手螺丝松动，关不严实，晚上有风灌进来。', '一般', '已派单', 2, 20, 0, NULL
  UNION ALL SELECT  3, 'B01', '1单元', '101', '家电', '抽油烟机不工作', '抽油烟机按下开关没有任何反应，怀疑是电机烧坏了。', '一般', '已评价', 3, 120, 0, NULL
  UNION ALL SELECT  4, 'B01', '1单元', '601', '公共设施', '楼道声控灯不亮', '5楼到6楼之间的楼道声控灯不亮，晚上上下楼看不见路。', '紧急', '处理中', 2, 10, 0, NULL
  UNION ALL SELECT  5, 'B01', '1单元', '601', '水电', '卫生间下水道返味', '卫生间地漏返味严重，整个屋子都有异味。', '一般', '已完成', 4, 60, 0, NULL
  UNION ALL SELECT  6, 'B01', '2单元', '501', '其他', '入户门锁芯卡顿', '入户门锁芯转动很费劲，钥匙插拔不顺畅，担心哪天打不开门。', '一般', '待受理', NULL, 5, 0, NULL
  UNION ALL SELECT  7, 'B01', '1单元', '102', '家电', '客厅空调不制冷', '客厅空调开了一个小时还是不制冷，只有风没有冷气。', '紧急', '已评价', 2, 200, 0, NULL
  UNION ALL SELECT  8, 'B01', '1单元', '102', '水电', '阳台水龙头滴水', '阳台水龙头关紧后仍然不停滴水，一天能接小半盆。', '一般', '已派单', 3, 15, 0, NULL
  UNION ALL SELECT  9, 'B01', '1单元', '602', '门窗', '阳台推拉门滑轮损坏', '阳台推拉门下方滑轮坏了，推拉时卡顿并且有异响。', '一般', '已评价', 4, 150, 0, NULL
  UNION ALL SELECT 10, 'B01', '2单元', '101', '公共设施', '单元门禁刷卡失灵', '1号楼2单元门禁刷卡没反应，只能等别人开门才能进。', '紧急', '处理中', 3, 12, 0, NULL
  UNION ALL SELECT 11, 'B01', '2单元', '101', '水电', '厨房水管漏水', '厨房水管漏水。', '一般', '已驳回', NULL, 90, 0, '经核查该处漏水属于业主户内自用管道，不在物业维修范围，建议联系装修公司处理'
  UNION ALL SELECT 12, 'B01', '1单元', '201', '家电', '热水器打不着火', '燃气热水器打不着火，洗澡没有热水。', '紧急', '已评价', 2, 180, 0, NULL
  UNION ALL SELECT 13, 'B01', '2单元', '102', '门窗', '入户门合页异响', '入户门开关时合页咯吱咯吱响，影响休息。', '一般', '已评价', 4, 170, 0, NULL
  UNION ALL SELECT 14, 'B01', '1单元', '202', '其他', '楼道堆放杂物清理', '邻居在楼道堆放纸箱和旧家具，希望物业协调清理。', '一般', '已取消', NULL, 96, 0, '业主自行与邻居协商解决，主动取消该工单'
  UNION ALL SELECT 15, 'B01', '2单元', '201', '水电', '卫生间马桶堵塞', '卫生间马桶堵塞，冲水后水位上涨，无法正常使用。', '紧急', '待受理', NULL, 28, 1, '已超24小时未受理，系统自动标记超时'
  UNION ALL SELECT 16, 'B01', '2单元', '201', '家电', '洗衣机排水不畅', '洗衣机排水很慢，洗完衣服地上都是水。', '一般', '已评价', 3, 140, 0, NULL
  UNION ALL SELECT 17, 'B01', '1单元', '301', '公共设施', '电梯按键失灵', '1号楼1单元电梯 3 层按键按下后不亮，电梯也不停靠。', '非常紧急', '处理中', 2, 8, 0, NULL
  UNION ALL SELECT 18, 'B01', '2单元', '202', '水电', '厨房水管漏水', '厨房水槽下水管接口漏水，橱柜里面都湿了。', '紧急', '已评价', 4, 160, 0, NULL
  UNION ALL SELECT 19, 'B01', '1单元', '302', '门窗', '卫生间门锁损坏', '卫生间门锁反锁后打不开，人在里面出不来。', '紧急', '已派单', 3, 14, 0, NULL
  UNION ALL SELECT 20, 'B01', '2单元', '301', '家电', '冰箱不制冷', '冰箱冷藏室不制冷，里面的菜都坏了。', '一般', '已评价', 2, 210, 0, NULL
  UNION ALL SELECT 21, 'B01', '1单元', '401', '其他', '楼道感应灯延时过短', '楼道感应灯亮几秒就灭，走到一半就黑了。', '一般', '已完成', 4, 55, 0, NULL
  UNION ALL SELECT 22, 'B01', '2单元', '302', '水电', '暖气不热', '供暖季暖气片一直不热，室温只有 16 度。', '紧急', '已评价', 3, 190, 0, NULL
  UNION ALL SELECT 23, 'B01', '1单元', '402', '公共设施', '小区健身器材损坏', '中心广场的漫步机踏板断裂，存在安全隐患。', '紧急', '已评价', 2, 130, 0, NULL
  UNION ALL SELECT 24, 'B01', '2单元', '401', '门窗', '纱窗破损', '厨房纱窗破了一个大口子，蚊子都飞进来了。', '一般', '已取消', NULL, 88, 0, '业主已在网上自行购买纱窗更换，取消工单'
  UNION ALL SELECT 25, 'B01', '1单元', '501', '水电', '厨房水管漏水', '厨房水管接口处渗水，橱柜底板已经发霉。', '紧急', '已评价', 4, 220, 0, NULL
  UNION ALL SELECT 26, 'B01', '2单元', '402', '家电', '微波炉不通电', '微波炉插上电后完全没反应，指示灯也不亮。', '一般', '已评价', 3, 100, 0, NULL
  UNION ALL SELECT 27, 'B01', '1单元', '502', '其他', '门禁卡补办', '门禁卡丢失，申请补办一张。', '一般', '已驳回', NULL, 110, 0, '补办门禁卡请携带身份证到物业服务中心前台办理，无需报修'
  UNION ALL SELECT 28, 'B02', '1单元', '401', '公共设施', '地下车库照明损坏', '地下车库 B 区照明灯管损坏多根，光线很暗，存在剐蹭风险。', '紧急', '待受理', NULL, 26, 1, '已超24小时未受理，系统自动标记超时'
  UNION ALL SELECT 29, 'B03', '2单元', '101', '水电', '厨房水管漏水', '厨房水管漏水，水已经渗到楼下邻居家了。', '非常紧急', '已评价', 2, 230, 0, NULL
  UNION ALL SELECT 30, 'B02', '2单元', '301', '门窗', '防盗门锁更换', '防盗门锁芯老化，申请更换新锁芯。', '一般', '已评价', 4, 240, 0, NULL
  UNION ALL SELECT 31, 'B03', '1单元', '201', '家电', '空调外机噪音大', '楼上邻居的空调外机噪音很大，晚上影响睡眠。', '一般', '已评价', 3, 250, 0, NULL
  UNION ALL SELECT 32, 'B03', '2单元', '601', '其他', '楼道声控灯不亮', '6楼楼道声控灯完全不亮。', '一般', '已评价', 2, 260, 0, NULL
  UNION ALL SELECT 33, 'B02', '1单元', '402', '门窗', '入户门密封条脱落', '入户门下方密封条脱落，门缝漏风。', '一般', '已完成', 3, 45, 0, NULL
  UNION ALL SELECT 34, 'B03', '1单元', '202', '家电', '抽油烟机噪音异常', '抽油烟机工作时噪音特别大，还会抖动。', '一般', '已完成', 2, 40, 0, NULL
  UNION ALL SELECT 35, 'B03', '1单元', '302', '水电', '卫生间水管爆裂', '卫生间进水管爆裂，一直在喷水，已关闭总阀。', '非常紧急', '处理中', 4, 4, 0, NULL
) m
JOIN building b ON b.building_code = m.bcode
JOIN unit u ON u.building_id = b.id AND u.unit_name = m.uname
JOIN room r ON r.unit_id = u.id AND r.room_no = m.rno
LEFT JOIN owner_room orr ON orr.room_id = r.id AND orr.is_primary = 1 AND orr.deleted = 0;

-- ---------- 8. 工单评价（16 条，对应已评价工单） ----------
INSERT INTO repair_evaluation (order_id, owner_id, score, attitude_score, speed_score, content, create_time)
SELECT o.id, o.owner_id,
       CASE (o.id % 5) WHEN 0 THEN 4 WHEN 1 THEN 5 WHEN 2 THEN 5 WHEN 3 THEN 3 ELSE 4 END,
       CASE (o.id % 5) WHEN 0 THEN 5 WHEN 1 THEN 5 WHEN 2 THEN 5 WHEN 3 THEN 4 ELSE 4 END,
       CASE (o.id % 5) WHEN 0 THEN 4 WHEN 1 THEN 5 WHEN 2 THEN 4 WHEN 3 THEN 3 ELSE 4 END,
       CASE (o.id % 6)
         WHEN 0 THEN '师傅上门很及时，问题解决得很彻底，给物业点赞！'
         WHEN 1 THEN '维修师傅态度很好，修完之后还把地面打扫干净了，非常满意。'
         WHEN 2 THEN '报修当天就安排人过来了，效率很高，问题已经解决。'
         WHEN 3 THEN '问题解决了，不过上门时间比约定的晚了半小时，整体还可以。'
         WHEN 4 THEN '师傅技术不错，一次就修好了，收费也合理。'
         ELSE '处理结果满意，希望以后能再快一点。' END,
       o.evaluate_time
FROM repair_order o
WHERE o.status = '已评价';

-- ---------- 9. 工单处理记录（由工单状态自动派生） ----------
-- 8.1 提交报修
INSERT INTO repair_record (order_id, operator_id, operator_name, action, content, images, create_time)
SELECT o.id, su.id, COALESCE(su.real_name, '业主'), '提交报修',
       CONCAT('业主提交报修：', o.title, '（', o.repair_type, ' / 紧急程度：', o.urgency, '）'),
       o.images, o.submit_time
FROM repair_order o
LEFT JOIN owner ow ON ow.id = o.owner_id
LEFT JOIN sys_user su ON su.id = ow.user_id;

-- 8.2 受理工单
INSERT INTO repair_record (order_id, operator_id, operator_name, action, content, images, create_time)
SELECT o.id, o.handler_id, COALESCE(hu.real_name, '物业员工'), '受理工单',
       '物业服务中心已受理该报修，正在安排维修人员。', '', o.accept_time
FROM repair_order o
LEFT JOIN sys_user hu ON hu.id = o.handler_id
WHERE o.accept_time IS NOT NULL;

-- 8.3 派单
INSERT INTO repair_record (order_id, operator_id, operator_name, action, content, images, create_time)
SELECT o.id, o.handler_id, COALESCE(hu.real_name, '物业员工'), '派单',
       CONCAT('工单已指派给维修工 ', COALESCE(hu.real_name, '物业员工'), ' 上门处理。'), '', o.assign_time
FROM repair_order o
LEFT JOIN sys_user hu ON hu.id = o.handler_id
WHERE o.assign_time IS NOT NULL;

-- 8.4 处理中
INSERT INTO repair_record (order_id, operator_id, operator_name, action, content, images, create_time)
SELECT o.id, o.handler_id, COALESCE(hu.real_name, '物业员工'), '处理中',
       '维修人员已上门查看，正在准备材料进行维修。', '/media/uploads/repair_progress.jpg',
       DATE_ADD(o.assign_time, INTERVAL 1 HOUR)
FROM repair_order o
LEFT JOIN sys_user hu ON hu.id = o.handler_id
WHERE o.status IN ('处理中', '已完成', '已评价');

-- 8.5 完成
INSERT INTO repair_record (order_id, operator_id, operator_name, action, content, images, create_time)
SELECT o.id, o.handler_id, COALESCE(hu.real_name, '物业员工'), '完成',
       '维修已完成，已通知业主验收。', '/media/uploads/repair_progress.jpg', o.finish_time
FROM repair_order o
LEFT JOIN sys_user hu ON hu.id = o.handler_id
WHERE o.finish_time IS NOT NULL;

-- 8.6 评价
INSERT INTO repair_record (order_id, operator_id, operator_name, action, content, images, create_time)
SELECT o.id, ow.user_id, ow.name, '评价',
       CONCAT('业主已确认完成并评价，综合评分 ', e.score, ' 星。'), '', o.evaluate_time
FROM repair_order o
JOIN repair_evaluation e ON e.order_id = o.id
LEFT JOIN owner ow ON ow.id = o.owner_id
WHERE o.evaluate_time IS NOT NULL;

-- 8.7 驳回 / 取消
INSERT INTO repair_record (order_id, operator_id, operator_name, action, content, images, create_time)
SELECT o.id, NULL, '物业服务中心', o.status,
       COALESCE(o.remark, CONCAT('工单', o.status)), '', DATE_ADD(o.submit_time, INTERVAL 3 HOUR)
FROM repair_order o
WHERE o.status IN ('已驳回', '已取消');

-- ---------- 11. 物业费账单（1~3 号楼 × 2026-07/08/09 三个账期） ----------
INSERT INTO fee_bill (bill_no, room_id, owner_id, fee_type, period, unit_price, months, amount,
                      paid_amount, late_fee, status, due_date, generate_batch, pay_time, remark)
SELECT
  CONCAT('WY', REPLACE(p.period, '-', ''), LPAD(r.id, 5, '0')),
  r.id, orr.owner_id, '物业费', p.period, 2.50, 1,
  ROUND(r.area * 2.50, 2),
  CASE
    WHEN p.period = '2026-07' THEN CASE WHEN r.id % 7 = 0 THEN 0.00 ELSE ROUND(r.area * 2.50, 2) END
    WHEN p.period = '2026-08' THEN CASE WHEN r.id % 7 = 0 THEN 0.00 WHEN r.id % 5 = 0 THEN ROUND(r.area * 2.50 / 2, 2) ELSE ROUND(r.area * 2.50, 2) END
    ELSE CASE WHEN r.id % 3 = 0 THEN ROUND(r.area * 2.50, 2) ELSE 0.00 END
  END,
  0.00,
  CASE
    WHEN p.period = '2026-07' THEN CASE WHEN r.id % 7 = 0 THEN '未缴' ELSE '已缴' END
    WHEN p.period = '2026-08' THEN CASE WHEN r.id % 7 = 0 THEN '未缴' WHEN r.id % 5 = 0 THEN '部分缴纳' ELSE '已缴' END
    ELSE CASE WHEN r.id % 3 = 0 THEN '已缴' ELSE '未缴' END
  END,
  p.due_date, CONCAT('BATCH-', p.period),
  CASE
    WHEN p.period = '2026-07' THEN CASE WHEN r.id % 7 = 0 THEN NULL ELSE DATE_SUB(p.due_date, INTERVAL (r.id % 20) DAY) END
    WHEN p.period = '2026-08' THEN CASE WHEN r.id % 7 = 0 THEN NULL WHEN r.id % 5 = 0 THEN DATE_SUB(p.due_date, INTERVAL (r.id % 10) DAY) ELSE DATE_SUB(p.due_date, INTERVAL (r.id % 20) DAY) END
    ELSE CASE WHEN r.id % 3 = 0 THEN DATE_SUB(p.due_date, INTERVAL (r.id % 15) DAY) ELSE NULL END
  END,
  NULL
FROM room r
JOIN building b ON b.id = r.building_id
LEFT JOIN owner_room orr ON orr.room_id = r.id AND orr.is_primary = 1 AND orr.deleted = 0
CROSS JOIN (
  SELECT '2026-07' AS period, '2026-07-31' AS due_date
  UNION ALL SELECT '2026-08', '2026-08-31'
  UNION ALL SELECT '2026-09', '2026-09-30'
) p
WHERE b.building_code IN ('B01', 'B02', 'B03');

-- ---------- 10. 停车位（20 个） ----------
INSERT INTO parking_spot (spot_no, spot_type, area, owner_id, room_id, fee, status, start_date, end_date, remark)
SELECT m.spot_no, m.spot_type, m.area, m.owner_id,
       (SELECT r.id FROM owner_room orr JOIN room r ON r.id = orr.room_id
        WHERE orr.owner_id = m.owner_id AND orr.is_primary = 1 AND orr.deleted = 0
        ORDER BY r.id LIMIT 1),
       m.fee, m.status, m.start_date, m.end_date, m.remark
FROM (
            SELECT 'D-001' AS spot_no, '地下' AS spot_type, '地下车库A区' AS area, 1 AS owner_id, 200.00 AS fee, '已租' AS status, '2025-01-01' AS start_date, '2026-12-31' AS end_date, '固定车位' AS remark
  UNION ALL SELECT 'D-002', '地下', '地下车库A区', 2,  200.00, '已租', '2025-01-01', '2026-12-31', '固定车位'
  UNION ALL SELECT 'D-003', '地下', '地下车库A区', 3,  200.00, '已租', '2025-03-01', '2026-12-31', NULL
  UNION ALL SELECT 'D-004', '地下', '地下车库A区', 4,  200.00, '已租', '2025-03-01', '2026-12-31', NULL
  UNION ALL SELECT 'D-005', '地下', '地下车库B区', 5,  200.00, '已租', '2025-05-01', '2026-12-31', NULL
  UNION ALL SELECT 'D-006', '地下', '地下车库B区', 6,  200.00, '已租', '2025-05-01', '2026-12-31', NULL
  UNION ALL SELECT 'D-007', '地下', '地下车库B区', 7,  200.00, '已租', '2024-09-01', '2026-08-31', '即将到期'
  UNION ALL SELECT 'D-008', '固定', '地下车库B区', 8,  300.00, '已租', '2025-06-01', '2026-12-31', '带充电桩'
  UNION ALL SELECT 'D-009', '固定', '地下车库C区', 9,  300.00, '已租', '2025-06-01', '2026-12-31', '带充电桩'
  UNION ALL SELECT 'D-010', '固定', '地下车库C区', 10, 300.00, '已租', '2025-07-01', '2026-12-31', NULL
  UNION ALL SELECT 'D-011', '地下', '地下车库C区', NULL, 200.00, '空闲', NULL, NULL, NULL
  UNION ALL SELECT 'D-012', '地下', '地下车库C区', NULL, 200.00, '空闲', NULL, NULL, NULL
  UNION ALL SELECT 'G-001', '地上', '1号楼东侧地面', 11, 120.00, '已租', '2025-02-01', '2026-12-31', NULL
  UNION ALL SELECT 'G-002', '地上', '1号楼东侧地面', 12, 120.00, '已租', '2025-02-01', '2026-12-31', NULL
  UNION ALL SELECT 'G-003', '地上', '2号楼南侧地面', NULL, 120.00, '空闲', NULL, NULL, NULL
  UNION ALL SELECT 'G-004', '地上', '2号楼南侧地面', NULL, 120.00, '空闲', NULL, NULL, NULL
  UNION ALL SELECT 'G-005', '地上', '中心广场北侧', NULL, 120.00, '停用', NULL, NULL, '地面塌陷维修中'
  UNION ALL SELECT 'L-001', '临时', '小区东门访客区', NULL, 5.00, '空闲', NULL, NULL, '临时车位，按次收费'
  UNION ALL SELECT 'L-002', '临时', '小区东门访客区', NULL, 5.00, '空闲', NULL, NULL, '临时车位，按次收费'
  UNION ALL SELECT 'L-003', '临时', '小区西门访客区', NULL, 5.00, '空闲', NULL, NULL, '临时车位，按次收费'
) m;

-- 车位费账单（已绑定业主的地下车位）
INSERT INTO fee_bill (bill_no, room_id, owner_id, fee_type, period, unit_price, months, amount,
                      paid_amount, late_fee, status, due_date, generate_batch, pay_time, remark)
SELECT CONCAT('CW202609', LPAD(p.id, 5, '0')), p.room_id, p.owner_id, '车位费', '2026-09',
       p.fee, 1, p.fee,
       CASE WHEN p.id % 3 = 0 THEN 0.00 ELSE p.fee END, 0.00,
       CASE WHEN p.id % 3 = 0 THEN '未缴' ELSE '已缴' END,
       '2026-09-30', 'BATCH-PARK-2026-09',
       CASE WHEN p.id % 3 = 0 THEN NULL ELSE DATE_SUB('2026-09-30', INTERVAL 6 DAY) END,
       CONCAT('车位 ', p.spot_no, ' 月度车位费')
FROM parking_spot p
WHERE p.status = '已租' AND p.owner_id IS NOT NULL AND p.room_id IS NOT NULL;

-- ---------- 12. 缴费记录 ----------
INSERT INTO payment_record (bill_id, room_id, owner_id, amount, pay_method, trade_no, pay_time, operator, remark)
SELECT b.id, b.room_id, b.owner_id, b.paid_amount,
       CASE (b.id % 4) WHEN 0 THEN '微信' WHEN 1 THEN '支付宝' WHEN 2 THEN '银行卡' ELSE '现金' END,
       CONCAT('PAY', DATE_FORMAT(b.pay_time, '%Y%m%d'), LPAD(b.id, 6, '0')),
       b.pay_time, '物业收费员', CASE WHEN b.fee_type = '车位费' THEN '车位费缴纳' ELSE '物业费缴纳' END
FROM fee_bill b
WHERE b.status <> '未缴' AND b.paid_amount > 0;

-- 滞纳金：对已过缴费截止日仍未缴的账单按日计收（0.05%/日）
UPDATE fee_bill
SET late_fee = ROUND((amount - paid_amount) * 0.0005 * DATEDIFF(CURDATE(), due_date), 2)
WHERE status <> '已缴' AND deleted = 0 AND DATEDIFF(CURDATE(), due_date) > 0;

-- ---------- 13. 公告（15 条） ----------
INSERT INTO notice (title, content, notice_type, is_top, publisher_id, publish_time, expire_time, status) VALUES
 ('关于小区供暖系统试水的通知', '各位业主：本小区定于 2026 年 10 月 15 日至 10 月 18 日进行供暖系统试水，请各户留人在家，注意观察暖气片及管道接口是否有渗漏。如发现漏水请立即联系物业服务中心，电话 010-88886666。', '通知', 1, 1, '2026-09-20 09:00:00', '2026-10-20 23:59:59', '已发布'),
 ('中秋节社区文化活动报名开始啦', '为丰富社区文化生活，物业将于 9 月 28 日晚 19:00 在中心广场举办中秋游园会，现场有猜灯谜、做月饼、文艺演出等活动，欢迎各位业主携家人参加。报名请到物业服务中心或在小程序内登记。', '活动', 1, 1, '2026-09-18 14:30:00', '2026-09-29 23:59:59', '已发布'),
 ('关于小区地下车库照明改造的施工公告', '地下车库照明改造工程将于 2026 年 10 月 8 日开工，工期约 15 天。施工期间 B 区部分车位将临时封闭，请相关车主配合挪车，给您带来不便敬请谅解。', '通知', 0, 1, '2026-09-22 10:15:00', '2026-10-25 23:59:59', '已发布'),
 ('2026 年 9 月物业费缴纳提醒', '各位业主：2026 年 9 月物业费已开始收缴，请于 9 月 30 日前通过物业服务中心或线上渠道缴纳。逾期将按日加收 0.05% 滞纳金，感谢配合。', '提醒', 0, 1, '2026-09-01 08:30:00', '2026-09-30 23:59:59', '已发布'),
 ('小区门禁系统升级完成通知', '小区门禁系统已于 9 月 12 日完成升级，原门禁卡需到物业服务中心免费激活后方可继续使用，激活时间为每日 8:30-17:30。', '通知', 0, 1, '2026-09-12 16:00:00', '2026-10-12 23:59:59', '已发布'),
 ('关于电动车禁止上楼充电的安全提示', '近期多地发生电动车入户充电引发的火灾事故。为保障全体业主生命财产安全，严禁将电动自行车及电池推入楼道、电梯和住户家中充电，请到小区集中充电棚充电。', '紧急', 1, 1, '2026-09-10 11:00:00', '2026-12-31 23:59:59', '已发布'),
 ('小区绿化修剪作业安排', '物业将于 9 月 26 日至 9 月 30 日对小区绿化带进行修剪，作业期间请勿在绿化带附近停放车辆和晾晒衣物。', '通知', 0, 1, '2026-09-23 09:40:00', '2026-10-01 23:59:59', '已发布'),
 ('电梯年度检验停梯安排', '根据特种设备管理规定，小区 1-8 号楼电梯将于 10 月 10 日进行年度检验，检验期间每栋楼电梯停运约 2 小时，请合理安排出行。', '通知', 0, 1, '2026-09-21 15:20:00', '2026-10-11 23:59:59', '已发布'),
 ('关于小区快递柜调整的通知', '因场地改造，小区东门快递柜将于 9 月 30 日迁移至东门保安室旁，请各位业主及时取件，避免包裹滞留。', '通知', 0, 1, '2026-09-19 10:00:00', '2026-10-19 23:59:59', '已发布'),
 ('邀请业主参加第三季度业主座谈会', '物业定于 10 月 12 日下午 14:00 在物业服务中心二楼会议室召开第三季度业主座谈会，就物业服务、费用收支等情况进行沟通，欢迎业主代表参加。', '活动', 0, 1, '2026-09-15 09:00:00', '2026-10-13 23:59:59', '已发布'),
 ('关于小区消防通道严禁停车的通告', '消防通道是生命通道。近期发现部分车辆违规停放在消防通道上，物业将联合消防部门进行整治，违规车辆将被拖移并处以罚款。', '紧急', 0, 1, '2026-09-08 08:00:00', '2026-12-31 23:59:59', '已发布'),
 ('小区生活垃圾分类投放时间调整', '自 10 月 1 日起，小区垃圾分类投放时间调整为每日 6:30-9:00、17:30-20:00，请各位业主在规定时间内投放。', '通知', 0, 1, '2026-09-16 13:00:00', '2026-11-30 23:59:59', '已发布'),
 ('关于近期强降雨天气的温馨提示', '据气象部门预报，本周将出现强降雨天气，请各位业主关好门窗，收好阳台物品，地下车库车主请将车辆停至地势较高处。', '提醒', 1, 1, '2026-09-24 07:30:00', '2026-09-28 23:59:59', '已发布'),
 ('2026 年 8 月物业服务工作报告', '现将 2026 年 8 月物业服务情况公示如下：受理报修 128 件，完成 121 件，完成率 94.5%；完成公共区域保洁 62 次；绿化养护 8 次；处理业主投诉 6 起，均已回复。', '通知', 0, 1, '2026-09-05 09:00:00', '2026-10-05 23:59:59', '已发布'),
 ('关于夏季小区泳池开放的旧公告', '小区泳池于 7 月 1 日至 8 月 31 日开放，开放时间每日 9:00-21:00，请业主凭门禁卡入场。', '通知', 0, 1, '2026-06-28 10:00:00', '2026-08-31 23:59:59', '已下线');

-- ---------- 14. 公告已读 ----------
INSERT INTO notice_read (notice_id, user_id, read_time)
SELECT n.id, u.id, DATE_ADD(n.publish_time, INTERVAL (u.id * 7 + n.id * 3) HOUR)
FROM notice n
JOIN sys_user u ON u.id BETWEEN 5 AND 14
WHERE (n.id + u.id) % 3 <> 0;

-- ---------- 15. 访客登记（18 条） ----------
INSERT INTO visitor (visitor_name, phone, owner_id, room_id, visit_time, leave_time, visit_code, purpose, car_no, status)
SELECT m.vname, m.vphone, m.owner_id,
       (SELECT r.id FROM owner_room orr JOIN room r ON r.id = orr.room_id
        WHERE orr.owner_id = m.owner_id AND orr.is_primary = 1 AND orr.deleted = 0
        ORDER BY r.id LIMIT 1),
       m.visit_time, m.leave_time, m.vcode, m.purpose, m.car_no, m.status
FROM (
            SELECT '刘伟'   AS vname, '13701234501' AS vphone, 1 AS owner_id, '2026-09-24 18:30:00' AS visit_time, NULL AS leave_time, 'V20260924001' AS vcode, '探亲' AS purpose, '京A12345' AS car_no, '待到访' AS status
  UNION ALL SELECT '陈静',   '13701234502', 1, '2026-09-20 14:00:00', '2026-09-20 17:20:00', 'V20260920001', '探亲', NULL, '已离开'
  UNION ALL SELECT '赵鹏',   '13701234503', 2, '2026-09-23 10:30:00', '2026-09-23 12:10:00', 'V20260923001', '朋友聚会', '京B23456', '已离开'
  UNION ALL SELECT '孙丽娟', '13701234504', 2, '2026-09-25 15:00:00', NULL, 'V20260925001', '家政保洁', NULL, '待到访'
  UNION ALL SELECT '周海峰', '13701234505', 3, '2026-09-22 09:00:00', '2026-09-22 10:45:00', 'V20260922001', '上门维修空调', '京C34567', '已离开'
  UNION ALL SELECT '吴敏',   '13701234506', 3, '2026-09-25 19:00:00', NULL, 'V20260925002', '探亲', NULL, '待到访'
  UNION ALL SELECT '郑昊',   '13701234507', 4, '2026-09-21 16:20:00', '2026-09-21 20:00:00', 'V20260921001', '家庭聚餐', '京D45678', '已离开'
  UNION ALL SELECT '冯雪',   '13701234508', 4, '2026-09-24 11:00:00', '2026-09-24 13:30:00', 'V20260924002', '送快递', NULL, '已离开'
  UNION ALL SELECT '韩磊',   '13701234509', 5, '2026-09-19 15:30:00', '2026-09-19 18:00:00', 'V20260919001', '探亲', '京E56789', '已离开'
  UNION ALL SELECT '曹颖',   '13701234510', 5, '2026-09-25 09:30:00', NULL, 'V20260925003', '房产中介带看', NULL, '已到访'
  UNION ALL SELECT '邓超',   '13701234511', 6, '2026-09-18 10:00:00', '2026-09-18 11:40:00', 'V20260918001', '上门安装宽带', NULL, '已离开'
  UNION ALL SELECT '许晴',   '13701234512', 6, '2026-09-25 16:30:00', NULL, 'V20260925004', '朋友聚会', '京F67890', '待到访'
  UNION ALL SELECT '沈涛',   '13701234513', 7, '2026-09-17 14:00:00', '2026-09-17 16:00:00', 'V20260917001', '探亲', NULL, '已离开'
  UNION ALL SELECT '谢婷',   '13701234514', 7, '2026-09-24 20:00:00', NULL, 'V20260924003', '送外卖', NULL, '已取消'
  UNION ALL SELECT '罗强',   '13701234515', 8, '2026-09-23 08:30:00', '2026-09-23 09:15:00', 'V20260923002', '上门维修热水器', '京G78901', '已离开'
  UNION ALL SELECT '梁静',   '13701234516', 8, '2026-09-25 14:00:00', NULL, 'V20260925005', '探亲', NULL, '待到访'
  UNION ALL SELECT '高鹏飞', '13701234517', 9, '2026-09-22 19:30:00', '2026-09-22 21:00:00', 'V20260922002', '朋友聚会', '京H89012', '已离开'
  UNION ALL SELECT '林晓芸', '13701234518', 10, '2026-09-21 11:20:00', '2026-09-21 12:00:00', 'V20260921002', '家政保洁', NULL, '已离开'
) m;

-- 重算超时标记：待受理且提交超过 24 小时
UPDATE repair_order
SET timeout_flag = 1
WHERE status = '待受理' AND deleted = 0 AND TIMESTAMPDIFF(HOUR, submit_time, NOW()) >= 24;

-- =============================================================
--  数据校验
-- =============================================================
SELECT '楼栋' AS 表名, COUNT(*) AS 条数 FROM building
UNION ALL SELECT '单元', COUNT(*) FROM unit
UNION ALL SELECT '房屋', COUNT(*) FROM room
UNION ALL SELECT '业主', COUNT(*) FROM owner
UNION ALL SELECT '房屋业主绑定', COUNT(*) FROM owner_room
UNION ALL SELECT '报修工单', COUNT(*) FROM repair_order
UNION ALL SELECT '工单处理记录', COUNT(*) FROM repair_record
UNION ALL SELECT '工单评价', COUNT(*) FROM repair_evaluation
UNION ALL SELECT '物业费账单', COUNT(*) FROM fee_bill
UNION ALL SELECT '缴费记录', COUNT(*) FROM payment_record
UNION ALL SELECT '停车位', COUNT(*) FROM parking_spot
UNION ALL SELECT '公告', COUNT(*) FROM notice
UNION ALL SELECT '公告已读', COUNT(*) FROM notice_read
UNION ALL SELECT '访客登记', COUNT(*) FROM visitor
UNION ALL SELECT '系统用户', COUNT(*) FROM sys_user;
