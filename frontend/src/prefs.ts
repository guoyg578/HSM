/* 用户界面偏好：localStorage 持久化（显示模式 / 自定义列 / 上次选中的电台）。 */

export type ViewMode = 'table' | 'timeline'

const KEYS = {
  viewMode: 'hsm.viewMode',
  columns: 'hsm.columns',
  lastStation: 'hsm.lastStation',
  activeView: 'hsm.activeView',
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

/** 当前所在页面：'dashboard' | 'quick' | 'st:<id>'，刷新后原样还原 */
export function loadActiveView(): string {
  return localStorage.getItem(KEYS.activeView) ?? 'dashboard'
}

export function saveActiveView(key: string): void {
  localStorage.setItem(KEYS.activeView, key)
}

export function loadLastStation(): number | null {
  const raw = localStorage.getItem(KEYS.lastStation)
  const id = raw ? Number(raw) : NaN
  return Number.isFinite(id) ? id : null
}

export function saveLastStation(id: number): void {
  localStorage.setItem(KEYS.lastStation, String(id))
}
