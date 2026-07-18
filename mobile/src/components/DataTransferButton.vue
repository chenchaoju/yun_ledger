<template>
  <div class="settings-cell settings-row data-transfer-row">
    <span>数据管理</span>
    <span class="data-transfer-actions">
      <button type="button" :disabled="working" @click="openImportPicker">
        <el-icon><Download /></el-icon>
        <span>导入</span>
      </button>
      <button type="button" :disabled="working" @click="exportData">
        <el-icon><Upload /></el-icon>
        <span>导出</span>
      </button>
    </span>
    <input
      ref="fileInput"
      type="file"
      accept=".json,application/json"
      class="transfer-file-input"
      @change="handleFileChange"
    />
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { ref } from 'vue'
import { Download, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { notifyFinanceDataChanged } from '../utils/events'
import http from '../utils/http'

const emit = defineEmits(['imported'])

const working = ref(false)
const fileInput = ref(null)

async function exportData() {
  working.value = true
  try {
    const { data } = await http.get('/data/export', {
      responseType: 'blob',
      timeout: 30000
    })
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = `finance-data-${dayjs().format('YYYYMMDD-HHmmss')}.json`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
    ElMessage.success('数据已导出')
  } finally {
    working.value = false
  }
}

function openImportPicker() {
  fileInput.value?.click()
}

async function importData(file) {
  const confirmed = await ElMessageBox.confirm(
    '导入会覆盖当前账号已有的支出、收入和固定支出设置，确认继续？',
    '确认导入',
    {
      type: 'warning',
      confirmButtonText: '继续导入',
      cancelButtonText: '取消'
    }
  ).catch(() => false)

  if (!confirmed) return

  let payload
  try {
    payload = JSON.parse(await file.text())
  } catch {
    ElMessage.error('请选择有效的 JSON 数据文件')
    return
  }

  working.value = true
  try {
    const { data } = await http.post('/data/import', payload, { timeout: 30000 })
    ElMessage.success(
      `导入完成：${data.expenses} 条支出，${data.monthly_incomes} 条收入，${data.recurring_expenses || 0} 个固定支出`
    )
    notifyFinanceDataChanged()
    emit('imported', inferImportedPeriod(payload))
  } finally {
    working.value = false
  }
}

function inferImportedPeriod(payload) {
  if (payload?.scope?.year && payload?.scope?.month) {
    return {
      year: Number(payload.scope.year),
      month: Number(payload.scope.month)
    }
  }

  const incomePeriods = (payload?.monthly_incomes || [])
    .map((item) => ({ year: Number(item.year), month: Number(item.month) }))
    .filter((item) => item.year && item.month)
  const expensePeriods = (payload?.expenses || [])
    .map((item) => String(item.spent_at || '').slice(0, 7))
    .filter(Boolean)
    .map((value) => {
      const [year, month] = value.split('-').map(Number)
      return { year, month }
    })
    .filter((item) => item.year && item.month)

  const periods = [...incomePeriods, ...expensePeriods]
  if (!periods.length) return null

  periods.sort((left, right) => left.year - right.year || left.month - right.month)
  return periods[periods.length - 1]
}

async function handleFileChange(event) {
  const [file] = event.target.files || []
  if (file) {
    await importData(file)
  }
  event.target.value = ''
}
</script>

<style scoped>
.transfer-file-input {
  display: none;
}

.data-transfer-row::after {
  content: "";
}

.data-transfer-actions {
  display: grid;
  grid-template-columns: repeat(2, auto);
  gap: 8px;
  align-items: center;
}

.data-transfer-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 64px;
  min-height: 32px;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #f8fafc;
  color: #17202a;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
}

.data-transfer-actions button:active {
  background: #eaf2ff;
}

.data-transfer-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
</style>
