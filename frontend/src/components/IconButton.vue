<script setup lang="ts">
// 纯图标操作按钮：正方形悬停底色，danger 用于删除类操作
defineProps<{
  title?: string
  danger?: boolean
  disabled?: boolean
}>()
</script>

<template>
  <button
    type="button"
    :title="title"
    :disabled="disabled"
    class="inline-flex size-7 shrink-0 cursor-pointer items-center justify-center rounded-md transition-colors disabled:cursor-not-allowed disabled:opacity-35"
    :class="
      danger
        ? 'text-red-500 enabled:hover:bg-red-50 enabled:hover:text-red-600'
        : 'text-gray-500 enabled:hover:bg-gray-100 enabled:hover:text-gray-900'
    "
  >
    <slot />
  </button>
</template>
