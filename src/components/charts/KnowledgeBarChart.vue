<template>
  <div ref="chartRef" :style="{ height: `${height}px`, width: '100%' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import type { ECharts } from 'echarts/core'
import { chartColors, masteryColor } from '@/composables/useEChartsTheme'
import { initChart } from '@/composables/useECharts'

export interface KnowledgeChartItem {
  name: string
  mastery_rate: number
}

const props = withDefaults(
  defineProps<{
    items: KnowledgeChartItem[]
    height?: number
    horizontal?: boolean
  }>(),
  {
    height: 280,
    horizontal: true,
  },
)

const chartRef = ref<HTMLDivElement | null>(null)
let chart: ECharts | null = null

const renderChart = async () => {
  if (!chartRef.value || props.items.length === 0) return
  if (!chart) {
    chart = await initChart(chartRef.value)
  }

  const sorted = [...props.items].sort((a, b) => a.mastery_rate - b.mastery_rate)
  const names = sorted.map((item) => item.name)
  const values = sorted.map((item) => item.mastery_rate)
  const colors = sorted.map((item) => masteryColor(item.mastery_rate))

  if (props.horizontal) {
    chart.setOption({
      tooltip: {
        trigger: 'axis',
        formatter: (params: unknown) => {
          const row = (params as { value: number; name: string }[])[0]
          return `${row.name}<br/>掌握率：${row.value}%`
        },
      },
      grid: { left: 80, right: 24, top: 16, bottom: 16 },
      xAxis: {
        type: 'value',
        max: 100,
        axisLabel: { formatter: '{value}%', color: chartColors.text },
        splitLine: { lineStyle: { color: chartColors.grid } },
      },
      yAxis: {
        type: 'category',
        data: names,
        axisLabel: { color: chartColors.text, fontSize: 11 },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: 'bar',
          data: values.map((value, index) => ({
            value,
            itemStyle: { color: colors[index], borderRadius: [0, 4, 4, 0] },
          })),
          barMaxWidth: 18,
        },
      ],
    })
    return
  }

  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 24, bottom: 48 },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: { color: chartColors.text, rotate: 30, fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { formatter: '{value}%', color: chartColors.text },
      splitLine: { lineStyle: { color: chartColors.grid } },
    },
    series: [
      {
        type: 'bar',
        data: values.map((value, index) => ({
          value,
          itemStyle: { color: colors[index], borderRadius: [4, 4, 0, 0] },
        })),
        barMaxWidth: 32,
      },
    ],
  })
}

const handleResize = () => chart?.resize()

watch(() => props.items, () => void renderChart(), { deep: true })

onMounted(() => {
  void renderChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>
