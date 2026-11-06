<template>
  <div class="p-6">
    <h1 class="text-lg font-semibold text-gray-900 mb-2">数据导出</h1>
    <p class="text-sm text-gray-500 mb-6">在学情分析中按班级筛选后导出 CSV 报告与错题汇总</p>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
      <RouterLink
        to="/teacher/analytics"
        class="bg-white border border-gray-200 rounded-xl p-5 hover:border-indigo-300"
      >
        <div class="font-medium text-gray-900">学情报告导出</div>
        <p class="text-sm text-gray-500 mt-1">作业完成率、正确率、学生提交明细</p>
      </RouterLink>
      <RouterLink
        to="/teacher/analytics"
        class="bg-white border border-gray-200 rounded-xl p-5 hover:border-indigo-300"
      >
        <div class="font-medium text-gray-900">班级错题汇总导出</div>
        <p class="text-sm text-gray-500 mt-1">高频错题与班级错题明细 CSV</p>
      </RouterLink>
    </div>
    <p class="text-xs text-gray-400 mt-6">进入「学情分析」后使用右上角「导出报告 / 导出错题汇总」按钮</p>
  </div>
</template>

<script setup lang="ts">
import { usePageDwell } from '@/composables/usePageDwell'

usePageDwell('teacher_export_dwell', '/teacher/export', 'teacher')
</script>
