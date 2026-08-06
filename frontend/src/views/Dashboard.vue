<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { KEmpty, KMessage, KSelect, KTag } from '@guoyg578/k-ui'
import {
  Antenna as AntennaIcon,
  CalendarDays,
  Globe2,
  Medal,
  RadioTower,
  TrendingUp,
  Waves,
} from '@lucide/vue'
import type { QSO, Stats } from '../types'
import { api } from '../api'
import { dateKey, fmtDate, fmtDateTime, fmtFreq } from '../utils'
import { stations } from '../store'

const stats = ref<Stats | null>(null)
const allQsos = ref<QSO[]>([])
// 0 = 全部电台（Select 底层会把 null 字符串化，不能用 null 作选项值）
const filterStation = ref<number>(0)

async function load() {
  // 兜底归一化：清空/字符串化后的值统一转为 undefined（=不过滤）
  const sid = Number(filterStation.value ?? 0) || undefined
  try {
    stats.value = await api.stats(sid)
    // 拉取最近 500 条用于列表与分布图（个人日志规模足够）
    const page = await api.listQsos({ station_id: sid, page: 1, page_size: 500 })
    allQsos.value = page.items
  } catch (e) {
    KMessage.error(`加载统计失败: ${(e as Error).message}`)
  }
}

watch(filterStation, load)
watch(() => stations.value.length, load)
onMounted(load)

const recent = computed(() => allQsos.value.slice(0, 8))

function aggregate(field: 'band' | 'mode') {
  const counts = new Map<string, number>()
  for (const q of allQsos.value) {
    const key = q[field]
    if (!key) continue
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([name, count]) => ({ name, count }))
}

const bandDist = computed(() => aggregate('band'))
const modeDist = computed(() => aggregate('mode'))
const bandMax = computed(() => Math.max(1, ...bandDist.value.map((d) => d.count)))
const modeMax = computed(() => Math.max(1, ...modeDist.value.map((d) => d.count)))

// 近 30 天每日通联数
const dailyActivity = computed(() => {
  // 按北京/本地日期分桶，与列表展示一致
  const counts = new Map<string, number>()
  for (const q of allQsos.value) {
    const d = fmtDate(q.datetime_utc)
    counts.set(d, (counts.get(d) ?? 0) + 1)
  }
  const days: { date: string; count: number }[] = []
  const today = new Date()
  for (let i = 29; i >= 0; i--) {
    const key = dateKey(new Date(today.getTime() - i * 86400_000))
    days.push({ date: key, count: counts.get(key) ?? 0 })
  }
  return days
})
const dailyMax = computed(() => Math.max(1, ...dailyActivity.value.map((d) => d.count)))
const dailyTotal = computed(() => dailyActivity.value.reduce((s, d) => s + d.count, 0))

