<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  KButton,
  KDatePicker,
  KDrawer,
  KInput,
  KInputNumber,
  KMessage,
  KSelect,
  KTextarea,
  KUpload,
} from '@guoyg578/k-ui'
import type { UploadCustomRequestOptions } from '@guoyg578/k-ui'
import type { QSO, QSODefaults } from '../types'
import { api } from '../api'
import { appSettings, modeOptions } from '../settings'
import { gridDistanceKm } from '../utils'

const props = defineProps<{
  open: boolean
  stationId: number
  qso: QSO | null
}>()

const emit = defineEmits<{
  'update:open': [v: boolean]
  saved: []
}>()

const defaults = ref<QSODefaults | null>(null)
const saving = ref(false)

const model = ref({
  datetime: '',
  call: '',
  freq_mhz: null as number | null,
  mode: 'FM',
  rst_sent: '59',
  rst_rcvd: '59',
  qth: '',
  grid: '',
  distance_km: null as number | null,
  their_equipment: '',
  their_antenna: '',
  their_power: '',
  remark: '',
  qsl_path: '',
  audio_path: '',
  my_power: null as string | null,
})

// 表单内显示/输入北京时间（浏览器本地时区），存库统一 UTC。
// KDatePicker(enableTime) 的模型格式为 "yyyy-MM-dd HH:mm"
function toLocalInput(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

function utcIsoToLocal(iso: string): string {
  return toLocalInput(new Date(iso.endsWith('Z') ? iso : `${iso}Z`))
}

function localToUtcIso(value: string): string {
  return new Date(value.replace(' ', 'T')).toISOString().slice(0, 19)
}

// 打开表单时的原值；保存时据此判断用户是否改过网格/距离
let originalDistance: number | null = null
let originalGrid = ''

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    defaults.value = null
    try {
      defaults.value = await api.qsoDefaults(props.stationId)
    } catch (e) {
      KMessage.error(`加载本台信息失败: ${(e as Error).message}`)
    }
    const q = props.qso
    model.value = {
      datetime: q ? utcIsoToLocal(q.datetime_utc) : toLocalInput(new Date()),
      call: q?.call ?? '',
      freq_mhz: q?.freq_mhz ?? null,
      mode: q?.mode || appSettings.value.default_mode,
      rst_sent: q?.rst_sent || appSettings.value.default_rst,
      rst_rcvd: q?.rst_rcvd || appSettings.value.default_rst,
      qth: q?.qth ?? '',
      grid: q?.grid ?? '',
      distance_km: q?.distance_km ?? null,
      their_equipment: q?.their_equipment ?? '',
      their_antenna: q?.their_antenna ?? '',
      their_power: q?.their_power ?? '',
      remark: q?.remark ?? '',
      qsl_path: q?.qsl_path ?? '',
      audio_path: q?.audio_path ?? '',
      my_power: q ? q.my_power || null : null,
    }
    originalDistance = model.value.distance_km
    originalGrid = model.value.grid
    qthGuess.value = null
    refreshQthGuess()
  },
)

const myInfo = computed(() => {
  if (props.qso) {
    const q = props.qso
    return {
      my_callsign: q.my_callsign,
      my_qth: q.my_qth,
      my_grid: q.my_grid,
      my_equipment: q.my_equipment,
      my_antenna: q.my_antenna,
      my_power: q.my_power,
    }
  }
  return defaults.value
})

const powerOptions = computed(() =>
  (defaults.value?.power_profiles ?? []).map((p) => ({
    value: `${p.power_watts}W`,
    label: `${p.mode_name} ${p.power_watts}W`,
  })),
)

// 按 QTH 地名估算的网格（后端离线查表），仅在网格留空时作为兜底
const qthGuess = ref<{ grid: string; matched: string } | null>(null)
let qthTimer: ReturnType<typeof setTimeout> | undefined

