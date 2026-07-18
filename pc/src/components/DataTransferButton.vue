<template>
  <span>
    <el-dropdown :disabled="working" @command="handleCommand">
      <el-button :icon="Download" :loading="working">
        导出
        <el-icon class="el-icon--right"><ArrowDown /></el-icon>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="export">
            <el-icon><Download /></el-icon>
            <span>导出数据</span>
          </el-dropdown-item>
          <el-dropdown-item command="import">
            <el-icon><Upload /></el-icon>
            <span>导入数据</span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
    <input
      ref="fileInput"
      type="file"
      accept=".json,application/json"
      class="transfer-file-input"
      @change="handleFileChange"
    />
  </span>
</template>

<script setup>
import dayjs from 'dayjs'
import { ref } from 'vue'
import { ArrowDown, Download, Upload } from '@element-plus/icons-vue'
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
    { type: 'warning' }
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

function handleCommand(command) {
  if (command === 'export') {
    exportData()
    return
  }
  if (command === 'import') {
    openImportPicker()
  }
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
</style>
