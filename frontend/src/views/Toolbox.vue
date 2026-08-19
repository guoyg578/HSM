<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { KInput, KInputNumber, KTag } from '@guoyg578/k-ui'
import { Calculator, Compass, MapPin, Ruler, Waves } from '@lucide/vue'
import { api } from '../api'
import { appSettings } from '../settings'
import { gridDistanceKm, gridToLatLon, isValidGrid } from '../utils'

// ---- 网格距离计算 ----
const gridA = ref('')
const gridB = ref('')
const distance = computed(() => gridDistanceKm(gridA.value, gridB.value))

// ---- QTH 地名 → 网格 ----
const qthQuery = ref('')
const qthResult = ref<{ grid: string; matched: string; found: boolean } | null>(null)
let qthTimer: ReturnType<typeof setTimeout> | undefined
watch(qthQuery, (v) => {
  clearTimeout(qthTimer)
  if (!v.trim()) {
    qthResult.value = null
    return
  }
  qthTimer = setTimeout(async () => {
    try {
      qthResult.value = await api.qthGrid(v)
    } catch {
      qthResult.value = null
    }
  }, 300)
})

// ---- 网格 → 经纬度 ----
const gridQuery = ref('')
const latlon = computed(() => gridToLatLon(gridQuery.value))
const gridInvalid = computed(() => !!gridQuery.value.trim() && !isValidGrid(gridQuery.value))

// ---- 频率 ↔ 波长 ----
const freqMhz = ref<number | null>(null)
const wavelength = computed(() =>
  freqMhz.value && freqMhz.value > 0 ? 299.792458 / freqMhz.value : null,
)
const matchedBand = computed(() => {
  if (!freqMhz.value) return ''
  const hit = appSettings.value.bands.find(
    (b) => freqMhz.value! >= b.low_mhz && freqMhz.value! <= b.high_mhz,
  )
  return hit?.name ?? ''
})

function fmtCoord(v: number, pos: string, neg: string): string {
  return `${Math.abs(v).toFixed(4)}° ${v >= 0 ? pos : neg}`
}

// ---- RST 速查 ----
const RST_R = ['1 无法辨认', '2 勉强辨认', '3 较困难', '4 无困难', '5 完全清晰']
const RST_S = ['1 微弱', '3 弱', '5 尚好', '7 中强', '9 极强']
</script>

