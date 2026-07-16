<template>
  <div class="container">
    <div class="header">
      <el-button @click="$router.push('/')">返回首页</el-button>
      <h1>系统设置</h1>
    </div>

    <h2>关于系统</h2>
    <el-descriptions :column="2" border>
      <el-descriptions-item label="系统名称">股票估值系统</el-descriptions-item>
      <el-descriptions-item label="版本">1.5.0</el-descriptions-item>
      <el-descriptions-item label="后端框架">FastAPI 0.139+</el-descriptions-item>
      <el-descriptions-item label="前端框架">Vue3 3.4+</el-descriptions-item>
      <el-descriptions-item label="UI库">Element Plus 2.4+</el-descriptions-item>
      <el-descriptions-item label="图表库">ECharts 5.4+</el-descriptions-item>
      <el-descriptions-item label="数据库">SQLite</el-descriptions-item>
      <el-descriptions-item label="缓存">Redis 7.0+</el-descriptions-item>
      <el-descriptions-item label="定时任务">Celery 5.3+</el-descriptions-item>
      <el-descriptions-item label="Python版本">3.12</el-descriptions-item>
    </el-descriptions>

    <h2>数据更新频率设置</h2>
    <el-form :model="settings" label-width="180px" v-loading="loading" style="max-width: 600px">
      <el-form-item label="财报数据更新频率(天)">
        <el-input-number v-model="settings.financial_update_frequency" :min="1" :max="30" />
        <span style="margin-left: 10px; color: #909399">每隔多少天更新一次财报数据</span>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { schedulerAPI } from '../api'

const settings = ref({
  financial_update_frequency: 7
})
const loading = ref(false)
const saving = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const config = await schedulerAPI.getConfig()
    settings.value.financial_update_frequency = config.financial_update_frequency
  } catch (error) {
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
})

const saveSettings = async () => {
  saving.value = true
  try {
    const config = await schedulerAPI.getConfig()
    await schedulerAPI.updateConfig({
      ...config,
      financial_update_frequency: settings.value.financial_update_frequency
    })
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
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
h2 {
  margin: 20px 0 15px 0;
  color: #333;
}
</style>
