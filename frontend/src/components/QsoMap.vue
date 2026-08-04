<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import L from 'leaflet'
import { gridToLatLon } from '../utils'

const props = defineProps<{
  myGrid: string
  grid: string
  myLabel?: string
  label?: string
}>()

const el = ref<HTMLDivElement | null>(null)
const failed = ref(false)
let map: L.Map | null = null

onMounted(() => {
  const a = gridToLatLon(props.myGrid)
  const b = gridToLatLon(props.grid)
  if (!el.value || (!a && !b)) {
    failed.value = true
    return
  }
  map = L.map(el.value, { attributionControl: false, zoomControl: false })
  const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
  })
  // 在线瓦片加载失败（NAS 无外网）时降级为提示
  tiles.on('tileerror', () => {
    failed.value = true
  })
  tiles.addTo(map)

  const points: L.LatLngExpression[] = []
  if (a) {
    L.circleMarker(a, { radius: 7, color: '#2563eb', fillOpacity: 0.9 })
      .addTo(map)
      .bindTooltip(props.myLabel || '本台')
    points.push(a)
  }
  if (b) {
    L.circleMarker(b, { radius: 7, color: '#dc2626', fillOpacity: 0.9 })
      .addTo(map)
      .bindTooltip(props.label || '对方')
    points.push(b)
  }
  if (a && b) {
    L.polyline([a, b], { color: '#6b7280', dashArray: '6 6', weight: 2 }).addTo(map)
    map.fitBounds(L.latLngBounds(points), { padding: [30, 30] })
  } else {
    map.setView(points[0]!, 6)
  }

  // 在对话框等弹层中挂载时，容器尺寸在动画结束后才稳定，需要重算
  setTimeout(() => {
    if (!map) return
    map.invalidateSize()
    if (a && b) map.fitBounds(L.latLngBounds(points), { padding: [30, 30] })
  }, 250)
})

onBeforeUnmount(() => {
  map?.remove()
  map = null
})
</script>

<template>
  <div class="relative h-full min-h-52 w-full overflow-hidden rounded-lg border border-gray-200">
    <div ref="el" class="h-full w-full" />
    <div
      v-if="failed"
      class="absolute inset-0 z-[500] flex items-center justify-center bg-gray-50 text-xs text-gray-400"
    >
      地图不可用（无法加载在线瓦片或网格无效）
    </div>
  </div>
</template>
