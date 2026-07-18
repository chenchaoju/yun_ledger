<template>
  <section class="page-stack">
    <el-card shadow="never">
      <el-form class="filter-bar" :model="filters" inline>
        <el-form-item label="月份">
          <el-date-picker v-model="filters.month" type="month" value-format="YYYY-MM" :editable="false" clearable />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="filters.category" clearable class="filter-select">
            <el-option v-for="item in recordCategories" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="items" empty-text="暂无明细" class="desktop-record-table">
        <el-table-column prop="record_date" label="日期" width="130" />
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <span class="record-category-tag" :style="{ '--category-color': categoryColorMap[row.category] }">
              {{ row.category }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip />
        <el-table-column label="金额" width="150" align="right">
          <template #default="{ row }">
            <span :class="recordAmountClass(row)">{{ recordAmount(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button :icon="Edit" circle @click="openEdit(row)" />
            <el-button :icon="Delete" circle type="danger" @click="confirmDelete(row)" />
          </template>
        </el-table-column>
      </el-table>

      <div v-loading="loading" class="mobile-record-list">
        <article v-for="row in items" :key="row.id" class="mobile-record-card">
          <div class="mobile-record-main">
            <div class="mobile-record-info">
              <span class="record-category-tag" :style="{ '--category-color': categoryColorMap[row.category] }">
                {{ row.category }}
              </span>
              <span>{{ row.note || '无备注' }}</span>
            </div>
            <div class="mobile-record-amount">
              <strong :class="recordAmountClass(row)">{{ recordAmount(row) }}</strong>
            </div>
          </div>
          <div class="mobile-record-foot">
            <span class="mobile-record-date">{{ row.record_date }}</span>
            <div class="mobile-record-actions">
              <el-button size="small" :icon="Edit" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" :icon="Delete" type="danger" @click="confirmDelete(row)">删除</el-button>
            </div>
          </div>
        </article>
        <el-empty v-if="!loading && !items.length" description="暂无明细" :image-size="80" />
      </div>
      <div class="pagination-row">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          layout="total, prev, pager, next, sizes"
          :total="total"
          :page-sizes="[10, 20, 50]"
          @change="loadExpenses"
        />
      </div>
    </el-card>

    <ExpenseFormDialog v-model="dialogVisible" :expense="editingExpense" @saved="afterSaved" />
    <el-dialog
      v-model="recordDialogVisible"
      :title="recordDialogTitle"
      width="min(420px, calc(100vw - 24px))"
      class="finance-dialog"
      destroy-on-close
    >
      <el-form ref="recordFormRef" :model="recordForm" label-position="top" @submit.prevent>
        <el-form-item label="金额" required>
          <el-input-number
            v-model="recordForm.amount"
            :min="0"
            :precision="2"
            :step="100"
            controls-position="right"
            class="full-width"
          />
        </el-form-item>
        <el-form-item v-if="canEditRecordCategory" label="分类">
          <el-select v-model="recordForm.category" class="full-width">
            <el-option v-for="item in expenseCategories" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="canEditRecordNote" :label="recordNoteLabel">
          <el-input v-model.trim="recordForm.note" maxlength="80" />
        </el-form-item>
        <el-form-item v-if="canEditRecordDate" label="日期">
          <el-date-picker
            v-model="recordForm.record_date"
            type="date"
            value-format="YYYY-MM-DD"
            :editable="false"
            class="full-width"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingRecord" @click="saveRecord">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Delete, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ExpenseFormDialog from '../components/ExpenseFormDialog.vue'
import { allExpenseCategories, categoryChangedEvent, categoryColorMapFrom } from '../constants/categories'
import { FINANCE_DATA_CHANGED, notifyFinanceDataChanged } from '../utils/events'
import { currency } from '../utils/format'
import http from '../utils/http'

const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const editingExpense = ref(null)
const recordDialogVisible = ref(false)
const editingRecord = ref(null)
const savingRecord = ref(false)
const recordFormRef = ref(null)
const expenseCategories = ref(allExpenseCategories())
const incomeCategoryOptions = [
  { label: '工资收入', value: '工资收入', color: '#2563eb' },
  { label: '额外收入', value: '额外收入', color: '#16a34a' }
]
const categoryColorMap = ref({
  ...categoryColorMapFrom(expenseCategories.value),
  工资收入: '#2563eb',
  额外收入: '#16a34a'
})

const recordCategories = computed(() => [...incomeCategoryOptions, ...expenseCategories.value])
const recordDialogTitle = computed(() => `编辑${recordTypeLabel(editingRecord.value?.record_type)}`)
const canEditRecordCategory = computed(() => editingRecord.value?.record_type === 'recurring_expense')
const canEditRecordNote = computed(() => ['extra_income', 'recurring_expense'].includes(editingRecord.value?.record_type))
const canEditRecordDate = computed(() => ['extra_income', 'recurring_expense'].includes(editingRecord.value?.record_type))
const recordNoteLabel = computed(() => (editingRecord.value?.record_type === 'recurring_expense' ? '固定支出名称' : '收入来源'))

const recordForm = reactive({
  amount: 0,
  category: '',
  note: '',
  record_date: ''
})

const filters = reactive({
  month: '',
  category: ''
})

function buildParams() {
  const params = {
    limit: pageSize.value,
    offset: (page.value - 1) * pageSize.value
  }

  if (filters.month) {
    const start = dayjs(filters.month).startOf('month')
    params.start_date = start.format('YYYY-MM-DD')
    params.end_date = start.endOf('month').format('YYYY-MM-DD')
  }

  if (filters.category) {
    params.category = filters.category
  }

  return params
}

async function loadExpenses() {
  loading.value = true
  try {
    const { data } = await http.get('/records', { params: buildParams() })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  loadExpenses()
}

function openEdit(row) {
  if (row.record_type !== 'expense') {
    editingRecord.value = row
    recordForm.amount = Number(row.amount || 0)
    recordForm.category = row.category
    recordForm.note = row.note || ''
    recordForm.record_date = row.record_date
    recordDialogVisible.value = true
    return
  }

  editingExpense.value = {
    id: row.source_id,
    amount: row.amount,
    category: row.category,
    note: row.note,
    spent_at: row.record_date
  }
  dialogVisible.value = true
}

async function confirmDelete(row) {
  const confirmed = await ElMessageBox.confirm(deleteMessage(row), '删除明细', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    confirmButtonClass: 'el-button--danger'
  }).catch(() => false)
  if (!confirmed) return
  if (row.record_type === 'expense') {
    await http.delete(`/expenses/${row.source_id}`)
  } else {
    await http.delete(`/records/${row.id}`)
  }
  ElMessage.success('已删除')
  notifyFinanceDataChanged()
  loadExpenses()
}

async function saveRecord() {
  if (!editingRecord.value) return
  const amount = Number(recordForm.amount || 0)
  if (amount <= 0 && editingRecord.value.record_type !== 'salary_income') {
    ElMessage.error('请输入金额')
    return
  }
  savingRecord.value = true
  try {
    const payload = {
      amount,
      category: recordForm.category,
      note: recordForm.note || null,
      record_date: recordForm.record_date
    }
    await http.put(`/records/${editingRecord.value.id}`, payload)
    ElMessage.success('已保存')
    recordDialogVisible.value = false
    editingRecord.value = null
    notifyFinanceDataChanged()
    loadExpenses()
  } finally {
    savingRecord.value = false
  }
}

function isIncomeRecord(row) {
  return ['salary_income', 'extra_income'].includes(row.record_type)
}

function recordAmount(row) {
  return `${isIncomeRecord(row) ? '+' : '-'}${currency(row.amount)}`
}

function recordAmountClass(row) {
  return isIncomeRecord(row) ? 'record-amount-income' : 'record-amount-expense'
}

function recordTypeLabel(type) {
  return {
    salary_income: '工资收入',
    extra_income: '额外收入',
    recurring_expense: '固定支出',
    expense: '支出'
  }[type] || '明细'
}

function deleteMessage(row) {
  if (row.record_type === 'salary_income') return '确定删除这条工资收入吗？删除后本月工资会变成 0。'
  if (row.record_type === 'extra_income') return '确定删除这条额外收入吗？删除后会影响本月收入和余额。'
  if (row.record_type === 'recurring_expense') return '确定删除这条固定支出吗？删除后这个固定支出项目会停用。'
  return '确定删除这条明细吗？删除后不能恢复。'
}

function afterSaved() {
  editingExpense.value = null
  loadExpenses()
}

watch(
  () => [filters.month, filters.category],
  () => {
    reload()
  }
)

onMounted(loadExpenses)

function refreshCategories() {
  expenseCategories.value = allExpenseCategories()
  categoryColorMap.value = {
    ...categoryColorMapFrom(expenseCategories.value),
    工资收入: '#2563eb',
    额外收入: '#16a34a'
  }
}

window.addEventListener(categoryChangedEvent, refreshCategories)
window.addEventListener(FINANCE_DATA_CHANGED, reload)

onBeforeUnmount(() => {
  window.removeEventListener(categoryChangedEvent, refreshCategories)
  window.removeEventListener(FINANCE_DATA_CHANGED, reload)
})
</script>
