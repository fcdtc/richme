import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import BacktestView from '../views/BacktestView.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardView
  },
  {
    path: '/backtest',
    name: 'backtest',
    component: BacktestView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
