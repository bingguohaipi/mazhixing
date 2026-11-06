<template>
  <BasicAccountProfile
    role-label="教师"
    centered
    :load="teacherProfileApi.getProfile"
    :save-nickname="teacherProfileApi.updateNickname"
  >
    <template #extra="{ profile }">
      <section
        v-if="profile && 'class_names' in profile"
        class="bg-white rounded-xl border border-gray-100 p-6 text-center"
      >
        <h2 class="text-sm font-semibold text-gray-900 mb-2">任教班级</h2>
        <p v-if="profile.class_names.length" class="text-sm text-gray-700">
          {{ profile.class_names.join('、') }}
        </p>
        <p v-else class="text-sm text-gray-500">暂无班级，请先在班级管理中创建</p>
      </section>
    </template>
  </BasicAccountProfile>
</template>

<script setup lang="ts">
import BasicAccountProfile from '@/components/BasicAccountProfile.vue'
import { teacherProfileApi } from '@/api/teacher-profile'
</script>
