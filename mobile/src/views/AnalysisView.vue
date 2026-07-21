<template>
  <section class="analysis-page page-stack">
    <div class="analysis-filter-panel">
      <el-date-picker
        v-model="selectedYear"
        type="year"
        value-format="YYYY"
        :editable="false"
        class="analysis-year-picker"
      />
    </div>

    <el-alert
      v-if="stats.monthly_income.is_over_salary"
      type="warning"
      :closable="false"
      show-icon
      :title="`${selectedYear}年${selectedMonth}月支出已超出工资收入 ${currency(Math.abs(stats.monthly_income.salary_balance))}`"
    />

    <el-tabs
      v-model="activeAnalysisTab"
      class="analysis-tabs"
      @touchstart.passive="handleAnalysisTouchStart"
      @touchend="handleAnalysisTouchEnd"
    >
      <el-tab-pane label="年度账单" name="bill">
        <div class="annual-bill-card" :class="{ negative: annualBillSummary.balance < 0 }">
          <span>{{ annualBillSummary.balance >= 0 ? '结余' : '超支' }}</span>
          <strong>{{ formatPlainAmount(Math.abs(annualBillSummary.balance)) }}</strong>
          <div>
            <em>收入 <b>{{ formatPlainAmount(annualBillSummary.income) }}</b></em>
            <em>支出 <b>{{ formatPlainAmount(annualBillSummary.expense) }}</b></em>
          </div>
          <i>¥</i>
        </div>

        <div class="annual-bill-table">
          <div class="annual-bill-head">
            <span>月份</span>
            <span>月收入</span>
            <span>月支出</span>
            <span>月结余</span>
          </div>
          <div v-for="row in annualBillRows" :key="row.month" class="annual-bill-row">
            <strong>{{ String(row.month).padStart(2, '0') }}月</strong>
            <span>{{ formatPlainAmount(row.income) }}</span>
            <span>{{ formatPlainAmount(row.expense) }}</span>
            <span :class="{ negative: row.balance < 0 }">{{ formatPlainAmount(row.balance) }}</span>
          </div>
        </div>
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
      <el-tab-pane label="余额分析" name="totalBalance">
        <el-card shadow="never" class="chart-card">
          <div class="chart-note">
            <span><i class="legend-line blue"></i>蓝线=余额变化</span>
            <span><i class="legend-dot teal"></i>节点=有收入或支出变化</span>
          </div>
          <BaseChart :option="totalBalanceOption" :loading="loading" />
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
        <el-card shadow="never" class="chart-card">
          <div class="monthly-structure-toolbar">
            <el-select v-model="selectedMonth" class="month-select">
              <el-option v-for="month in 12" :key="month" :label="`${month}月`" :value="month" />
            </el-select>
          </div>
          <div class="chart-note">
            <span>当前显示 {{ selectedYear }} 年 {{ selectedMonth }} 月分类结构</span>
          </div>
          <BaseChart :option="pieOption" :loading="loading" />
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
      </el-tab-pane>
    </el-tabs>

  </section>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import BaseChart from '../components/BaseChart.vue'
import { categoryChangedEvent, categoryColorMapFrom } from '../constants/categories'
import { currency } from '../utils/format'
import http from '../utils/http'

const loading = ref(false)
const selectedYear = ref(dayjs().format('YYYY'))
const selectedMonth = ref(dayjs().month() + 1)
const activeAnalysisTab = ref('bill')
const touchStartX = ref(0)
const stats = ref(emptyStats())
const categoryColorMap = ref(categoryColorMapFrom())
const analysisTabOrder = ['bill', 'trend', 'balance', 'totalBalance', 'daily', 'category']
const annualBalance = computed(() => {
  return yearlyBalanceRows.value.reduce((total, item) => {
    if (!item.hasExpense) return total
    return total + Number(item.balance || 0)
  }, 0)
})
const annualSalaryIncome = computed(() => {
  return yearlyBalanceRows.value.reduce((total, item) => {
    if (!item.hasExpense) return total
    return total + Number(item.salary_income || 0)
  }, 0)
})
const annualExtraIncome = computed(() => {
  return stats.value.monthly_trend.reduce((total, item) => total + Number(item.extra_income || 0), 0)
})

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

const topCategorySummary = computed(() => {
  const [topItem] = [...categoryStructureRows.value].sort((left, right) => Number(right.total || 0) - Number(left.total || 0))
  if (!topItem) return null
  return {
    category: topItem.category,
    percent: topItem.percent
  }
})

const annualBillRows = computed(() => {
  const maxMonth = selectedYear.value === dayjs().format('YYYY') ? dayjs().month() + 1 : 12
  return stats.value.monthly_trend
    .filter((item) => item.month <= maxMonth)
    .map((item) => {
      const hasExpense = Number(item.total || 0) > 0
      const salaryIncome = hasExpense ? Number(item.salary_income || 0) : 0
      const extraIncome = Number(item.extra_income || 0)
      const income = Number((salaryIncome + extraIncome).toFixed(2))
      const expense = hasExpense ? Number(item.total || 0) : 0
      return {
        month: item.month,
        income,
        expense,
        balance: Number((income - expense).toFixed(2))
      }
    })
    .reverse()
})

