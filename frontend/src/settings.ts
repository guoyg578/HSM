/* 运行时配置：后台管理页编辑，应用启动时加载，加载完成前使用内置默认值。 */
import { computed, ref } from 'vue'
import { api } from './api'
import type { AppSettings } from './types'

const FALLBACK: AppSettings = {
  mode_options: ['FM', 'FMO', 'SSB', 'CW', 'AM', 'FT8', 'FT4', 'RTTY', 'DMR', 'C4FM', 'D-STAR', 'Digital'],
  default_mode: 'FM',
  default_rst: '59',
  qso_columns: ['date', 'time', 'call', 'freq', 'mode', 'rst', 'qth'],
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
        // 与内置默认合并：后端版本较旧、响应缺少新增字段时仍有默认值可用
        appSettings.value = { ...FALLBACK, ...s }
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
