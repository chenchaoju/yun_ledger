<template>
  <section class="page-stack">
    <div class="toolbar-row">
      <div class="period-picker">
        <el-date-picker v-model="selectedMonth" type="month" value-format="YYYY-MM" />
      </div>
      <div class="toolbar-actions">
        <el-button :icon="Refresh" @click="loadStats">刷新</el-button>
        <DataTransferButton @imported="handleImported" />
        <el-button :icon="Wallet" @click="openIncome">收入</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增</el-button>
      </div>
    </div>

    <el-alert
      v-if="stats.monthly_income.is_over_salary"
      type="warning"
      :closable="false"
      show-icon
      :title="`${selectedMonth} 支出已超出工资收入 ${currency(Math.abs(stats.monthly_income.salary_balance))}`"
    />

    <div class="metric-grid">
      <article v-for="metric in metrics" :key="metric.label" class="metric-card">
        <div class="metric-icon" :class="metric.tone">
          <el-icon><component :is="metric.icon" /></el-icon>
        </div>
        <div>
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
        </div>
      </article>
    </div>

    <div class="content-grid">
      <el-card shadow="never" class="chart-card category-chart-card">
        <template #header>本月分类结构</template>
        <BaseChart :option="categoryOption" :loading="loading" />
        <div v-if="categoryRows.length" class="category-structure-list">
          <div
            v-for="row in categoryRows"
            :key="row.category"
            class="category-structure-item"
            :style="{ '--category-color': categoryColorMap[row.category] || '#64748b' }"
          >
            <span><i></i><b>{{ row.category }}</b></span>
            <strong>{{ currency(row.total) }}</strong>
            <em>{{ percent(row.ratio) }}</em>
          </div>
        </div>
      </el-card>
      <el-card shadow="never" class="chart-card">
        <template #header>{{ selectedYear }} 年趋势</template>
        <BaseChart :option="trendOption" :loading="loading" />
      </el-card>
    </div>

    <el-card shadow="never">
      <template #header>最近记录</template>
      <el-table :data="stats.recent_expenses" empty-text="暂无记录" class="desktop-record-table">
        <el-table-column prop="spent_at" label="日期" width="130" />
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag :color="categoryColorMap[row.category]" effect="dark" round>{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="160" show-overflow-tooltip />
        <el-table-column label="金额" width="140" align="right">
          <template #default="{ row }">{{ currency(row.amount) }}</template>
        </el-table-column>
      </el-table>
      <div class="mobile-record-list">
        <article v-for="row in stats.recent_expenses" :key="row.id" class="mobile-record-card">
          <div class="mobile-record-main">
            <el-tag :color="categoryColorMap[row.category]" effect="dark" round>{{ row.category }}</el-tag>
            <strong>{{ currency(row.amount) }}</strong>
          </div>
          <div class="mobile-record-meta">
            <span>{{ row.spent_at }}</span>
            <span>{{ row.note || '无备注' }}</span>
          </div>
        </article>
        <el-empty v-if="!stats.recent_expenses.length" description="暂无记录" :image-size="80" />
      </div>
    </el-card>

    <ExpenseFormDialog v-model="dialogVisible" @saved="loadStats" />
    <IncomeFormDialog
      v-model="incomeDialogVisible"
      :year="selectedYear"
      :month="selectedMonthNumber"
      :income="stats.monthly_income"
      @saved="loadStats"
    />
  </section>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onMounted, ref } from 'vue'
import { Calendar, Plus, Refresh, Tickets, Timer, Wallet } from '@element-plus/icons-vue'
import BaseChart from '../components/BaseChart.vue'
import DataTransferButton from '../components/DataTransferButton.vue'
import ExpenseFormDialog from '../components/ExpenseFormDialog.vue'
import IncomeFormDialog from '../components/IncomeFormDialog.vue'
import { categoryColorMap } from '../constants/categories'
import { currency, percent } from '../utils/format'
import http from '../utils/http'

const loading = ref(false)
const dialogVisible = ref(false)
const incomeDialogVisible = ref(false)
const selectedMonth = ref(dayjs().format('YYYY-MM'))
const stats = ref(emptyStats())

const selectedYear = computed(() => dayjs(selectedMonth.value).year())
const selectedMonthNumber = computed(() => dayjs(selectedMonth.value).month() + 1)
const monthCountdown = computed(() => {
  const today = dayjs()
  const monthStart = dayjs(selectedMonth.value).startOf('month')
  const monthEnd = monthStart.endOf('month')

  if (monthEnd.isBefore(today, 'day')) {
    return '已结束'
  }

  if (monthStart.isAfter(today, 'day')) {
    return '未开始'
  }

  const daysLeft = monthEnd.date() - today.date()
  return daysLeft === 0 ? '最后一天' : `剩余 ${daysLeft} 天`
})
const salaryBalanceMetric = computed(() => {
  const salary = Number(stats.value.monthly_income.salary_income || 0)
  const balance = Number(stats.value.monthly_income.salary_balance || 0)
  if (!salary) {
    return { label: '工资剩余', value: '未设置' }
  }
  return {
    label: balance >= 0 ? '工资剩余' : '工资已超',
    value: currency(Math.abs(balance))
  }
})

