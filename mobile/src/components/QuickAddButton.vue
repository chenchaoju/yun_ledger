<template>
  <button type="button" class="quick-add-fab" aria-label="快捷记账" @click="openDialog">
    <el-icon :size="24"><Plus /></el-icon>
  </button>
  <ExpenseFormDialog v-model="dialogVisible" @saved="onSaved" />
</template>

<script setup>
import { ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import ExpenseFormDialog from './ExpenseFormDialog.vue'
import { notifyFinanceDataChanged } from '../utils/events'

const dialogVisible = ref(false)

function openDialog() {
  dialogVisible.value = true
}

function onSaved() {
  notifyFinanceDataChanged()
}
</script>