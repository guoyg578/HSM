<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  KButton,
  KCheckbox,
  KCheckboxGroup,
  KDataTable,
  KDialog,
  KDrawer,
  KEmpty,
  KImage,
  KMessage,
  KPagination,
  KPopconfirm,
  KPopover,
  KRadio,
  KRadioGroup,
  KSearchBar,
  KTag,
} from '@guoyg578/k-ui'
import type { Column } from '@guoyg578/k-ui'

type SortState = { columnKey: string; order: 'ascend' | 'descend' }
import { FileDown, List, Map as MapIcon, PanelRight, Pencil, Plus, Settings, Table as TableIcon, Trash2 } from '@lucide/vue'
import type { QSO, StationDetail } from '../types'
import { api } from '../api'
import { COLUMN_DEFS, loadViewMode, saveLastStation, saveViewMode, type ViewMode } from '../prefs'
import { appSettings, loadAppSettings } from '../settings'
import { fmtDate, fmtFreq, fmtTime } from '../utils'
import { refreshStations } from '../store'
import IconButton from '../components/IconButton.vue'
import QsoForm from '../components/QsoForm.vue'
import AdifDialog from '../components/AdifDialog.vue'
import QsoMap from '../components/QsoMap.vue'
import ConfigPanel from '../components/ConfigPanel.vue'
import StationDialog from '../components/StationDialog.vue'

const route = useRoute()
const router = useRouter()

// 电台 id 来自路由；App 层用 route.path 作 key，切换电台时本组件整体重建
const stationId = Number(route.params.id)
const station = ref<StationDetail | null>(null)
const editOpen = ref(false)
const configOpen = ref(false)

async function loadStation() {
  try {
    station.value = await api.getStation(stationId)
    saveLastStation(stationId)
  } catch (e) {
    KMessage.error(`加载电台失败: ${(e as Error).message}`)
    router.replace('/dashboard')
  }
}

async function onStationSaved() {
  await Promise.all([loadStation(), refreshStations()])
}

// ---- 状态 ----
const viewMode = ref<ViewMode>(loadViewMode())
// 显示列 = 后台配置的 qso_columns：这里改动直接写回服务端，与后台管理页同步
const visibleCols = ref<string[]>([...appSettings.value.qso_columns])
loadAppSettings().then(() => {
  visibleCols.value = [...appSettings.value.qso_columns]
})

async function onColsChange(v: (string | number)[]) {
  const cols = v.map(String)
  if (!cols.length) {
    KMessage.warning('至少保留一列')
    visibleCols.value = [...appSettings.value.qso_columns]
    return
  }
  try {
    appSettings.value = await api.updateSettings({ qso_columns: cols })
  } catch (e) {
    KMessage.error(`保存显示列失败: ${(e as Error).message}`)
    visibleCols.value = [...appSettings.value.qso_columns]
  }
}
const search = ref('')
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const qsos = ref<QSO[]>([])
const loading = ref(false)
// 初始为 null：后端默认即按日期降序，不在表头显示排序箭头
const sortState = ref<SortState | null>(null)

const formOpen = ref(false)
const editingQso = ref<QSO | null>(null)
const adifOpen = ref(false)
const mapQso = ref<QSO | null>(null)

watch(viewMode, (m) => {
  saveViewMode(m)
  fetchQsos()
})
// ---- 数据加载 ----
let searchTimer: ReturnType<typeof setTimeout> | undefined

async function fetchQsos() {
  loading.value = true
  try {
    // 时间线模式固定按时间倒序（按日期分组展示的前提）
    const timeline = viewMode.value === 'timeline'
    const result = await api.listQsos({
      station_id: stationId,
      q: search.value || undefined,
      sort_by: timeline
        ? 'date'
        : ((sortState.value?.columnKey as 'date' | 'freq' | 'distance') ?? 'date'),
      order: timeline ? 'desc' : sortState.value?.order === 'ascend' ? 'asc' : 'desc',
      page: page.value,
      page_size: pageSize.value,
    })
    qsos.value = result.items
    total.value = result.total
  } catch (e) {
    KMessage.error(`加载日志失败: ${(e as Error).message}`)
  } finally {
    loading.value = false
  }
}

watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    fetchQsos()
  }, 300)
})
watch([page, sortState], fetchQsos)
onMounted(() => {
  loadStation()
  fetchQsos()
})

// ---- 时间线卡片左侧色条渐变（无 QSL 图片时按 id 轮换） ----
const GRADIENTS = [
  'from-blue-500 to-indigo-600',
  'from-emerald-500 to-sky-500',
  'from-amber-500 to-red-500',
  'from-violet-500 to-pink-500',
]
function coverGradient(q: QSO): string {
  return GRADIENTS[q.id % GRADIENTS.length]!
}

// ---- 表格列（列定义见 prefs.ts，与后台「默认列」配置共用） ----
const columns = computed<Column<QSO>[]>(() => {
  const cols: Column<QSO>[] = COLUMN_DEFS.filter((c) => visibleCols.value.includes(c.key)).map(
    (c) => ({
      key: c.key,
      label: c.label,
      sorter: ['date', 'freq', 'distance'].includes(c.key),
      ellipsis: c.key === 'remark' || c.key === 'qth',
      maxWidth: c.key === 'remark' ? 200 : undefined,
    }),
  )
  cols.push({ key: 'actions', label: '操作', width: 90, align: 'right' })
  return cols
})

// ---- 操作 ----
function newQso() {
  editingQso.value = null
  formOpen.value = true
}

function editQso(q: QSO) {
  editingQso.value = q
  formOpen.value = true
}

async function deleteQso(q: QSO) {
  try {
    await api.deleteQso(q.id)
    KMessage.success('已删除')
    await fetchQsos()
  } catch (e) {
    KMessage.error(`删除失败: ${(e as Error).message}`)
  }
}

async function deleteStation() {
  try {
    await api.deleteStation(stationId)
    KMessage.success('电台已删除')
    await refreshStations()
    router.replace('/dashboard')
  } catch (e) {
    KMessage.error(`删除失败: ${(e as Error).message}`)
  }
}
</script>

