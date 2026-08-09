<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { KButton, KInput, KInputNumber, KMessage, KPopconfirm, KSelect } from '@guoyg578/k-ui'
import { ArrowDown, ArrowUp, DatabaseBackup, Plus, Settings as SettingsIcon, Trash2 } from '@lucide/vue'
import type { AppSettings } from '../types'
import { api } from '../api'
import { appSettings, loadAppSettings } from '../settings'

const form = ref<AppSettings | null>(null)
const saving = ref(false)
const backingUp = ref(false)
const newMode = ref('')

onMounted(async () => {
  await loadAppSettings(true)
  form.value = JSON.parse(JSON.stringify(appSettings.value))
})

const defaultModeOptions = computed(() =>
  (form.value?.mode_options ?? []).filter((m) => m.trim()).map((m) => ({ value: m, label: m })),
)

// ---- 模式选项 ----
function addMode() {
  const m = newMode.value.trim()
  if (!m) return
  if (form.value!.mode_options.includes(m)) {
    KMessage.warning('该模式已存在')
    return
  }
  form.value!.mode_options.push(m)
  newMode.value = ''
}

function removeMode(i: number) {
  form.value!.mode_options.splice(i, 1)
}

function moveMode(i: number, delta: number) {
  const list = form.value!.mode_options
  const j = i + delta
  if (j < 0 || j >= list.length) return
  ;[list[i], list[j]] = [list[j]!, list[i]!]
}

// ---- 波段表 ----
function addBand() {
  form.value!.bands.push({ name: '', low_mhz: 0, high_mhz: 0 })
}

function removeBand(i: number) {
  form.value!.bands.splice(i, 1)
}

// ---- 保存 / 恢复默认 / 立即备份 ----
function validate(f: AppSettings): string | null {
  if (!f.mode_options.some((m) => m.trim())) return '至少保留一个模式'
  for (const b of f.bands) {
    if (!b.name.trim()) return '波段名称不能为空'
    if (!(b.low_mhz > 0) || !(b.high_mhz > b.low_mhz))
      return `波段「${b.name}」频率范围无效（需 0 < 下限 < 上限）`
  }
  if (!(f.backup_interval_hours >= 1)) return '备份间隔至少 1 小时'
  if (!(f.backup_keep >= 1)) return '至少保留 1 份备份'
  return null
}

async function save() {
  const f = form.value!
  f.mode_options = f.mode_options.map((m) => m.trim()).filter(Boolean)
  const err = validate(f)
  if (err) {
    KMessage.warning(err)
    return
  }
  if (!f.mode_options.includes(f.default_mode)) f.default_mode = f.mode_options[0]!
  saving.value = true
  try {
    appSettings.value = await api.updateSettings(f)
    form.value = JSON.parse(JSON.stringify(appSettings.value))
    KMessage.success('配置已保存，立即生效')
  } catch (e) {
    KMessage.error(`保存失败: ${(e as Error).message}`)
  } finally {
    saving.value = false
  }
}

async function resetDefaults() {
  try {
    form.value = await api.getSettingsDefaults()
    KMessage.info('已载入内置默认值，点击「保存」后生效')
  } catch (e) {
    KMessage.error(`加载默认值失败: ${(e as Error).message}`)
  }
}

