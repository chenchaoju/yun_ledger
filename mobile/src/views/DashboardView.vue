<template>
  <section class="page-stack">
    <el-alert
      v-if="stats.monthly_income.is_over_salary"
      type="warning"
      :closable="false"
      show-icon
      :title="`${selectedMonth} 支出已超出工资收入 ${currency(Math.abs(stats.monthly_income.salary_balance))}`"
    />
    <el-alert
      v-if="todayOverspent"
      type="error"
      :closable="false"
      show-icon
      :title="`今日消费 ${currency(todayExpenseTotal)}，已超过日工资额度 ${currency(dailySalaryBudget)}，超额 ${currency(todayOverAmount)}`"
    />

    <div class="metric-grid compact-metric-grid">
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
      <el-card shadow="never" class="chart-card">
        <template #header>本月分类结构</template>
        <BaseChart :option="categoryOption" :loading="loading" />
        <div v-if="categoryStructureRows.length" class="category-structure-list">
          <div v-for="item in categoryStructureRows" :key="item.category" class="category-structure-row">
            <span>
              <i :style="{ background: item.color }"></i>
              <strong>{{ item.category }}</strong>
            </span>
            <em>{{ currency(item.total) }} · {{ item.percent }}%</em>
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
            <span class="record-category-tag" :style="{ '--category-color': categoryColorMap[row.category] }">
              {{ row.category }}
            </span>
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

  </section>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Calendar, Tickets, Timer, Wallet } from '@element-plus/icons-vue'
import BaseChart from '../components/BaseChart.vue'
import { categoryChangedEvent, categoryColorMapFrom } from '../constants/categories'
import { FINANCE_DATA_CHANGED } from '../utils/events'
import { currency } from '../utils/format'
import http from '../utils/http'

const loading = ref(false)
const selectedMonth = ref(dayjs().format('YYYY-MM'))
const stats = ref(emptyStats())
const categoryColorMap = ref(categoryColorMapFrom())

const selectedYear = computed(() => dayjs(selectedMonth.value).year())
const selectedMonthNumber = computed(() => dayjs(selectedMonth.value).month() + 1)
const selectedMonthDate = computed(() => dayjs(selectedMonth.value))
const isCurrentSelectedMonth = computed(() => selectedMonthDate.value.isSame(dayjs(), 'month'))
const daysInSelectedMonth = computed(() => selectedMonthDate.value.daysInMonth())
const todayExpenseTotal = computed(() => {
  if (!isCurrentSelectedMonth.value) return 0
  const todayDay = dayjs().date()
  return Number(stats.value.daily_expenses.find((item) => item.day === todayDay)?.total || 0)
})
const dailySalaryBudget = computed(() => {
  const salary = Number(stats.value.monthly_income.salary_income || 0)
  if (!salary) return 0
  return Number((salary / Math.max(daysInSelectedMonth.value, 1)).toFixed(2))
})
const todayOverspent = computed(() => isCurrentSelectedMonth.value && dailySalaryBudget.value > 0 && todayExpenseTotal.value > dailySalaryBudget.value)
const todayOverAmount = computed(() => Math.max(todayExpenseTotal.value - dailySalaryBudget.value, 0))
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
  { label: '总余额', value: currency(stats.value.total_balance), icon: Wallet, tone: 'tone-teal' },
  { label: '本月支出', value: currency(stats.value.month_total), icon: Calendar, tone: 'tone-orange' },
  { label: '今日消费', value: currency(todayExpenseTotal.value), icon: Calendar, tone: todayOverspent.value ? 'tone-red' : 'tone-blue' },
  { label: '倒计时', value: monthCountdown.value, icon: Timer, tone: 'tone-blue' },
  { label: '工资收入', value: currency(stats.value.monthly_income.salary_income), icon: Wallet, tone: 'tone-blue' },
  { label: salaryBalanceMetric.value.label, value: salaryBalanceMetric.value.value, icon: Wallet, tone: 'tone-teal' },
  { label: '笔数', value: `${stats.value.month_count} 笔`, icon: Tickets, tone: 'tone-pink' },
  { label: '日均', value: currency(stats.value.average_day), icon: Calendar, tone: 'tone-teal' }
])

const categoryStructureRows = computed(() => {
  const total = Number(stats.value.month_total || 0)
  return stats.value.category_summary.map((item) => {
    const value = Number(item.total || 0)
    return {
      ...item,
      color: categoryColorMap.value[item.category] || '#64748b',
      percent: total > 0 ? Number(((value / total) * 100).toFixed(1)) : 0
    }
  })
})

const topCategoryLabelNames = computed(() => {
  return new Set(
    [...stats.value.category_summary]
      .sort((left, right) => Number(right.total || 0) - Number(left.total || 0))
      .slice(0, 3)
      .map((item) => item.category)
  )
})

const topCategorySummary = computed(() => {
  const [topItem] = [...categoryStructureRows.value].sort((left, right) => Number(right.total || 0) - Number(left.total || 0))
  if (!topItem) return null
  return {
    category: topItem.category,
    percent: topItem.percent
  }
})

const categoryOption = computed(() => ({
  color: stats.value.category_summary.map((item) => categoryColorMap.value[item.category] || '#64748b'),
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
      labelLayout: { hideOverlap: true },
      data: stats.value.category_summary.map((item) => {
        const color = categoryColorMap.value[item.category] || '#64748b'
        const showLabel = topCategoryLabelNames.value.has(item.category)
        return {
          name: item.category,
          value: item.total,
          itemStyle: { color },
          label: {
            show: showLabel,
            position: 'inside',
            color: '#ffffff',
            fontSize: 10,
            fontWeight: 700,
            lineHeight: 14,
            textShadowColor: 'rgba(15, 23, 42, 0.35)',
            textShadowBlur: 3,
            formatter: () => `${item.category}\n${currency(item.total)}`
          },
          labelLine: { show: false }
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
            text: topCategorySummary.value
              ? `${topCategorySummary.value.category}\n${topCategorySummary.value.percent}%`
              : `本月支出\n${currency(stats.value.month_total)}`,
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
    total_balance: 0,
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
      total_balance: null,
      has_expense: false,
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

onMounted(loadStats)
watch(selectedMonth, loadStats)

function refreshCategoryColors() {
  categoryColorMap.value = categoryColorMapFrom()
}

window.addEventListener(categoryChangedEvent, refreshCategoryColors)
window.addEventListener(FINANCE_DATA_CHANGED, loadStats)

onBeforeUnmount(() => {
  window.removeEventListener(categoryChangedEvent, refreshCategoryColors)
  window.removeEventListener(FINANCE_DATA_CHANGED, loadStats)
})
</script>
