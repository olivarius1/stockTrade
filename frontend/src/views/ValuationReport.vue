<template>
  <div class="report-container">
    <div class="header">
      <el-button @click="goBack">返回</el-button>
      <h1>{{ stockInfo.name || '加载中...' }} ({{ stockInfo.code || route.params.code }})</h1>
      <div class="header-actions">
        <el-button type="primary" plain @click="$router.push('/')">自选股</el-button>
      </div>
    </div>

    <div v-loading="loading" class="report-content">
      <!-- 无报告空状态 -->
      <div v-if="!loading && !valuation" class="empty-state">
        <el-empty description="该股票暂无估值报告">
          <template #default>
            <p class="empty-hint">股票 <strong>{{ stockInfo.name || route.params.code }}</strong> 尚未计算估值报告</p>
            <p class="empty-hint">请先在首页「自选股」中添加该股票，再通过「批量计算」生成报告</p>
            <el-button type="primary" @click="goBack">返回首页</el-button>
          </template>
        </el-empty>
      </div>

      <div v-if="valuation" class="report-body">
        <!-- 计算时间 -->
        <div class="report-meta">
          <span class="meta-item">
            <el-icon><Clock /></el-icon>
            计算时间：{{ valuation.date }}
          </span>
        </div>
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
            <span class="label">档位</span>
            <span class="value" :class="getBandClass">{{ valuation.score_bands?.band_label || '--' }}</span>
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

        <!-- 分级参考线说明 -->
        <div v-if="valuation.score_bands" class="bands-info">
          <span class="bands-label">分级参考</span>
          <span class="bands-range">极低 &lt;{{ valuation.score_bands.thresholds.p10 }}</span>
          <span class="bands-range">偏低 {{ valuation.score_bands.thresholds.p10 }}-{{ valuation.score_bands.thresholds.p25 }}</span>
          <span class="bands-range bands-neutral">中性 {{ valuation.score_bands.thresholds.p25 }}-{{ valuation.score_bands.thresholds.p75 }}</span>
          <span class="bands-range">偏高 {{ valuation.score_bands.thresholds.p75 }}-{{ valuation.score_bands.thresholds.p90 }}</span>
          <span class="bands-range">极高 ≥{{ valuation.score_bands.thresholds.p90 }}</span>
          <span class="bands-source">({{ valuation.score_bands.source === 'stock' ? '个股' : '同模型' }} · {{ valuation.score_bands.sample_count }}天)</span>
        </div>

        <div class="chart-section">
          <h3>估值曲线 <span class="chart-hint">（点击曲线上数据点可选为对比日期）</span></h3>
          <div ref="chartRef" style="height: 400px"></div>
        </div>

        <div class="factors-section">
          <div class="factors-header">
            <h3>因子得分详情</h3>
            <!-- 操作区始终可见：对比按钮 + 日期输入框，可随时修改日期 -->
            <div class="factors-actions">
              <el-button size="small" @click="toggleDateInput">
                {{ showDateInput || showCompare ? '收起' : '对比' }}
              </el-button>
              <div v-if="showDateInput || showCompare" class="date-input-group">
                <el-input
                  v-model="dateInput"
                  :placeholder="selectedDate || '如 2019-11-01'"
                  size="small"
                  style="width: 140px"
                  @keyup.enter="onDateInputConfirm"
                />
                <el-button size="small" type="primary" @click="onDateInputConfirm">确认</el-button>
              </div>
            </div>
          </div>
          <!-- 对比状态条：[历史日期 ×] → 最新，删除按钮紧跟历史日期避免误解 -->
          <div v-if="showCompare" class="compare-tip">
            <span class="tip-label">当前对比：</span>
            <span class="tip-selected">{{ selectedDate }}</span>
            <span class="tip-close" @click="clearCompare" title="删除对比">×</span>
            <span class="tip-arrow">→</span>
            <span class="tip-latest">最新({{ latestDate }})</span>
          </div>
          <!-- :key 随 showCompare 变化，强制重建表格。
               规避 Element Plus el-table-column 动态 v-if 导致行渲染不全的已知问题。 -->
          <el-table :data="factorList" :key="showCompare ? 'with-compare' : 'single'" border>
            <el-table-column label="因子" width="160">
              <template #default="{ row }">
                <span>{{ row.name }}</span>
                <span v-if="!row.participated" class="not-participated-tag">未参与</span>
              </template>
            </el-table-column>
            <el-table-column label="得分对比" min-width="320">
              <template #default="{ row }">
                <!-- 未参与因子：显示灰色文字，不渲染进度条 -->
                <div v-if="!row.participated" class="not-participated-cell">未参与</div>
                <div v-else class="dual-bar">
                  <!-- 上方深色：最新一天，用该因子的深色 -->
                  <div class="bar-row bar-latest">
                    <span class="bar-tag bar-tag-latest">最新</span>
                    <el-progress
                      :percentage="Math.round(row.latestScore)"
                      :color="row.deepColor"
                      :stroke-width="14"
                      :show-text="false"
                    />
                    <span class="bar-value">{{ row.latestScore.toFixed(1) }}</span>
                  </div>
                  <!-- 下方浅色：选择的历史日期，用该因子的同色系浅色 -->
                  <div v-if="showCompare" class="bar-row bar-selected">
                    <span class="bar-tag bar-tag-selected">历史</span>
                    <el-progress
                      :percentage="Math.round(row.selectedScore)"
                      :color="row.lightColor"
                      :stroke-width="14"
                      :show-text="false"
                    />
                    <span class="bar-value">{{ row.selectedScore.toFixed(1) }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="变化" width="80" v-if="showCompare">
              <template #default="{ row }">
                <span v-if="!row.participated">—</span>
                <span v-else :class="getDeltaClass(row.latestScore - row.selectedScore)">
                  {{ formatDelta(row.latestScore - row.selectedScore) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 估值报告页面。
 *
 * 核心交互：因子得分历史对比。
 * 用户点击「对比」按钮 → 选择历史日期 → 表格显示该日期与最新的因子得分对比。
 * 对比状态条右上角 X 可删除对比，恢复单列显示。
 * 放弃光标联动方案：光标离开图表区域（如向上滚动查看表格）时对比会消失，体验不佳。
 */
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Clock } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { stockAPI, valuationAPI } from '../api'

const router = useRouter()
const route = useRoute()
const stockInfo = ref({ code: '', name: '' })
const valuation = ref(null)
const chartRef = ref(null)
const factorList = ref([])
const loading = ref(true)
const historyData = ref([])
const selectedDate = ref(null)
const selectedFactors = ref({})
// 手动输入日期相关状态
const showDateInput = ref(false)
const dateInput = ref('')
let chartInstance = null

const factorNames = {
  pe_score: 'PE评分',
  pb_score: 'PB评分',
  peg_score: 'PEG评分',
  ma_score: 'MA偏离度',
  volatility_score: '波动率',
  volume_score: '量能',
  roe_score: 'ROE评分',
  dividend_score: '股息率',
  ai_score: 'AI深度分析'
}

/**
 * 前端 factorList 的 key 与后端 factors 返回的 code 映射。
 * 用于判断该因子是否实际参与当前估值模型的计算。
 */
const factorKeyToCode = {
  pe_score: 'pe',
  pb_score: 'pb',
  peg_score: 'peg',
  ma_score: 'ma_deviation',
  volatility_score: 'volatility',
  volume_score: 'volume',
  roe_score: 'roe',
  dividend_score: 'dividend',
  ai_score: 'ai_analysis'
}

/**
 * 每个因子分配固定色系（深色/浅色成对），最新用深色、历史用同色系浅色。
 * 不同因子色系不同，视觉上一眼区分；同因子深浅区分最新/历史。
 */
const factorColors = {
  pe_score: { deep: '#3b82f6', light: '#bfdbfe' },         // 蓝
  pb_score: { deep: '#10b981', light: '#a7f3d0' },         // 绿
  peg_score: { deep: '#8b5cf6', light: '#ddd6fe' },        // 紫
  ma_score: { deep: '#f59e0b', light: '#fde68a' },         // 橙
  volatility_score: { deep: '#ef4444', light: '#fecaca' }, // 红
  volume_score: { deep: '#06b6d4', light: '#a5f3fc' },     // 青
  roe_score: { deep: '#ec4899', light: '#fbcfe8' },        // 粉
  dividend_score: { deep: '#84cc16', light: '#d9f99d' },   // 黄绿
  ai_score: { deep: '#6366f1', light: '#c7d2fe' },         // 靛
}

const latestDate = computed(() => {
  if (historyData.value.length === 0) return null
  return historyData.value[historyData.value.length - 1].date
})

const latestFactors = computed(() => {
  if (historyData.value.length === 0) return {}
  return historyData.value[historyData.value.length - 1]
})

/** 仅当选中了非最新日期时才显示对比列 */
const showCompare = computed(() => {
  return selectedDate.value && selectedDate.value !== latestDate.value
})

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
  valuation.value = null
  const code = route.params.code
  try {
    stockInfo.value = await stockAPI.getInfo(code)
  } catch (error) {
    // 股票信息获取失败，保留代码显示
    stockInfo.value = { code, name: '' }
  }
  try {
    valuation.value = await valuationAPI.getReport(code)
    await loadHistory()
  } catch (error) {
    // 估值报告不存在时不弹错误，由空状态组件提示
    console.log('No valuation report found for:', code)
  } finally {
    loading.value = false
  }
}

const loadHistory = async () => {
  try {
    const history = await valuationAPI.getHistory(route.params.code)
    historyData.value = history
    await nextTick()
    renderChart(history)
    initFactorList()
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

const initFactorList = () => {
  const latest = latestFactors.value
  // valuation.factors 是后端返回的参与计算的因子 code 集合
  const participatedCodes = valuation.value?.factors
    ? Object.keys(valuation.value.factors)
    : []
  factorList.value = Object.keys(factorNames).map(key => {
    const code = factorKeyToCode[key]
    return {
      name: factorNames[key],
      key: key,
      // 该因子是否参与当前模型计算
      participated: participatedCodes.includes(code),
      // 携带该因子的色系对，模板中直接取用
      deepColor: factorColors[key]?.deep || '#409EFF',
      lightColor: factorColors[key]?.light || '#d9ecff',
      latestScore: latest[key] || 0,
      selectedScore: latest[key] || 0
    }
  })
}

const updateFactorList = () => {
  const latest = latestFactors.value
  const selected = selectedFactors.value

  factorList.value = factorList.value.map(item => ({
    ...item,
    latestScore: latest[item.key] || 0,
    selectedScore: selected[item.key] || 0
  }))
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

  updateChartOption(history, dates, scores, prices)

  // 点击图表数据点选为对比日期。
  // 用 click 事件而非光标停留：点击是主动操作，稳定可靠，不受滚动影响。
  // 点击非最新日期时建立对比，点击最新日期时清除对比。
  chartInstance.on('click', (params) => {
    if (params.componentType !== 'series') return
    const idx = params.dataIndex
    if (idx == null || idx < 0 || idx >= history.length) return
    const item = history[idx]
    // 点击最新日期：本身就是基准，无需对比，清除已有对比
    if (item.date === latestDate.value) {
      clearCompare()
      return
    }
    selectedDate.value = item.date
    selectedFactors.value = item
    updateFactorList()
    // 刷新图表标记，高亮选中的历史日期点位
    refreshChartMark()
    // 滚动到因子表格，方便查看对比结果
    document.querySelector('.factors-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

/**
 * 构建/更新图表 option。
 * 独立为函数：selectedDate 变化时只需调用此函数刷新 markPoint 标记，
 * 无需销毁重建图表实例，保留已有交互状态。
 */
const updateChartOption = (history, dates, scores, prices) => {
  // 查找选中日期对应的索引，用于 markPoint 标记
  const selectedIdx = selectedDate.value
    ? history.findIndex(h => h.date === selectedDate.value)
    : -1

  // 选中点位的 markPoint：大圆圈高亮
  const markPoint = selectedIdx >= 0 ? {
    symbol: 'circle',
    symbolSize: 16,
    itemStyle: { color: '#f56c6c', borderColor: '#fff', borderWidth: 2 },
    label: { show: false },
    data: [{ xAxis: selectedIdx, yAxis: scores[selectedIdx] }]
  } : undefined

  // 百分位参考线（语义色）+ 选中日期竖线，合并到同一 markLine。
  // 使用 score_bands 的 P90/P50/P10 作为低估/中性/高估分界线；
  // 无 score_bands 时回退到固定值 80/40/20。
  const bands = valuation.value?.score_bands?.thresholds
  const p90 = bands?.p90 ?? 80
  const p50 = bands?.p50 ?? 40
  const p10 = bands?.p10 ?? 20
  const markLineData = [
    {
      yAxis: p90,
      lineStyle: { color: '#10b981', type: 'dashed', width: 1.5 },
      label: { show: true, formatter: `P90:${p90}`, position: 'end', color: '#10b981', fontSize: 11 }
    },
    {
      yAxis: p50,
      lineStyle: { color: '#f59e0b', type: 'dashed', width: 1.5 },
      label: { show: true, formatter: `P50:${p50}`, position: 'end', color: '#f59e0b', fontSize: 11 }
    },
    {
      yAxis: p10,
      lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 },
      label: { show: true, formatter: `P10:${p10}`, position: 'end', color: '#ef4444', fontSize: 11 }
    }
  ]
  // 选中日期竖线，仅对比时添加
  if (selectedIdx >= 0) {
    markLineData.push({
      xAxis: selectedIdx,
      lineStyle: { color: '#f56c6c', type: 'dashed', width: 1.5 },
      label: { show: false }
    })
  }
  const markLine = {
    symbol: 'none',
    silent: true,
    data: markLineData
  }

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params) => {
        if (!params || params.length === 0) return ''
        const date = params[0].axisValue
        const score = params[0].value
        const price = params[1]?.value || 0
        return `<strong>${date}</strong><br/>估值分: ${score}<br/>价格: ¥${price}`
      }
    },
    legend: { data: ['估值分', '价格'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: dates },
    yAxis: [
      { type: 'value', name: '估值分', min: 0, max: 100 },
      { type: 'value', name: '价格' }
    ],
    series: [
      {
        name: '估值分', type: 'line', data: scores, smooth: true,
        // 粗线 + 数据点，保持视觉主体地位
        symbol: 'circle', symbolSize: 6,
        lineStyle: { width: 2, color: '#409EFF' },
        itemStyle: { color: '#409EFF' },
        emphasis: { itemStyle: { borderWidth: 2 } },
        // z 层级在上，避免被价格面积图遮挡
        z: 2,
        markPoint,
        markLine,
      },
      {
        name: '价格', type: 'line', yAxisIndex: 1, data: prices, smooth: true,
        // 浅灰细线 + 半透明面积填充，视觉弱化不抢主视觉
        symbol: 'none',
        lineStyle: { width: 1, color: '#c0c4cc' },
        areaStyle: { color: 'rgba(192,196,204,0.25)' },
        itemStyle: { color: '#c0c4cc' },
        // z 层级在下，作为背景参考
        z: 1,
      }
    ]
  })
}

/**
 * 切换日期输入框显示状态。
 * 未对比时：切换输入框显隐。
 * 已对比时：收起输入框并清除对比（点「收起」等同删除对比）。
 */
const toggleDateInput = () => {
  if (showCompare.value) {
    // 已对比状态，收起即清除对比
    clearCompare()
    showDateInput.value = false
    dateInput.value = ''
    return
  }
  showDateInput.value = !showDateInput.value
  if (!showDateInput.value) {
    dateInput.value = ''
  }
}

/**
 * 解析多种常用日期格式为 YYYY-MM-DD。
 * 支持：20191101、2019-11-1、2019-11-01、2019/11/1 等。
 * 解析失败返回 null。
 */
const parseDateInput = (input) => {
  if (!input) return null
  const str = String(input).trim()
  // 纯数字 8 位：20191101 → 2019-11-01
  if (/^\d{8}$/.test(str)) {
    return `${str.slice(0, 4)}-${str.slice(4, 6)}-${str.slice(6, 8)}`
  }
  // 已有分隔符：统一替换为 - 再 split
  const normalized = str.replace(/[/.]/g, '-')
  const parts = normalized.split('-').filter(Boolean)
  if (parts.length !== 3) return null
  const [y, m, d] = parts
  if (!y || !m || !d) return null
  // 补零：2019-11-1 → 2019-11-01
  const mm = m.padStart(2, '0')
  const dd = d.padStart(2, '0')
  if (!/^\d{4}$/.test(y) || !/^\d{2}$/.test(mm) || !/^\d{2}$/.test(dd)) return null
  return `${y}-${mm}-${dd}`
}

/**
 * 刷新图表上的选中日期标记（markPoint + markLine）。
 * selectedDate 变化时调用，无需销毁重建图表实例。
 */
const refreshChartMark = () => {
  if (!chartInstance || historyData.value.length === 0) return
  const history = historyData.value
  const dates = history.map(h => h.date)
  const scores = history.map(h => h.score)
  const prices = history.map(h => h.price)
  updateChartOption(history, dates, scores, prices)
}

/**
 * 确认手动输入的日期，建立对比。
 * 解析失败或日期无数据时提示用户。
 */
const onDateInputConfirm = () => {
  const parsed = parseDateInput(dateInput.value)
  if (!parsed) {
    ElMessage.warning('日期格式不正确，支持如 2019-11-01、20191101、2019/11/1')
    return
  }
  if (parsed === latestDate.value) {
    ElMessage.info('所选日期为最新日期，无需对比')
    return
  }
  const item = historyData.value.find(h => h.date === parsed)
  if (!item) {
    ElMessage.warning(`该日期 ${parsed} 无历史数据`)
    return
  }
  selectedDate.value = item.date
  selectedFactors.value = item
  updateFactorList()
  // 刷新图表标记，高亮选中的历史日期点位
  refreshChartMark()
  showDateInput.value = false
  dateInput.value = ''
}

/** 删除对比，恢复为单列显示最新得分 */
const clearCompare = () => {
  selectedDate.value = null
  selectedFactors.value = latestFactors.value
  updateFactorList()
  // 清除图表上的标记
  refreshChartMark()
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

// 档位样式：基于分位数分级，颜色与档位含义对应
const getBandClass = computed(() => {
  const label = valuation.value?.score_bands?.band_label
  const map = {
    '极高(低估)': 'status-very-low',
    '偏高': 'status-low',
    '中性': 'status-neutral-low',
    '偏低': 'status-neutral-high',
    '极低(高估)': 'status-very-high'
  }
  return map[label] || ''
})

const getDeltaClass = (delta) => {
  if (delta > 0) return 'delta-up'
  if (delta < 0) return 'delta-down'
  return 'delta-flat'
}

const formatDelta = (delta) => {
  if (delta > 0) return `+${delta.toFixed(1)}`
  return delta.toFixed(1)
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
  flex: 1;
}
.header-actions {
  margin-left: auto;
}
.report-content {
  min-height: 400px;
}
/* 空状态 */
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}
.empty-hint {
  color: #909399;
  font-size: 14px;
  margin: 4px 0;
}
/* 报告元信息栏 */
.report-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  margin-bottom: 16px;
  background: #f0f9ff;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
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
/* 分级参考栏 */
.bands-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 20px;
  background: #fafafa;
  border-radius: 6px;
  font-size: 12px;
  color: #909399;
  flex-wrap: wrap;
}
.bands-label {
  font-weight: 600;
  color: #606266;
}
.bands-range {
  padding: 2px 8px;
  border-radius: 3px;
  background: #f0f0f0;
}
.bands-range.bands-neutral {
  background: #e8f4fd;
  color: #409eff;
}
.bands-source {
  font-style: italic;
  font-size: 11px;
}
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
.chart-hint {
  font-size: 13px;
  font-weight: normal;
  color: #909399;
}

/* 因子得分区头部：标题与操作区紧凑排列，按钮紧跟标题而非靠右 */
.factors-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 15px;
}
.factors-header h3 {
  margin: 0;
}
.factors-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.date-input-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.compare-tip {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  padding: 10px 15px;
  background: #f0f5ff;
  border-radius: 6px;
  font-size: 14px;
}
.tip-label { color: #606266; }
.tip-latest {
  padding: 2px 10px;
  background: #409EFF;
  color: white;
  border-radius: 4px;
  font-weight: bold;
}
.tip-arrow { color: #909399; }
.tip-selected {
  padding: 2px 10px;
  background: #f5f5f5;
  color: #303133;
  border-radius: 4px;
  font-weight: bold;
  border: 1px solid #dcdfe6;
}
/* 对比状态条删除按钮：紧跟内容右侧，用左间距与内容区分 */
.tip-close {
  margin-left: 12px;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  color: #909399;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s;
}
.tip-close:hover {
  color: #f56c6c;
  background: #fef0f0;
}

.score-cell {
  padding: 8px;
  border-radius: 4px;
}

/* 单列双进度条：每个因子一格内上下两条进度条 */
.dual-bar {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 4px 0;
}
.bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.bar-tag {
  flex-shrink: 0;
  width: 36px;
  text-align: center;
  font-size: 11px;
  font-weight: bold;
  padding: 2px 0;
  border-radius: 3px;
}
.bar-tag-latest {
  background: #409EFF;
  color: white;
}
.bar-tag-selected {
  background: #f5f5f5;
  color: #606266;
  border: 1px solid #dcdfe6;
}
/* el-progress 占据剩余空间 */
.bar-row :deep(.el-progress) {
  flex: 1;
}
.bar-value {
  flex-shrink: 0;
  width: 40px;
  text-align: right;
  font-size: 12px;
  font-weight: bold;
  color: #303133;
}

/* 未参与因子标注：灰色小标签紧跟因子名称 */
.not-participated-tag {
  margin-left: 6px;
  padding: 1px 6px;
  font-size: 11px;
  color: #909399;
  background: #f5f5f5;
  border: 1px solid #e4e7ed;
  border-radius: 3px;
}
/* 未参与因子得分单元格：灰色居中文字 */
.not-participated-cell {
  color: #c0c4cc;
  font-size: 13px;
  text-align: center;
  padding: 8px 0;
}

.delta-up { color: #e6a23c; font-weight: bold; }
.delta-down { color: #67c23a; font-weight: bold; }
.delta-flat { color: #909399; }
</style>
