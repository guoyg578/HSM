/* 极简共享状态：电台列表（左侧菜单与各视图共用）。 */
import { ref } from 'vue'
import { api } from './api'
import type { Station } from './types'

export const stations = ref<Station[]>([])

export async function refreshStations(): Promise<void> {
  stations.value = await api.listStations()
}
