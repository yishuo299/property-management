<template>
  <div>
    <PageHeader title="个人中心" desc="查看与维护个人基本信息，修改登录密码" />

    <el-row :gutter="16">
      <el-col :span="9">
        <div class="page-card profile-card">
          <el-avatar :size="80" class="big-avatar">{{ (info.realName || info.username || '').slice(0, 1) }}</el-avatar>
          <div class="p-name">{{ info.realName || info.username }}</div>
          <el-tag :type="roleType" effect="light" round>{{ roleName }}</el-tag>
          <div class="p-rows">
            <div class="p-row"><span class="k">登录账号</span><span>{{ info.username }}</span></div>
            <div class="p-row"><span class="k">手机号</span><span>{{ info.phone || '-' }}</span></div>
            <div class="p-row"><span class="k">邮箱</span><span>{{ info.email || '-' }}</span></div>
            <div v-if="info.ownerId" class="p-row"><span class="k">业主档案</span><span>已关联（编号 {{ info.ownerId }}）</span></div>
          </div>
        </div>
      </el-col>
      <el-col :span="15">
        <div class="page-card">
          <div class="chart-title">基本信息维护</div>
          <el-form :model="form" label-width="90px" style="max-width: 460px; margin-top: 10px">
            <el-form-item label="手机号">
              <el-input v-model="form.phone" maxlength="11" placeholder="11 位手机号" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="form.email" placeholder="选填" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="save">保存信息</el-button>
            </el-form-item>
          </el-form>

          <el-divider content-position="left">修改密码</el-divider>
          <el-form :model="pwdForm" :rules="pwdRules" ref="pwdRef" label-width="90px" style="max-width: 460px">
            <el-form-item label="原密码" prop="oldPassword">
              <el-input v-model="pwdForm.oldPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="pwdForm.newPassword" type="password" show-password placeholder="至少 6 位" />
            </el-form-item>
            <el-form-item>
              <el-button type="warning" @click="changePwd">确认修改</el-button>
              <span style="margin-left: 10px; color: #78716c; font-size: 12.5px">修改成功后需要重新登录</span>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import { getInfo, updateProfile, changePassword } from '../../api'
import { useUserStore } from '../../store/user'

const router = useRouter()
const userStore = useUserStore()
const info = reactive({})
const form = reactive({ phone: '', email: '' })
const pwdRef = ref()
const pwdForm = reactive({ oldPassword: '', newPassword: '' })

const roleName = computed(() => ({ ADMIN: '物业管理员', STAFF: '物业员工', OWNER: '业主' }[userStore.role] || ''))
const roleType = computed(() => ({ ADMIN: 'warning', STAFF: 'success', OWNER: 'primary' }[userStore.role] || 'info'))

const pwdRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码长度不能少于 6 位', trigger: 'blur' }
  ]
}

async function load() {
  const d = await getInfo()
  Object.assign(info, d)
  form.phone = d.phone || ''
  form.email = d.email || ''
}

async function save() {
  if (form.phone && !/^\d{11}$/.test(form.phone)) {
    ElMessage.warning('请输入 11 位有效手机号')
    return
  }
  const d = await updateProfile(form)
  userStore.setUserInfo({ ...userStore.userInfo, ...d })
  ElMessage.success('个人信息已更新')
  load()
}

async function changePwd() {
  try {
    await pwdRef.value.validate()
  } catch (e) {
    return
  }
  await changePassword(pwdForm)
  ElMessage.success('密码修改成功，请重新登录')
  userStore.logout()
  router.push('/login')
}

onMounted(load)
</script>

<style scoped>
.profile-card {
  text-align: center;
}

.big-avatar {
  background: linear-gradient(135deg, #fb923c, #ea580c);
  color: #fff;
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 12px;
}

.p-name {
  font-size: 19px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #7c2d12;
}

.p-rows {
  margin-top: 20px;
  text-align: left;
}

.p-row {
  display: flex;
  justify-content: space-between;
  padding: 9px 0;
  border-bottom: 1px dashed #f5ece0;
  font-size: 13.5px;
}

.p-row .k {
  color: var(--pm-text-sub);
}
</style>
