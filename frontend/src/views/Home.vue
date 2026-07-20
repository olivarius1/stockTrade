<template>
  <div class="home-container">
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="输入股票代码查看估值报告"
        style="width: 280px"
        @keyup.enter="searchStock"
      >
        <template #append>
          <el-button @click="searchStock">搜索</el-button>
        </template>
      </el-input>
      <div class="toolbar-actions">
        <el-button type="primary" @click="addStock">添加股票</el-button>
        <el-button @click="batchCalculate" :loading="batchLoading">批量计算</el-button>
      </div>
    </div>

    <GroupTabs
      v-model="activeTab"
      :groups="groups"
      @change="onGroupChange"
      @add="showAddGroup"
      @rename="showRenameGroup"
      @delete="deleteGroup"
    />

    <StockTable
      :data="stockList"
      :loading="tableLoading"
      :show-actions="true"
      :groups="groups"
      @view-report="viewReport"
      @move-group="moveToGroup"
      @remove="removeStock"
    />

    <!-- 添加股票对话框 -->
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
        <el-button type="primary" :loading="addLoading" @click="confirmAdd">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 首页 - 自选股分组管理 + 估值摘要列表。
 * 默认显示"自选"（group_id=null），可通过Tab切换到自定义分组。
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { watchlistAPI, groupAPI } from '../api'
import StockTable from '../components/StockTable.vue'
import GroupTabs from '../components/GroupTabs.vue'

const router = useRouter()
const searchKeyword = ref('')
const stockList = ref([])
const groups = ref([])
const activeTab = ref('default')
const tableLoading = ref(false)
const batchLoading = ref(false)
const addDialogVisible = ref(false)
const addLoading = ref(false)
const newStock = ref({
  stock_code: '',
  stock_name: '',
  model_type: 'tech',
  ai_enabled: false
})

onMounted(async () => {
  await Promise.all([loadGroups(), loadSummary()])
})

const loadGroups = async () => {
  try {
    groups.value = await groupAPI.getList()
  } catch (e) {
    // 分组加载失败不阻塞主流程
  }
}

const loadSummary = async (groupId = null) => {
  tableLoading.value = true
  try {
    stockList.value = await watchlistAPI.getSummary(groupId)
  } catch (error) {
    ElMessage.error('加载自选股失败')
  } finally {
    tableLoading.value = false
  }
}

const onGroupChange = (groupId) => {
  loadSummary(groupId)
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
  newStock.value = { stock_code: '', stock_name: '', model_type: 'tech', ai_enabled: false }
  addDialogVisible.value = true
}

const confirmAdd = async () => {
  if (!newStock.value.stock_code) {
    ElMessage.warning('请填写股票代码')
    return
  }
  addLoading.value = true
  try {
    await watchlistAPI.add(newStock.value)
    ElMessage.success('添加成功')
    addDialogVisible.value = false
    await loadSummary(activeTab.value === 'default' ? null : parseInt(activeTab.value))
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  } finally {
    addLoading.value = false
  }
}

const removeStock = async (code) => {
  try {
    await ElMessageBox.confirm('确认从自选中删除该股票?', '提示', { type: 'warning' })
    await watchlistAPI.remove(code)
    ElMessage.success('删除成功')
    await loadSummary(activeTab.value === 'default' ? null : parseInt(activeTab.value))
    await loadGroups()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

const moveToGroup = async (code, groupId) => {
  try {
    await watchlistAPI.moveToGroup(code, groupId)
    ElMessage.success('已移动')
    await loadSummary(activeTab.value === 'default' ? null : parseInt(activeTab.value))
    await loadGroups()
  } catch (error) {
    ElMessage.error('移动失败')
  }
}

const batchCalculate = async () => {
  batchLoading.value = true
  try {
    const result = await watchlistAPI.batchCalculate()
    ElMessage.success(`批量计算完成，共处理 ${result.results?.length || 0} 只股票`)
    await loadSummary(activeTab.value === 'default' ? null : parseInt(activeTab.value))
  } catch (error) {
    ElMessage.error('批量计算失败')
  } finally {
    batchLoading.value = false
  }
}

// 分组管理
const showAddGroup = async () => {
  try {
    const { value } = await ElMessageBox.prompt('输入分组名称', '新建分组', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
    })
    if (value) {
      await groupAPI.create({ name: value })
      ElMessage.success('分组已创建')
      await loadGroups()
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '创建失败')
  }
}

const showRenameGroup = async (groupId) => {
  const group = groups.value.find(g => g.id === groupId)
  try {
    const { value } = await ElMessageBox.prompt('输入新名称', '重命名分组', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputValue: group?.name || '',
    })
    if (value) {
      await groupAPI.rename(groupId, { name: value, sort_order: group?.sort_order || 0 })
      ElMessage.success('已重命名')
      await loadGroups()
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '重命名失败')
  }
}

const deleteGroup = async (groupId) => {
  try {
    await ElMessageBox.confirm('删除分组后，组内股票将回归默认自选。确认删除？', '提示', { type: 'warning' })
    await groupAPI.remove(groupId)
    ElMessage.success('分组已删除')
    activeTab.value = 'default'
    await Promise.all([loadGroups(), loadSummary(null)])
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.toolbar-actions {
  display: flex;
  gap: 10px;
}
</style>
