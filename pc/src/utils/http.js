import axios from 'axios'
import { ElMessage } from 'element-plus'

function trimTrailingSlash(value) {
  return String(value || '').replace(/\/+$/, '')
}

function loginPath() {
  return `${import.meta.env.BASE_URL || '/'}login`.replace(/\/{2,}/g, '/')
}

const http = axios.create({
  baseURL: trimTrailingSlash(import.meta.env.VITE_API_BASE_URL || '/api'),
  timeout: 15000
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    const message = Array.isArray(detail) ? '请求参数有误' : detail || '请求失败'

    const targetLoginPath = loginPath()

    if (status === 401 && window.location.pathname !== targetLoginPath) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('current_user')
      window.location.href = targetLoginPath
    }

    if (status !== 401 || window.location.pathname === targetLoginPath) {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

export default http
