<template>
  <el-table :data="data" border v-loading="loading" style="width: 100%">
    <el-table-column prop="stock_name" label="名称" min-width="100" />
    <el-table-column prop="stock_code" label="代码" width="90" />
    <el-table-column label="估值分" width="90" sortable>
      <template #default="{ row }">
        <span v-if="row.score != null" :style="{ color: scoreColor(row.score) }">
          {{ row.score.toFixed(1) }}
        </span>
        <span v-else class="text-muted">-</span>
      </template>
    </el-table-column>
    <el-table-column label="百分位" width="90" sortable>
      <template #default="{ row }">
        <span v-if="row.percentile != null">{{ row.percentile.toFixed(1) }}%</span>
        <span v-else class="text-muted">-</span>
      </template>
    </el-table-column>
    <el-table-column label="估值评价" width="120">
      <template #default="{ row }">
        <el-tag v-if="row.status" :type="statusTagType(row.status)" size="small">
          {{ row.status }}
        </el-tag>
        <span v-else class="text-muted">未计算</span>
      </template>
    </el-table-column>
    <el-table-column label="数据" width="60" align="center">
      <template #default="{ row }">
        <el-tooltip
          v-if="row.valuation_date && !row.is_latest"
          :content="`数据日期: ${row.valuation_date}`"
          placement="top"
        >
          <el-icon color="#E6A23C"><WarningFilled /></el-icon>
        </el-tooltip>
        <el-icon v-else-if="row.is_latest" color="#67C23A"><CircleCheckFilled /></el-icon>
        <span v-else class="text-muted">-</span>
      </template>
    </el-table-column>
    <el-table-column v-if="showActions" label="操作" width="200" fixed="right">
      <template #default="{ row }">
        <el-button size="small" @click="$emit('viewReport', row.stock_code)">报告</el-button>
        <el-dropdown size="small" @command="(gid) => $emit('moveGroup', row.stock_code, gid)" style="margin: 0 8px">
          <el-button size="small">分组</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item :command="null">自选(默认)</el-dropdown-item>
              <el-dropdown-item v-for="g in groups" :key="g.id" :command="g.id">{{ g.name }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button size="small" type="danger" @click="$emit('remove', row.stock_code)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { WarningFilled, CircleCheckFilled } from '@element-plus/icons-vue'

defineProps({
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  showActions: { type: Boolean, default: false },
  groups: { type: Array, default: () => [] },
})

defineEmits(['viewReport', 'moveGroup', 'remove'])

const scoreColor = (score) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#95D475'
  if (score >= 40) return '#909399'
  if (score >= 20) return '#E6A23C'
  return '#F56C6C'
}

const statusTagType = (status) => {
  const map = {
    '极度低估': 'success',
    '低估': 'success',
    '中性偏低': '',
    '中性偏高': 'warning',
    '高估': 'danger',
    '极度高估': 'danger',
  }
  return map[status] || 'info'
}
</script>

<style scoped>
.text-muted {
  color: #c0c4cc;
}
</style>
