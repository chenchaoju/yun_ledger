import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { useAuthStore } from '../stores/auth'
import AnalysisView from '../views/AnalysisView.vue'
import DashboardView from '../views/DashboardView.vue'
import LoginView from '../views/LoginView.vue'
import RecordsView from '../views/RecordsView.vue'
import SettingsView from '../views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { title: '登录' }
    },
    {
      path: '/',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: DashboardView,
          meta: { title: '消费概览' }
        },
        {
          path: 'records',
          name: 'records',
          component: RecordsView,
          meta: { title: '消费记录' }
        },
        {
          path: 'analysis',
          name: 'analysis',
          component: AnalysisView,
          meta: { title: '统计分析' }
        },
        {
          path: 'settings',
          name: 'settings',
          component: SettingsView,
          meta: { title: '账号设置' }
        }
      ]
    }
  ]
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.name === 'login' && authStore.isAuthenticated) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
