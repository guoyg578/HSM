import type {
  AdifImportResult,
  Antenna,
  Equipment,
  PowerProfile,
  QSO,
  QSODefaults,
  QSOPage,
  QSOQuery,
  Station,
  StationDetail,
  Stats,
  UploadResult,
} from './types'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: options?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const data = await resp.json()
      detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    } catch {
      /* 保留 statusText */
    }
    throw new Error(detail)
  }
  return resp.json()
}

function qs(params: Record<string, unknown>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') search.set(key, String(value))
  }
  const s = search.toString()
  return s ? `?${s}` : ''
}

export const api = {
  // ---- 电台 ----
  listStations: () => request<Station[]>('/api/stations'),
  getStation: (id: number) => request<StationDetail>(`/api/stations/${id}`),
  createStation: (data: Partial<Station>) =>
    request<StationDetail>('/api/stations', { method: 'POST', body: JSON.stringify(data) }),
  updateStation: (id: number, data: Partial<Station>) =>
    request<StationDetail>(`/api/stations/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteStation: (id: number) => request<void>(`/api/stations/${id}`, { method: 'DELETE' }),
  qsoDefaults: (id: number) => request<QSODefaults>(`/api/stations/${id}/qso-defaults`),

  // ---- 电台配置 ----
  addEquipment: (sid: number, data: Partial<Equipment>) =>
    request<Equipment>(`/api/stations/${sid}/equipments`, { method: 'POST', body: JSON.stringify(data) }),
  deleteEquipment: (sid: number, id: number) =>
    request<void>(`/api/stations/${sid}/equipments/${id}`, { method: 'DELETE' }),
  addAntenna: (sid: number, data: Partial<Antenna>) =>
    request<Antenna>(`/api/stations/${sid}/antennas`, { method: 'POST', body: JSON.stringify(data) }),
  deleteAntenna: (sid: number, id: number) =>
    request<void>(`/api/stations/${sid}/antennas/${id}`, { method: 'DELETE' }),
  addPowerProfile: (sid: number, data: Partial<PowerProfile>) =>
    request<PowerProfile>(`/api/stations/${sid}/power-profiles`, { method: 'POST', body: JSON.stringify(data) }),
  deletePowerProfile: (sid: number, id: number) =>
    request<void>(`/api/stations/${sid}/power-profiles/${id}`, { method: 'DELETE' }),

  // ---- QSO ----
  listQsos: (query: QSOQuery) => request<QSOPage>(`/api/qsos${qs({ ...query })}`),
  createQso: (data: Record<string, unknown>) =>
    request<QSO>('/api/qsos', { method: 'POST', body: JSON.stringify(data) }),
  updateQso: (id: number, data: Record<string, unknown>) =>
    request<QSO>(`/api/qsos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteQso: (id: number) => request<void>(`/api/qsos/${id}`, { method: 'DELETE' }),

  // ---- 统计 ----
  stats: (stationId?: number) => request<Stats>(`/api/stats${qs({ station_id: stationId })}`),

  // ---- 文件 ----
  upload: (kind: 'audio' | 'qsl', file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<UploadResult>(`/api/upload/${kind}`, { method: 'POST', body: form })
  },

  // ---- ADIF ----
  adifImport: (stationId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<AdifImportResult>(`/api/adif/import?station_id=${stationId}`, {
      method: 'POST',
      body: form,
    })
  },
  adifExportUrl: (stationId?: number) => `/api/adif/export${qs({ station_id: stationId })}`,
}
