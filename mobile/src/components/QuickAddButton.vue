<template>
  <button type="button" class="quick-add-fab" aria-label="快捷记账" @click="openExpenseDialog">
    <el-icon :size="24"><Plus /></el-icon>
  </button>
  <ExpenseFormDialog v-model="expenseDialogVisible" @saved="onSaved" />
</template>

<script setup>
import { ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import ExpenseFormDialog from './ExpenseFormDialog.vue'
import { notifyFinanceDataChanged } from '../utils/events'

const expenseDialogVisible = ref(false)

function openExpenseDialog() {
  expenseDialogVisible.value = true
}

function onSaved() {
  notifyFinanceDataChanged()
}
</script>
