import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { noLayout: true }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/buyers',
    name: 'Buyers',
    component: () => import('../views/Buyers.vue')
  },
  {
    path: '/buyers/:id',
    name: 'BuyerDetail',
    component: () => import('../views/BuyerDetail.vue')
  },
  {
    path: '/import',
    name: 'Import',
    component: () => import('../views/Import.vue')
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/Search.vue')
  },
  {
    path: '/crm',
    name: 'CRM',
    component: () => import('../views/CRM.vue')
  },
  {
    path: '/outreach',
    name: 'Outreach',
    component: () => import('../views/Outreach.vue')
  },
  {
    path: '/export',
    name: 'Export',
    component: () => import('../views/Export.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue')
  },
  {
    path: '/quote',
    name: 'Quote',
    component: () => import('../views/Quote.vue')
  },
  {
    path: '/demo',
    name: 'Demo',
    component: () => import('../views/Demo.vue'),
    meta: { noLayout: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 导航守卫：未登录跳转登录页，已登录访问登录页跳转首页
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router