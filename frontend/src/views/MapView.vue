<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import { KMessage, KSelect } from '@guoyg578/k-ui'
import type { QSO } from '../types'
import { api } from '../api'
import { fmtDate, gridToLatLon } from '../utils'
import { stations } from '../store'

const el = ref<HTMLDivElement | null>(null)
const failed = ref(false)
const filterStation = ref(0)
const total = ref(0)
const plotted = ref(0)

let map: L.Map | null = null
let layer: L.LayerGroup | null = null

async function load() {
  try {
    const sid = Number(filterStation.value) || undefined
    const page = await api.listQsos({ station_id: sid, page: 1, page_size: 500 })
    total.value = page.total
    render(page.items)
  } catch (e) {
    KMessage.error(`加载通联失败: ${(e as Error).message}`)
  }
}

function render(qsos: QSO[]) {
  if (!map) return
  layer?.remove()
  layer = L.layerGroup().addTo(map)

  const bounds: L.LatLngExpression[] = []
  const myGrids = new Set<string>()
  let count = 0

  for (const q of qsos) {
    const b = gridToLatLon(q.grid || '')
    if (!b) continue
    const a = gridToLatLon(q.my_grid || '')
    L.circleMarker(b, { radius: 5, color: '#dc2626', weight: 1.5, fillOpacity: 0.75 })
      .addTo(layer)
      .bindTooltip(
        `<b>${q.call}</b><br>${q.grid}${q.qth ? ' · ' + q.qth : ''}<br>${fmtDate(q.datetime_utc)}${q.distance_km ? ` · ${q.distance_km} km` : ''}`,
      )
    bounds.push(b)
    count++
    if (a) {
      L.polyline([a, b], { color: '#94a3b8', weight: 1, opacity: 0.55 }).addTo(layer)
      if (q.my_grid && !myGrids.has(q.my_grid)) {
        myGrids.add(q.my_grid)
        L.circleMarker(a, { radius: 7, color: '#2563eb', weight: 2, fillOpacity: 0.9 })
          .addTo(layer)
          .bindTooltip(`本台 ${q.my_callsign}（${q.my_grid}）`)
        bounds.push(a)
      }
    }
  }
  plotted.value = count
  if (bounds.length) map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40], maxZoom: 10 })
}

watch(filterStation, load)

onMounted(() => {
  if (!el.value) return
  map = L.map(el.value, { attributionControl: false })
  const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18 })
  tiles.on('tileerror', () => (failed.value = true))
  tiles.addTo(map)
  map.setView([34, 108], 4)
  load()
})

onBeforeUnmount(() => {
  map?.remove()
  map = null
})
</script>

<template>
  <div class="flex h-full flex-col p-4 sm:p-6">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-y-2">
      <div>
        <h1 class="text-xl font-bold">通联地图</h1>
        <p class="mt-0.5 text-xs text-gray-400">
          红点为对方位置，蓝点为本台位置（按网格定位绘制）
        </p>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs text-gray-400">
          已绘制 {{ plotted }} 条<template v-if="total > 500">（最近 500 条中）</template>
        </span>
        <div class="w-44">
          <KSelect
            v-model="filterStation"
            :options="[
              { value: 0, label: '全部电台' },
              ...stations.map((s) => ({ value: s.id, label: s.name })),
            ]"
            size="sm"
          />
        </div>
      </div>
    </div>

    <!-- z-0 隔离 Leaflet 内部的高 z-index，避免盖住页面弹层（如电台下拉框） -->
    <div class="relative z-0 min-h-0 flex-1 overflow-hidden rounded-2xl border border-gray-200 shadow-sm">
      <div ref="el" class="h-full w-full" />
      <div
        v-if="failed"
        class="absolute inset-0 z-[500] flex items-center justify-center bg-gray-50 text-xs text-gray-400"
      >
        地图不可用（无法加载在线瓦片）
      </div>
    </div>
  </div>
</template>
