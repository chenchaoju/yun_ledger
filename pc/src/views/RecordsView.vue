<template>
  <section class="page-stack">
    <el-card shadow="never">
      <el-form class="filter-bar" :model="filters" inline>
        <el-form-item label="月份">
          <el-date-picker v-model="filters.month" type="month" value-format="YYYY-MM" clearable />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="filters.category" clearable class="filter-select">
            <el-option label="额外收入" value="额外收入" />
            <el-option v-for="item in expenseCategories" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button :icon="Search" @click="reload">查询</el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
          <el-button type="primary" :icon="Plus" @click="openCreate">新增</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="items" empty-text="暂无记录" class="desktop-record-table">
        <el-table-column prop="record_date" label="日期" width="130" />
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.record_type === 'income'" type="success" round>{{ row.category }}</el-tag>
            <el-tag v-else :color="categoryColorMap[row.category]" effect="dark" round>{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip />
        <el-table-column label="金额" width="150" align="right">
          <template #default="{ row }">
            <span :class="{ 'record-income-amount': row.record_type === 'income' }">
              {{ row.record_type === 'income' ? '+' : '' }}{{ currency(row.amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <template v-if="row.record_type === 'expense'">
              <el-button :icon="Edit" circle @click="openEdit(row)" />
              <el-button :icon="Delete" circle type="danger" @click="confirmDelete(row)" />
            </template>
            <span v-else class="record-muted-action">{{ row.record_type === 'income' ? '收入' : '固定支出' }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div v-loading="loading" class="mobile-record-list">
        <article v-for="row in items" :key="row.id" class="mobile-record-card">
          <div class="mobile-record-main">
            <el-tag v-if="row.record_type === 'income'" type="success" round>{{ row.category }}</el-tag>
            <el-tag v-else :color="categoryColorMap[row.category]" effect="dark" round>{{ row.category }}</el-tag>
            <strong :class="{ 'record-income-amount': row.record_type === 'income' }">
              {{ row.record_type === 'income' ? '+' : '' }}{{ currency(row.amount) }}
            </strong>
          </div>
          <div class="mobile-record-meta">
            <span>{{ row.record_date }}</span>
            <span>{{ row.note || '无备注' }}</span>
          </div>
          <div v-if="row.record_type === 'expense'" class="mobile-record-actions">
            <el-button :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button :icon="Delete" type="danger" @click="confirmDelete(row)">删除</el-button>
          </div>
        </article>
        <el-empty v-if="!loading && !items.length" description="暂无记录" :image-size="80" />
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
  </section>
</template>

<script setup>
import dayjs from 'dayjs'
import { onMounted, reactive, ref } from 'vue'
import { Delete, Edit, Plus, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ExpenseFormDialog from '../components/ExpenseFormDialog.vue'
import { categoryColorMap, expenseCategories } from '../constants/categories'
import { notifyFinanceDataChanged } from '../utils/events'
import { currency } from '../utils/format'
import http from '../utils/http'

const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const editingExpense = ref(null)

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

function resetFilters() {
  filters.month = ''
  filters.category = ''
  reload()
}

function openCreate() {
  editingExpense.value = null
  dialogVisible.value = true
}

function openEdit(row) {
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
  await ElMessageBox.confirm(`删除 ${row.record_date} 的 ${row.category} 记录？`, '确认删除', {
    type: 'warning'
  })
  await http.delete(`/expenses/${row.source_id}`)
  ElMessage.success('已删除')
  notifyFinanceDataChanged()
  loadExpenses()
}

function afterSaved() {
  editingExpense.value = null
  loadExpenses()
}

onMounted(loadExpenses)
</script>
