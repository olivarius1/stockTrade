<template>
  <div class="container">
    <div class="header">
      <el-button @click="$router.push('/')">返回首页</el-button>
      <h1>定时任务配置</h1>
    </div>

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
        <el-button @click="runNow" :loading="running">立即执行</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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
})

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
</style>
