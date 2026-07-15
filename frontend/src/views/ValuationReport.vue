<template>
  <div class="report-container">
    <div class="header">
      <el-button @click="goBack">返回</el-button>
      <h1>{{ stockInfo.name || '加载中...' }} ({{ stockInfo.code || route.params.code }})</h1>
    </div>

    <div v-loading="loading" class="report-content">
      <div v-if="valuation" class="report-body">
        <div class="summary-card">
          <div class="summary-item">
            <span class="label">估值分</span>
            <span class="value" :class="getStatusClass(valuation.status)">{{ valuation.score }}</span>
          </div>
          <div class="summary-item">
            <span class="label">百分位</span>
            <span class="value">{{ valuation.percentile }}%</span>
          </div>
          <div class="summary-item">
            <span class="label">状态</span>
            <span class="value" :class="getStatusClass(valuation.status)">{{ valuation.status }}</span>
          </div>
          <div class="summary-item">
            <span class="label">PE</span>
            <span class="value">{{ valuation.pe }}</span>
          </div>
          <div class="summary-item">
            <span class="label">PB</span>
            <span class="value">{{ valuation.pb }}</span>
          </div>
          <div class="summary-item">
            <span class="label">价格</span>
            <span class="value">¥{{ valuation.price }}</span>
          </div>
        </div>

        <div class="chart-section">
          <h3>估值曲线</h3>
          <div ref="chartRef" style="height: 400px"></div>
        </div>

        <div class="factors-section">
          <h3>因子得分详情</h3>
          <el-table :data="factorList" border>
            <el-table-column prop="name" label="因子" width="180" />
            <el-table-column label="得分" min-width="200">
              <template #default="{ row }">
                <el-progress :percentage="Math.round(row.score)" :color="getScoreColor(row.score)" />
              </template>
            </el-table-column>
            <el-table-column prop="score" label="分数" width="100" />
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { stockAPI } from '../api'

const router = useRouter()
const route = useRoute()
const stockInfo = ref({ code: '', name: '' })
const valuation = ref(null)
const chartRef = ref(null)
const factorList = ref([])
const loading = ref(true)
let chartInstance = null

const factorNames = {
  pe: 'PE评分',
  pb: 'PB评分',
  peg: 'PEG评分',
  ma_deviation: 'MA偏离度',
  volatility: '波动率',
  volume: '量能',
  roe: 'ROE评分',
  dividend: '股息率',
  ai_analysis: 'AI深度分析'
}

onMounted(async () => {
  await loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

const loadData = async () => {
  loading.value = true
  const code = route.params.code
  try {
    stockInfo.value = await stockAPI.getInfo(code)
    valuation.value = await stockAPI.getValuation(code)

    factorList.value = Object.entries(valuation.value.factors || {}).map(([code, score]) => ({
      name: factorNames[code] || code,
      score: score
    }))

    await loadHistory()
  } catch (error) {
    ElMessage.error('加载数据失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const loadHistory = async () => {
  try {
    const history = await stockAPI.getHistory(route.params.code)
    await nextTick()
    renderChart(history)
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

const renderChart = (history) => {
  if (!chartRef.value) return
  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)

  const dates = history.map(h => h.date)
  const scores = history.map(h => h.score)
  const prices = history.map(h => h.price)

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['估值分', '价格']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: [
      {
        type: 'value',
        name: '估值分',
        min: 0,
        max: 100
      },
      {
        type: 'value',
        name: '价格'
      }
    ],
    series: [
      {
        name: '估值分',
        type: 'line',
        data: scores,
        smooth: true,
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '价格',
        type: 'line',
        yAxisIndex: 1,
        data: prices,
        smooth: true,
        itemStyle: { color: '#67C23A' }
      }
    ]
  })
}

const getStatusClass = (status) => {
  const classes = {
    '极度低估': 'status-very-low',
    '低估': 'status-low',
    '中性偏低': 'status-neutral-low',
    '中性偏高': 'status-neutral-high',
    '高估': 'status-high',
    '极度高估': 'status-very-high'
  }
  return classes[status] || ''
}

const getScoreColor = (score) => {
  if (score >= 80) return '#10b981'
  if (score >= 70) return '#3b82f6'
  if (score >= 60) return '#6b7280'
  if (score >= 40) return '#f59e0b'
  if (score >= 20) return '#ef4444'
  return '#dc2626'
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.report-container {
  padding: 20px;
}
.header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}
.header h1 {
  margin: 0;
  color: #333;
}
.report-content {
  min-height: 400px;
}
.summary-card {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.summary-item {
  background: #f5f7fa;
  padding: 15px 25px;
  border-radius: 8px;
  text-align: center;
  min-width: 100px;
}
.summary-item .label {
  display: block;
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}
.summary-item .value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}
.status-very-low { color: #10b981; }
.status-low { color: #3b82f6; }
.status-neutral-low { color: #6b7280; }
.status-neutral-high { color: #f59e0b; }
.status-high { color: #ef4444; }
.status-very-high { color: #dc2626; }
.chart-section, .factors-section {
  margin-bottom: 20px;
  background: white;
  padding: 20px;
  border-radius: 8px;
}
.chart-section h3, .factors-section h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #333;
}
</style>
