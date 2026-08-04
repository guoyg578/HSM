<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { KMenu, KMessage } from '@guoyg578/k-ui'
import type { MenuOption } from '@guoyg578/k-ui'
import { LayoutDashboard, Plus, RadioTower, Zap } from '@lucide/vue'
import type { Station, StationDetail } from './types'
import { api } from './api'
import { loadActiveView, saveActiveView, saveLastStation } from './prefs'
import Dashboard from './views/Dashboard.vue'
import QuickLog from './views/QuickLog.vue'
import StationLog from './views/StationLog.vue'
import ConfigPanel from './components/ConfigPanel.vue'
import StationDialog from './components/StationDialog.vue'

const stations = ref<Station[]>([])
const activeKey = ref<string>('dashboard')
const expandedKeys = ref<string[]>(['stations'])
const stationDetail = ref<StationDetail | null>(null)

const dialogOpen = ref(false)
const editingStation = ref<StationDetail | null>(null)

const currentStationId = computed(() =>
  activeKey.value.startsWith('st:') ? Number(activeKey.value.slice(3)) : null,
)

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

async function refreshStations() {
  stations.value = await api.listStations()
}

async function loadDetail(id: number) {
  try {
    stationDetail.value = await api.getStation(id)
  } catch (e) {
    KMessage.error(`加载电台失败: ${(e as Error).message}`)
    stationDetail.value = null
  }
}

async function onSelect(key: string) {
  if (key === 'new-station') {
    editingStation.value = null
    dialogOpen.value = true
    return
  }
  activeKey.value = key
  saveActiveView(key)
  if (key.startsWith('st:')) {
    const id = Number(key.slice(3))
    saveLastStation(id)
    await loadDetail(id)
  } else {
    stationDetail.value = null
  }
}

function onEditStation() {
  editingStation.value = stationDetail.value
  dialogOpen.value = true
}

async function onStationSaved(station: StationDetail) {
  await refreshStations()
  await onSelect(`st:${station.id}`)
}

async function onStationDeleted() {
  await refreshStations()
  activeKey.value = 'dashboard'
  stationDetail.value = null
}

async function onConfigChanged() {
  if (currentStationId.value) await loadDetail(currentStationId.value)
}

onMounted(async () => {
  await refreshStations()
  // 还原刷新前所在的页面；电台已被删除则回到首页
  const saved = loadActiveView()
  if (saved.startsWith('st:')) {
    const id = Number(saved.slice(3))
    if (stations.value.some((s) => s.id === id)) {
      await onSelect(saved)
    }
  } else if (saved === 'quick') {
    await onSelect(saved)
  }
})
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

    <!-- 中间：内容区 -->
    <main class="min-w-0 flex-1 overflow-y-auto">
      <Dashboard v-if="activeKey === 'dashboard'" :stations="stations" />
      <QuickLog v-else-if="activeKey === 'quick'" :stations="stations" />
      <StationLog
        v-else-if="currentStationId && stationDetail"
        :key="currentStationId"
        :station="stationDetail"
        @edit-station="onEditStation"
        @station-deleted="onStationDeleted"
      />
    </main>

    <!-- 右侧：当前电台配置 -->
    <aside
      v-if="currentStationId && stationDetail"
      class="w-72 shrink-0 overflow-y-auto border-l border-gray-200 bg-white"
    >
      <ConfigPanel :station="stationDetail" @changed="onConfigChanged" />
    </aside>

    <StationDialog
      v-model:open="dialogOpen"
      :station="editingStation"
      @saved="onStationSaved"
    />
  </div>
</template>
