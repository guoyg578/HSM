<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { KMessage } from '@guoyg578/k-ui'
import { CalendarCheck, Flame, TrendingUp } from '@lucide/vue'
import type { QSO } from '../types'
import { api } from '../api'
import { dateKey, fmtDate } from '../utils'

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

const countsByDay = computed(() => {
  const m = new Map<string, number>()
  for (const q of qsos.value) {
    const d = fmtDate(q.datetime_utc)
    m.set(d, (m.get(d) ?? 0) + 1)
  }
  return m
})

// 过去 53 周的格子（列 = 周，行 = 周日到周六），最后一列到今天
type Cell = { date: string; count: number } | null
const weeks = computed<Cell[][]>(() => {
  const today = new Date()
  const end = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const start = new Date(end.getTime() - (52 * 7 + end.getDay()) * 86400_000)
  const cols: Cell[][] = []
  const cursor = new Date(start)
  while (cursor <= end) {
    const col: Cell[] = []
    for (let dow = 0; dow < 7; dow++) {
      if (cursor > end || cursor < start) {
        col.push(null)
      } else {
        const key = dateKey(cursor)
        col.push({ date: key, count: countsByDay.value.get(key) ?? 0 })
        cursor.setDate(cursor.getDate() + 1)
      }
    }
    cols.push(col)
  }
  return cols
})

// 每列顶部的月份标签（该列首日进入新月份时显示）
const monthLabels = computed(() => {
  let prev = ''
  return weeks.value.map((col) => {
    const first = col.find(Boolean)
    if (!first) return ''
    const m = first.date.slice(0, 7)
    if (m === prev) return ''
    prev = m
    return `${Number(first.date.slice(5, 7))}月`
  })
})

function cellClass(count: number): string {
  if (!count) return 'bg-gray-100'
  if (count === 1) return 'bg-blue-200'
  if (count <= 3) return 'bg-blue-400'
  if (count <= 6) return 'bg-blue-600'
  return 'bg-indigo-700'
}

const yearTotal = computed(() => {
  let sum = 0
  for (const col of weeks.value) for (const c of col) if (c) sum += c.count
  return sum
})

const activeDays = computed(() => {
  let n = 0
  for (const col of weeks.value) for (const c of col) if (c && c.count) n++
  return n
})

// 连续活跃天数（当前 / 历史最长）
const streaks = computed(() => {
  const days: { date: string; count: number }[] = []
  for (let i = 0; i < 7; i++)
    for (const col of weeks.value) {
      const c = col[i]
      if (c) days.push(c)
    }
  days.sort((a, b) => (a.date < b.date ? -1 : 1))
  let best = 0
  let cur = 0
  for (const d of days) {
    cur = d.count ? cur + 1 : 0
    if (cur > best) best = cur
  }
  let current = 0
  for (let i = days.length - 1; i >= 0; i--) {
    if (!days[i]!.count) {
      // 今天还没通联不打断连击，从昨天起算
      if (i === days.length - 1) continue
      break
    }
    current++
  }
  return { best, current }
})
</script>

<template>
  <div class="h-full overflow-y-auto p-4 sm:p-6">
    <div class="mb-4">
      <h1 class="text-xl font-bold">通联日历</h1>
      <p class="mt-0.5 text-xs text-gray-400">
        近一年每日通联热力图<template v-if="total > 500">（基于最近 500 条记录）</template>
      </p>
    </div>

    <!-- 摘要 -->
    <div class="mb-4 grid grid-cols-3 gap-4 sm:max-w-2xl">
      <div class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
        <div class="mb-2 inline-flex rounded-lg bg-blue-50 p-2">
          <TrendingUp class="size-5 text-blue-600" />
        </div>
        <div class="text-2xl font-semibold">{{ yearTotal }}</div>
        <div class="mt-0.5 text-xs text-gray-500">近一年 QSO</div>
      </div>
      <div class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
        <div class="mb-2 inline-flex rounded-lg bg-emerald-50 p-2">
          <CalendarCheck class="size-5 text-emerald-600" />
        </div>
        <div class="text-2xl font-semibold">{{ activeDays }}</div>
        <div class="mt-0.5 text-xs text-gray-500">活跃天数</div>
      </div>
      <div class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
        <div class="mb-2 inline-flex rounded-lg bg-orange-50 p-2">
          <Flame class="size-5 text-orange-500" />
        </div>
        <div class="text-2xl font-semibold">{{ streaks.current }}</div>
        <div class="mt-0.5 text-xs text-gray-500">连续活跃 · 最长 {{ streaks.best }} 天</div>
      </div>
    </div>

    <!-- 热力图 -->
    <div class="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
      <div class="mb-3 flex items-center gap-1.5 text-sm font-semibold">
        <CalendarCheck class="size-4 text-blue-500" /> 年度热力图
      </div>
      <div class="overflow-x-auto pb-1">
        <div class="inline-block">
          <div class="mb-1 flex gap-[3px] pl-5 text-[10px] leading-none text-gray-400">
            <span v-for="(label, i) in monthLabels" :key="i" class="w-[11px] shrink-0">
              {{ label ? label : '' }}
            </span>
          </div>
          <div class="flex gap-[3px]">
            <div class="mr-0.5 flex w-3.5 flex-col gap-[3px] text-[9px] leading-none text-gray-400">
              <span
                v-for="(d, i) in ['', '一', '', '三', '', '五', '']"
                :key="i"
                class="flex h-[11px] items-center"
              >{{ d }}</span>
            </div>
            <div v-for="(col, i) in weeks" :key="i" class="flex flex-col gap-[3px]">
              <div
                v-for="(cell, j) in col"
                :key="j"
                class="size-[11px] rounded-[2px] transition-transform hover:scale-125"
                :class="cell ? cellClass(cell.count) : 'bg-transparent'"
                :title="cell ? `${cell.date}：${cell.count} 次通联` : ''"
              />
            </div>
          </div>
          <div class="mt-2 flex items-center justify-end gap-1 text-[10px] text-gray-400">
            少
            <span class="size-[11px] rounded-[2px] bg-gray-100" />
            <span class="size-[11px] rounded-[2px] bg-blue-200" />
            <span class="size-[11px] rounded-[2px] bg-blue-400" />
            <span class="size-[11px] rounded-[2px] bg-blue-600" />
            <span class="size-[11px] rounded-[2px] bg-indigo-700" />
            多
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
