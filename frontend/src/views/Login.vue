<template>
  <div class="login-page">
    <div class="bg-deco deco-1"></div>
    <div class="bg-deco deco-2"></div>
    <div class="bg-deco deco-3"></div>

    <div class="login-box">
      <div class="left-panel">
        <div class="logo-badge">家</div>
        <h1 class="sys-name">幸福家园</h1>
        <p class="sys-sub">社区物业管理与报修系统</p>
        <ul class="feature-list">
          <li><el-icon><Tools /></el-icon> 一键报修，实时跟踪维修进度</li>
          <li><el-icon><Money /></el-icon> 物业费在线缴纳，账单清清楚楚</li>
          <li><el-icon><Van /></el-icon> 车位、访客、公告一站式服务</li>
        </ul>
        <div class="warm-tip">让社区生活更温暖 · 让物业服务更贴心</div>
      </div>

      <div class="right-panel">
        <div class="form-title">用户登录</div>
        <div class="form-desc">请选择身份并输入账号密码</div>

        <el-form :model="form" :rules="rules" ref="formRef" size="large" @keyup.enter="onSubmit">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" clearable>
              <template #prefix><el-icon><User /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password>
              <template #prefix><el-icon><Lock /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-button type="primary" class="login-btn" :loading="loading" @click="onSubmit">
            登 录
          </el-button>
        </el-form>

        <div class="quick-title">快速体验（密码均为 123456）</div>
        <div class="quick-list">
          <div v-for="a in accounts" :key="a.username" class="quick-item" @click="fill(a)">
            <el-tag :type="a.type" size="small" effect="light" round>{{ a.role }}</el-tag>
            <span class="quick-name">{{ a.username }}</span>
            <span class="quick-desc">{{ a.desc }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Tools, Money, Van, User, Lock } from '@element-plus/icons-vue'
import { login } from '../api'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: 'admin', password: '123456' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const accounts = [
  { username: 'admin', role: '管理员', type: 'warning', desc: '物业管理员' },
  { username: 'staff01', role: '员工', type: 'success', desc: '维修工 王建军' },
  { username: 'owner01', role: '业主', type: 'primary', desc: '业主 张伟民' }
]

function fill(a) {
  form.username = a.username
  form.password = '123456'
}

async function onSubmit() {
  try {
    await formRef.value.validate()
  } catch (e) {
    return
  }
  loading.value = true
  try {
    const data = await login({ username: form.username, password: form.password })
    userStore.setLogin(data.token, data.userInfo)
    ElMessage.success(`欢迎回来，${data.userInfo.realName || data.userInfo.username}`)
    router.push('/home')
  } catch (e) {
    // 错误提示已由拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fff7ed 0%, #fef3c7 45%, #ecfccb 100%);
  position: relative;
  overflow: hidden;
}

.bg-deco {
  position: absolute;
  border-radius: 50%;
  opacity: 0.5;
}

.deco-1 {
  width: 340px;
  height: 340px;
  background: radial-gradient(circle, #fdba74, transparent 68%);
  top: -110px;
  left: -80px;
}

.deco-2 {
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, #bef264, transparent 68%);
  bottom: -170px;
  right: -110px;
}

.deco-3 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, #fed7aa, transparent 70%);
  bottom: 40px;
  left: 12%;
}

.login-box {
  position: relative;
  z-index: 2;
  display: flex;
  width: 880px;
  min-height: 500px;
  background: rgba(255, 255, 255, 0.96);
  border-radius: 24px;
  box-shadow: 0 18px 50px rgba(194, 65, 12, 0.16);
  overflow: hidden;
}

.left-panel {
  width: 380px;
  flex-shrink: 0;
  padding: 46px 34px;
  background: linear-gradient(160deg, #ea580c 0%, #f97316 55%, #84cc16 130%);
  color: #fff;
  display: flex;
  flex-direction: column;
}

.logo-badge {
  width: 62px;
  height: 62px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.22);
  border: 1.5px solid rgba(255, 255, 255, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  font-weight: 700;
}

.sys-name {
  font-size: 30px;
  margin: 20px 0 6px;
  letter-spacing: 3px;
  font-weight: 700;
}

.sys-sub {
  font-size: 14px;
  opacity: 0.92;
  margin: 0 0 28px;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  flex: 1;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13.5px;
  padding: 9px 0;
  opacity: 0.96;
}

.warm-tip {
  font-size: 12px;
  opacity: 0.85;
  border-top: 1px dashed rgba(255, 255, 255, 0.4);
  padding-top: 14px;
}

.right-panel {
  flex: 1;
  padding: 44px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.form-title {
  font-size: 24px;
  font-weight: 700;
  color: #7c2d12;
}

.form-desc {
  font-size: 13px;
  color: var(--pm-text-sub);
  margin: 6px 0 24px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  letter-spacing: 4px;
  border-radius: 12px;
  background: linear-gradient(90deg, #ea580c, #f97316);
  border: none;
}

.quick-title {
  margin: 26px 0 10px;
  font-size: 12.5px;
  color: var(--pm-text-sub);
}

.quick-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  border: 1px dashed #e7d9c8;
  border-radius: 11px;
  cursor: pointer;
  transition: all 0.18s;
  font-size: 13px;
}

.quick-item:hover {
  background: #fff7ed;
  border-color: #fdba74;
}

.quick-name {
  font-weight: 600;
  color: #7c2d12;
  width: 62px;
}

.quick-desc {
  color: var(--pm-text-sub);
  font-size: 12.5px;
}
</style>
