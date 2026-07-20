<template>
  <div class="group-tabs">
    <el-tabs :model-value="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="自选" name="default" />
      <el-tab-pane
        v-for="g in groups"
        :key="g.id"
        :name="String(g.id)"
      >
        <template #label>
          <span class="group-tab-label">
            {{ g.name }}
            <el-badge :value="g.stock_count" :max="99" type="info" class="group-badge" />
          </span>
        </template>
      </el-tab-pane>
    </el-tabs>
    <div class="group-actions">
      <el-button size="small" :icon="Plus" circle @click="$emit('add')" />
      <el-dropdown
        v-if="activeTab !== 'default'"
        size="small"
        @command="onGroupAction"
      >
        <el-button size="small" :icon="MoreFilled" circle />
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="rename">重命名</el-dropdown-item>
            <el-dropdown-item command="delete" divided>删除分组</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Plus, MoreFilled } from '@element-plus/icons-vue'

const props = defineProps({
  groups: { type: Array, default: () => [] },
  modelValue: { type: [String, Number], default: 'default' },
})

const emit = defineEmits(['update:modelValue', 'change', 'add', 'rename', 'delete'])

const activeTab = computed(() => String(props.modelValue))

const onTabChange = (name) => {
  const groupId = name === 'default' ? null : parseInt(name)
  emit('update:modelValue', name)
  emit('change', groupId)
}

const onGroupAction = (command) => {
  const groupId = parseInt(activeTab.value)
  emit(command, groupId)
}
</script>

<style scoped>
.group-tabs {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.group-tabs :deep(.el-tabs) {
  flex: 1;
}
.group-actions {
  display: flex;
  gap: 4px;
  padding-top: 4px;
}
.group-tab-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.group-badge :deep(.el-badge__content) {
  transform: none;
  position: static;
}
</style>
