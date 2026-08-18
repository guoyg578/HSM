<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { KButton, KDialog, KInput, KInputNumber, KMessage, KSelect } from '@guoyg578/k-ui'
import { Zap } from '@lucide/vue'
import { api } from '../api'
import { loadLastStation, saveLastStation } from '../prefs'
import { appSettings, modeOptions } from '../settings'
import { stations } from '../store'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
}>()

const stationId = ref<number | null>(null)
const call = ref('')
const freq = ref<number | null>(null)
const mode = ref(appSettings.value.default_mode)
const rstSent = ref(appSettings.value.default_rst)
const rstRcvd = ref(appSettings.value.default_rst)
const saving = ref(false)
const savedCount = ref(0)

const callBox = ref<HTMLElement | null>(null)
function focusCall() {
  nextTick(() => callBox.value?.querySelector('input')?.focus())
}

watch(
  () => props.open,
  (open) => {
    if (!open) return
    // 每次打开重置为默认值；频率/模式保留上次会话的选择（连续通联场景）
    call.value = ''
    mode.value = mode.value || appSettings.value.default_mode
    rstSent.value = appSettings.value.default_rst
    rstRcvd.value = appSettings.value.default_rst
    savedCount.value = 0
    const last = loadLastStation()
    if (last && stations.value.some((s) => s.id === last)) stationId.value = last
    else if (stations.value.length) stationId.value = stations.value[0]!.id
    focusCall()
  },
)

watch(stationId, (id) => {
  if (id) saveLastStation(id)
})

async function save() {
  if (!stationId.value) {
    KMessage.warning('请先选择电台')
    return
  }
  if (!call.value.trim()) {
    KMessage.warning('请输入对方呼号')
    return
  }
  saving.value = true
  try {
    // 时间/设备/功率/天线由服务端自动补充
    await api.createQso({
      station_id: stationId.value,
      call: call.value.trim().toUpperCase(),
      freq_mhz: freq.value,
      mode: mode.value,
      rst_sent: rstSent.value,
      rst_rcvd: rstRcvd.value,
    })
    savedCount.value++
    KMessage.success(`已记录 ${call.value.trim().toUpperCase()}`)
    // 保留频率/模式（连续通联场景），只清呼号和 RST
    call.value = ''
    rstSent.value = appSettings.value.default_rst
    rstRcvd.value = appSettings.value.default_rst
    emit('saved')
    focusCall()
  } catch (e) {
    KMessage.error(`保存失败: ${(e as Error).message}`)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <KDialog
    :open="open"
    size="sm"
    @update:open="emit('update:open', $event)"
  >
    <template #title>
      <div class="flex items-center gap-3">
        <div class="flex size-9 items-center justify-center rounded-xl bg-amber-100">
          <Zap class="size-5 text-amber-500" />
        </div>
        <div>
          <div class="text-base font-bold leading-tight">快速记录</div>
          <div class="mt-0.5 text-xs text-gray-400">时间 · 设备 · 功率 · 天线自动补充</div>
        </div>
      </div>
    </template>

    <div class="space-y-4">
      <label class="block">
        <span class="mb-1.5 block text-xs font-medium text-gray-500">使用电台</span>
        <KSelect
          v-model="stationId"
          size="sm"
          :options="stations.map((s) => ({ value: s.id, label: `${s.name}（${s.callsign}）` }))"
        />
      </label>

      <label class="block">
        <span class="mb-1.5 block text-xs font-medium text-gray-500">对方呼号</span>
        <div ref="callBox" class="quick-call">
          <KInput v-model="call" placeholder="BD5XXX" @keyup.enter="save" />
        </div>
      </label>

      <div class="grid grid-cols-2 gap-x-3 gap-y-4">
        <label class="block">
          <span class="mb-1.5 block text-xs font-medium text-gray-500">频率（MHz）</span>
          <KInputNumber
            v-model="freq"
            placeholder="438.500"
            :min="0"
            :step="0.001"
            :show-button="false"
          />
        </label>
        <label class="block">
          <span class="mb-1.5 block text-xs font-medium text-gray-500">模式</span>
          <KSelect v-model="mode" :options="modeOptions" />
        </label>
        <label class="block">
          <span class="mb-1.5 block text-xs font-medium text-gray-500">RST 发送</span>
          <KInput v-model="rstSent" placeholder="59" />
        </label>
        <label class="block">
          <span class="mb-1.5 block text-xs font-medium text-gray-500">RST 收到</span>
          <KInput v-model="rstRcvd" placeholder="59" />
        </label>
      </div>

      <div class="pt-1">
        <KButton type="primary" block :loading="saving" @click="save">
          <Zap class="mr-1.5 size-4" /> 保存
        </KButton>
        <div class="mt-2.5 flex items-center justify-center gap-2 text-xs text-gray-400">
          <span>呼号框内按回车即可连续记录</span>
          <span
            v-if="savedCount"
            class="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-600"
          >
            已记录 {{ savedCount }} 条
          </span>
        </div>
      </div>
    </div>
  </KDialog>
</template>

<style scoped>
/* 呼号是快速记录的主角：大号、居中、等宽感 */
.quick-call :deep(input) {
  text-align: center;
  text-transform: uppercase;
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: 0.08em;
  font-variant-numeric: tabular-nums;
}
.quick-call :deep(input::placeholder) {
  font-weight: 400;
  font-size: 0.875rem;
  letter-spacing: normal;
  text-transform: none;
}
</style>
