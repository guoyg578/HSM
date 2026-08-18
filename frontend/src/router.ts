import { createRouter, createWebHistory } from 'vue-router'
import Admin from './views/Admin.vue'
import Awards from './views/Awards.vue'
import Callbook from './views/Callbook.vue'
import CalendarView from './views/CalendarView.vue'
import Dashboard from './views/Dashboard.vue'
import MapView from './views/MapView.vue'
import StationLog from './views/StationLog.vue'
import Toolbox from './views/Toolbox.vue'

/* URL 是导航的唯一事实来源：
   /dashboard 首页统计（含快速记录弹框） · /map 通联地图 · /callbook 呼号簿
   /calendar 通联日历 · /awards 成就徽章 · /tools 工具箱
   /station/:id 电台日志 · /admin 后台管理 */
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: Dashboard },
    { path: '/map', component: MapView },
    { path: '/callbook', component: Callbook },
    { path: '/calendar', component: CalendarView },
    { path: '/awards', component: Awards },
    { path: '/tools', component: Toolbox },
    { path: '/station/:id(\\d+)', component: StationLog },
    { path: '/admin', component: Admin },
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
})
