<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="text-center">
      <div class="text-6xl font-bold text-gray-300 mb-4">403</div>
      <h1 class="text-xl font-semibold text-gray-900 mb-2">暂无权限访问该页面</h1>
      <p class="text-gray-500 mb-6">您当前的角色无法访问此功能</p>
      <button
        class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        @click="router.push(auth.homeRoute)"
      >
        返回首页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
</script>
