<script setup lang="ts">
import { ref } from 'vue'
import {
  KDialog,
  KInput,
  KInputNumber,
  KMessage,
  KPopconfirm,
  KTag,
} from '@guoyg578/k-ui'
import { Antenna as AntennaIcon, Gauge, Plus, Radio, Trash2 } from '@lucide/vue'
import type { StationDetail } from '../types'
import { api } from '../api'
import IconButton from './IconButton.vue'

const props = defineProps<{ station: StationDetail }>()
const emit = defineEmits<{ changed: [] }>()

type DialogKind = 'equipment' | 'antenna' | 'power'
const dialogKind = ref<DialogKind | null>(null)
const saving = ref(false)

const equipModel = ref({ brand: '', model: '', type: '', remark: '' })
const antennaModel = ref({ name: '', remark: '' })
const powerModel = ref({ mode_name: '', power_watts: null as number | null })

function openDialog(kind: DialogKind) {
  equipModel.value = { brand: '', model: '', type: '', remark: '' }
  antennaModel.value = { name: '', remark: '' }
  powerModel.value = { mode_name: '', power_watts: null }
  dialogKind.value = kind
}

async function save() {
  const sid = props.station.id
  saving.value = true
  try {
    if (dialogKind.value === 'equipment') {
      if (!equipModel.value.model.trim()) {
        KMessage.warning('型号为必填项')
        return
      }
      await api.addEquipment(sid, equipModel.value)
    } else if (dialogKind.value === 'antenna') {
      if (!antennaModel.value.name.trim()) {
        KMessage.warning('天线名称为必填项')
        return
      }
      await api.addAntenna(sid, antennaModel.value)
    } else if (dialogKind.value === 'power') {
      if (!powerModel.value.mode_name.trim() || powerModel.value.power_watts == null) {
        KMessage.warning('模式与功率为必填项')
        return
      }
      await api.addPowerProfile(sid, {
        mode_name: powerModel.value.mode_name,
        power_watts: powerModel.value.power_watts!,
      })
    }
    dialogKind.value = null
    emit('changed')
  } catch (e) {
    KMessage.error(`保存失败: ${(e as Error).message}`)
  } finally {
    saving.value = false
  }
}

async function remove(kind: DialogKind, id: number) {
  const sid = props.station.id
  try {
    if (kind === 'equipment') await api.deleteEquipment(sid, id)
    else if (kind === 'antenna') await api.deleteAntenna(sid, id)
    else await api.deletePowerProfile(sid, id)
    emit('changed')
  } catch (e) {
    KMessage.error(`删除失败: ${(e as Error).message}`)
  }
}

const dialogTitles: Record<DialogKind, string> = {
  equipment: '添加设备',
  antenna: '添加天线',
  power: '添加功率配置',
}
</script>

