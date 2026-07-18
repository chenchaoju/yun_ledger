<template>
  <span>
    <el-button class="extra-income-top-button" :icon="Wallet" @click="openDialog">额外收入</el-button>
    <el-dialog
      v-model="dialogVisible"
      title="额外收入"
      width="min(420px, calc(100vw - 24px))"
      class="finance-dialog"
      destroy-on-close
    >
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="收入来源">
          <el-input v-model.trim="form.name" maxlength="60" placeholder="例如：奖金、报销、兼职" />
        </el-form-item>
        <el-form-item label="金额">
          <el-input-number
            v-model="form.amount"
            :min="0"
            :precision="2"
            :step="100"
            controls-position="right"
            class="full-width"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </span>
</template>

<script setup>
import dayjs from 'dayjs'
import { reactive, ref } from 'vue'
import { Wallet } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { notifyFinanceDataChanged } from '../utils/events'
import http from '../utils/http'

const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  name: '',
  amount: null
})

async function openDialog() {
  form.name = ''
  form.amount = null
  dialogVisible.value = true
}

function normalizeExtraItems(items) {
  return (Array.isArray(items) ? items : [])
    .map((item) => ({
      name: String(item.name || '额外收入').trim() || '额外收入',
      amount: Number(item.amount || 0)
    }))
    .filter((item) => item.amount > 0)
}

async function save() {
  const amount = Number(form.amount || 0)
  if (amount <= 0) {
    ElMessage.error('请输入额外收入金额')
    return
  }

  const now = dayjs()
  saving.value = true
  try {
    const { data } = await http.get('/incomes/monthly', {
      params: {
        year: now.year(),
        month: now.month() + 1
      }
    })
    const extraItems = normalizeExtraItems(data.extra_income_items)
    extraItems.push({
      name: form.name || '额外收入',
      amount,
      occurred_at: now.format('YYYY-MM-DD')
    })
    await http.put('/incomes/monthly', {
      year: now.year(),
      month: now.month() + 1,
      salary_income: Number(data.salary_income || 0),
      extra_income_items: extraItems
    })
    ElMessage.success('额外收入已添加')
    notifyFinanceDataChanged()
    dialogVisible.value = false
  } finally {
    saving.value = false
  }
}
</script>