const annualBillSummary = computed(() => {
  return annualBillRows.value.reduce(
    (summary, row) => {
      summary.income += Number(row.income || 0)
      summary.expense += Number(row.expense || 0)
      summary.balance += Number(row.balance || 0)
      return summary
    },
    { income: 0, expense: 0, balance: 0 }
  )
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
    const hasExpense = hasAnalyzedExpense(item)
    const balance = Number(item.balance || 0)
    if (isFuture || !hasExpense) {
      return {
        ...item,
        isFuture,
        hasExpense,
        balance: null,
        cumulative: null
      }
    }

    if (hasExpense) {
      cumulative += balance
    }

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

function hasAnalyzedExpense(item) {
  return Boolean(item.has_expense) || Number(item.total || 0) > 0
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

function chartPointLabel(value) {
  if (!isVisibleChartValue(value)) return ''
  const number = Number(value || 0)
  if (Math.abs(number) < 0.005) return ''
  if (Math.abs(number) >= 10000) return `${Number((number / 10000).toFixed(1))}万`
  if (Math.abs(number) >= 1000) return `${Number((number / 1000).toFixed(1))}k`
  return Number(number.toFixed(0)).toString()
}

function formatPlainAmount(value) {
  const number = Number(value || 0)
  if (!number) return '0'
  return Number(number.toFixed(2)).toString()
}

function switchAnalysisTab(direction) {
  const currentIndex = analysisTabOrder.indexOf(activeAnalysisTab.value)
  if (currentIndex < 0) return
  const nextIndex = currentIndex + direction
  if (nextIndex < 0 || nextIndex >= analysisTabOrder.length) return
  activeAnalysisTab.value = analysisTabOrder[nextIndex]
}

function handleAnalysisTouchStart(event) {
  touchStartX.value = event.changedTouches?.[0]?.clientX || 0
}

function handleAnalysisTouchEnd(event) {
  const endX = event.changedTouches?.[0]?.clientX || 0
  const distance = endX - touchStartX.value
  if (Math.abs(distance) < 48) return
  switchAnalysisTab(distance < 0 ? 1 : -1)
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
      if (!hasAnalyzedExpense(item)) return `${item.month}月<br/>暂无支出记录`
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
      label: {
        show: true,
        position: 'top',
        fontSize: 10,
        color: '#475569',
        formatter: (params) => chartPointLabel(params.value)
      },
      data: stats.value.monthly_trend.map((item) => ({
        value: isFutureMonth(item.month) || !hasAnalyzedExpense(item) ? null : item.total,
        itemStyle: { color: !isFutureMonth(item.month) && hasAnalyzedExpense(item) && item.is_over_salary ? '#dc2626' : '#2563eb' }
      }))
    },
    {
      name: '工资收入',
      type: 'line',
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 2, color: '#0f766e' },
      itemStyle: { color: '#0f766e' },
      data: stats.value.monthly_trend.map((item) => (isFutureMonth(item.month) || !hasAnalyzedExpense(item) ? null : item.salary_income))
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
      if (!item.hasExpense) return `${item.month}月<br/>暂无支出记录`
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
      label: {
        show: true,
        position: 'top',
        fontSize: 10,
        color: '#475569',
        formatter: (params) => chartPointLabel(params.value)
      },
      data: yearlyBalanceRows.value.map((item) => ({
        value: item.hasExpense ? item.balance : null,
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
  ],
  graphic: yearlyBalanceRows.value.some((item) => item.hasExpense && isVisibleChartValue(item.balance))
    ? []
    : [{ type: 'text', left: 'center', top: 'middle', style: { text: '暂无支出记录', fill: '#94a3b8' } }]
}))

const totalBalanceOption = computed(() => ({
  color: ['#2563eb'],
  title: {
    text: `${selectedYear.value} 余额分析`,
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
      if (!isVisibleChartValue(item.total_balance)) return `${item.month}月<br/>暂无余额变化`
      return [
        `${item.month}月`,
        `余额：${currency(item.total_balance)}`,
        `收入：${currency(item.total_income)}`,
        `支出：${currency(item.total)}`
      ].join('<br/>')
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
      name: '余额',
      type: 'line',
      smooth: true,
      connectNulls: false,
      symbolSize: 7,
      label: {
        show: true,
        position: 'top',
        fontSize: 10,
        color: '#2563eb',
        formatter: (params) => chartPointLabel(params.value)
      },
      lineStyle: { width: 3, color: '#2563eb' },
      itemStyle: { color: '#2563eb' },
      areaStyle: { opacity: 0.08 },
      data: stats.value.monthly_trend.map((item) => (isFutureMonth(item.month) ? null : item.total_balance))
    }
  ],
  graphic: stats.value.monthly_trend.some((item) => !isFutureMonth(item.month) && isVisibleChartValue(item.total_balance))
    ? []
    : [{ type: 'text', left: 'center', top: 'middle', style: { text: '暂无余额变化', fill: '#94a3b8' } }]
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
      label: {
        show: true,
        position: 'top',
        fontSize: 9,
        color: '#475569',
        formatter: (params) => chartPointLabel(params.value)
      },
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
      radius: ['40%', '64%'],
      center: ['50%', '48%'],
      avoidLabelOverlap: false,
      label: {
        show: true,
        position: 'outer',
        color: '#334155',
        fontSize: 10,
        fontWeight: 700,
        lineHeight: 14,
        formatter: (params) => `${params.name}\n${currency(params.value)}`
      },
      labelLine: { show: true, length: 12, length2: 6 },
      labelLayout: { hideOverlap: false },
      data: stats.value.category_summary.map((item) => {
        const color = categoryColorMap.value[item.category] || '#64748b'
        return {
          name: item.category,
          value: item.total,
          itemStyle: { color },
          label: { color: '#334155' },
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
        year: Number(selectedYear.value),
        month: selectedMonth.value
      }
    })
    stats.value = data
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
watch(selectedYear, loadStats)
watch(selectedMonth, loadStats)

function refreshCategoryColors() {
  categoryColorMap.value = categoryColorMapFrom()
}

window.addEventListener(categoryChangedEvent, refreshCategoryColors)

onBeforeUnmount(() => {
  window.removeEventListener(categoryChangedEvent, refreshCategoryColors)
})
</script>
