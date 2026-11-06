<template>
  <div class="toast-container">
    <div
      v-for="item in toasts"
      :key="item.id"
      class="toast-item"
      :class="`toast-${item.type}`"
    >
      {{ item.message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToastState } from '@/utils/toast'

const toasts = useToastState()
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 24px;
  left: 50%;
  right: auto;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  pointer-events: none;
  width: max-content;
  max-width: min(92vw, 420px);
}

.toast-item {
  min-width: 200px;
  max-width: min(92vw, 420px);
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  text-align: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  word-break: break-word;
}

.toast-success {
  background: #52c41a;
}

.toast-error {
  background: #ff4d4f;
}

.toast-info {
  background: #1890ff;
}
</style>
