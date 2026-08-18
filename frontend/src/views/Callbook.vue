<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { KEmpty, KMessage, KSearchBar, KTag } from '@guoyg578/k-ui'
import { Users } from '@lucide/vue'
import type { QSO } from '../types'
import { api } from '../api'
import { fmtDate } from '../utils'

type Entry = {
  call: string
  count: number
  firstDate: string
  lastDate: string
  qth: string
  bands: string[]
  modes: string[]
  maxDistance: number | null
}

const search = ref('')
const total = ref(0)
const qsos = ref<QSO[]>([])

onMounted(async () => {
  try {
    const page = await api.listQsos({ page: 1, page_size: 500 })
    total.value = page.total
    qsos.value = page.items
  } catch (e) {
    KMessage.error(`加载通联失败: ${(e as Error).message}`)
  }
})

// 头像配色：按呼号哈希轮换的柔和色板
const AVATAR_COLORS = [
  'bg-blue-50 text-blue-600',
  'bg-emerald-50 text-emerald-600',
  'bg-amber-50 text-amber-600',
  'bg-violet-50 text-violet-600',
  'bg-rose-50 text-rose-600',
  'bg-sky-50 text-sky-600',
  'bg-teal-50 text-teal-600',
]
function avatarClass(call: string): string {
  let h = 0
  for (const c of call) h = (h + c.charCodeAt(0)) % AVATAR_COLORS.length
  return AVATAR_COLORS[h]!
}

const entries = computed<Entry[]>(() => {
  const byCall = new Map<string, Entry>()
  for (const q of qsos.value) {
    const call = q.call.toUpperCase()
    let e = byCall.get(call)
    if (!e) {
      e = {
        call,
        count: 0,
        firstDate: q.datetime_utc,
        lastDate: q.datetime_utc,
        qth: '',
        bands: [],
        modes: [],
        maxDistance: null,
      }
      byCall.set(call, e)
    }
    e.count++
    if (q.datetime_utc < e.firstDate) e.firstDate = q.datetime_utc
    if (q.datetime_utc > e.lastDate) e.lastDate = q.datetime_utc
    if (q.qth) e.qth = q.qth
    if (q.band && !e.bands.includes(q.band)) e.bands.push(q.band)
    if (q.mode && !e.modes.includes(q.mode)) e.modes.push(q.mode)
    if (q.distance_km && (!e.maxDistance || q.distance_km > e.maxDistance))
      e.maxDistance = q.distance_km
  }
  const kw = search.value.trim().toUpperCase()
  return [...byCall.values()]
    .filter((e) => !kw || e.call.includes(kw) || e.qth.toUpperCase().includes(kw))
    .sort((a, b) => b.count - a.count || (a.call < b.call ? -1 : 1))
})
</script>

<template>
  <div class="h-full overflow-y-auto p-4 sm:p-6">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-y-2">
      <div>
        <h1 class="text-xl font-bold">呼号簿</h1>
        <p class="mt-0.5 text-xs text-gray-400">
          按呼号汇总的通联对象名录，共 {{ entries.length }} 位火腿<template v-if="total > 500">
            （基于最近 500 条记录）</template>
        </p>
      </div>
      <KSearchBar v-model="search" placeholder="搜索呼号 / QTH" />
    </div>

    <KEmpty v-if="!entries.length" title="暂无通联对象" description="记录第一条 QSO 后这里会自动汇总" />

    <div v-else class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
      <div
        v-for="e in entries"
        :key="e.call"
        class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div
              class="flex size-10 shrink-0 items-center justify-center rounded-full text-sm font-bold tracking-wide"
              :class="avatarClass(e.call)"
            >
              {{ e.call.slice(0, 2) }}
            </div>
            <div>
              <div class="text-base font-bold tracking-wide">{{ e.call }}</div>
              <div class="mt-0.5 text-xs text-gray-400">
                {{ e.qth || '未知 QTH' }}
              </div>
            </div>
          </div>
          <span
            class="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-600"
          >
            <Users class="size-3" /> {{ e.count }} 次
          </span>
        </div>

        <div class="mt-3 flex flex-wrap gap-1">
          <KTag v-for="b in e.bands" :key="b" size="sm">{{ b }}</KTag>
          <KTag v-for="m in e.modes" :key="m" size="sm" type="info">{{ m }}</KTag>
        </div>

        <div class="mt-3 flex items-center justify-between border-t border-gray-50 pt-2 text-xs text-gray-400">
          <span>首次 {{ fmtDate(e.firstDate) }} · 最近 {{ fmtDate(e.lastDate) }}</span>
          <span v-if="e.maxDistance" class="font-medium text-gray-600">
            {{ e.maxDistance.toLocaleString() }} km
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
