<script setup lang="ts">
import { ref } from 'vue'
import { KAlert, KButton, KDialog, KMessage, KUpload } from '@guoyg578/k-ui'
import type { UploadCustomRequestOptions } from '@guoyg578/k-ui'
import { FileDown, FileUp } from '@lucide/vue'
import type { AdifImportResult } from '../types'
import { api } from '../api'

const props = defineProps<{
  open: boolean
  stationId: number
  stationName: string
}>()

const emit = defineEmits<{
  'update:open': [v: boolean]
  imported: []
}>()

const importResult = ref<AdifImportResult | null>(null)
const importing = ref(false)

function doExport(all: boolean) {
  window.open(api.adifExportUrl(all ? undefined : props.stationId), '_blank')
}

function customRequest(options: UploadCustomRequestOptions) {
  const file = options.file.file
  if (!file) {
    options.onError('文件为空')
    return
  }
  importing.value = true
  importResult.value = null
  api
    .adifImport(props.stationId, file)
    .then((result) => {
      importResult.value = result
      options.onFinish()
      KMessage.success(`导入完成：成功 ${result.imported} 条`)
      emit('imported')
    })
    .catch((e) => {
      options.onError(e)
      KMessage.error(`导入失败: ${(e as Error).message}`)
    })
    .finally(() => {
      importing.value = false
    })
}
</script>

<template>
  <KDialog
    :open="open"
    title="ADIF 导入 / 导出"
    subtitle="兼容 LoTW / eQSL / QRZ / ClubLog"
    @update:open="emit('update:open', $event)"
  >
    <div class="space-y-5">
      <div>
        <div class="mb-2 flex items-center gap-1.5 text-sm font-semibold">
          <FileDown class="size-4" /> 导出
        </div>
        <div class="flex gap-2">
          <KButton @click="doExport(false)">导出「{{ stationName }}」</KButton>
          <KButton @click="doExport(true)">导出全部电台</KButton>
        </div>
        <div class="mt-1 text-xs text-gray-400">
          生成 .adi 文件并下载，同时保存一份到 NAS 的 /data/export 目录。
        </div>
      </div>

      <div>
        <div class="mb-2 flex items-center gap-1.5 text-sm font-semibold">
          <FileUp class="size-4" /> 导入到「{{ stationName }}」
        </div>
        <KUpload
          accept=".adi,.adif,.txt"
          :show-list="false"
          :disabled="importing"
          button-text="选择 ADIF 文件（.adi）"
          :custom-request="customRequest"
        />
        <div v-if="importResult" class="mt-3 space-y-2">
          <KAlert
            :type="importResult.errors.length ? 'warning' : 'success'"
            :title="`导入 ${importResult.imported} 条，跳过 ${importResult.skipped} 条，失败 ${importResult.errors.length} 条`"
          />
          <div v-if="importResult.errors.length" class="max-h-32 overflow-y-auto rounded bg-gray-50 p-2 text-xs text-red-500">
            <div v-for="(err, i) in importResult.errors" :key="i">{{ err }}</div>
          </div>
        </div>
      </div>
    </div>
  </KDialog>
</template>
