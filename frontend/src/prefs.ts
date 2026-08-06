/* 用户界面偏好：localStorage 持久化（显示模式 / 自定义列 / 上次选中的电台）。 */

export type ViewMode = 'table' | 'timeline'

const KEYS = {
  viewMode: 'hsm.viewMode',
  columns: 'hsm.columns',
  lastStation: 'hsm.lastStation',
}

export const DEFAULT_COLUMNS = ['date', 'time', 'call', 'freq', 'mode', 'rst', 'qth']

export function loadViewMode(): ViewMode {
  return localStorage.getItem(KEYS.viewMode) === 'timeline' ? 'timeline' : 'table'
}

export function saveViewMode(mode: ViewMode): void {
  localStorage.setItem(KEYS.viewMode, mode)
}

export function loadColumns(): string[] {
  try {
    const raw = localStorage.getItem(KEYS.columns)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length) return parsed
    }
  } catch {
    /* 回退默认列 */
  }
  return [...DEFAULT_COLUMNS]
}

export function saveColumns(cols: string[]): void {
  localStorage.setItem(KEYS.columns, JSON.stringify(cols))
}

export function loadLastStation(): number | null {
  const raw = localStorage.getItem(KEYS.lastStation)
  const id = raw ? Number(raw) : NaN
  return Number.isFinite(id) ? id : null
}

export function saveLastStation(id: number): void {
  localStorage.setItem(KEYS.lastStation, String(id))
}
