<template>
  <div ref="chartRef" class="base-chart"></div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GraphicComponent,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent
} from 'echarts/components'
import { init, use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

use([
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  GraphicComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
  CanvasRenderer
])

const props = defineProps({
  option: {
    type: Object,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const chartRef = ref(null)
let chart = null
let observer = null

function renderChart() {
  if (!chart || !props.option) return
  chart.setOption(props.option, true)
  props.loading ? chart.showLoading() : chart.hideLoading()
}

onMounted(async () => {
  await nextTick()
  chart = init(chartRef.value)
  observer = new ResizeObserver(() => chart?.resize())
  observer.observe(chartRef.value)
  renderChart()
})

watch(() => props.option, renderChart, { deep: true })
watch(() => props.loading, renderChart)

onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
})
</script>
