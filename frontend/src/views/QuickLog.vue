<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { KButton, KEmpty, KInput, KInputNumber, KMessage, KSelect } from '@guoyg578/k-ui'
import { Zap } from '@lucide/vue'
import { api } from '../api'
import { loadLastStation, saveLastStation } from '../prefs'
import { appSettings, loadAppSettings, modeOptions } from '../settings'
import { stations } from '../store'

const stationId = ref<number | null>(null)
const call = ref('')
const freq = ref<number | null>(null)
const mode = ref(appSettings.value.default_mode)
const rstSent = ref(appSettings.value.default_rst)
const rstRcvd = ref(appSettings.value.default_rst)

// 配置异步加载：就绪后套用默认模式 / RST（用户此时尚未输入）
loadAppSettings().then(() => {
  mode.value = appSettings.value.default_mode
  rstSent.value = appSettings.value.default_rst
  rstRcvd.value = appSettings.value.default_rst
})
const saving = ref(false)
const savedCount = ref(0)

// 电台列表由 store 异步加载，就绪后再选默认电台
function pickDefaultStation() {
  if (stationId.value) return
  const last = loadLastStation()
  if (last && stations.value.some((s) => s.id === last)) stationId.value = last
  else if (stations.value.length) stationId.value = stations.value[0]!.id
}
onMounted(pickDefaultStation)
watch(() => stations.value.length, pickDefaultStation)

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
  } catch (e) {
    KMessage.error(`保存失败: ${(e as Error).message}`)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
  <div class="mx-auto max-w-md">
    <div class="mb-1 flex items-center gap-2">
      <Zap class="size-5 text-amber-500" />
      <h1 class="text-xl font-bold">快速记录</h1>
    </div>
    <p class="mb-5 text-sm text-gray-400">
      适合开车 / 手持机 / 比赛场景。时间、设备、功率、天线自动补充。
    </p>

    <KEmpty v-if="!stations.length" title="还没有电台" description="请先在左侧新建电台" />

    <div v-else class="space-y-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <label class="block">
        <span class="mb-1 block text-xs text-gray-500">使用电台</span>
        <KSelect
          v-model="stationId"
          :options="stations.map((s) => ({ value: s.id, label: `${s.name}（${s.callsign}）` }))"
        />
      </label>
      <label class="block">
        <span class="mb-1 block text-xs text-gray-500">对方呼号 *</span>
        <KInput v-model="call" placeholder="BD5XXX" size="lg" @keyup.enter="save" />
      </label>
      <div class="grid grid-cols-2 gap-3">
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">频率（MHz）</span>
          <KInputNumber v-model="freq" placeholder="438.500" :min="0" :step="0.001" :show-button="false" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">模式</span>
          <KSelect v-model="mode" :options="modeOptions" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">RST 发送</span>
          <KInput v-model="rstSent" placeholder="59" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs text-gray-500">RST 收到</span>
          <KInput v-model="rstRcvd" placeholder="59" />
        </label>
      </div>
      <KButton type="primary" block size="lg" :loading="saving" @click="save">保存</KButton>
      <div v-if="savedCount" class="text-center text-xs text-gray-400">
        本次会话已记录 {{ savedCount }} 条
      </div>
    </div>
  </div>
  </div>
</template>
