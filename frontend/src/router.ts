import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import QuickLog from './views/QuickLog.vue'
import StationLog from './views/StationLog.vue'

/* URL 是导航的唯一事实来源：
   /dashboard 首页统计 · /quick 快速记录 · /station/:id 电台日志 */
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: Dashboard },
    { path: '/quick', component: QuickLog },
    { path: '/station/:id(\\d+)', component: StationLog },
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
})
