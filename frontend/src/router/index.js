import { createRouter, createWebHistory } from 'vue-router'

const routes = [
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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router