<template>
  <div ref="chartRef" style="width: 100%; height: 300px"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({
      labels: [],
      paces: [],
      heart_rates: [],
    }),
  },
})

const chartRef = ref(null)
let chartInstance = null

// 将秒数转换为 M'SS" 格式
const formatPace = (seconds) => {
  if (!seconds || seconds === 0) return "N/A"
  const minutes = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${minutes}'${secs.toString().padStart(2, '0')}"`
}

const initChart = () => {
  if (!chartRef.value) return

  // 转换数据格式
  const chartData = props.data.labels.map((label, index) => ({
    label,
    pace: props.data.paces[index] || 0,
    heartRate: props.data.heart_rates[index] || 0,
  }))

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value, 'dark')
  }

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1c1c1e',
      borderColor: '#00ccff',
      borderWidth: 1,
      textStyle: {
        color: '#ffffff',
      },
      formatter: (params) => {
        let result = params[0].name + '<br/>'
        params.forEach((param) => {
          if (param.seriesName === '配速') {
            result += `${param.marker}${param.seriesName}: ${formatPace(param.value)}<br/>`
          } else {
            result += `${param.marker}${param.seriesName}: ${param.value} bpm<br/>`
          }
        })
        return result
      },
    },
    legend: {
      data: ['心率', '配速'],
      textStyle: {
        color: '#ffffff',
      },
      top: 10,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: chartData.map((d) => d.label),
      axisLine: {
        lineStyle: {
          color: '#333333',
        },
      },
      axisLabel: {
        color: '#999999',
      },
    },
    yAxis: [
      {
        type: 'value',
        name: '心率 (bpm)',
        position: 'left',
        axisLine: {
          lineStyle: {
            color: '#ff4444',
          },
        },
        axisLabel: {
          color: '#ff4444',
        },
        nameTextStyle: {
          color: '#ff4444',
        },
        splitLine: {
          lineStyle: {
            color: '#1a1a1a',
          },
        },
      },
      {
        type: 'value',
        name: '配速',
        position: 'right',
        inverse: true, // 逆序
        axisLine: {
          lineStyle: {
            color: '#00ccff',
          },
        },
        axisLabel: {
          color: '#00ccff',
          formatter: (value) => formatPace(value),
        },
        nameTextStyle: {
          color: '#00ccff',
        },
        splitLine: {
          show: false,
        },
      },
    ],
    series: [
      {
        name: '心率',
        type: 'line',
        yAxisIndex: 0,
        data: chartData.map((d) => d.heartRate),
        smooth: true,
        lineStyle: {
          color: '#ff4444',
          width: 2,
        },
        itemStyle: {
          color: '#ff4444',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: 'rgba(255, 68, 68, 0.3)',
              },
              {
                offset: 1,
                color: 'rgba(255, 68, 68, 0.05)',
              },
            ],
          },
        },
      },
      {
        name: '配速',
        type: 'line',
        yAxisIndex: 1,
        data: chartData.map((d) => d.pace),
        smooth: true,
        lineStyle: {
          color: '#00ccff',
          width: 2,
        },
        itemStyle: {
          color: '#00ccff',
        },
      },
    ],
  }

  chartInstance.setOption(option)
}

const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(() => {
  if (props.data && props.data.labels && props.data.labels.length > 0) {
    initChart()
  }
  window.addEventListener('resize', resizeChart)
})

watch(
  () => props.data,
  () => {
    if (props.data && props.data.labels && props.data.labels.length > 0) {
      initChart()
    }
  },
  { deep: true }
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>
