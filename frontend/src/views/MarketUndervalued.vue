<template>
  <div class="market-container">
    <div class="page-header">
      <h2>全市场低估</h2>
      <div class="filters">
        <el-select v-model="filters.model_type" placeholder="模型类型" clearable style="width: 130px" @change="loadData">
          <el-option label="必选消费" value="staples" />
          <el-option label="周期股" value="cyclical" />
          <el-option label="科技股" value="tech" />
          <el-option label="银行保险" value="bank" />
          <el-option label="医药股" value="pharma" />
          <el-option label="央企国企" value="soe" />
        </el-select>
        <el-select v-model="filters.limit" style="width: 100px" @change="loadData">
          <el-option :label="'Top 30'" :value="30" />
          <el-option :label="'Top 50'" :value="50" />
          <el-option :label="'Top 100'" :value="100" />
        </el-select>
      </div>
    </div>

    <StockTable
      :data="stockList"
      :loading="loading"
      :show-actions="false"
    />
  </div>
</template>

<script setup>
/**
 * 全市场低估页 - 按估值分降序展示所有已计算股票中的低估标的。
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { valuationAPI } from '../api'
import StockTable from '../components/StockTable.vue'

const stockList = ref([])
const loading = ref(false)
const filters = ref({
  model_type: '',
  limit: 50,
})

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    const params = { limit: filters.value.limit }
    if (filters.value.model_type) params.model_type = filters.value.model_type
    stockList.value = await valuationAPI.getMarketUndervalued(params)
  } catch (error) {
    ElMessage.error('加载全市场数据失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.market-container {
  max-width: 1200px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0;
}
.filters {
  display: flex;
  gap: 10px;
}
</style>
