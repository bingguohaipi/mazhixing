<template>
  <Teleport to="body">
    <div
      class="modal-mask"
      :class="{ 'modal-mask--main-panel': centerInMain }"
      @click.self="emit('close')"
    >
      <div class="modal-box">
        <ChangePasswordForm theme="modal" show-cancel @cancel="emit('close')" @success="emit('success')" />
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import ChangePasswordForm from '@/components/ChangePasswordForm.vue'

withDefaults(
  defineProps<{
    /** 在个人中心主内容区内居中（与侧栏布局对齐） */
    centerInMain?: boolean
  }>(),
  { centerInMain: false },
)

const emit = defineEmits(['close', 'success'])
</script>
