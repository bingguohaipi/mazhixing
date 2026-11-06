<template>
  <div class="modal-mask" @click.self="$emit('close')">
    <div class="modal-box" style="width: 420px;">
      <h3 class="modal-title">学生信息</h3>
      <p class="modal-sub">登录账号 {{ account }}（不可修改）</p>
      <dl class="space-y-3 text-sm mt-4">
        <div class="flex justify-between gap-4 border-b border-gray-100 pb-2">
          <dt class="text-gray-500">真实姓名</dt>
          <dd class="font-medium text-gray-900 text-right">{{ realName || '—' }}</dd>
        </div>
        <div class="flex justify-between gap-4 border-b border-gray-100 pb-2">
          <dt class="text-gray-500">昵称</dt>
          <dd class="text-gray-900 text-right">{{ nickname || '—' }}</dd>
        </div>
      </dl>
      <p class="text-xs text-gray-400 mt-4 leading-relaxed">
        真实姓名由管理员在用户管理中维护；昵称由学生在个人中心自行修改。
      </p>
      <div class="modal-actions mt-6">
        <button class="modal-btn-confirm w-full" type="button" @click="$emit('close')">知道了</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  account: string
  realName: string | null
  nickname: string | null
}>()

defineEmits<{ close: [] }>()
</script>
