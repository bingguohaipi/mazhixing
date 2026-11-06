<template>
  <div class="modal-mask">
    <div class="modal-box" style="width: 520px; max-height: 85vh; display: flex; flex-direction: column;">
      <h3 class="modal-title">从学生名单添加</h3>
      <p class="modal-sub">勾选要加入本班的学生（账号需在「学生名单」中预先创建）</p>
      <div class="modal-field">
        <input
          v-model="keyword"
          type="text"
          class="modal-input input-light-bg"
          placeholder="搜索姓名或账号"
        >
      </div>
      <div v-if="loading" class="text-sm text-gray-500 py-6 text-center">加载中...</div>
      <div v-else-if="available.length === 0" class="text-sm text-gray-500 py-6 text-center">
        暂无可添加的学生，请先在「学生名单」中批量创建
      </div>
      <div v-else class="overflow-y-auto border border-gray-100 rounded-lg flex-1 min-h-0 max-h-64">
        <label
          v-for="item in available"
          :key="item.id"
          class="flex items-center gap-3 px-3 py-2 border-b border-gray-50 hover:bg-gray-50 cursor-pointer text-sm"
        >
          <input v-model="selectedIds" type="checkbox" :value="item.id">
          <span class="font-medium">{{ item.display_name }}</span>
          <span class="text-gray-400 font-mono text-xs">{{ item.account }}</span>
          <span v-if="item.class_names.length" class="text-gray-400 text-xs ml-auto">
            已在：{{ item.class_names.join('、') }}
          </span>
        </label>
      </div>
      <div v-if="formError" class="modal-error show" style="margin-top: 12px;">{{ formError }}</div>
      <div class="modal-actions" style="margin-top: 12px;">
        <button class="modal-btn-cancel" @click="$emit('close')">取消</button>
        <button class="modal-btn-confirm" :disabled="submitting || selectedIds.length === 0" @click="submit">
          {{ submitting ? '添加中...' : `确认添加（${selectedIds.length}）` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { classApi } from '@/api/classes'
import { rosterApi } from '@/api/roster'
import type { RosterStudentItem } from '@/types/roster'

const props = defineProps<{ classId: number; enrolledStudentIds: number[] }>()
const emit = defineEmits<{ close: []; success: [message: string] }>()

const keyword = ref('')
const roster = ref<RosterStudentItem[]>([])
const loading = ref(true)
const selectedIds = ref<number[]>([])
const submitting = ref(false)
const formError = ref('')

const enrolledSet = computed(() => new Set(props.enrolledStudentIds))

const available = computed(() =>
  roster.value.filter((item) => !enrolledSet.value.has(item.id)),
)

const loadRoster = async () => {
  loading.value = true
  try {
    const data = await rosterApi.list(keyword.value.trim() || undefined)
    roster.value = data.items
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '加载名单失败'
  } finally {
    loading.value = false
  }
}

useDebouncedWatch(keyword, () => {
  void loadRoster()
})

const submit = async () => {
  formError.value = ''
  if (selectedIds.value.length === 0) {
    formError.value = '请至少选择一名学生'
    return
  }
  submitting.value = true
  try {
    const enrolled = await classApi.enrollStudents(props.classId, selectedIds.value)
    emit('success', `已成功添加 ${enrolled.length} 名学生到班级`)
    emit('close')
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '添加失败'
  } finally {
    submitting.value = false
  }
}

onMounted(loadRoster)
</script>
