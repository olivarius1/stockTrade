import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/stock/:code',
    name: 'ValuationReport',
    component: () => import('../views/ValuationReport.vue')
  },
  {
    path: '/models',
    name: 'ModelManager',
    component: () => import('../views/ModelManager.vue')
  },
  {
    path: '/scheduler',
    name: 'Scheduler',
    component: () => import('../views/Scheduler.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
