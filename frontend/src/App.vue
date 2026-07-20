<template>
  <div v-if="!hideLayout" class="app-layout">
    <el-menu
      mode="horizontal"
      :default-active="activeMenu"
      router
      class="top-nav"
    >
      <el-menu-item index="/">首页</el-menu-item>
      <el-menu-item index="/market">全市场低估</el-menu-item>
      <el-menu-item index="/sectors">板块</el-menu-item>
      <el-sub-menu index="more">
        <template #title>更多</template>
        <el-menu-item index="/models">模型管理</el-menu-item>
        <el-menu-item index="/scheduler">定时任务</el-menu-item>
        <el-menu-item index="/settings">系统设置</el-menu-item>
      </el-sub-menu>
      <div class="nav-right">
        <el-button text @click="logout">退出</el-button>
      </div>
    </el-menu>
    <main class="app-main">
      <router-view />
    </main>
  </div>
  <router-view v-else />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const hideLayout = computed(() => route.path === '/login')
const activeMenu = computed(() => {
  if (route.path.startsWith('/market')) return '/market'
  if (route.path.startsWith('/sectors')) return '/sectors'
  if (route.path.startsWith('/models')) return '/models'
  if (route.path.startsWith('/scheduler')) return '/scheduler'
  if (route.path.startsWith('/settings')) return '/settings'
  return '/'
})

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style>
html,
#app {
  min-height: 100%;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}
</style>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.top-nav {
  padding: 0 20px;
}
.nav-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  padding-right: 12px;
}
.app-main {
  flex: 1;
  padding: 20px;
}
</style>
