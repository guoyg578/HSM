<script setup lang="ts">
import { ref, watch } from 'vue'
import { KDialog, KForm, KFormField, KInput, KMessage, KTextarea } from '@guoyg578/k-ui'
import type { StationDetail } from '../types'
import { api } from '../api'

const props = defineProps<{
  open: boolean
  station: StationDetail | null
}>()

const emit = defineEmits<{
  'update:open': [v: boolean]
  saved: [station: StationDetail]
}>()

const model = ref({
  name: '',
  callsign: '',
  qth: '',
  grid: '',
  cq_zone: '',
  itu_zone: '',
  remark: '',
})
const saving = ref(false)

watch(
  () => props.open,
  (open) => {
    if (!open) return
    const s = props.station
    model.value = {
      name: s?.name ?? '',
      callsign: s?.callsign ?? '',
      qth: s?.qth ?? '',
      grid: s?.grid ?? '',
      cq_zone: s?.cq_zone ?? '',
      itu_zone: s?.itu_zone ?? '',
      remark: s?.remark ?? '',
    }
  },
)

async function save() {
  if (!model.value.name.trim() || !model.value.callsign.trim()) {
    KMessage.warning('电台名称与呼号为必填项')
    return
  }
  saving.value = true
  try {
    const data = { ...model.value, callsign: model.value.callsign.toUpperCase() }
    const saved = props.station
      ? await api.updateStation(props.station.id, data)
      : await api.createStation(data)
    KMessage.success(props.station ? '电台已更新' : '电台已创建')
    emit('update:open', false)
    emit('saved', saved)
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
    :title="station ? '编辑电台' : '新建电台'"
    footer
    :confirm-loading="saving"
    confirm-text="保存"
    cancel-text="取消"
    @update:open="emit('update:open', $event)"
    @confirm="save"
    @cancel="emit('update:open', false)"
  >
    <KForm :model="model" label-position="top">
      <div class="grid grid-cols-2 gap-x-4">
        <KFormField name="name" label="电台名称" required>
          <KInput v-model="model.name" placeholder="如：家庭电台" />
        </KFormField>
        <KFormField name="callsign" label="呼号 CALLSIGN" required>
          <KInput v-model="model.callsign" placeholder="如：BG5XXX" />
        </KFormField>
        <KFormField name="qth" label="QTH 所在地">
          <KInput v-model="model.qth" placeholder="如：安徽合肥" />
        </KFormField>
        <KFormField name="grid" label="Grid 网格定位">
          <KInput v-model="model.grid" placeholder="如：OM81 / OM81mt" />
        </KFormField>
        <KFormField name="cq_zone" label="CQ Zone（可选）">
          <KInput v-model="model.cq_zone" placeholder="如：24" />
        </KFormField>
        <KFormField name="itu_zone" label="ITU Zone（可选）">
          <KInput v-model="model.itu_zone" placeholder="如：44" />
        </KFormField>
      </div>
      <KFormField name="remark" label="备注（可选）">
        <KTextarea v-model="model.remark" :rows="2" placeholder="其他说明" />
      </KFormField>
    </KForm>
  </KDialog>
</template>
