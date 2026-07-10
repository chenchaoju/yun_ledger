<template>
  <section class="page-stack">
    <div class="toolbar-row">
      <div class="period-picker">
        <el-date-picker v-model="selectedYear" type="year" value-format="YYYY" />
      </div>
    </div>

    <el-alert
      v-if="stats.monthly_income.is_over_salary"
      type="warning"
      :closable="false"
      show-icon
      :title="`${selectedYear}年${selectedMonth}月支出已超出工资收入 ${currency(Math.abs(stats.monthly_income.salary_balance))}`"
    />

    <el-tabs v-model="activeAnalysisTab" class="analysis-tabs">
      <el-tab-pane label="年度账单" name="bill">
        <el-card shadow="never" class="annual-ledger-panel">
          <section v-loading="loading" class="annual-ledger">
            <div class="annual-ledger-card" :class="{ negative: annualBillSummary.balance < 0 }">
              <div class="annual-ledger-card-main">
                <span>结余</span>
                <strong>{{ billSummaryAmount(annualBillSummary.balance) }}</strong>
              </div>
              <div class="annual-ledger-card-foot">
                <span>收入 <b>{{ billTableAmount(annualBillSummary.income) }}</b></span>
                <span>支出 <b>{{ billTableAmount(annualBillSummary.expense) }}</b></span>
              </div>
              <i>¥</i>
            </div>

            <div class="annual-ledger-table" role="table" :aria-label="`${selectedYear}年度账单`">
              <div class="annual-ledger-row annual-ledger-head" role="row">
                <span role="columnheader">月份</span>
                <span role="columnheader">月收入</span>
                <span role="columnheader">月支出</span>
                <span role="columnheader">月结余</span>
              </div>
              <div v-for="row in annualBillRows" :key="row.month" class="annual-ledger-row" role="row">
                <strong role="cell">{{ row.monthLabel }}</strong>
                <span role="cell">{{ billTableAmount(row.income) }}</span>
                <span role="cell">{{ billTableAmount(row.expense) }}</span>
                <span role="cell" :class="{ negative: row.balance < 0 }">{{ billTableAmount(row.balance) }}</span>
              </div>
              <el-empty v-if="!annualBillRows.length" description="暂无账单" :image-size="80" />
            </div>
          </section>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="年度趋势" name="trend">
        <el-card shadow="never" class="chart-card">
          <div class="chart-note">
            <span><i class="legend-dot blue"></i>柱形=月支出</span>
            <span><i class="legend-line teal"></i>绿线=工资收入</span>
            <span><i class="legend-dot red"></i>红柱=超工资</span>
          </div>
          <BaseChart :option="barOption" :loading="loading" />
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="年度剩余" name="balance">
        <el-card shadow="never" class="chart-card">
          <div class="chart-note">
            <span><i class="legend-dot teal"></i>柱形=当月剩余</span>
            <span><i class="legend-line blue"></i>蓝线=累计剩余</span>
            <span><i class="legend-dot red"></i>红柱=当月为负</span>
          </div>
          <BaseChart :option="annualBalanceOption" :loading="loading" />
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="每日累计" name="daily">
        <el-card shadow="never" class="chart-card">
          <div class="chart-note">
            <span><i class="legend-dot orange"></i>柱形=当日花费</span>
            <span><i class="legend-line blue"></i>蓝线=累计消费</span>
            <span><i class="legend-line red dashed"></i>红虚线=工资上限</span>
          </div>
          <BaseChart :option="dailyOption" :loading="loading" />
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="月度结构" name="category">
        <div class="content-grid">
          <el-card shadow="never" class="chart-card">
            <div class="chart-note">
              <span>点击图形可查看分类金额和占比</span>
            </div>
            <BaseChart :option="pieOption" :loading="loading" />
          </el-card>
          <el-card shadow="never">
            <el-table :data="categoryRows" empty-text="暂无数据">
              <el-table-column prop="category" label="分类" />
              <el-table-column prop="count" label="笔数" width="90" />
              <el-table-column label="金额" width="140" align="right">
                <template #default="{ row }">{{ currency(row.total) }}</template>
              </el-table-column>
              <el-table-column label="占比" width="100" align="right">
                <template #default="{ row }">{{ percent(row.ratio) }}</template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>

  </section>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import BaseChart from '../components/BaseChart.vue'
import { categoryChangedEvent, categoryColorMapFrom } from '../constants/categories'
import { currency, percent } from '../utils/format'
import http from '../utils/http'

