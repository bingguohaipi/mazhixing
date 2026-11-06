<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="text-center max-w-md px-6">
      <div class="text-6xl mb-4">📡</div>
      <h1 class="text-xl font-semibold text-gray-900 mb-2">网络连接异常</h1>
      <p class="text-gray-500 mb-6">请检查网络后重试，你的本地草稿已保留</p>
      <div class="flex items-center justify-center gap-3">
        <button
          class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          @click="retry"
        >
          重新加载
        </button>
        <button
          class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          @click="goHome"
        >
          返回首页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const retry = () => {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : auth.homeRoute
  router.replace(redirect || auth.homeRoute)
}

const goHome = () => {
  router.replace(auth.isAuthenticated ? auth.homeRoute : '/login')
}
</script>
