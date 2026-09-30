import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const service = axios.create({
  baseURL: '/api',
  timeout: 20000
})

service.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = 'Bearer ' + token
  }
  return config
})

service.interceptors.response.use(
  (response) => {
    // 文件下载（Excel）直接返回
    if (response.config.responseType === 'blob') {
      return response
    }
    const res = response.data
    if (res.code === 200) {
      return res.data
    }
    if (res.code === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      router.push('/login')
    }
    ElMessage.error(res.msg || '操作失败')
    return Promise.reject(new Error(res.msg || '操作失败'))
  },
  (error) => {
    const status = error.response?.status
    const res = error.response?.data
    const isLogin = error.config?.url?.includes('/auth/login')
    if (status === 401) {
      if (isLogin) {
        ElMessage.error(res?.msg || '用户名或密码错误')
      } else {
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        ElMessage.error(res?.msg || '登录已过期，请重新登录')
        router.push('/login')
      }
    } else if (status === 403) {
      ElMessage.error(res?.msg || '无权限访问')
    } else {
      ElMessage.error(res?.msg || error.message || '请求失败')
    }
    return Promise.reject(error)
  }
)

export default service
