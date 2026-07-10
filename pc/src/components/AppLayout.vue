<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="brand">
        <el-icon><Wallet /></el-icon>
        <span>云记账</span>
      </div>
      <el-menu :default-active="route.path" router class="sidebar-menu">
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>概览</span>
        </el-menu-item>
        <el-menu-item index="/records">
          <el-icon><Tickets /></el-icon>
          <span>记录</span>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><TrendCharts /></el-icon>
          <span>分析</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <main class="app-main">
      <header class="app-topbar">
        <div>
          <h1>{{ route.meta.title }}</h1>
          <p>{{ todayLabel }}</p>
        </div>
        <div class="topbar-actions">
          <span class="account">{{ displayName }}</span>
          <el-button :icon="SwitchButton" @click="logout">退出</el-button>
        </div>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { HomeFilled, Setting, SwitchButton, Tickets, TrendCharts, Wallet } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const todayLabel = computed(() => dayjs().format('YYYY年M月D日'))
const displayName = computed(() => authStore.user?.username || authStore.user?.email || '未命名用户')

function logout() {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>