const loading = ref(false)
const selectedYear = ref(dayjs().format('YYYY'))
const selectedMonth = ref(dayjs().month() + 1)
const activeAnalysisTab = ref('bill')
const stats = ref(emptyStats())
const categoryColorMap = ref(categoryColorMapFrom())

const annualBillRows = computed(() =>
  stats.value.monthly_trend
    .filter((item) => !isFutureMonth(item.month))
    .map((item) => {
      const expense = Number(item.total || 0)
      const hasExpense = expense > 0
      const income = hasExpense ? Number(item.total_income || 0) : 0
      return {
        month: item.month,
        monthLabel: `${String(item.month).padStart(2, '0')}月`,
        income,
        expense,
        balance: hasExpense ? Number((income - expense).toFixed(2)) : 0
      }
    })
    .reverse()
)

const annualBillSummary = computed(() =>
  annualBillRows.value.reduce(
    (summary, item) => {
      summary.income += item.income
      summary.expense += item.expense
      summary.balance += item.balance
      return summary
    },
    { income: 0, expense: 0, balance: 0 }
  )
)

const categoryRows = computed(() => {
  const total = stats.value.month_total || 0
  return stats.value.category_summary.map((item) => ({
    ...item,
    ratio: total ? (item.total / total) * 100 : 0
  }))
})

const dailyRows = computed(() =>
  stats.value.daily_expenses.map((item) => {
    const isFuture = isFutureDay(item.day)
    return {
      ...item,
      isFuture,
      total: isFuture ? null : Number(item.total || 0)
    }
  })
)

const dailyAccumulated = computed(() => {
  let total = 0
  return dailyRows.value.map((item) => {
    if (item.isFuture) return null
    total += Number(item.total || 0)
    return Number(total.toFixed(2))
  })
})

const yearlyBalanceRows = computed(() => {
  let cumulative = 0
  return stats.value.monthly_trend.map((item) => {
    const isFuture = isFutureMonth(item.month)
    const hasExpense = Number(item.total || 0) > 0
    const balance = hasExpense ? Number(item.balance || 0) : 0
    if (isFuture) {
      return {
        ...item,
        isFuture,
        hasExpense,
        balance: null,
        cumulative: null
      }
    }

    cumulative += balance

    return {
      ...item,
      isFuture,
      hasExpense,
      balance: Number(balance.toFixed(2)),
      cumulative: Number(cumulative.toFixed(2))
    }
  })
})

function isFutureMonth(month) {
  return dayjs(`${selectedYear.value}-${String(month).padStart(2, '0')}-01`).isAfter(dayjs(), 'month')
}

