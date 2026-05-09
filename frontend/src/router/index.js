import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', component: () => import('../views/Dashboard.vue') },
  { path: '/search', component: () => import('../views/Search.vue') },
  { path: '/customers', component: () => import('../views/Customers.vue') },
  { path: '/templates', component: () => import('../views/Templates.vue') },
  { path: '/campaigns', component: () => import('../views/Campaigns.vue') },
  { path: '/settings', component: () => import('../views/Settings.vue') }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
