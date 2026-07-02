import { createRouter, createWebHistory } from 'vue-router'

import BacktestView from './views/BacktestView.vue'
import PortfolioView from './views/PortfolioView.vue'

// 单标的回测（/）+ 组合回测（/portfolio）。参数寻优/结果对比留待 Phase 4-5。
const routes = [
  { path: '/', name: 'backtest', component: BacktestView },
  { path: '/portfolio', name: 'portfolio', component: PortfolioView },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
