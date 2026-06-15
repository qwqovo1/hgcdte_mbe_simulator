import { createRouter, createWebHistory } from 'vue-router'

// 路由懒加载
const Welcome = () => import('../views/Welcome.vue')
const Home = () => import('../views/Home.vue')
const ModelDirectory = () => import('../views/ModelDirectory.vue')
const ModelDisplay = () => import('../views/ModelDisplay.vue')
// 【新增】红外高温计展示组件
const PyrometerDisplay = () => import('../views/PyrometerDisplay.vue')
const Experiment = () => import('../views/Experiment.vue')
// 【新增】智能分析和建议组件
const Analysis = () => import('../views/Analysis.vue')
// 实验报告相关组件
const ReportDirectory = () => import('../views/ReportDirectory.vue')
const ReportManager = () => import('../views/ReportManager.vue')

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: Welcome
  },
  {
    path: '/home',
    name: 'Home',
    component: Home
  },
  {
    path: '/model',
    name: 'ModelDirectory',
    component: ModelDirectory
  },
  {
    path: '/model/preview',
    name: 'ModelDisplay',
    component: ModelDisplay
  },
  // 【新增】红外高温计功能路由
  {
    path: '/model/pyrometer',
    name: 'PyrometerDisplay',
    component: PyrometerDisplay
  },
  {
    path: '/experiment',
    name: 'Experiment',
    component: Experiment
  },
  // 【新增】智能分析和建议功能路由
  {
    path: '/analysis',
    name: 'Analysis',
    component: Analysis
  },
  // 实验报告功能路由
  {
    path: '/reports',
    name: 'ReportDirectory',
    component: ReportDirectory
  },
  {
    path: '/reports/mbe-sim',
    name: 'ReportManager',
    component: ReportManager
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router