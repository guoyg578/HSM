<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { KMenu } from '@guoyg578/k-ui'
import type { MenuOption } from '@guoyg578/k-ui'
import { LayoutDashboard, Plus, RadioTower, Zap } from '@lucide/vue'
import type { StationDetail } from './types'
import { refreshStations, stations } from './store'
import StationDialog from './components/StationDialog.vue'

const route = useRoute()
const router = useRouter()

const expandedKeys = ref<string[]>(['stations'])
const createOpen = ref(false)

// 菜单选中项完全由当前路由推导
const activeKey = computed(() => {
  if (route.path.startsWith('/station/')) return `st:${route.params.id}`
  if (route.path === '/quick') return 'quick'
  return 'dashboard'
})

const menuOptions = computed<MenuOption[]>(() => [
  { key: 'dashboard', label: '首页统计', icon: LayoutDashboard },
  { key: 'quick', label: '快速记录', icon: Zap },
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
])

function onSelect(key: string) {
  if (key === 'new-station') {
    createOpen.value = true
    return
  }
  if (key.startsWith('st:')) {
    router.push(`/station/${key.slice(3)}`)
  } else if (key === 'quick') {
    router.push('/quick')
  } else {
    router.push('/dashboard')
  }
}

async function onStationCreated(station: StationDetail) {
  await refreshStations()
  router.push(`/station/${station.id}`)
}

onMounted(refreshStations)
</script>

<template>
  <div class="flex h-full bg-gray-50 text-gray-900">
    <!-- 左侧：电台目录 -->
    <aside class="flex w-56 shrink-0 flex-col border-r border-gray-200 bg-white">
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

    <StationDialog v-model:open="createOpen" :station="null" @saved="onStationCreated" />
  </div>
</template>
