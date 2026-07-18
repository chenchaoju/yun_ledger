<template>
  <section class="page-stack">
    <div class="toolbar-row">
      <div class="period-picker">
        <el-date-picker v-model="selectedYear" type="year" value-format="YYYY" />
        <el-select v-model="selectedMonth" class="month-select">
          <el-option v-for="month in 12" :key="month" :label="`${month}月`" :value="month" />
        </el-select>
      </div>
      <div class="toolbar-actions">
        <el-button :icon="Refresh" @click="loadStats">刷新</el-button>
        <DataTransferButton @imported="handleImported" />
        <el-button :icon="Wallet" @click="openIncome">收入</el-button>
      </div>
    </div>

    <el-alert
      v-if="stats.monthly_income.is_over_salary"
      type="warning"
      :closable="false"
      show-icon
      :title="`${selectedYear}年${selectedMonth}月支出已超出工资收入 ${currency(Math.abs(stats.monthly_income.salary_balance))}`"
    />

    <div class="metric-grid">
      <article class="metric-card">
        <div class="metric-icon tone-blue"><el-icon><TrendCharts /></el-icon></div>
        <div>
          <span>年度支出</span>
          <strong>{{ currency(stats.year_total) }}</strong>
        </div>
      </article>
      <article class="metric-card">
        <div class="metric-icon tone-pink"><el-icon><Tickets /></el-icon></div>
        <div>
          <span>年度笔数</span>
          <strong>{{ stats.year_count }} 笔</strong>
        </div>
      </article>
      <article class="metric-card">
        <div class="metric-icon tone-teal"><el-icon><Wallet /></el-icon></div>
        <div>
          <span>年度工资收入</span>
          <strong>{{ currency(annualSalaryIncome) }}</strong>
        </div>
      </article>
      <article class="metric-card">
        <div class="metric-icon tone-blue"><el-icon><Wallet /></el-icon></div>
        <div>
          <span>年度额外收入</span>
          <strong>{{ currency(annualExtraIncome) }}</strong>
        </div>
      </article>
    </div>

    <el-tabs v-model="activeAnalysisTab" class="analysis-tabs">
      <el-tab-pane label="年度趋势" name="trend">
        <el-card shadow="never" class="chart-card">
          <BaseChart :option="barOption" :loading="loading" />
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="年度剩余" name="balance">
        <el-card shadow="never" class="chart-card">
          <BaseChart :option="annualBalanceOption" :loading="loading" />
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="每日累计" name="daily">
        <el-card shadow="never" class="chart-card">
          <BaseChart :option="dailyOption" :loading="loading" />
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="月度结构" name="category">
        <div class="content-grid">
          <el-card shadow="never" class="chart-card category-chart-card">
            <BaseChart :option="pieOption" :loading="loading" />
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

    <IncomeFormDialog
      v-model="incomeDialogVisible"
      :year="Number(selectedYear)"
      :month="selectedMonth"
      :income="stats.monthly_income"
      @saved="loadStats"
    />
  </section>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onMounted, ref } from 'vue'
import { Refresh, Tickets, TrendCharts, Wallet } from '@element-plus/icons-vue'
import BaseChart from '../components/BaseChart.vue'
import DataTransferButton from '../components/DataTransferButton.vue'
import IncomeFormDialog from '../components/IncomeFormDialog.vue'
import { categoryColorMap } from '../constants/categories'
import { currency, percent } from '../utils/format'
import http from '../utils/http'

const loading = ref(false)
const selectedYear = ref(dayjs().format('YYYY'))
const selectedMonth = ref(dayjs().month() + 1)
const incomeDialogVisible = ref(false)
const activeAnalysisTab = ref('trend')
const stats = ref(emptyStats())
const annualSalaryIncome = computed(() => {
  return stats.value.monthly_trend.reduce((total, item) => total + Number(item.salary_income || 0), 0)
})
const annualExtraIncome = computed(() => {
  return stats.value.monthly_trend.reduce((total, item) => total + Number(item.extra_income || 0), 0)
})

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
    const balance = Number(item.balance || 0)
    if (isFuture) {
      return {
        ...item,
        isFuture,
        balance: null,
        cumulative: null
      }
    }

    cumulative += balance
    return {
      ...item,
      isFuture,
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

const barOption = computed(() => ({
  title: {
    text: `${selectedYear.value} 年支出与工资对比`,
    subtext: '红色柱表示该月支出超过工资收入',
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
  legend: { top: 28 },
  grid: { left: 54, right: 24, top: 76, bottom: 42 },
  xAxis: { type: 'category', data: stats.value.monthly_trend.map((item) => `${item.month}月`) },
  yAxis: { type: 'value' },
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
      symbolSize: 7,
      lineStyle: { width: 2, color: '#0f766e' },
      itemStyle: { color: '#0f766e' },
      data: stats.value.monthly_trend.map((item) => (isFutureMonth(item.month) ? null : item.salary_income))
    }
  ]
}))

const annualBalanceOption = computed(() => ({
  color: ['#0f766e', '#2563eb'],
  title: {
    text: `${selectedYear.value} 年度剩余金额`,
    subtext: '柱形=每月剩余，蓝线=累计剩余',
    left: 8,
    top: 0,
    textStyle: { fontSize: 13, fontWeight: 700 },
    subtextStyle: { color: '#64748b' }
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
  legend: { top: 28 },
  grid: { left: 54, right: 24, top: 76, bottom: 42 },
  xAxis: { type: 'category', data: yearlyBalanceRows.value.map((item) => `${item.month}月`) },
  yAxis: { type: 'value' },
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
      symbolSize: 7,
      lineStyle: { width: 2, color: '#2563eb' },
      itemStyle: { color: '#2563eb' },
      data: yearlyBalanceRows.value.map((item) => item.cumulative)
    }
  ]
}))

const dailyOption = computed(() => ({
  color: ['#f97316', '#2563eb', '#dc2626'],
  title: {
    text: `${selectedMonth.value} 月每日花费与累计`,
    subtext: '柱形=当日花费，蓝线=累计消费，红虚线=工资收入上限',
    left: 8,
    top: 0,
    textStyle: { fontSize: 13, fontWeight: 700 },
    subtextStyle: { color: '#64748b' }
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
  legend: { top: 28 },
  grid: { left: 54, right: 24, top: 76, bottom: 42 },
  xAxis: { type: 'category', data: dailyRows.value.map((item) => `${item.day}日`) },
  yAxis: { type: 'value' },
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
      symbolSize: 6,
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
      radius: ['42%', '68%'],
      center: ['50%', '50%'],
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

function openIncome() {
  incomeDialogVisible.value = true
}

function handleImported(period) {
  if (period?.year && period?.month) {
    selectedYear.value = String(period.year)
    selectedMonth.value = Number(period.month)
  }
  loadStats()
}

onMounted(loadStats)
</script>
