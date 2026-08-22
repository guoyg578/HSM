/* 用户界面偏好：localStorage 持久化（显示模式 / 上次选中的电台）。
   表格显示列不在此处——那是全局配置（settings 的 qso_columns），存服务端。 */

export type ViewMode = 'table' | 'timeline'

const KEYS = {
  viewMode: 'hsm.viewMode',
  lastStation: 'hsm.lastStation',
}

/* 表格可选列定义：日志页显示列选择与后台「默认列」配置共用 */
export const COLUMN_DEFS: { key: string; label: string }[] = [
  { key: 'date', label: '日期' },
  { key: 'time', label: '时间' },
  { key: 'call', label: '呼号' },
  { key: 'freq', label: '频率' },
  { key: 'band', label: '波段' },
  { key: 'mode', label: '模式' },
  { key: 'rst', label: 'RST' },
  { key: 'qth', label: '对方QTH' },
  { key: 'grid', label: '网格' },
  { key: 'distance', label: '距离(km)' },
  { key: 'equipment', label: '我的设备' },
  { key: 'antenna', label: '我的天线' },
  { key: 'power', label: '我的功率' },
  { key: 'their_equipment', label: '对方设备' },
  { key: 'their_antenna', label: '对方天线' },
  { key: 'their_power', label: '对方功率' },
  { key: 'remark', label: '备注' },
]

export function loadViewMode(): ViewMode {
  return localStorage.getItem(KEYS.viewMode) === 'timeline' ? 'timeline' : 'table'
}

export function saveViewMode(mode: ViewMode): void {
  localStorage.setItem(KEYS.viewMode, mode)
}

export function loadLastStation(): number | null {
  const raw = localStorage.getItem(KEYS.lastStation)
  const id = raw ? Number(raw) : NaN
  return Number.isFinite(id) ? id : null
}

export function saveLastStation(id: number): void {
  localStorage.setItem(KEYS.lastStation, String(id))
}