function refreshQthGuess() {
  clearTimeout(qthTimer)
  const qth = model.value.qth.trim()
  if (!qth) {
    qthGuess.value = null
    return
  }
  qthTimer = setTimeout(async () => {
    try {
      const r = await api.qthGrid(qth)
      qthGuess.value = r.found ? { grid: r.grid, matched: r.matched } : null
    } catch {
      qthGuess.value = null
    }
  }, 300)
}

watch(() => model.value.qth, refreshQthGuess)

// 网格留空时后端会按 QTH 估算，预览沿用同一兜底值才能与保存结果一致
const effectiveGrid = computed(() => model.value.grid.trim() || qthGuess.value?.grid || '')

const previewDistance = computed(() => {
  const myGrid = props.qso ? props.qso.my_grid : defaults.value?.my_grid
  if (!myGrid || !effectiveGrid.value) return null
  return gridDistanceKm(myGrid, effectiveGrid.value)
})

// 距离框将被自动计算覆盖的两种情况：留空；或编辑时改了网格但没动距离
const willAutoCalc = computed(() => {
  if (previewDistance.value === null) return false
  if (model.value.distance_km === null) return true
  return (
    !!props.qso &&
    model.value.grid.trim() !== originalGrid &&
    model.value.distance_km === originalDistance
  )
})

function uploadFactory(kind: 'qsl' | 'audio') {
  return (options: UploadCustomRequestOptions) => {
    const file = options.file.file
    if (!file) {
      options.onError('文件为空')
      return
    }
    api
      .upload(kind, file)
      .then((result) => {
        model.value[kind === 'qsl' ? 'qsl_path' : 'audio_path'] = result.path
        options.onFinish()
        KMessage.success('上传成功')
      })
      .catch((e) => {
        options.onError(e)
        KMessage.error(`上传失败: ${(e as Error).message}`)
      })
  }
}

