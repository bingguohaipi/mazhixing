<template>
  <div ref="chartRef" :style="{ height: `${height}px`, width: '100%' }"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import type { ECharts } from 'echarts/core'
import { chartColors } from '@/composables/useEChartsTheme'
import { initChart } from '@/composables/useECharts'

export interface TrendChartItem {
  date: string
  label: string
  count: number
}

const props = withDefaults(
  defineProps<{
    items: TrendChartItem[]
    height?: number
    color?: string
    chartType?: 'bar' | 'line'
  }>(),
  {
    height: 220,
    color: chartColors.primary,
    chartType: 'bar',
  },
)

const chartRef = ref<HTMLDivElement | null>(null)
let chart: ECharts | null = null

const renderChart = async () => {
  if (!chartRef.value) return
  if (!chart) {
    chart = await initChart(chartRef.value)
  }
  const labels = props.items.map((item) => item.label)
  const values = props.items.map((item) => item.count)
  const rotate = labels.length > 12 ? 35 : 0
  const bottom = rotate ? 48 : 32

  const useZoom = labels.length > 12
  const zoomStart = useZoom ? Math.max(0, 100 - Math.round((12 / labels.length) * 100)) : 0

  chart.clear()
  chart.setOption(
    {
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 16, top: 24, bottom: useZoom ? bottom + 28 : bottom },
      dataZoom: useZoom
        ? [
            { type: 'inside', start: zoomStart, end: 100 },
            {
              type: 'slider',
              start: zoomStart,
              end: 100,
              height: 18,
              bottom: 4,
              borderColor: chartColors.grid,
              fillerColor: 'rgba(24, 144, 255, 0.15)',
              handleSize: '80%',
            },
          ]
        : [],
      xAxis: {
        type: 'category',
        data: labels,
        boundaryGap: props.chartType === 'bar',
        axisLabel: {
          color: chartColors.text,
          fontSize: 11,
          rotate,
          interval: labels.length > 20 ? 'auto' : 0,
          showMaxLabel: true,
        },
        axisLine: { lineStyle: { color: chartColors.grid } },
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: { color: chartColors.text, fontSize: 11 },
        splitLine: { lineStyle: { color: chartColors.grid } },
      },
      series: [
        props.chartType === 'line'
          ? {
              type: 'line',
              data: values,
              smooth: false,
              symbol: 'circle',
              symbolSize: 6,
              showSymbol: true,
              lineStyle: { color: props.color, width: 2 },
              itemStyle: { color: props.color },
              areaStyle: { color: props.color, opacity: 0.08 },
            }
          : {
              type: 'bar',
              data: values,
              itemStyle: { color: props.color, borderRadius: [2, 2, 0, 0] },
              barMaxWidth: labels.length > 20 ? 10 : 32,
            },
      ],
    },
    { notMerge: true },
  )
}

const handleResize = () => chart?.resize()

watch(
  () => [props.items, props.chartType] as const,
  () => void renderChart(),
  { deep: true },
)

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
