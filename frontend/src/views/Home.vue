<template>
  <div class="home-container">
    <div class="header">
      <h1>股票估值系统</h1>
      <div class="header-actions">
        <el-button @click="$router.push('/models')">模型管理</el-button>
        <el-button @click="$router.push('/scheduler')">定时任务</el-button>
        <el-button @click="$router.push('/settings')">系统设置</el-button>
        <el-button @click="logout">退出登录</el-button>
      </div>
    </div>

    <div class="search-section">
      <el-input
        v-model="searchKeyword"
        placeholder="输入股票代码查看估值报告"
        style="width: 300px"
        @keyup.enter="searchStock"
      >
        <template #append>
          <el-button @click="searchStock">搜索</el-button>
        </template>
      </el-input>
    </div>

    <div class="content">
      <div class="watchlist-section">
        <div class="section-header">
          <h2>自选股</h2>
          <div>
            <el-button type="primary" @click="addStock">添加股票</el-button>
            <el-button @click="batchCalculate" :loading="batchLoading">批量计算</el-button>
          </div>
        </div>

        <el-table :data="watchlist" border v-loading="tableLoading">
          <el-table-column prop="stock_code" label="代码" width="100" />
          <el-table-column prop="stock_name" label="名称" width="120" />
          <el-table-column prop="model_type" label="模型" width="100" />
          <el-table-column label="AI分析" width="80">
            <template #default="{ row }">
              <el-tag :type="row.ai_enabled ? 'success' : 'info'">
                {{ row.ai_enabled ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button size="small" @click="viewReport(row.stock_code)">查看报告</el-button>
              <el-button size="small" type="danger" @click="removeStock(row.stock_code)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <el-dialog title="添加股票到自选" v-model="addDialogVisible" width="500px">
      <el-form :model="newStock" label-width="100px">
        <el-form-item label="股票代码">
          <el-input v-model="newStock.stock_code" placeholder="如: 000001、000001.sz、sh.600519" />
        </el-form-item>
        <el-form-item label="股票名称">
          <el-input v-model="newStock.stock_name" placeholder="可不填，自动获取" />
        </el-form-item>
        <el-form-item label="估值模型">
          <el-select v-model="newStock.model_type" placeholder="选择模型" style="width: 100%">
            <el-option label="必选消费" value="staples" />
            <el-option label="周期股" value="cyclical" />
            <el-option label="科技股" value="tech" />
            <el-option label="银行保险" value="bank" />
            <el-option label="医药股" value="pharma" />
            <el-option label="央企国企" value="soe" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用AI分析">
          <el-switch v-model="newStock.ai_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAdd">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 首页/自选股管理页面。
 *
 * 功能：搜索股票跳转报告、自选股增删、批量估值计算。
 * 搜索是直接跳转到报告页（/valuation/report/:code），无需中间搜索结果页。
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { watchlistAPI } from '../api'

const router = useRouter()
const searchKeyword = ref('')
const watchlist = ref([])
const addDialogVisible = ref(false)
const tableLoading = ref(false)
const batchLoading = ref(false)
const newStock = ref({
  stock_code: '',
  stock_name: '',
  model_type: 'tech',
  ai_enabled: false
})

onMounted(async () => {
  await loadWatchlist()
})

const loadWatchlist = async () => {
  tableLoading.value = true
  try {
    watchlist.value = await watchlistAPI.getList()
  } catch (error) {
    ElMessage.error('加载自选股失败')
  } finally {
    tableLoading.value = false
  }
}

const searchStock = () => {
  if (!searchKeyword.value) {
    ElMessage.warning('请输入股票代码')
    return
  }
  router.push(`/valuation/report/${searchKeyword.value}`)
}

const viewReport = (code) => {
  router.push(`/valuation/report/${code}`)
}

const addStock = () => {
  newStock.value = {
    stock_code: '',
    stock_name: '',
    model_type: 'tech',
    ai_enabled: false
  }
  addDialogVisible.value = true
}

const confirmAdd = async () => {
  if (!newStock.value.stock_code) {
    ElMessage.warning('请填写股票代码')
    return
  }
  try {
    await watchlistAPI.add(newStock.value)
    ElMessage.success('添加成功')
    addDialogVisible.value = false
    await loadWatchlist()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  }
}

const removeStock = async (code) => {
  try {
    await ElMessageBox.confirm('确认从自选中删除该股票?', '提示', {
      type: 'warning'
    })
    await watchlistAPI.remove(code)
    ElMessage.success('删除成功')
    await loadWatchlist()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const batchCalculate = async () => {
  batchLoading.value = true
  try {
    const result = await watchlistAPI.batchCalculate()
    ElMessage.success(`批量计算完成，共处理 ${result.results?.length || 0} 只股票`)
    await loadWatchlist()
  } catch (error) {
    ElMessage.error('批量计算失败')
  } finally {
    batchLoading.value = false
  }
}

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.home-container {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}
.header h1 {
  color: #333;
  margin: 0;
}
.header-actions {
  display: flex;
  gap: 10px;
}
.search-section {
  margin-bottom: 20px;
}
.content {
  display: flex;
  gap: 20px;
}
.watchlist-section {
  flex: 1;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.section-header h2 {
  margin: 0;
}
</style>
