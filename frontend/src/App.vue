<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { KDrawer, KMenu } from '@guoyg578/k-ui'
import type { MenuOption } from '@guoyg578/k-ui'
import {
  BookUser,
  CalendarDays,
  LayoutDashboard,
  Map as MapIcon,
  Menu as MenuIcon,
  Plus,
  RadioTower,
  Settings as SettingsIcon,
  Trophy,
  Wrench,
} from '@lucide/vue'
import type { StationDetail } from './types'
import { loadAppSettings } from './settings'
import { refreshStations, stations } from './store'
import StationDialog from './components/StationDialog.vue'

const route = useRoute()
const router = useRouter()

const expandedKeys = ref<string[]>(['stations'])
const createOpen = ref(false)
const menuOpen = ref(false)

// key ↔ 路由/标题 对照表（电台子项单独处理）
const PAGES: Record<string, { path: string; title: string }> = {
  dashboard: { path: '/dashboard', title: '首页统计' },
  map: { path: '/map', title: '通联地图' },
  callbook: { path: '/callbook', title: '呼号簿' },
  calendar: { path: '/calendar', title: '通联日历' },
  awards: { path: '/awards', title: '成就徽章' },
  tools: { path: '/tools', title: '工具箱' },
  admin: { path: '/admin', title: '后台管理' },
}

// 菜单选中项完全由当前路由推导
const activeKey = computed(() => {
  if (route.path.startsWith('/station/')) return `st:${route.params.id}`
  const hit = Object.entries(PAGES).find(([, p]) => p.path === route.path)
  return hit?.[0] ?? 'dashboard'
})

const currentTitle = computed(() => {
  if (route.path.startsWith('/station/')) {
    const s = stations.value.find((x) => x.id === Number(route.params.id))
    return s?.name ?? '电台'
  }
  const hit = Object.values(PAGES).find((p) => p.path === route.path)
  return hit?.title ?? '首页统计'
})

const menuOptions = computed<MenuOption[]>(() => [
  { key: 'dashboard', label: '首页统计', icon: LayoutDashboard },
  { key: 'map', label: '通联地图', icon: MapIcon },
  { key: 'callbook', label: '呼号簿', icon: BookUser },
  { key: 'calendar', label: '通联日历', icon: CalendarDays },
  { key: 'awards', label: '成就徽章', icon: Trophy },
  { key: 'tools', label: '工具箱', icon: Wrench },
  { key: 'div1', type: 'divider' },
  {
    key: 'stations',
    label: '我的电台',
    children: stations.value.map((s) => ({
      key: `st:${s.id}`,
      label: s.name,
      icon: RadioTower,
    })),
  },
  { key: 'div2', type: 'divider' },
  { key: 'new-station', label: '新建电台', icon: Plus },
  { key: 'admin', label: '后台管理', icon: SettingsIcon },
])

function onSelect(key: string) {
  menuOpen.value = false
  if (key === 'new-station') {
    createOpen.value = true
    return
  }
  if (key.startsWith('st:')) {
    router.push(`/station/${key.slice(3)}`)
  } else {
    router.push(PAGES[key]?.path ?? '/dashboard')
  }
}

async function onStationCreated(station: StationDetail) {
  await refreshStations()
  router.push(`/station/${station.id}`)
}

onMounted(() => {
  refreshStations()
  loadAppSettings()
})
</script>

<template>
  <div class="flex h-full flex-col bg-gray-50 text-gray-900">
    <!-- 移动端顶栏 -->
    <header
      class="flex shrink-0 items-center gap-3 border-b border-gray-200 bg-white px-4 py-3 lg:hidden"
    >
      <button class="-ml-1 rounded-lg p-1 active:bg-gray-100" @click="menuOpen = true">
        <MenuIcon class="size-5 text-gray-600" />
      </button>
      <RadioTower class="size-5 text-blue-600" />
      <span class="text-sm font-bold">{{ currentTitle }}</span>
    </header>

    <div class="flex min-h-0 flex-1">
      <!-- 桌面端左侧目录 -->
      <aside class="hidden w-56 shrink-0 flex-col border-r border-gray-200 bg-white lg:flex">
        <div class="flex items-center gap-2 px-4 py-4">
          <RadioTower class="size-6 text-blue-600" />
          <div>
            <div class="text-sm font-bold leading-tight">HAM Station</div>
            <div class="text-xs text-gray-400">Manager V1.1</div>
          </div>
        </div>
        <div class="flex-1 overflow-y-auto px-2 pb-4">
          <KMenu
            :value="activeKey"
            :options="menuOptions"
            v-model:expanded-keys="expandedKeys"
            @select="onSelect"
          />
        </div>
      </aside>

      <!-- 内容区：由路由决定（每个路由自管滚动） -->
      <main class="min-w-0 flex-1 overflow-hidden">
        <RouterView :key="route.path" />
      </main>
    </div>

    <!-- 移动端菜单抽屉 -->
    <KDrawer
      :open="menuOpen"
      placement="left"
      title="HAM Station Manager"
      width="272px"
      @update:open="(v: boolean) => (menuOpen = v)"
    >
      <KMenu
        :value="activeKey"
        :options="menuOptions"
        v-model:expanded-keys="expandedKeys"
        @select="onSelect"
      />
    </KDrawer>

    <StationDialog v-model:open="createOpen" :station="null" @saved="onStationCreated" />
  </div>
</template>