<template>
  <div class="h-full overflow-y-auto p-4 sm:p-6">
    <div class="mb-4">
      <h1 class="text-xl font-bold">工具箱</h1>
      <p class="mt-0.5 text-xs text-gray-400">业余无线电常用小工具</p>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <!-- 网格距离 -->
      <section class="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
        <div class="mb-3 flex items-center gap-2 text-sm font-semibold">
          <span class="inline-flex rounded-lg bg-blue-50 p-1.5"><Ruler class="size-4 text-blue-600" /></span>
          网格距离计算
        </div>
        <div class="grid grid-cols-2 gap-3">
          <label class="block">
            <span class="mb-1 block text-xs text-gray-500">网格 A</span>
            <KInput v-model="gridA" placeholder="如 OM89" />
          </label>
          <label class="block">
            <span class="mb-1 block text-xs text-gray-500">网格 B</span>
            <KInput v-model="gridB" placeholder="如 PM01" />
          </label>
        </div>
        <div class="mt-4 rounded-xl bg-gray-50 p-3 text-center">
          <template v-if="distance !== null">
            <span class="text-2xl font-bold tabular-nums">{{ distance.toLocaleString() }}</span>
            <span class="ml-1 text-sm text-gray-500">km（大圆距离）</span>
          </template>
          <span v-else class="text-sm text-gray-400">输入两个有效的 Maidenhead 网格</span>
        </div>
      </section>

      <!-- QTH → 网格 -->
      <section class="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
        <div class="mb-3 flex items-center gap-2 text-sm font-semibold">
          <span class="inline-flex rounded-lg bg-amber-50 p-1.5"><MapPin class="size-4 text-amber-600" /></span>
          QTH 地名 → 网格
        </div>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">地名（支持省 / 市，中英文均可）</span>
          <KInput v-model="qthQuery" placeholder="如 安徽合肥 / 北京 / Tokyo" />
        </label>
        <div class="mt-4 rounded-xl bg-gray-50 p-3 text-center">
          <template v-if="qthResult?.found">
            <span class="text-2xl font-bold tracking-wide">{{ qthResult.grid }}</span>
            <div class="mt-0.5 text-xs text-gray-400">
              按「{{ qthResult.matched }}」估算的 4 位网格
            </div>
          </template>
          <span v-else-if="qthQuery.trim()" class="text-sm text-gray-400">未收录该地名</span>
          <span v-else class="text-sm text-gray-400">输入地名估算网格</span>
        </div>
      </section>

      <!-- 网格 → 经纬度 -->
      <section class="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
        <div class="mb-3 flex items-center gap-2 text-sm font-semibold">
          <span class="inline-flex rounded-lg bg-emerald-50 p-1.5"><Compass class="size-4 text-emerald-600" /></span>
          网格 → 经纬度
        </div>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">网格定位（4 / 6 / 8 位）</span>
          <KInput v-model="gridQuery" placeholder="如 OM89cv" />
        </label>
        <div class="mt-4 rounded-xl bg-gray-50 p-3 text-center">
          <template v-if="latlon">
            <span class="text-lg font-bold tabular-nums">{{ fmtCoord(latlon[0], 'N', 'S') }}</span>
            <span class="mx-2 text-gray-300">·</span>
            <span class="text-lg font-bold tabular-nums">{{ fmtCoord(latlon[1], 'E', 'W') }}</span>
            <div class="mt-0.5 text-xs text-gray-400">网格中心点坐标</div>
          </template>
          <span v-else-if="gridInvalid" class="text-sm text-red-400">网格格式无效</span>
          <span v-else class="text-sm text-gray-400">输入网格查看中心点坐标</span>
        </div>
      </section>

      <!-- 频率 ↔ 波长 -->
      <section class="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
        <div class="mb-3 flex items-center gap-2 text-sm font-semibold">
          <span class="inline-flex rounded-lg bg-violet-50 p-1.5"><Calculator class="size-4 text-violet-600" /></span>
          频率 ↔ 波长
        </div>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">频率（MHz）</span>
          <KInputNumber v-model="freqMhz" placeholder="438.500" :min="0" :step="0.001" :show-button="false" />
        </label>
        <div class="mt-4 rounded-xl bg-gray-50 p-3 text-center">
          <template v-if="wavelength">
            <span class="text-2xl font-bold tabular-nums">
              {{ wavelength >= 10 ? wavelength.toFixed(1) : wavelength.toFixed(2) }}
            </span>
            <span class="ml-1 text-sm text-gray-500">米</span>
            <KTag v-if="matchedBand" size="sm" class="ml-2">{{ matchedBand }} 波段</KTag>
            <div class="mt-0.5 text-xs text-gray-400">
              1/4 波长天线约 {{ (wavelength / 4).toFixed(2) }} m
            </div>
          </template>
          <span v-else class="text-sm text-gray-400">输入频率换算波长</span>
        </div>
      </section>

      <!-- RST 速查 -->
      <section class="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
        <div class="mb-3 flex items-center gap-2 text-sm font-semibold">
          <span class="inline-flex rounded-lg bg-rose-50 p-1.5"><Waves class="size-4 text-rose-600" /></span>
          RST 信号报告速查
        </div>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div class="mb-1.5 text-xs font-medium text-gray-400">R · 可辨度（1–5）</div>
            <ul class="space-y-1 text-gray-600">
              <li v-for="r in RST_R" :key="r" class="text-xs">{{ r }}</li>
            </ul>
          </div>
          <div>
            <div class="mb-1.5 text-xs font-medium text-gray-400">S · 信号强度（1–9）</div>
            <ul class="space-y-1 text-gray-600">
              <li v-for="s in RST_S" :key="s" class="text-xs">{{ s }}</li>
            </ul>
          </div>
        </div>
        <p class="mt-3 border-t border-gray-50 pt-2 text-xs text-gray-400">
          语音模式报 RS 两位（如 59）；CW / 数字模式加 T 音质位（如 599）。
        </p>
      </section>
    </div>
  </div>
</template>