<template>
  <div class="space-y-5 p-4">
    <!-- 电台信息 -->
    <div>
      <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        当前电台
      </div>
      <div class="rounded-lg bg-gray-50 p-3 text-sm">
        <div class="text-base font-bold">{{ station.callsign }}</div>
        <div class="mt-1 space-y-0.5 text-gray-600">
          <div>{{ station.name }}</div>
          <div v-if="station.qth">QTH：{{ station.qth }}</div>
          <div v-if="station.grid">Grid：{{ station.grid }}</div>
          <div v-if="station.cq_zone">CQ Zone：{{ station.cq_zone }}</div>
          <div v-if="station.itu_zone">ITU Zone：{{ station.itu_zone }}</div>
        </div>
      </div>
    </div>

    <!-- 设备 -->
    <div>
      <div class="mb-2 flex items-center justify-between">
        <div class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">
          <Radio class="size-3.5" /> 设备
        </div>
        <IconButton title="添加设备" @click="openDialog('equipment')">
          <Plus class="size-4" />
        </IconButton>
      </div>
      <div v-if="!station.equipments.length" class="text-xs text-gray-400">暂无设备</div>
      <div
        v-for="e in station.equipments"
        :key="e.id"
        class="group mb-1.5 flex items-start justify-between rounded-lg border border-gray-200 p-2.5 text-sm"
      >
        <div>
          <div class="font-medium">{{ e.brand }} {{ e.model }}</div>
          <KTag v-if="e.type" size="sm" class="mt-1">{{ e.type }}</KTag>
        </div>
        <KPopconfirm message="确定删除该设备？" confirm-type="danger" @confirm="remove('equipment', e.id)">
          <IconButton title="删除" danger>
            <Trash2 class="size-3.5" />
          </IconButton>
        </KPopconfirm>
      </div>
    </div>

    <!-- 天馈系统 -->
    <div>
      <div class="mb-2 flex items-center justify-between">
        <div class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">
          <AntennaIcon class="size-3.5" /> 天馈系统
        </div>
        <IconButton title="添加天线" @click="openDialog('antenna')">
          <Plus class="size-4" />
        </IconButton>
      </div>
      <div v-if="!station.antennas.length" class="text-xs text-gray-400">暂无天线</div>
      <div
        v-for="a in station.antennas"
        :key="a.id"
        class="group mb-1.5 flex items-center justify-between rounded-lg border border-gray-200 p-2.5 text-sm"
      >
        <div class="font-medium">{{ a.name }}</div>
        <KPopconfirm message="确定删除该天线？" confirm-type="danger" @confirm="remove('antenna', a.id)">
          <IconButton title="删除" danger>
            <Trash2 class="size-3.5" />
          </IconButton>
        </KPopconfirm>
      </div>
    </div>

    <!-- 功率配置 -->
    <div>
      <div class="mb-2 flex items-center justify-between">
        <div class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">
          <Gauge class="size-3.5" /> 功率配置
        </div>
        <IconButton title="添加功率配置" @click="openDialog('power')">
          <Plus class="size-4" />
        </IconButton>
      </div>
      <div v-if="!station.power_profiles.length" class="text-xs text-gray-400">暂无功率配置</div>
      <div
        v-for="p in station.power_profiles"
        :key="p.id"
        class="group mb-1.5 flex items-center justify-between rounded-lg border border-gray-200 p-2.5 text-sm"
      >
        <div>
          <span class="font-medium">{{ p.mode_name }}</span>
          <span class="ml-2 text-gray-500">{{ p.power_watts }}W</span>
        </div>
        <KPopconfirm message="确定删除该配置？" confirm-type="danger" @confirm="remove('power', p.id)">
          <IconButton title="删除" danger>
            <Trash2 class="size-3.5" />
          </IconButton>
        </KPopconfirm>
      </div>
    </div>

    <!-- 添加对话框 -->
    <KDialog
      :open="dialogKind !== null"
      :title="dialogKind ? dialogTitles[dialogKind] : ''"
      footer
      size="sm"
      :confirm-loading="saving"
      confirm-text="保存"
      cancel-text="取消"
      @update:open="(v: boolean) => { if (!v) dialogKind = null }"
      @confirm="save"
      @cancel="dialogKind = null"
    >
      <div v-if="dialogKind === 'equipment'" class="space-y-3">
        <KInput v-model="equipModel.brand" placeholder="品牌，如：八重洲" />
        <KInput v-model="equipModel.model" placeholder="型号，如：FTM-150R（必填）" />
        <KInput v-model="equipModel.type" placeholder="类型，如：车载电台" />
        <KInput v-model="equipModel.remark" placeholder="备注（可选）" />
      </div>
      <div v-else-if="dialogKind === 'antenna'" class="space-y-3">
        <KInput v-model="antennaModel.name" placeholder="天线名称，如：钻石SG7700（必填）" />
        <KInput v-model="antennaModel.remark" placeholder="备注（可选）" />
      </div>
      <div v-else-if="dialogKind === 'power'" class="space-y-3">
        <KInput v-model="powerModel.mode_name" placeholder="场景/模式，如：FM、数字模式、便携" />
        <KInputNumber v-model="powerModel.power_watts" placeholder="功率（W）" :min="0" :step="5" />
      </div>
    </KDialog>
  </div>
</template>
