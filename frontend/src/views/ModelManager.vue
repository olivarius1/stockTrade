<template>
  <div class="container">
    <div class="header">
      <el-button @click="$router.push('/')">返回首页</el-button>
      <h1>模型管理</h1>
    </div>

    <h2>估值模型</h2>
    <el-table :data="models" border v-loading="loading">
      <el-table-column prop="code" label="代码" width="100" />
      <el-table-column prop="name" label="名称" width="120" />
      <el-table-column label="因子">
        <template #default="{ row }">
          <el-tag v-for="f in (row.factors || [])" :key="f" size="small" style="margin-right: 5px">
            {{ f }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="权重">
        <template #default="{ row }">
          <span v-for="(val, key) in (row.weights || {})" :key="key" style="margin-right: 10px">
            {{ key }}: {{ (val * 100).toFixed(0) }}%
          </span>
        </template>
      </el-table-column>
    </el-table>

    <h2>估值因子</h2>
    <el-table :data="factors" border v-loading="loading">
      <el-table-column prop="code" label="代码" width="150" />
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column label="需要数据">
        <template #default="{ row }">
          <el-tag v-for="d in (row.requires_data || [])" :key="d" size="small" type="info" style="margin-right: 5px">
            {{ d }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { modelsAPI } from '../api'

const models = ref([])
const factors = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const [modelsData, factorsData] = await Promise.all([
      modelsAPI.getModels(),
      modelsAPI.getFactors()
    ])
    models.value = modelsData
    factors.value = factorsData
  } catch (error) {
    ElMessage.error('加载模型数据失败')
  } finally {
    loading.value = false
  }
})
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
