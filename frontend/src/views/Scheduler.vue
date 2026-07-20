<template>
  <div class="container">
    <div class="header">
      <el-button @click="$router.push('/')">返回首页</el-button>
      <h1>定时任务配置</h1>
    </div>

    <!-- K线批量获取任务 -->
    <el-card class="task-card">
      <template #header>
        <div class="card-header">
          <span>全市场K线数据获取 & 估值填充</span>
          <el-button type="primary" :loading="klineFetching" @click="triggerKlineFetch">
            {{ klineFetching ? '执行中...' : '手动触发' }}
          </el-button>
        </div>
      </template>

      <!-- 进度条 -->
      <div v-if="klineProgress" class="progress-section">
        <el-progress
          :percentage="progressPercent"
          :status="klineProgress.status === 'completed' ? 'success' : klineProgress.status === 'failed' ? 'exception' : ''"
          :stroke-width="18"
          striped
          striped-flow
        />
        <div class="progress-info">
          <span>总数: {{ klineProgress.total }}</span>
          <span>已完成: {{ klineProgress.completed }}</span>
          <span>失败: {{ klineProgress.failed }}</span>
          <span v-if="klineProgress.current">当前: {{ klineProgress.current }}</span>
          <el-tag :type="statusTagType" size="small">{{ statusText }}</el-tag>
        </div>
      </div>
      <el-empty v-else description="暂无任务记录" :image-size="60" />

      <!-- 历史执行记录 -->
      <div v-if="klineHistory.length > 0" class="history-section">
        <h4>历史执行记录</h4>
        <el-table :data="klineHistory" size="small" max-height="200">
          <el-table-column prop="id" label="ID" width="50" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'" size="small">
                {{ row.status === 'completed' ? '完成' : row.status === 'failed' ? '失败' : '运行中' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total" label="总数" width="60" />
          <el-table-column prop="completed" label="完成" width="60" />
          <el-table-column prop="failed" label="失败" width="60" />
          <el-table-column prop="started_at" label="开始时间" />
          <el-table-column prop="finished_at" label="结束时间" />
        </el-table>
      </div>
    </el-card>

    <!-- 定时配置 -->
    <el-card class="task-card">
      <template #header><span>定时任务参数</span></template>
      <el-form :model="config" label-width="180px" v-loading="loading" style="max-width: 600px">
        <el-form-item label="定时类型">
          <el-select v-model="config.schedule_type" placeholder="选择类型">
            <el-option label="每小时" value="hourly" />
            <el-option label="每天" value="daily" />
            <el-option label="每周" value="weekly" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron表达式">
          <el-input v-model="config.cron_expression" placeholder="如: 0 18 * * *" />
        </el-form-item>
        <el-form-item label="启用定时任务">
          <el-switch v-model="config.enabled" />
        </el-form-item>
        <el-form-item label="包含AI分析">
          <el-switch v-model="config.include_ai" />
        </el-form-item>
        <el-form-item label="财报更新频率(天)">
          <el-input-number v-model="config.financial_update_frequency" :min="1" :max="30" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveConfig" :loading="saving">保存配置</el-button>
          <el-button @click="runNow" :loading="running">立即执行估值计算</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { schedulerAPI } from '../api'

const config = ref({
  schedule_type: 'daily',
  cron_expression: '0 18 * * *',
  enabled: true,
  include_ai: false,
  financial_update_frequency: 7
})
const loading = ref(false)
const saving = ref(false)
const running = ref(false)
const klineFetching = ref(false)
const klineProgress = ref(null)
const klineHistory = ref([])
let pollTimer = null

const progressPercent = computed(() => {
  if (!klineProgress.value || !klineProgress.value.total) return 0
  return Math.round((klineProgress.value.completed + klineProgress.value.failed) / klineProgress.value.total * 100)
})

const statusTagType = computed(() => {
  const s = klineProgress.value?.status
  if (s === 'completed') return 'success'
  if (s === 'failed') return 'danger'
  if (s === 'running') return 'warning'
  return 'info'
})

const statusText = computed(() => {
  const s = klineProgress.value?.status
  if (s === 'completed') return '已完成'
  if (s === 'failed') return '失败'
  if (s === 'running') return '执行中'
  if (s === 'idle') return '空闲'
  return s || '未知'
})

onMounted(async () => {
  loading.value = true
  try {
    const data = await schedulerAPI.getConfig()
    config.value = data
  } catch (error) {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
  await loadProgress()
  await loadHistory()
})

onUnmounted(() => {
  stopPolling()
})

const loadProgress = async () => {
  try {
    const data = await schedulerAPI.getKlineFetchProgress()
    if (data && data.status !== 'idle') {
      klineProgress.value = data
    }
  } catch (e) { /* ignore */ }
}

const loadHistory = async () => {
  try {
    const data = await schedulerAPI.getKlineFetchHistory()
    klineHistory.value = data.results || []
  } catch (e) { /* ignore */ }
}

const startPolling = () => {
  stopPolling()
  pollTimer = setInterval(async () => {
    await loadProgress()
    if (klineProgress.value && klineProgress.value.status !== 'running') {
      stopPolling()
      klineFetching.value = false
      await loadHistory()
      if (klineProgress.value.status === 'completed') {
        ElMessage.success(`K线获取完成，成功 ${klineProgress.value.completed} 只`)
      }
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const triggerKlineFetch = async () => {
  klineFetching.value = true
  try {
    const result = await schedulerAPI.triggerKlineFetch()
    if (result.status === 'already_running') {
      ElMessage.warning(result.message)
      startPolling()
    } else {
      ElMessage.success('任务已触发')
      startPolling()
    }
  } catch (error) {
    ElMessage.error('触发失败')
    klineFetching.value = false
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    await schedulerAPI.updateConfig(config.value)
    ElMessage.success('配置已保存')
  } catch (error) {
    ElMessage.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

const runNow = async () => {
  running.value = true
  try {
    const result = await schedulerAPI.run()
    ElMessage.success(`任务已触发，处理了 ${result.results?.length || 0} 只股票`)
  } catch (error) {
    ElMessage.error('触发任务失败')
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.container {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}
.header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}
.header h1 {
  margin: 0;
}
.task-card {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.progress-section {
  margin-bottom: 16px;
}
.progress-info {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  font-size: 13px;
  color: #606266;
  align-items: center;
}
.history-section {
  margin-top: 16px;
}
.history-section h4 {
  margin: 0 0 8px 0;
  color: #333;
}
</style>
