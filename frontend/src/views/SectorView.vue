<template>
  <div class="sector-container">
    <div class="page-header">
      <h2>板块</h2>
    </div>

    <div class="sector-tags" v-loading="sectorsLoading">
      <el-radio-group v-model="activeSector" @change="onSectorChange">
        <el-radio-button
          v-for="s in sectors"
          :key="s.industry"
          :value="s.industry"
        >
          {{ s.industry }} ({{ s.count }})
        </el-radio-button>
      </el-radio-group>
      <el-empty v-if="!sectorsLoading && sectors.length === 0" description="暂无板块数据，请先在自选股中设置行业" :image-size="80" />
    </div>

    <StockTable
      v-if="activeSector"
      :data="stockList"
      :loading="tableLoading"
      :show-actions="false"
    />
  </div>
</template>

<script setup>
/**
 * 板块页 - 按行业板块分组查看股票及估值。
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { stockAPI } from '../api'
import StockTable from '../components/StockTable.vue'

const sectors = ref([])
const sectorsLoading = ref(false)
const activeSector = ref('')
const stockList = ref([])
const tableLoading = ref(false)

onMounted(async () => {
  await loadSectors()
})

const loadSectors = async () => {
  sectorsLoading.value = true
  try {
    sectors.value = await stockAPI.getSectors()
    if (sectors.value.length > 0 && !activeSector.value) {
      activeSector.value = sectors.value[0].industry
      await loadSectorStocks()
    }
  } catch (error) {
    ElMessage.error('加载板块列表失败')
  } finally {
    sectorsLoading.value = false
  }
}

const onSectorChange = () => {
  loadSectorStocks()
}

const loadSectorStocks = async () => {
  if (!activeSector.value) return
  tableLoading.value = true
  try {
    stockList.value = await stockAPI.getSectorStocks(activeSector.value)
  } catch (error) {
    ElMessage.error('加载板块股票失败')
  } finally {
    tableLoading.value = false
  }
}
</script>

<style scoped>
.sector-container {
  max-width: 1200px;
  margin: 0 auto;
}
.page-header {
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0;
}
.sector-tags {
  margin-bottom: 20px;
  min-height: 40px;
}
</style>
