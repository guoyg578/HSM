/* 通用工具：UTC 时间格式化、Maidenhead 网格换算（前端预览距离用）。 */

export function fmtDate(iso: string): string {
  return iso.slice(0, 10)
}

export function fmtTime(iso: string): string {
  return iso.slice(11, 16)
}

export function fmtDateTime(iso: string): string {
  return `${fmtDate(iso)} ${fmtTime(iso)}`
}

export function fmtFreq(freq: number | null): string {
  if (freq === null || freq === undefined) return ''
  return freq.toFixed(3)
}

const GRID_RE = /^[A-Ra-r]{2}[0-9]{2}([A-Xa-x]{2})?([0-9]{2})?$/

export function isValidGrid(grid: string): boolean {
  return !!grid && GRID_RE.test(grid.trim())
}

export function gridToLatLon(grid: string): [number, number] | null {
  const g = grid.trim()
  if (!isValidGrid(g)) return null
  const up = g.slice(0, 2).toUpperCase()
  let lon = (up.charCodeAt(0) - 65) * 20 - 180
  let lat = (up.charCodeAt(1) - 65) * 10 - 90
  lon += parseInt(g[2]!, 10) * 2
  lat += parseInt(g[3]!, 10) * 1
  if (g.length >= 6) {
    const low = g.slice(4, 6).toLowerCase()
    lon += (low.charCodeAt(0) - 97) * (2 / 24) + 2 / 24 / 2
    lat += (low.charCodeAt(1) - 97) * (1 / 24) + 1 / 24 / 2
  } else {
    lon += 1
    lat += 0.5
  }
  return [lat, lon]
}

export function gridDistanceKm(grid1: string, grid2: string): number | null {
  const a = gridToLatLon(grid1)
  const b = gridToLatLon(grid2)
  if (!a || !b) return null
  const [lat1, lon1] = a
  const [lat2, lon2] = b
  const rad = Math.PI / 180
  const dLat = (lat2 - lat1) * rad
  const dLon = (lon2 - lon1) * rad
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) ** 2
  return Math.round(2 * 6371 * Math.asin(Math.sqrt(h)) * 10) / 10
}

export const MODE_OPTIONS = [
  'FM',
  'SSB',
  'CW',
  'AM',
  'FT8',
  'FT4',
  'RTTY',
  'DMR',
  'C4FM',
  'D-STAR',
  'Digital',
].map((m) => ({ value: m, label: m }))
