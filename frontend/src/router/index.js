import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../layout/MainLayout.vue'),
    redirect: '/home',
    children: [
      // 通用
      { path: 'home', name: 'Home', component: () => import('../views/common/Home.vue'), meta: { roles: ['ADMIN', 'STAFF', 'OWNER'], title: '首页' } },
      { path: 'profile', name: 'Profile', component: () => import('../views/common/Profile.vue'), meta: { roles: ['ADMIN', 'STAFF', 'OWNER'], title: '个人中心' } },

      // 管理员
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/admin/Dashboard.vue'), meta: { roles: ['ADMIN'], title: '统计报表' } },
      { path: 'building', name: 'Building', component: () => import('../views/admin/Building.vue'), meta: { roles: ['ADMIN'], title: '楼栋单元管理' } },
      { path: 'room', name: 'Room', component: () => import('../views/admin/Room.vue'), meta: { roles: ['ADMIN'], title: '房屋管理' } },
      { path: 'owner', name: 'Owner', component: () => import('../views/admin/Owner.vue'), meta: { roles: ['ADMIN'], title: '业主管理' } },
      { path: 'repair', name: 'RepairManage', component: () => import('../views/admin/RepairManage.vue'), meta: { roles: ['ADMIN'], title: '报修工单管理' } },
      { path: 'bill', name: 'BillManage', component: () => import('../views/admin/BillManage.vue'), meta: { roles: ['ADMIN'], title: '物业费管理' } },
      { path: 'parking', name: 'Parking', component: () => import('../views/admin/Parking.vue'), meta: { roles: ['ADMIN'], title: '停车位管理' } },
      { path: 'notice', name: 'NoticeManage', component: () => import('../views/admin/NoticeManage.vue'), meta: { roles: ['ADMIN'], title: '公告管理' } },
      { path: 'visitor', name: 'VisitorManage', component: () => import('../views/admin/VisitorManage.vue'), meta: { roles: ['ADMIN'], title: '访客登记' } },

      // 物业员工
      { path: 'my-orders', name: 'StaffOrders', component: () => import('../views/staff/MyOrders.vue'), meta: { roles: ['STAFF'], title: '我的工单' } },
      { path: 'staff-notice', name: 'StaffNotice', component: () => import('../views/staff/StaffNotice.vue'), meta: { roles: ['STAFF'], title: '公告通知' } },

      // 业主
      { path: 'my-repairs', name: 'MyRepairs', component: () => import('../views/owner/MyRepairs.vue'), meta: { roles: ['OWNER'], title: '我的报修' } },
      { path: 'new-repair', name: 'NewRepair', component: () => import('../views/owner/NewRepair.vue'), meta: { roles: ['OWNER'], title: '在线报修' } },
      { path: 'my-bills', name: 'MyBills', component: () => import('../views/owner/MyBills.vue'), meta: { roles: ['OWNER'], title: '我的账单' } },
      { path: 'my-parking', name: 'MyParking', component: () => import('../views/owner/MyParking.vue'), meta: { roles: ['OWNER'], title: '我的车位' } },
      { path: 'my-notice', name: 'MyNotice', component: () => import('../views/owner/MyNotice.vue'), meta: { roles: ['OWNER'], title: '公告通知' } },
      { path: 'my-visitor', name: 'MyVisitor', component: () => import('../views/owner/MyVisitor.vue'), meta: { roles: ['OWNER'], title: '访客预约' } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/home' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || 'null')
  if (to.path === '/login') {
    next()
    return
  }
  if (!token) {
    next('/login')
    return
  }
  const role = userInfo?.role
  if (to.meta?.roles && role && !to.meta.roles.includes(role)) {
    next('/home')
    return
  }
  next()
})

export default router
