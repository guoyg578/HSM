<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { KMessage } from '@guoyg578/k-ui'
import {
  Award,
  CalendarCheck,
  Flame,
  Globe2,
  Layers,
  Moon,
  Radio,
  Rocket,
  Sunrise,
  Trophy,
  Users,
  Waves,
} from '@lucide/vue'
import type { Component } from 'vue'
import type { QSO } from '../types'
import { api } from '../api'
import { fmtDate } from '../utils'

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

type Badge = {
  key: string
  name: string
  desc: string
  icon: Component
  color: string
  bg: string
  achieved: boolean
  progress: number // 0-1
  progressText: string
}

function hourOf(q: QSO): number {
  const d = new Date(q.datetime_utc.endsWith('Z') ? q.datetime_utc : `${q.datetime_utc}Z`)
  return d.getHours()
}

const badges = computed<Badge[]>(() => {
  const list = qsos.value
  const count = total.value || list.length
  const calls = new Set(list.map((q) => q.call.toUpperCase()))
  const bands = new Set(list.map((q) => q.band).filter(Boolean))
  const modes = new Set(list.map((q) => q.mode).filter(Boolean))
  const maxDist = Math.max(0, ...list.map((q) => q.distance_km ?? 0))
  const nightCount = list.filter((q) => hourOf(q) >= 23 || hourOf(q) < 5).length
  const earlyCount = list.filter((q) => hourOf(q) >= 5 && hourOf(q) < 8).length
  const days = new Set(list.map((q) => fmtDate(q.datetime_utc)))
  // 最长连续活跃天数
  const sorted = [...days].sort()
  let bestStreak = 0
  let cur = 0
  let prev = ''
  for (const d of sorted) {
    if (prev && new Date(d).getTime() - new Date(prev).getTime() === 86400_000) cur++
    else cur = 1
    if (cur > bestStreak) bestStreak = cur
    prev = d
  }

  const make = (
    key: string,
    name: string,
    desc: string,
    icon: Component,
    color: string,
    bg: string,
    value: number,
    target: number,
    unit = '',
  ): Badge => ({
    key,
    name,
    desc,
    icon,
    color,
    bg,
    achieved: value >= target,
    progress: Math.min(1, value / target),
    progressText: `${Math.min(value, target).toLocaleString()} / ${target.toLocaleString()}${unit}`,
  })

  return [
    make('first', '首联达成', '完成第一次 QSO', Radio, 'text-blue-600', 'bg-blue-50', count, 1),
    make('c50', '小有名气', '累计 50 次 QSO', Award, 'text-emerald-600', 'bg-emerald-50', count, 50),
    make('c200', '通联老手', '累计 200 次 QSO', Trophy, 'text-amber-600', 'bg-amber-50', count, 200),
    make('c1000', '王牌操作员', '累计 1000 次 QSO', Rocket, 'text-violet-600', 'bg-violet-50', count, 1000),
    make('dx1k', 'DX 入门', '单次通联距离超过 1,000 km', Globe2, 'text-sky-600', 'bg-sky-50', maxDist, 1000, ' km'),
    make('dx5k', 'DX 猎手', '单次通联距离超过 5,000 km', Globe2, 'text-indigo-600', 'bg-indigo-50', maxDist, 5000, ' km'),
    make('bands', '波段收藏家', '在 5 个不同波段完成通联', Layers, 'text-orange-600', 'bg-orange-50', bands.size, 5),
    make('modes', '模式玩家', '使用 3 种不同模式通联', Waves, 'text-rose-600', 'bg-rose-50', modes.size, 3),
    make('friends', '人脉广布', '与 30 个不同呼号通联', Users, 'text-teal-600', 'bg-teal-50', calls.size, 30),
    make('night', '夜猫子', '深夜（23:00–05:00）通联 10 次', Moon, 'text-slate-600', 'bg-slate-100', nightCount, 10),
    make('early', '早鸟电台', '清晨（05:00–08:00）通联 5 次', Sunrise, 'text-yellow-600', 'bg-yellow-50', earlyCount, 5),
    make('streak', '七日连击', '连续 7 天保持通联', Flame, 'text-red-600', 'bg-red-50', bestStreak, 7, ' 天'),
    make('active30', '月度活跃', '累计 30 个活跃日', CalendarCheck, 'text-lime-600', 'bg-lime-50', days.size, 30, ' 天'),
  ]
})

const achievedCount = computed(() => badges.value.filter((b) => b.achieved).length)
</script>

<template>
  <div class="h-full overflow-y-auto p-4 sm:p-6">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-y-2">
      <div>
        <h1 class="text-xl font-bold">成就徽章</h1>
        <p class="mt-0.5 text-xs text-gray-400">
          根据通联记录自动点亮<template v-if="total > 500">（部分统计基于最近 500 条）</template>
        </p>
      </div>
      <span class="rounded-full bg-amber-50 px-3 py-1 text-sm font-medium text-amber-600">
        已点亮 {{ achievedCount }} / {{ badges.length }}
      </span>
    </div>

    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
      <div
        v-for="b in badges"
        :key="b.key"
        class="rounded-2xl border bg-white p-4 shadow-sm transition-all"
        :class="b.achieved ? 'border-gray-100 hover:shadow-md' : 'border-gray-100 opacity-70'"
      >
        <div class="flex items-center gap-3">
          <div
            class="flex size-11 shrink-0 items-center justify-center rounded-xl"
            :class="b.achieved ? b.bg : 'bg-gray-100'"
          >
            <component :is="b.icon" class="size-5" :class="b.achieved ? b.color : 'text-gray-400'" />
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-1.5 font-semibold" :class="b.achieved ? '' : 'text-gray-500'">
              {{ b.name }}
              <Trophy v-if="b.achieved" class="size-3.5 text-amber-500" />
            </div>
            <div class="truncate text-xs text-gray-400">{{ b.desc }}</div>
          </div>
        </div>
        <div v-if="!b.achieved" class="mt-3">
          <div class="h-1.5 overflow-hidden rounded-full bg-gray-100">
            <div
              class="h-full rounded-full bg-gray-300 transition-all"
              :style="{ width: `${b.progress * 100}%` }"
            />
          </div>
          <div class="mt-1 text-right text-[10px] text-gray-400">{{ b.progressText }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