async function backupNow() {
  backingUp.value = true
  try {
    const r = await api.backupNow()
    KMessage.success(r.message)
  } catch (e) {
    KMessage.error(`备份失败: ${(e as Error).message}`)
  } finally {
    backingUp.value = false
  }
}
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 顶部固定操作栏 -->
    <div
      class="flex shrink-0 items-center justify-between gap-3 border-b border-gray-200 bg-white px-4 py-3 sm:px-6"
    >
      <div class="flex items-center gap-2">
        <SettingsIcon class="size-5 text-blue-600" />
        <h1 class="text-lg font-bold">后台管理</h1>
        <span class="hidden text-xs text-gray-400 sm:inline">保存后立即生效</span>
      </div>
      <div class="flex items-center gap-2">
        <KPopconfirm
          title="恢复默认"
          message="将所有配置项恢复为内置默认值（需再点击「保存」生效），确定？"
          @confirm="resetDefaults"
        >
          <KButton :disabled="!form">恢复默认</KButton>
        </KPopconfirm>
        <KButton type="primary" :disabled="!form" :loading="saving" @click="save">保存</KButton>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-4 sm:p-6">
      <div v-if="!form" class="py-16 text-center text-sm text-gray-400">加载中…</div>

      <div v-else class="grid items-start gap-5 lg:grid-cols-2">
        <div class="space-y-5">
        <!-- 模式选项 -->
        <section class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 class="text-sm font-semibold">通联模式选项</h2>
          <p class="mb-3 mt-0.5 text-xs text-gray-400">
            新建 QSO / 快速记录的「模式」下拉列表，按此处顺序显示。
          </p>
          <div class="space-y-2">
            <div
              v-for="(_m, i) in form.mode_options"
              :key="i"
              class="flex items-center gap-2"
            >
              <div class="w-48">
                <KInput v-model="form.mode_options[i]" size="sm" />
              </div>
              <KButton size="sm" text :disabled="i === 0" title="上移" @click="moveMode(i, -1)">
                <ArrowUp class="size-3.5" />
              </KButton>
              <KButton
                size="sm"
                text
                :disabled="i === form.mode_options.length - 1"
                title="下移"
                @click="moveMode(i, 1)"
              >
                <ArrowDown class="size-3.5" />
              </KButton>
              <KButton size="sm" text title="删除" @click="removeMode(i)">
                <Trash2 class="size-3.5 text-red-500" />
              </KButton>
            </div>
          </div>
          <div class="mt-3 flex items-center gap-2">
            <div class="w-48">
              <KInput v-model="newMode" size="sm" placeholder="新模式，如 NFM" @keyup.enter="addMode" />
            </div>
            <KButton size="sm" @click="addMode">
              <Plus class="mr-1 size-3.5" /> 添加
            </KButton>
          </div>
        </section>

        <!-- 新建 QSO 默认值 -->
        <section class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 class="text-sm font-semibold">新建 QSO 默认值</h2>
          <p class="mb-3 mt-0.5 text-xs text-gray-400">打开新建 QSO / 快速记录表单时预填的值。</p>
          <div class="grid max-w-md grid-cols-2 gap-3">
            <label class="block">
              <span class="mb-1 block text-xs text-gray-500">默认模式</span>
              <KSelect v-model="form.default_mode" :options="defaultModeOptions" size="sm" />
            </label>
            <label class="block">
              <span class="mb-1 block text-xs text-gray-500">默认 RST</span>
              <KInput v-model="form.default_rst" size="sm" placeholder="59" />
            </label>
          </div>
        </section>
        </div>

        <div class="space-y-5">
        <!-- 波段表 -->
        <section class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 class="text-sm font-semibold">波段对照表</h2>
          <p class="mb-3 mt-0.5 text-xs text-gray-400">
            新建 / 编辑 QSO 和 ADIF 导入时按频率自动推导波段。修改只影响之后的记录，不改历史数据。
          </p>
          <div class="space-y-2">
            <div class="hidden gap-2 text-xs text-gray-400 sm:flex">
              <span class="w-28">波段名</span>
              <span class="w-32">下限 (MHz)</span>
              <span class="w-32">上限 (MHz)</span>
            </div>
            <div v-for="(b, i) in form.bands" :key="i" class="flex flex-wrap items-center gap-2">
              <div class="w-28">
                <KInput v-model="b.name" size="sm" placeholder="70cm" />
              </div>
              <div class="w-32">
                <KInputNumber v-model="b.low_mhz" size="sm" :min="0" :step="0.001" :show-button="false" />
              </div>
              <div class="w-32">
                <KInputNumber v-model="b.high_mhz" size="sm" :min="0" :step="0.001" :show-button="false" />
              </div>
              <KButton size="sm" text title="删除" @click="removeBand(i)">
                <Trash2 class="size-3.5 text-red-500" />
              </KButton>
            </div>
          </div>
          <div class="mt-3">
            <KButton size="sm" @click="addBand">
              <Plus class="mr-1 size-3.5" /> 添加波段
            </KButton>
          </div>
        </section>

        <!-- 自动备份 -->
        <section class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 class="text-sm font-semibold">自动备份</h2>
          <p class="mb-3 mt-0.5 text-xs text-gray-400">
            SQLite 定时备份到数据目录 backups/。保存后备份计时按新间隔重新开始。
          </p>
          <div class="grid max-w-md grid-cols-2 gap-3">
            <label class="block">
              <span class="mb-1 block text-xs text-gray-500">备份间隔（小时）</span>
              <KInputNumber v-model="form.backup_interval_hours" size="sm" :min="1" :max="8760" />
            </label>
            <label class="block">
              <span class="mb-1 block text-xs text-gray-500">保留份数</span>
              <KInputNumber v-model="form.backup_keep" size="sm" :min="1" :max="365" />
            </label>
          </div>
          <div class="mt-3">
            <KButton size="sm" :loading="backingUp" @click="backupNow">
              <DatabaseBackup class="mr-1 size-3.5" /> 立即备份一次
            </KButton>
          </div>
        </section>
        </div>
      </div>
    </div>
  </div>
</template>
