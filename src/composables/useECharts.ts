import type { ECharts } from 'echarts/core'

let echartsModule: typeof import('echarts/core') | null = null
let registered = false

async function loadEChartsCore() {
  if (!echartsModule) {
    echartsModule = await import('echarts/core')
  }
  if (!registered) {
    const [{ BarChart }, { GridComponent, TooltipComponent }, { CanvasRenderer }] = await Promise.all([
      import('echarts/charts'),
      import('echarts/components'),
      import('echarts/renderers'),
    ])
    echartsModule.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])
    registered = true
  }
  return echartsModule
}

export async function initChart(el: HTMLElement): Promise<ECharts> {
  const echarts = await loadEChartsCore()
  return echarts.init(el)
}
