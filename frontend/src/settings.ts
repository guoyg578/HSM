/* 运行时配置：后台管理页编辑，应用启动时加载，加载完成前使用内置默认值。 */
import { computed, ref } from 'vue'
import { api } from './api'
import type { AppSettings } from './types'

const FALLBACK: AppSettings = {
  mode_options: ['FM', 'FMO', 'SSB', 'CW', 'AM', 'FT8', 'FT4', 'RTTY', 'DMR', 'C4FM', 'D-STAR', 'Digital'],
  default_mode: 'FM',
  default_rst: '59',
  bands: [],
  backup_interval_hours: 24,
  backup_keep: 7,
}

export const appSettings = ref<AppSettings>({ ...FALLBACK })

let loadPromise: Promise<void> | null = null

export function loadAppSettings(force = false): Promise<void> {
  if (!loadPromise || force) {
    loadPromise = api.getSettings().then(
      (s) => {
        appSettings.value = s
      },
      () => {
        /* 加载失败保留内置默认值 */
      },
    )
  }
  return loadPromise
}

export const modeOptions = computed(() =>
  appSettings.value.mode_options.map((m) => ({ value: m, label: m })),
)
