export interface Equipment {
  id: number
  station_id: number
  brand: string
  model: string
  type: string
  remark: string
}

export interface Antenna {
  id: number
  station_id: number
  name: string
  remark: string
}

export interface PowerProfile {
  id: number
  station_id: number
  mode_name: string
  power_watts: number
}

export interface Station {
  id: number
  name: string
  callsign: string
  qth: string
  grid: string
  cq_zone: string
  itu_zone: string
  remark: string
  created_at: string
}

export interface StationDetail extends Station {
  equipments: Equipment[]
  antennas: Antenna[]
  power_profiles: PowerProfile[]
}

export interface QSO {
  id: number
  station_id: number
  datetime_utc: string
  call: string
  freq_mhz: number | null
  band: string
  mode: string
  rst_sent: string
  rst_rcvd: string
  qth: string
  grid: string
  distance_km: number | null
  their_equipment: string
  their_antenna: string
  their_power: string
  remark: string
  audio_path: string
  qsl_path: string
  my_callsign: string
  my_qth: string
  my_grid: string
  my_equipment: string
  my_antenna: string
  my_power: string
  created_at: string
}

export interface QSOPage {
  total: number
  page: number
  page_size: number
  items: QSO[]
}

export interface QSODefaults {
  my_callsign: string
  my_qth: string
  my_grid: string
  my_equipment: string
  my_antenna: string
  my_power: string
  power_profiles: PowerProfile[]
}

export interface Stats {
  total_qso: number
  month_qso: number
  max_distance_km: number | null
  top_band: string
  top_mode: string
}

export interface UploadResult {
  path: string
  url: string
}

export interface AdifImportResult {
  imported: number
  skipped: number
  errors: string[]
}

export interface QSOQuery {
  station_id?: number
  q?: string
  sort_by?: 'date' | 'freq' | 'distance'
  order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}