const metrics = computed(() => [
  { label: '本月支出', value: currency(stats.value.month_total), icon: Calendar, tone: 'tone-orange' },
  { label: '当月倒计时', value: monthCountdown.value, icon: Timer, tone: 'tone-blue' },
  { label: '工资收入', value: currency(stats.value.monthly_income.salary_income), icon: Wallet, tone: 'tone-blue' },
  { label: salaryBalanceMetric.value.label, value: salaryBalanceMetric.value.value, icon: Wallet, tone: 'tone-teal' },
  { label: '额外收入', value: currency(stats.value.monthly_income.extra_income), icon: Wallet, tone: 'tone-teal' },
  { label: '本月笔数', value: `${stats.value.month_count} 笔`, icon: Tickets, tone: 'tone-pink' },
  { label: '日均支出', value: currency(stats.value.average_day), icon: Calendar, tone: 'tone-teal' }
])

const categoryRows = computed(() => {
  const total = stats.value.month_total || 0
  return stats.value.category_summary.map((item) => ({
    ...item,
    ratio: total ? (item.total / total) * 100 : 0
  }))
})

const categoryOption = computed(() => ({
  color: stats.value.category_summary.map((item) => categoryColorMap[item.category] || '#64748b'),
  tooltip: {
    trigger: 'item',
    formatter: (params) => {
      return `${params.name}<br/>${currency(params.value)} (${params.percent}%)`
    }
  },
  legend: { show: false },
  series: [
    {
      type: 'pie',
      radius: ['44%', '68%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: true,
      label: {
        show: false
      },
      labelLine: { show: false },
      data: stats.value.category_summary.map((item) => {
        const color = categoryColorMap[item.category] || '#64748b'
        return {
          name: item.category,
          value: item.total,
          itemStyle: { color },
          label: { color },
          labelLine: { lineStyle: { color } }
        }
      })
    }
  ],
  graphic: stats.value.category_summary.length
    ? [
        {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: `本月支出\n${currency(stats.value.month_total)}`,
            fill: '#17202a',
            fontSize: 14,
            fontWeight: 700,
            lineHeight: 22,
            textAlign: 'center'
          }
        }
      ]
    : [{ type: 'text', left: 'center', top: 'middle', style: { text: '暂无数据', fill: '#94a3b8' } }]
}))

const trendOption = computed(() => ({
  color: ['#0f766e'],
  title: {
    text: `${selectedYear.value} 年消费趋势`,
    subtext: '红色节点表示该月支出超过工资收入',
    left: 8,
    top: 0,
    textStyle: { fontSize: 13, fontWeight: 700 },
    subtextStyle: { color: '#64748b' }
  },
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      const item = stats.value.monthly_trend[params[0]?.dataIndex]
      if (!item) return ''
      if (isFutureMonth(item.month)) return `${item.month}月`
      return `${item.month}月<br/>支出：${currency(item.total)}<br/>工资：${currency(item.salary_income)}<br/>额外收入：${currency(item.extra_income)}<br/>总收入：${currency(item.total_income)}`
    }
  },
  grid: { left: 48, right: 24, top: 58, bottom: 42 },
  xAxis: { type: 'category', data: stats.value.monthly_trend.map((item) => `${item.month}月`) },
  yAxis: { type: 'value' },
  series: [
    {
      type: 'line',
      smooth: true,
      areaStyle: { opacity: 0.12 },
      data: stats.value.monthly_trend.map((item) => ({
        value: isFutureMonth(item.month) ? null : item.total,
        itemStyle: !isFutureMonth(item.month) && item.is_over_salary ? { color: '#dc2626' } : undefined
      }))
    }
  ]
}))

function isFutureMonth(month) {
  return dayjs(`${selectedYear.value}-${String(month).padStart(2, '0')}-01`).isAfter(dayjs(), 'month')
}

function emptyStats() {
  return {
    month_total: 0,
    year_total: 0,
    year_count: 0,
    month_count: 0,
    average_day: 0,
    monthly_income: {
      year: dayjs().year(),
      month: dayjs().month() + 1,
      salary_income: 0,
      extra_income: 0,
      extra_income_items: [],
      total_income: 0,
      balance: 0,
      salary_balance: 0,
      is_over_salary: false
    },
    category_summary: [],
    monthly_trend: Array.from({ length: 12 }, (_, index) => ({
      month: index + 1,
      total: 0,
      salary_income: 0,
      extra_income: 0,
      total_income: 0,
      balance: 0,
      is_over_salary: false
    })),
    daily_expenses: [],
    recent_expenses: []
  }
}

async function loadStats() {
  loading.value = true
  try {
    const { data } = await http.get('/stats/overview', {
      params: {
        year: selectedYear.value,
        month: selectedMonthNumber.value
      }
    })
    stats.value = data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogVisible.value = true
}

function openIncome() {
  incomeDialogVisible.value = true
}

function handleImported(period) {
  if (period?.year && period?.month) {
    selectedMonth.value = `${period.year}-${String(period.month).padStart(2, '0')}`
  }
  loadStats()
}

onMounted(loadStats)
</script>