function isFutureDay(day) {
  const date = dayjs(
    `${selectedYear.value}-${String(selectedMonth.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  )
  return date.isAfter(dayjs(), 'day')
}

function isVisibleChartValue(value) {
  return value !== null && value !== undefined && value !== ''
}

function chartAxisLabel(value) {
  const number = Number(value || 0)
  if (Math.abs(number) >= 10000) return `${Math.round(number / 10000)}万`
  if (Math.abs(number) >= 1000) return `${Math.round(number / 1000)}k`
  return String(Math.round(number))
}

function billTableAmount(value) {
  const number = Number(value || 0)
  if (Math.abs(number) < 0.005) return '0'
  return number.toFixed(2).replace(/\.?0+$/, '')
}

function billSummaryAmount(value) {
  const number = Number(value || 0)
  if (Math.abs(number) < 0.005) return '0.00'
  return number.toFixed(2)
}

const barOption = computed(() => ({
  title: {
    text: `${selectedYear.value} 年支出对比`,
    left: 8,
    top: 0,
    textStyle: { fontSize: 13, fontWeight: 700 }
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
  legend: { show: false },
  grid: { left: 42, right: 10, top: 46, bottom: 30 },
  xAxis: {
    type: 'category',
    data: stats.value.monthly_trend.map((item) => `${item.month}月`),
    axisLabel: { fontSize: 11 }
  },
  yAxis: {
    type: 'value',
    splitNumber: 4,
    axisLabel: { formatter: chartAxisLabel, fontSize: 11 }
  },
  series: [
    {
      name: '支出',
      type: 'bar',
      barMaxWidth: 34,
      data: stats.value.monthly_trend.map((item) => ({
        value: isFutureMonth(item.month) ? null : item.total,
        itemStyle: { color: !isFutureMonth(item.month) && item.is_over_salary ? '#dc2626' : '#2563eb' }
      }))
    },
    {
      name: '工资收入',
      type: 'line',
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 2, color: '#0f766e' },
      itemStyle: { color: '#0f766e' },
      data: stats.value.monthly_trend.map((item) => (isFutureMonth(item.month) ? null : item.salary_income))
    }
  ]
}))

const annualBalanceOption = computed(() => ({
  color: ['#0f766e', '#2563eb'],
  title: {
    text: `${selectedYear.value} 年度剩余`,
    left: 8,
    top: 0,
    textStyle: { fontSize: 13, fontWeight: 700 }
  },
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      const item = yearlyBalanceRows.value[params[0]?.dataIndex]
      if (!item) return ''
      if (item.isFuture) return `${item.month}月`
      return [
        `${item.month}月`,
        `总收入：${currency(item.total_income)}`,
        `支出：${currency(item.total)}`,
        `当月剩余：${currency(item.balance)}`,
        `累计剩余：${currency(item.cumulative)}`
      ].join('<br/>')
    }
  },
  legend: { show: false },
  grid: { left: 42, right: 10, top: 46, bottom: 30 },
  xAxis: {
    type: 'category',
    data: yearlyBalanceRows.value.map((item) => `${item.month}月`),
    axisLabel: { fontSize: 11 }
  },
  yAxis: {
    type: 'value',
    splitNumber: 4,
    axisLabel: { formatter: chartAxisLabel, fontSize: 11 }
  },
  series: [
    {
      name: '当月剩余',
      type: 'bar',
      barMaxWidth: 34,
      data: yearlyBalanceRows.value.map((item) => ({
        value: item.balance,
        itemStyle: { color: isVisibleChartValue(item.balance) && item.balance < 0 ? '#dc2626' : '#0f766e' }
      }))
    },
    {
      name: '累计剩余',
      type: 'line',
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 2, color: '#2563eb' },
      itemStyle: { color: '#2563eb' },
      data: yearlyBalanceRows.value.map((item) => item.cumulative)
    }
  ]
}))

const dailyOption = computed(() => ({
  color: ['#f97316', '#2563eb', '#dc2626'],
  title: {
    text: `${selectedMonth.value} 月每日累计`,
    left: 8,
    top: 0,
    textStyle: { fontSize: 13, fontWeight: 700 }
  },
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      const day = params[0]?.axisValue || ''
      const visibleParams = params.filter((item) => isVisibleChartValue(item.value))
      return [
        day,
        ...visibleParams.map((item) => `${item.marker}${item.seriesName}：${currency(item.value)}`)
      ].join('<br/>')
    }
  },
  legend: { show: false },
  grid: { left: 42, right: 10, top: 46, bottom: 30 },
  xAxis: {
    type: 'category',
    data: dailyRows.value.map((item) => `${item.day}日`),
    axisLabel: {
      interval: 4,
      fontSize: 11
    }
  },
  yAxis: {
    type: 'value',
    splitNumber: 4,
    axisLabel: { formatter: chartAxisLabel, fontSize: 11 }
  },
  series: [
    {
      name: '每日花费',
      type: 'bar',
      barMaxWidth: 18,
      data: dailyRows.value.map((item) => item.total)
    },
    {
      name: '累计消费',
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: dailyAccumulated.value
    },
    {
      name: '工资上限',
      type: 'line',
      symbol: 'none',
      lineStyle: { type: 'dashed', width: 2 },
      data: dailyRows.value.map((item) => (item.isFuture ? null : stats.value.monthly_income.salary_income))
    }
  ],
  graphic: dailyRows.value.some((item) => isVisibleChartValue(item.total) && item.total > 0)
    ? []
    : [{ type: 'text', left: 'center', top: 'middle', style: { text: '暂无数据', fill: '#94a3b8' } }]
}))

const pieOption = computed(() => ({
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
      radius: ['42%', '68%'],
      center: ['50%', '50%'],
      label: {
        show: false
      },
      labelLine: { show: false },
      data: stats.value.category_summary.map((item) => {
        const color = categoryColorMap.value[item.category] || '#64748b'
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
        year: Number(selectedYear.value),
        month: selectedMonth.value
      }
    })
    stats.value = data
  } finally {
    loading.value = false
  }
}

watch(selectedYear, loadStats, { immediate: true })

function refreshCategoryColors() {
  categoryColorMap.value = categoryColorMapFrom()
}

window.addEventListener(categoryChangedEvent, refreshCategoryColors)

onBeforeUnmount(() => {
  window.removeEventListener(categoryChangedEvent, refreshCategoryColors)
})
</script>