// 距离排行 Top 5
const distanceRank = computed(() =>
  [...allQsos.value]
    .filter((q) => q.distance_km)
    .sort((a, b) => (b.distance_km ?? 0) - (a.distance_km ?? 0))
    .slice(0, 5),
)
const medalColors = ['text-amber-500', 'text-gray-400', 'text-orange-400']
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <div class="mb-5 flex items-center justify-between">
      <h1 class="text-xl font-bold">电台统计</h1>
      <div class="w-52">
        <KSelect
          v-model="filterStation"
          :options="[
            { value: 0, label: '全部电台' },
            ...stations.map((s) => ({ value: s.id, label: s.name })),
          ]"
          placeholder="全部电台"
          size="sm"
        />
      </div>
    </div>

    <template v-if="stats">
      <!-- 第一行：英雄数字 + 统计瓦片 -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4 xl:grid-cols-12">
        <div
          class="relative col-span-2 flex flex-col justify-between overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 p-6 text-white shadow-lg lg:col-span-4 xl:col-span-4"
        >
          <RadioTower class="absolute -right-6 -top-6 size-40 opacity-10" />
          <div class="text-sm font-medium text-blue-100">累计 QSO</div>
          <div class="my-2 text-6xl font-semibold leading-none">
            {{ stats.total_qso.toLocaleString() }}
          </div>
          <div class="flex items-center gap-2 text-sm text-blue-100">
            <span class="inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-0.5">
              本月 +{{ stats.month_qso }}
            </span>
            <span v-if="stats.top_band">主力 {{ stats.top_band }} · {{ stats.top_mode }}</span>
          </div>
        </div>

        <div class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm xl:col-span-2">
          <div class="mb-2 inline-flex rounded-lg bg-emerald-50 p-2">
            <CalendarDays class="size-5 text-emerald-600" />
          </div>
          <div class="text-2xl font-semibold">{{ stats.month_qso }}</div>
          <div class="mt-0.5 text-xs text-gray-500">本月 QSO</div>
        </div>

        <div class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm xl:col-span-2">
          <div class="mb-2 inline-flex rounded-lg bg-amber-50 p-2">
            <Globe2 class="size-5 text-amber-600" />
          </div>
          <div class="text-2xl font-semibold">
            {{ stats.max_distance_km ? stats.max_distance_km.toLocaleString() : '—' }}
            <span v-if="stats.max_distance_km" class="text-sm font-normal text-gray-400">km</span>
          </div>
          <div class="mt-0.5 text-xs text-gray-500">最远距离</div>
        </div>

        <div class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm xl:col-span-2">
          <div class="mb-2 inline-flex rounded-lg bg-violet-50 p-2">
            <AntennaIcon class="size-5 text-violet-600" />
          </div>
          <div class="text-2xl font-semibold">{{ stats.top_band || '—' }}</div>
          <div class="mt-0.5 text-xs text-gray-500">常用频段</div>
        </div>

        <div class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm xl:col-span-2">
          <div class="mb-2 inline-flex rounded-lg bg-rose-50 p-2">
            <Waves class="size-5 text-rose-600" />
          </div>
          <div class="text-2xl font-semibold">{{ stats.top_mode || '—' }}</div>
          <div class="mt-0.5 text-xs text-gray-500">常用模式</div>
        </div>
      </div>

      <!-- 第二行：近30天活跃度 + 波段分布 + 模式分布 -->
      <div class="mt-4 grid gap-4 lg:grid-cols-3">
        <div class="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
          <div class="mb-1 flex items-center justify-between">
            <div class="flex items-center gap-1.5 text-sm font-semibold">
              <TrendingUp class="size-4 text-blue-500" /> 近 30 天活跃度
            </div>
            <div class="text-xs text-gray-400">共 {{ dailyTotal }} 次</div>
          </div>
          <div class="mt-4 flex h-24 items-end gap-[3px]">
            <div
              v-for="d in dailyActivity"
              :key="d.date"
              class="group relative flex-1 rounded-t"
              :class="d.count ? 'bg-blue-500 hover:bg-blue-600' : 'bg-gray-100'"
              :style="{ height: d.count ? `${Math.max(8, (d.count / dailyMax) * 100)}%` : '4px' }"
              :title="`${d.date}：${d.count} 次通联`"
            />
          </div>
          <div class="mt-2 flex justify-between text-[10px] text-gray-400">
            <span>{{ dailyActivity[0]?.date.slice(5) }}</span>
            <span>今天</span>
          </div>
        </div>

        <div class="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
          <div class="mb-4 text-sm font-semibold">波段分布</div>
          <KEmpty v-if="!bandDist.length" title="暂无数据" compact />
          <div v-else class="space-y-3">
            <div v-for="d in bandDist" :key="d.name" class="flex items-center gap-3">
              <div class="w-12 shrink-0 text-right text-xs text-gray-500">{{ d.name }}</div>
              <div class="h-4 flex-1 overflow-hidden rounded-r bg-gray-100">
                <div
                  class="h-full rounded-r bg-blue-500 transition-all"
                  :style="{ width: `${(d.count / bandMax) * 100}%` }"
                />
              </div>
              <div class="w-8 shrink-0 text-xs font-medium text-gray-700">{{ d.count }}</div>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
          <div class="mb-4 text-sm font-semibold">模式分布</div>
          <KEmpty v-if="!modeDist.length" title="暂无数据" compact />
          <div v-else class="space-y-3">
            <div v-for="d in modeDist" :key="d.name" class="flex items-center gap-3">
              <div class="w-12 shrink-0 text-right text-xs text-gray-500">{{ d.name }}</div>
              <div class="h-4 flex-1 overflow-hidden rounded-r bg-gray-100">
                <div
                  class="h-full rounded-r bg-blue-500 transition-all"
                  :style="{ width: `${(d.count / modeMax) * 100}%` }"
                />
              </div>
              <div class="w-8 shrink-0 text-xs font-medium text-gray-700">{{ d.count }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 第三行：最近通联 + 距离排行 -->
      <div class="mt-4 grid gap-4 xl:grid-cols-3">
        <div class="xl:col-span-2">
          <div class="rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div class="border-b border-gray-100 px-5 py-3 text-sm font-semibold">最近通联</div>
            <KEmpty v-if="!recent.length" title="暂无通联记录" compact class="py-8" />
            <div v-else class="divide-y divide-gray-50">
              <div
                v-for="q in recent"
                :key="q.id"
                class="flex items-center justify-between px-5 py-2.5 text-sm transition-colors hover:bg-gray-50"
              >
                <div class="flex items-center gap-3">
                  <span class="font-semibold">{{ q.call }}</span>
                  <KTag v-if="q.band" size="sm">{{ q.band }}</KTag>
                  <span class="text-gray-500">{{ q.mode }}</span>
                  <span v-if="q.freq_mhz" class="text-gray-400">{{ fmtFreq(q.freq_mhz) }} MHz</span>
                  <span v-if="q.qth" class="hidden text-xs text-gray-400 sm:inline">{{ q.qth }}</span>
                </div>
                <span class="text-xs text-gray-400">{{ fmtDateTime(q.datetime_utc) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-gray-100 bg-white shadow-sm">
          <div class="flex items-center gap-1.5 border-b border-gray-100 px-5 py-3 text-sm font-semibold">
            <Medal class="size-4 text-amber-500" /> 距离排行
          </div>
          <KEmpty v-if="!distanceRank.length" title="暂无距离数据" compact class="py-8" />
          <div v-else class="divide-y divide-gray-50">
            <div
              v-for="(q, i) in distanceRank"
              :key="q.id"
              class="flex items-center justify-between px-5 py-2.5 text-sm"
            >
              <div class="flex items-center gap-3">
                <span
                  class="w-5 text-center text-sm font-bold"
                  :class="medalColors[i] ?? 'text-gray-300'"
                >{{ i + 1 }}</span>
                <div>
                  <div class="font-semibold">{{ q.call }}</div>
                  <div class="text-xs text-gray-400">{{ q.qth || q.grid }} · {{ q.band }}</div>
                </div>
              </div>
              <span class="font-semibold tabular-nums text-gray-700">
                {{ q.distance_km?.toLocaleString() }} km
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
