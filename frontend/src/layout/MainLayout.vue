<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand" @click="goHome">
        <div class="brand-badge">家</div>
        <div class="brand-text">
          <div class="brand-name">幸福家园</div>
          <div class="brand-sub">社区物业服务</div>
        </div>
      </div>
      <el-menu :default-active="$route.path" router class="menu" :collapse="false">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
          <el-badge v-if="m.path === '/my-notice' && unread > 0" :value="unread" class="menu-badge" />
        </el-menu-item>
      </el-menu>
      <div class="sidebar-foot">
        <div class="foot-tip">物业服务热线</div>
        <div class="foot-phone">010-8888 6666</div>
      </div>
    </aside>

    <div class="main-wrap">
      <header class="header">
        <div class="crumb">
          <span class="crumb-page">{{ $route.meta?.title || '首页' }}</span>
        </div>
        <div class="header-right">
          <el-tag class="role-tag" :type="roleType" effect="light" round>{{ roleName }}</el-tag>
          <el-dropdown @command="onCommand">
            <span class="user-chip">
              <el-avatar :size="32" class="avatar">{{ realName.slice(0, 1) }}</el-avatar>
              <span class="user-name">{{ realName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      <main class="main">
        <router-view />
      </main>
    </div>

    <el-dialog v-model="pwdVisible" title="修改密码" width="420px">
      <el-form :model="pwdForm" label-width="90px">
        <el-form-item label="原密码">
          <el-input v-model="pwdForm.oldPassword" type="password" show-password placeholder="请输入原密码" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.newPassword" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" @click="onChangePassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '../store/user'
import { changePassword, unreadCount } from '../api'

const router = useRouter()
const userStore = useUserStore()

const role = computed(() => userStore.role)
const realName = computed(() => userStore.realName)
const roleName = computed(() => ({ ADMIN: '物业管理员', STAFF: '物业员工', OWNER: '业主' }[role.value] || ''))
const roleType = computed(() => ({ ADMIN: 'warning', STAFF: 'success', OWNER: 'primary' }[role.value] || 'info'))

const menuMap = {
  ADMIN: [
    { path: '/home', title: '首页概览', icon: 'HomeFilled' },
    { path: '/dashboard', title: '统计报表', icon: 'TrendCharts' },
    { path: '/building', title: '楼栋单元', icon: 'OfficeBuilding' },
    { path: '/room', title: '房屋管理', icon: 'House' },
    { path: '/owner', title: '业主管理', icon: 'User' },
    { path: '/repair', title: '报修工单', icon: 'Tools' },
    { path: '/bill', title: '物业费管理', icon: 'Money' },
    { path: '/parking', title: '停车位管理', icon: 'Van' },
    { path: '/notice', title: '公告管理', icon: 'Bell' },
    { path: '/visitor', title: '访客登记', icon: 'Postcard' }
  ],
  STAFF: [
    { path: '/home', title: '首页概览', icon: 'HomeFilled' },
    { path: '/my-orders', title: '我的工单', icon: 'Tools' },
    { path: '/staff-notice', title: '公告通知', icon: 'Bell' }
  ],
  OWNER: [
    { path: '/home', title: '我的首页', icon: 'HomeFilled' },
    { path: '/new-repair', title: '在线报修', icon: 'EditPen' },
    { path: '/my-repairs', title: '我的报修', icon: 'Tools' },
    { path: '/my-bills', title: '我的账单', icon: 'Money' },
    { path: '/my-parking', title: '我的车位', icon: 'Van' },
    { path: '/my-notice', title: '公告通知', icon: 'Bell' },
    { path: '/my-visitor', title: '访客预约', icon: 'Postcard' }
  ]
}

const menus = computed(() => menuMap[role.value] || [])
const unread = ref(0)

function goHome() {
  router.push('/home')
}

async function loadUnread() {
  if (role.value === 'ADMIN') return
  try {
    const d = await unreadCount()
    unread.value = d?.unread || 0
  } catch (e) {}
}

onMounted(loadUnread)

function onCommand(cmd) {
  if (cmd === 'profile') router.push('/profile')
  else if (cmd === 'password') pwdVisible.value = true
  else if (cmd === 'logout') {
    ElMessageBox.confirm('确定退出登录吗？', '提示', { type: 'warning' })
      .then(() => {
        userStore.logout()
        router.push('/login')
      })
      .catch(() => {})
  }
}

const pwdVisible = ref(false)
const pwdForm = reactive({ oldPassword: '', newPassword: '' })
async function onChangePassword() {
  if (!pwdForm.newPassword || pwdForm.newPassword.length < 6) {
    ElMessage.warning('新密码长度不能少于6位')
    return
  }
  try {
    await changePassword(pwdForm)
    ElMessage.success('密码修改成功，请重新登录')
    pwdVisible.value = false
    userStore.logout()
    router.push('/login')
  } catch (e) {}
}
</script>

<style scoped>
.layout {
  height: 100%;
  display: flex;
  background: var(--pm-bg);
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid var(--pm-border);
  display: flex;
  flex-direction: column;
  padding: 16px 12px 12px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px 16px;
  cursor: pointer;
}

.brand-badge {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: linear-gradient(135deg, #fb923c, #ea580c 60%, #65a30d);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 21px;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(234, 88, 12, 0.28);
}

.brand-name {
  font-size: 17px;
  font-weight: 700;
  color: #7c2d12;
  letter-spacing: 1px;
}

.brand-sub {
  font-size: 11.5px;
  color: var(--pm-text-sub);
  margin-top: 1px;
}

.menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
}

.menu :deep(.el-menu-item) {
  height: 44px;
  line-height: 44px;
  border-radius: 11px;
  margin-bottom: 4px;
  color: #57534e;
  font-size: 14px;
}

.menu :deep(.el-menu-item:hover) {
  background: var(--pm-primary-soft);
  color: #c2410c;
}

.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #ffedd5, #fef3c7);
  color: #c2410c;
  font-weight: 600;
}

.menu-badge {
  margin-left: auto;
}

.sidebar-foot {
  border-top: 1px dashed var(--pm-border);
  padding: 12px 10px 4px;
}

.foot-tip {
  font-size: 11.5px;
  color: var(--pm-text-sub);
}

.foot-phone {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--pm-green);
  margin-top: 2px;
}

.main-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.header {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid var(--pm-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  flex-shrink: 0;
}

.crumb-page {
  font-size: 15.5px;
  font-weight: 600;
  color: #7c2d12;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.role-tag {
  font-weight: 600;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}

.avatar {
  background: linear-gradient(135deg, #fb923c, #ea580c);
  color: #fff;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  color: var(--pm-text);
}

.main {
  flex: 1;
  overflow: auto;
  padding: 18px 22px 30px;
}
</style>
