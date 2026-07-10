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
      </header>
      <RouterView />
    </main>
    <QuickAddButton />
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, Setting, Tickets, TrendCharts, Wallet } from '@element-plus/icons-vue'
import QuickAddButton from './QuickAddButton.vue'

const route = useRoute()

const todayLabel = computed(() => dayjs().format('YYYY年M月D日'))
</script>
