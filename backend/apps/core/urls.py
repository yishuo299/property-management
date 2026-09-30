from django.urls import path

from . import (views_auth, views_system, views_repair, views_fee, views_parking,
               views_notice, views_visitor, views_stats, views_common)

urlpatterns = [
    # ---------- 认证 ----------
    path('auth/login', views_auth.login),
    path('auth/info', views_auth.info),
    path('auth/password', views_auth.change_password),
    path('auth/logout', views_auth.logout),
    path('auth/profile', views_auth.profile_update),
    path('auth/staff-list', views_auth.staff_list),

    # ---------- 楼栋 ----------
    path('building/list', views_system.building_list),
    path('building/page', views_system.building_page),
    path('building', views_system.building_create),
    path('building/<int:pk>', views_system.building_update),
    path('building/<int:pk>/delete', views_system.building_delete),

    # ---------- 单元 ----------
    path('unit/list', views_system.unit_list),
    path('unit/page', views_system.unit_page),
    path('unit', views_system.unit_create),
    path('unit/<int:pk>', views_system.unit_update),
    path('unit/<int:pk>/delete', views_system.unit_delete),

    # ---------- 房屋 ----------
    path('room/list', views_system.room_list),
    path('room/page', views_system.room_page),
    path('room', views_system.room_create),
    path('room/<int:pk>', views_system.room_update),
    path('room/<int:pk>/delete', views_system.room_delete),

    # ---------- 业主 ----------
    path('owner/list', views_system.owner_list),
    path('owner/page', views_system.owner_page),
    path('owner/<int:pk>/detail', views_system.owner_detail),
    path('owner', views_system.owner_create),
    path('owner/<int:pk>', views_system.owner_update),
    path('owner/<int:pk>/delete', views_system.owner_delete),
    path('owner/bind', views_system.owner_bind),
    path('owner/binding/<int:pk>/unbind', views_system.owner_unbind),
    path('owner/transfer', views_system.owner_transfer),
    path('owner/room-bindings', views_system.owner_room_bindings),

    # ---------- 报修工单 ----------
    path('repair/page', views_repair.repair_page),
    path('repair/mine', views_repair.repair_mine),
    path('repair/detail/<int:pk>', views_repair.repair_detail),
    path('repair', views_repair.repair_create),
    path('repair/<int:pk>/assign', views_repair.repair_assign),
    path('repair/<int:pk>/process', views_repair.repair_process),
    path('repair/<int:pk>/finish', views_repair.repair_finish),
    path('repair/<int:pk>/evaluate', views_repair.repair_evaluate),
    path('repair/<int:pk>/reject', views_repair.repair_reject),
    path('repair/<int:pk>/cancel', views_repair.repair_cancel),

    # ---------- 物业费账单 ----------
    path('bill/page', views_fee.bill_page),
    path('bill/mine', views_fee.bill_mine),
    path('bill/preview', views_fee.bill_preview),
    path('bill/generate', views_fee.bill_generate),
    path('bill/arrears', views_fee.bill_arrears),
    path('bill/<int:pk>/detail', views_fee.bill_detail),
    path('bill/<int:pk>/pay', views_fee.bill_pay),
    path('bill/<int:pk>/payments', views_fee.bill_payments),
    path('bill/<int:pk>/delete', views_fee.bill_delete),

    # ---------- 停车位 ----------
    path('parking/page', views_parking.parking_page),
    path('parking/list', views_parking.parking_list),
    path('parking/mine', views_parking.parking_mine),
    path('parking', views_parking.parking_create),
    path('parking/<int:pk>', views_parking.parking_update),
    path('parking/<int:pk>/bind', views_parking.parking_bind),
    path('parking/<int:pk>/release', views_parking.parking_release),
    path('parking/<int:pk>/delete', views_parking.parking_delete),

    # ---------- 公告 ----------
    path('notice/page', views_notice.notice_page),
    path('notice/list', views_notice.notice_list),
    path('notice/unread-count', views_notice.notice_unread_count),
    path('notice/<int:pk>/detail', views_notice.notice_detail),
    path('notice/<int:pk>/read', views_notice.notice_read),
    path('notice', views_notice.notice_create),
    path('notice/<int:pk>', views_notice.notice_update),
    path('notice/<int:pk>/delete', views_notice.notice_delete),

    # ---------- 访客 ----------
    path('visitor/page', views_visitor.visitor_page),
    path('visitor', views_visitor.visitor_create),
    path('visitor/<int:pk>', views_visitor.visitor_update),
    path('visitor/<int:pk>/checkin', views_visitor.visitor_checkin),
    path('visitor/<int:pk>/checkout', views_visitor.visitor_checkout),
    path('visitor/<int:pk>/cancel', views_visitor.visitor_cancel),
    path('visitor/<int:pk>/delete', views_visitor.visitor_delete),

    # ---------- 统计报表 ----------
    path('stats/overview', views_stats.overview),
    path('stats/my-overview', views_stats.my_overview),
    path('stats/repair-type', views_stats.repair_type),
    path('stats/repair-trend', views_stats.repair_trend),
    path('stats/repair-efficiency', views_stats.repair_efficiency),
    path('stats/fee-rate', views_stats.fee_rate),
    path('stats/building-fee', views_stats.building_fee),
    path('stats/staff-workload', views_stats.staff_workload),
    path('stats/fee-composition', views_stats.fee_composition),

    # ---------- 上传与导出 ----------
    path('upload', views_common.upload),
    path('export/repairs', views_common.export_repairs),
    path('export/bills', views_common.export_bills),
    path('export/owners', views_common.export_owners),
]
