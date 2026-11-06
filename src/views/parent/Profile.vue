<template>
  <BasicAccountProfile
    role-label="家长"
    centered
    centered-lower
    :load="parentProfileApi.getProfile"
    :save-nickname="parentProfileApi.updateNickname"
  >
    <template #extra="{ profile }">
      <section v-if="profile" class="bg-white rounded-xl border border-gray-100 p-6 space-y-4 text-center">
        <div>
          <h2 class="text-sm font-semibold text-gray-900 mb-2">关联班级</h2>
          <p v-if="profile.class_names.length" class="text-sm text-gray-700">
            {{ profile.class_names.join('、') }}
          </p>
          <p v-else class="text-sm text-gray-500">绑定子女后将显示其所在班级</p>
        </div>
        <div>
          <h2 class="text-sm font-semibold text-gray-900 mb-2">我的孩子</h2>
          <ul v-if="childrenOf(profile).length" class="space-y-2 text-sm">
            <li v-for="c in childrenOf(profile)" :key="c.id" class="text-gray-800">
              <span class="font-medium">{{ c.real_name || c.account }}</span>
              <span class="text-gray-500">（{{ c.account }}）</span>
              <span v-if="c.class_names.length" class="text-gray-500"> · {{ c.class_names.join('、') }}</span>
            </li>
          </ul>
          <p v-else class="text-sm text-gray-500">暂未绑定孩子，请联系管理员或老师</p>
        </div>
      </section>
    </template>
  </BasicAccountProfile>
</template>

<script setup lang="ts">
import BasicAccountProfile from '@/components/BasicAccountProfile.vue'
import { parentProfileApi } from '@/api/parent-profile'
import type { ParentProfile } from '@/types/role-profile'

function childrenOf(profile: unknown): ParentProfile['children'] {
  if (!profile || typeof profile !== 'object' || !('children' in profile)) return []
  const list = (profile as ParentProfile).children
  return Array.isArray(list) ? list : []
}
</script>