async function save() {
  if (!model.value.call.trim()) {
    KMessage.warning('对方呼号为必填项')
    return
  }
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      datetime_utc: model.value.datetime ? localToUtcIso(model.value.datetime) : null,
      call: model.value.call.trim().toUpperCase(),
      freq_mhz: model.value.freq_mhz,
      mode: model.value.mode,
      rst_sent: model.value.rst_sent,
      rst_rcvd: model.value.rst_rcvd,
      qth: model.value.qth,
      grid: model.value.grid.trim(),
      their_equipment: model.value.their_equipment,
      their_antenna: model.value.their_antenna,
      their_power: model.value.their_power,
      remark: model.value.remark,
      qsl_path: model.value.qsl_path,
      audio_path: model.value.audio_path,
    }
    if (model.value.my_power) payload.my_power = model.value.my_power
    // 编辑时若改了网格但没动距离，则不提交距离，由后端按新网格重算；其余情况原样提交
    const gridChanged = props.qso && model.value.grid.trim() !== originalGrid
    if (!(gridChanged && model.value.distance_km === originalDistance)) {
      payload.distance_km = model.value.distance_km
    }
    if (props.qso) {
      await api.updateQso(props.qso.id, payload)
      KMessage.success('QSO 已更新')
    } else {
      await api.createQso({ ...payload, station_id: props.stationId })
      KMessage.success('QSO 已保存')
    }
    emit('update:open', false)
    emit('saved')
  } catch (e) {
    KMessage.error(`保存失败: ${(e as Error).message}`)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <KDrawer
    :open="open"
    :title="qso ? '编辑 QSO' : '新建 QSO'"
    size="lg"
    width="min(640px, 100vw)"
    @update:open="emit('update:open', $event)"
  >
    <div class="space-y-4 pb-4">
      <!-- 本台信息（自动继承） -->
      <div class="rounded-lg bg-blue-50 p-3 text-sm">
        <div class="mb-1 text-xs font-semibold text-blue-500">本台信息（自动继承）</div>
        <div v-if="myInfo" class="grid grid-cols-2 gap-x-4 gap-y-0.5 text-gray-700">
          <div>呼号：{{ myInfo.my_callsign || '—' }}</div>
          <div>QTH：{{ myInfo.my_qth || '—' }}</div>
          <div>设备：{{ myInfo.my_equipment || '—' }}</div>
          <div>天线：{{ myInfo.my_antenna || '—' }}</div>
          <div>Grid：{{ myInfo.my_grid || '—' }}</div>
          <div>功率：{{ model.my_power || myInfo.my_power || '—' }}</div>
        </div>
        <div v-if="!qso && powerOptions.length > 1" class="mt-2">
          <KSelect
            v-model="model.my_power"
            :options="powerOptions"
            placeholder="选择本次通联使用的功率"
            size="sm"
            clearable
          />
        </div>
      </div>

      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">时间（北京时间，存储自动转 UTC）</span>
          <KDatePicker v-model="model.datetime" enable-time placeholder="选择日期时间" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">对方呼号 *</span>
          <KInput v-model="model.call" placeholder="如：BD5XXX" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">频率（MHz）</span>
          <KInputNumber
            v-model="model.freq_mhz"
            placeholder="如：438.500"
            :min="0"
            :step="0.001"
            :show-button="false"
          />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">模式</span>
          <KSelect v-model="model.mode" :options="modeOptions" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">对方设备</span>
          <KInput v-model="model.their_equipment" placeholder="如：ICOM IC-7300" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">对方天馈</span>
          <KInput v-model="model.their_antenna" placeholder="如：GP 天线" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">对方功率</span>
          <KInput v-model="model.their_power" placeholder="如：100W" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">对方 QTH</span>
          <KInput v-model="model.qth" placeholder="如：上海" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">RST 发送（我给对方）</span>
          <KInput v-model="model.rst_sent" placeholder="59" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">RST 收到（对方给我）</span>
          <KInput v-model="model.rst_rcvd" placeholder="59" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">
            对方 Grid
            <template v-if="!model.grid.trim() && qthGuess">
              —— 将按「{{ qthGuess.matched }}」自动填 {{ qthGuess.grid }}
            </template>
          </span>
          <KInput v-model="model.grid" placeholder="留空则按 QTH 估算" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">
            距离（公里）
            <template v-if="willAutoCalc">
              —— 将按网格自动计算：约 {{ previewDistance }} km
            </template>
          </span>
          <KInputNumber
            v-model="model.distance_km"
            placeholder="留空则按双方 Grid 自动计算"
            :min="0"
            :show-button="false"
          />
        </label>
      </div>

      <label class="block">
        <span class="mb-1 block text-xs text-gray-500">备注</span>
        <KTextarea v-model="model.remark" :rows="2" placeholder="通联内容、天气、信号情况等" />
      </label>

      <!-- QSL 图片 / 录音 -->
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <span class="mb-1 block text-xs text-gray-500">QSL 图片</span>
          <KUpload
            accept="image/*"
            :show-list="false"
            button-text="上传 QSL 图片"
            :custom-request="uploadFactory('qsl')"
          />
          <div v-if="model.qsl_path" class="mt-2 flex items-center gap-2">
            <img :src="`/files/${model.qsl_path}`" class="h-16 rounded border border-gray-200 object-cover" alt="QSL" />
            <KButton size="sm" text @click="model.qsl_path = ''">移除</KButton>
          </div>
        </div>
        <div>
          <span class="mb-1 block text-xs text-gray-500">通联录音</span>
          <KUpload
            accept="audio/*,.mp3,.wav,.m4a,.ogg"
            :show-list="false"
            button-text="上传录音"
            :custom-request="uploadFactory('audio')"
          />
          <div v-if="model.audio_path" class="mt-2 flex items-center gap-2">
            <audio :src="`/files/${model.audio_path}`" controls class="h-8 w-full" />
            <KButton size="sm" text @click="model.audio_path = ''">移除</KButton>
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-2 border-t border-gray-100 pt-4">
        <KButton @click="emit('update:open', false)">取消</KButton>
        <KButton type="primary" :loading="saving" @click="save">保存</KButton>
      </div>
    </div>
  </KDrawer>
</template>