<template>
  <div v-if="!station" class="flex h-full items-center justify-center text-sm text-gray-400">
    加载中…
  </div>
  <div v-else class="flex h-full">
  <div class="flex min-w-0 flex-1 flex-col">
    <!-- 顶部：电台信息 + 操作 -->
    <div class="border-b border-gray-200 bg-white px-4 py-4 sm:px-6">
      <div class="flex flex-wrap items-center justify-between gap-y-2">
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-lg font-bold">{{ station.name }}</h1>
            <KTag size="sm" type="info">{{ station.callsign }}</KTag>
            <div
              class="ml-1 flex items-center divide-x divide-gray-200 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-xs"
            >
              <button
                type="button"
                title="编辑电台"
                class="inline-flex size-7 cursor-pointer items-center justify-center text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-900"
                @click="editOpen = true"
              >
                <Pencil class="size-3.5" />
              </button>
              <KPopconfirm
                title="删除电台"
                message="将同时删除该电台的全部 QSO 记录，确定？"
                confirm-type="danger"
                @confirm="deleteStation"
              >
                <button
                  type="button"
                  title="删除电台"
                  class="inline-flex size-7 cursor-pointer items-center justify-center text-gray-500 transition-colors hover:bg-red-50 hover:text-red-500"
                >
                  <Trash2 class="size-3.5" />
                </button>
              </KPopconfirm>
            </div>
          </div>
          <div class="mt-0.5 text-xs text-gray-400">
            共 {{ total }} 条通联记录<span v-if="station.qth"> · {{ station.qth }}</span>
          </div>
        </div>
        <KButton type="primary" @click="newQso">
          <Plus class="mr-1 size-4" /> 新建 QSO
        </KButton>
      </div>

      <!-- 工具栏：搜索 + 模式切换 + 列设置 + 次要操作 -->
      <div class="mt-3 flex flex-wrap items-center gap-2 sm:gap-3">
        <div class="w-full sm:w-72">
          <KSearchBar v-model="search" size="sm" placeholder="搜索呼号 / QTH / 备注" />
        </div>
        <KRadioGroup v-model="viewMode" button size="sm">
          <KRadio value="table">
            <span class="inline-flex items-center gap-1"><TableIcon class="size-3.5" /> 表格模式</span>
          </KRadio>
          <KRadio value="timeline">
            <span class="inline-flex items-center gap-1"><List class="size-3.5" /> 时间线模式</span>
          </KRadio>
        </KRadioGroup>
        <KPopover v-if="viewMode === 'table'" side="bottom" align="end">
          <IconButton title="自定义列">
            <Settings class="size-4" />
          </IconButton>
          <template #content>
            <div class="p-2">
              <div class="mb-2 text-xs font-semibold text-gray-400">显示列</div>
              <KCheckboxGroup
                v-model="visibleCols"
                direction="vertical"
                size="sm"
                @update:model-value="onColsChange"
              >
                <KCheckbox v-for="c in COLUMN_DEFS" :key="c.key" :value="c.key" :label="c.label" />
              </KCheckboxGroup>
            </div>
          </template>
        </KPopover>

        <div class="ml-auto flex items-center gap-2">
          <div class="xl:hidden">
            <KButton size="sm" title="电台配置" @click="configOpen = true">
              <PanelRight class="size-4" />
            </KButton>
          </div>
          <KButton size="sm" @click="adifOpen = true">
            <FileDown class="mr-1 size-3.5" /> ADIF
          </KButton>
        </div>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="flex-1 overflow-y-auto p-4 sm:p-6">
      <KEmpty
        v-if="!loading && !qsos.length"
        title="暂无通联记录"
        description="点击右上角「新建 QSO」记录第一次通联"
      />

      <!-- 表格模式 -->
      <template v-else-if="viewMode === 'table'">
        <div class="overflow-x-auto rounded-lg">
        <KDataTable
          :columns="columns"
          :rows="qsos"
          :loading="loading"
          remote
          striped
          hoverable
          size="sm"
          row-key="id"
          :sort-state="sortState"
          :pagination="false"
          @update:sort-state="(s: SortState | null) => (sortState = s)"
        >
          <template #cell-date="{ row }">{{ fmtDate(row.datetime_utc) }}</template>
          <template #cell-time="{ row }">{{ fmtTime(row.datetime_utc) }}</template>
          <template #cell-call="{ row }">
            <span class="font-semibold">{{ row.call }}</span>
          </template>
          <template #cell-freq="{ row }">{{ fmtFreq(row.freq_mhz) }}</template>
          <template #cell-band="{ row }">
            <KTag v-if="row.band" size="sm">{{ row.band }}</KTag>
          </template>
          <template #cell-mode="{ row }">{{ row.mode }}</template>
          <template #cell-rst="{ row }">
            <span class="tabular-nums">{{ row.rst_sent || '—' }} / {{ row.rst_rcvd || '—' }}</span>
          </template>
          <template #cell-qth="{ row }">{{ row.qth }}</template>
          <template #cell-grid="{ row }">{{ row.grid }}</template>
          <template #cell-distance="{ row }">{{ row.distance_km ?? '' }}</template>
          <template #cell-equipment="{ row }">{{ row.my_equipment }}</template>
          <template #cell-antenna="{ row }">{{ row.my_antenna }}</template>
          <template #cell-power="{ row }">{{ row.my_power }}</template>
          <template #cell-their_equipment="{ row }">{{ row.their_equipment }}</template>
          <template #cell-their_antenna="{ row }">{{ row.their_antenna }}</template>
          <template #cell-their_power="{ row }">{{ row.their_power }}</template>
          <template #cell-remark="{ row }">{{ row.remark }}</template>
          <template #cell-actions="{ row }">
            <div class="flex justify-end gap-1">
              <IconButton title="编辑" @click="editQso(row)">
                <Pencil class="size-3.5" />
              </IconButton>
              <KPopconfirm message="确定删除该 QSO？" confirm-type="danger" @confirm="deleteQso(row)">
                <IconButton title="删除" danger>
                  <Trash2 class="size-3.5" />
                </IconButton>
              </KPopconfirm>
            </div>
          </template>
        </KDataTable>
        </div>
        <div class="mt-4 flex justify-end">
          <KPagination v-model:page="page" :page-size="pageSize" :total="total" show-summary />
        </div>
      </template>

      <!-- 时间线模式：卡片网格（方案C） -->
      <template v-else>
        <div class="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          <div
            v-for="q in qsos"
            :key="q.id"
            class="group overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-lg"
          >
            <!-- 有 QSL 照片时用照片头图，文字压在图上 -->
            <div v-if="q.qsl_path" class="relative h-24">
              <KImage
                :src="`/files/${q.qsl_path}`"
                alt="QSL"
                width="100%"
                height="96px"
                fit="cover"
                preview
                class="absolute inset-0"
              />
              <!-- 暗色压边保证文字可读 -->
              <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />
              <div class="pointer-events-none absolute bottom-2 left-4 text-lg font-extrabold tracking-wide text-white drop-shadow">
                {{ q.call }}
              </div>
              <div class="pointer-events-none absolute right-3 top-2 text-[11px] font-medium text-white/85">
                {{ fmtDate(q.datetime_utc) }} {{ fmtTime(q.datetime_utc) }}
              </div>
            </div>
            <!-- 无照片时用轻量文字头：细色条保留识别度，避免大色块头重脚轻 -->
            <div v-else class="flex items-center justify-between gap-2 px-4 pt-3.5">
              <div class="flex min-w-0 items-center gap-2.5">
                <span class="h-5 w-1.5 shrink-0 rounded-full bg-gradient-to-b" :class="coverGradient(q)" />
                <span class="truncate text-lg font-extrabold tracking-wide text-gray-800">{{ q.call }}</span>
              </div>
              <span class="shrink-0 text-[11px] font-medium text-gray-400">
                {{ fmtDate(q.datetime_utc) }} {{ fmtTime(q.datetime_utc) }}
              </span>
            </div>

            <div class="p-4" :class="q.qsl_path ? '' : 'pt-3'">
              <div class="mb-3 flex flex-wrap items-center gap-1.5">
                <KTag v-if="q.band" size="sm">{{ q.band }}</KTag>
                <KTag v-if="q.mode" size="sm" type="info">{{ q.mode }}</KTag>
                <KTag v-if="q.qth" size="sm">{{ q.qth }}</KTag>
                <span v-if="q.grid" class="text-[11px] text-gray-400">{{ q.grid }}</span>
              </div>

              <!-- 关键数据三格 -->
              <div class="flex overflow-hidden rounded-xl border border-gray-100">
                <div class="flex-1 bg-gray-50 px-1 py-2 text-center">
                  <div class="text-[13px] font-bold tabular-nums text-gray-700">
                    {{ q.freq_mhz ? fmtFreq(q.freq_mhz) : '—' }}
                  </div>
                  <div class="mt-0.5 text-[10px] text-gray-400">MHz</div>
                </div>
                <div class="flex-1 border-l border-gray-100 bg-gray-50 px-1 py-2 text-center">
                  <div class="text-[13px] font-bold tabular-nums text-gray-700">
                    {{ q.rst_sent || '—' }} / {{ q.rst_rcvd || '—' }}
                  </div>
                  <div class="mt-0.5 text-[10px] text-gray-400">RST</div>
                </div>
                <div class="flex-1 border-l border-gray-100 bg-gray-50 px-1 py-2 text-center">
                  <div class="text-[13px] font-bold tabular-nums text-gray-700">
                    {{ q.distance_km ? `${q.distance_km.toLocaleString()} km` : '—' }}
                  </div>
                  <div class="mt-0.5 text-[10px] text-gray-400">距离</div>
                </div>
              </div>

              <div
                v-if="q.their_equipment || q.their_antenna || q.their_power"
                class="mt-2 truncate text-xs text-gray-400"
                :title="[q.their_equipment, q.their_antenna, q.their_power].filter(Boolean).join(' · ')"
              >
                对方：{{ [q.their_equipment, q.their_antenna, q.their_power].filter(Boolean).join(' · ') }}
              </div>

              <audio
                v-if="q.audio_path"
                :src="`/files/${q.audio_path}`"
                controls
                class="mt-3 h-8 w-full"
              />

              <div class="mt-3 flex items-center justify-between gap-2">
                <div class="min-w-0 flex-1 truncate text-xs text-gray-400" :title="q.remark">
                  {{ q.remark || [q.my_equipment, q.my_power].filter(Boolean).join(' · ') }}
                </div>
                <div class="flex shrink-0 gap-0.5">
                  <IconButton v-if="q.grid || q.my_grid" title="显示地图" @click="mapQso = q">
                    <MapIcon class="size-3.5" />
                  </IconButton>
                  <IconButton title="编辑" @click="editQso(q)">
                    <Pencil class="size-3.5" />
                  </IconButton>
                  <KPopconfirm message="确定删除该 QSO？" confirm-type="danger" @confirm="deleteQso(q)">
                    <IconButton title="删除" danger>
                      <Trash2 class="size-3.5" />
                    </IconButton>
                  </KPopconfirm>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-4 flex justify-end">
          <KPagination v-model:page="page" :page-size="pageSize" :total="total" show-summary />
        </div>
      </template>
    </div>
    </div>

    <!-- 右侧：当前电台配置（大屏常驻，小屏抽屉） -->
    <aside class="hidden w-72 shrink-0 overflow-y-auto border-l border-gray-200 bg-white xl:block">
      <ConfigPanel :station="station" @changed="loadStation" />
    </aside>
    <KDrawer
      :open="configOpen"
      title="电台配置"
      placement="right"
      width="min(320px, 90vw)"
      @update:open="(v: boolean) => (configOpen = v)"
    >
      <ConfigPanel :station="station" @changed="loadStation" />
    </KDrawer>

    <!-- 编辑电台对话框 -->
    <StationDialog v-model:open="editOpen" :station="station" @saved="onStationSaved" />

    <!-- 通联地图对话框 -->
    <KDialog
      :open="mapQso !== null"
      :title="mapQso ? `${mapQso.my_callsign || '本台'} ⇋ ${mapQso.call}` : ''"
      :subtitle="mapQso?.distance_km ? `距离约 ${mapQso.distance_km} km` : ''"
      size="xl"
      width="min(1000px, 96vw)"
      @update:open="(v: boolean) => { if (!v) mapQso = null }"
    >
      <div v-if="mapQso" class="h-[65vh]">
        <QsoMap
          :my-grid="mapQso.my_grid"
          :grid="mapQso.grid"
          :my-label="`${mapQso.my_callsign}（${mapQso.my_grid || '?'}）`"
          :label="`${mapQso.call}（${mapQso.grid || '?'}）`"
        />
      </div>
    </KDialog>

    <QsoForm v-model:open="formOpen" :station-id="station.id" :qso="editingQso" @saved="fetchQsos" />
    <AdifDialog
      v-model:open="adifOpen"
      :station-id="station.id"
      :station-name="station.name"
      @imported="fetchQsos"
    />
  </div>
</template>
