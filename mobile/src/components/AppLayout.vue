<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="brand">
        <el-icon><Wallet /></el-icon>
        <span>云记账</span>
      </div>
      <button type="button" class="sidebar-create-button" @click="quickDialogVisible = true">
        <el-icon><Plus /></el-icon>
        <span>新增支出</span>
      </button>
      <el-menu :default-active="route.path" router class="sidebar-menu">
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>概览</span>
        </el-menu-item>
        <el-menu-item index="/records">
          <el-icon><Tickets /></el-icon>
          <span>明细</span>
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
      <header v-if="showPageHeader" class="app-topbar">
        <div class="app-topbar-main">
          <h1>{{ route.meta.title }}</h1>
          <p>{{ todayLabel }}</p>
        </div>
        <ExtraIncomeButton />
      </header>
      <RouterView />
    </main>

    <button type="button" class="quick-add-fab" aria-label="快捷新增支出" @click="quickDialogVisible = true">
      <el-icon><Plus /></el-icon>
    </button>
    <ExpenseFormDialog v-model="quickDialogVisible" />
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, Plus, Setting, Tickets, TrendCharts, Wallet } from '@element-plus/icons-vue'
import ExtraIncomeButton from './ExtraIncomeButton.vue'
import ExpenseFormDialog from './ExpenseFormDialog.vue'

const route = useRoute()
const quickDialogVisible = ref(false)

const showPageHeader = computed(() => route.name === 'dashboard')
const todayLabel = computed(() => dayjs().format('YYYY年M月D日'))
</script>
