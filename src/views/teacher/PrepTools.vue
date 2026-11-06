<template>
  <div class="p-6">
    <h1 class="text-lg font-semibold text-gray-900 mb-2">备课工具</h1>
    <p class="text-sm text-gray-500 mb-6">题库导入、备课包导出与班级错题复盘</p>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <RouterLink
        to="/teacher/questions"
        class="bg-white border border-gray-200 rounded-xl p-5 hover:border-indigo-300"
      >
        <div class="font-medium">批量导入题目</div>
        <p class="text-sm text-gray-500 mt-1">JSON 模板导入私有题库</p>
      </RouterLink>
      <RouterLink
        to="/teacher/questions"
        class="bg-white border border-gray-200 rounded-xl p-5 hover:border-indigo-300"
      >
        <div class="font-medium">导出备课包</div>
        <p class="text-sm text-gray-500 mt-1">在题库页勾选题目导出 Markdown</p>
      </RouterLink>
      <RouterLink
        to="/teacher/analytics"
        class="bg-white border border-gray-200 rounded-xl p-5 hover:border-indigo-300"
      >
        <div class="font-medium">班级错题汇总</div>
        <p class="text-sm text-gray-500 mt-1">学情分析 → 错题汇总 Tab</p>
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePageDwell } from '@/composables/usePageDwell'

usePageDwell('teacher_prep_dwell', '/teacher/prep-tools', 'teacher')
</script>
