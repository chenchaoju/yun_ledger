import axios from 'axios'
import { ElMessage } from 'element-plus'

const autoLoginPausedKey = 'finance_mobile_auto_login_paused'
const skipAutoLoginKey = 'skip_auto_login_once'

function trimTrailingSlash(value) {
  return String(value || '').replace(/\/+$/, '')
}

function resolveApiBaseURL() {
  const configured = import.meta.env.VITE_API_BASE_URL
  if (configured) return trimTrailingSlash(configured)

  if (import.meta.env.PROD) {
    return '/mobile-api/api'
  }

  return '/api'
}

function loginPath() {
  return `${import.meta.env.BASE_URL || '/'}login`.replace(/\/{2,}/g, '/')
}

const http = axios.create({
  baseURL: resolveApiBaseURL(),
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
    const message = error.response
      ? Array.isArray(detail)
        ? '请求参数有误'
        : detail || '请求失败'
      : '网络请求失败，请检查网络后重试'

    const targetLoginPath = loginPath()

    if (status === 401 && window.location.pathname !== targetLoginPath) {
      sessionStorage.setItem(skipAutoLoginKey, '1')
      localStorage.setItem(autoLoginPausedKey, '1')
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
