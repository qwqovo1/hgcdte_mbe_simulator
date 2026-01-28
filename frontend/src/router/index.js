                     import { createRouter, createWebHistory } from 'vue-router'

// 路由懒加载
const Welcome = () => import('../views/Welcome.vue')
const Home = () => import('../views/Home.vue')
const ModelDisplay = () => import('../views/ModelDisplay.vue')
const Experiment = () => import('../views/Experiment.vue')

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
    name: 'ModelDisplay',
    component: ModelDisplay
  },
  {
    path: '/experiment',
    name: 'Experiment',
    component: Experiment
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router