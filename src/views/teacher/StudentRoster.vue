<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <h1 class="text-lg font-semibold text-gray-900">学生名单</h1>
      <div class="flex items-center gap-3 flex-wrap">
        <select
          v-model="selectedClassId"
          class="select-field-flat h-9 pl-3 pr-9 text-sm border border-gray-300 rounded-lg min-w-[140px] focus:outline-none focus:ring-2 focus:ring-indigo-500"
          aria-label="按班级筛选学生"
          @change="load"
        >
          <option value="">全部学生</option>
          <option v-for="cls in classes" :key="cls.id" :value="String(cls.id)">{{ cls.name }}</option>
        </select>
        <input
          v-model="keyword"
          type="search"
          placeholder="搜索姓名、昵称或账号"
          class="search-field input-light-bg h-9 px-3 text-sm border border-gray-300 rounded-lg w-48 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
          @click="showBatch = true"
        >
          + 批量添加
        </button>
      </div>
    </div>

    <div class="p-6">
      <p class="text-sm text-gray-500 mb-4">
        在此创建学生账号（格式 stu + 年份 + 三位序号，如 stu2026001），再在「班级管理」中将学生加入班级。初始密码 123456。
      </p>

      <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>
      <div v-else-if="items.length === 0" class="bg-white rounded-xl border p-12 text-center">
        <p class="text-gray-500 mb-4">还没有学生，点击「批量添加」创建账号</p>
        <button class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg" @click="showBatch = true">
          批量添加
        </button>
      </div>
      <div v-else class="bg-white rounded-xl border overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500">
            <tr>
              <th class="px-4 py-2 text-left w-14">序号</th>
              <th class="px-4 py-2 text-left">真实姓名</th>
              <th class="px-4 py-2 text-left">昵称</th>
              <th class="px-4 py-2 text-left">登录账号</th>
              <th class="px-4 py-2 text-left">所在班级</th>
              <th class="px-4 py-2 text-left">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in items" :key="row.id" class="border-t">
              <td class="px-4 py-2 text-gray-500 tabular-nums">{{ index + 1 }}</td>
              <td class="px-4 py-2">{{ row.real_name || '—' }}</td>
              <td class="px-4 py-2 text-gray-600">{{ row.nickname || '—' }}</td>
              <td class="px-4 py-2 font-mono text-xs text-gray-600">{{ row.account }}</td>
              <td class="px-4 py-2 text-gray-500">{{ row.class_names.length ? row.class_names.join('、') : '未分班' }}</td>
              <td class="px-4 py-2">
                <button class="text-indigo-600 hover:underline text-sm" @click="openView(row)">查看</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="px-4 py-2 border-t border-gray-100 text-sm text-gray-500 bg-gray-50">
          共 {{ items.length }} 名学生
        </div>
      </div>
    </div>

    <div v-if="showBatch" class="modal-mask">
      <div class="modal-box" style="width: 480px;">
        <h3 class="modal-title">批量添加学生</h3>
        <p class="modal-sub">每行一个姓名；账号自动生成 stu + 年份 + 三位序号</p>
        <div class="modal-field">
          <label class="modal-label">入学年份</label>
          <input v-model.number="batchYear" type="number" class="modal-input" min="2000" max="2100">
        </div>
        <div class="modal-field">
          <label class="modal-label">姓名列表 <span style="color:#ef4444">*</span></label>
          <textarea
            v-model="namesText"
            class="modal-input"
            rows="8"
            placeholder="张小明&#10;李小红&#10;王小华"
          />
        </div>
        <div v-if="batchError" class="modal-error show" style="margin-bottom: 12px;">{{ batchError }}</div>
        <div class="modal-actions">
          <button class="modal-btn-cancel" @click="closeBatch">取消</button>
          <button class="modal-btn-confirm" :disabled="batchSubmitting" @click="submitBatch">
            {{ batchSubmitting ? '创建中...' : '确认创建' }}
          </button>
        </div>
      </div>
    </div>

    <ViewStudentInfoModal
      v-if="viewTarget"
      :account="viewTarget.account"
      :real-name="viewTarget.real_name"
      :nickname="viewTarget.nickname"
      @close="viewTarget = null"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import ViewStudentInfoModal from '@/components/ViewStudentInfoModal.vue'
import { classApi } from '@/api/classes'
import { rosterApi } from '@/api/roster'
import type { ClassListItem } from '@/types/class'
import type { RosterStudentItem } from '@/types/roster'
import { toast } from '@/utils/toast'

const keyword = ref('')
const classes = ref<ClassListItem[]>([])
/** 空字符串表示「全部学生」；option value 均为字符串以兼容原生 select */
const selectedClassId = ref('')
const items = ref<RosterStudentItem[]>([])
const loading = ref(true)
const showBatch = ref(false)
const namesText = ref('')
const batchYear = ref(new Date().getFullYear())
const batchError = ref('')
const batchSubmitting = ref(false)
const viewTarget = ref<RosterStudentItem | null>(null)

const openView = (row: RosterStudentItem) => {
  viewTarget.value = row
}

const load = async () => {
  loading.value = true
  try {
    const classId = selectedClassId.value ? Number(selectedClassId.value) : undefined
    const data = await rosterApi.list(keyword.value.trim() || undefined, classId)
    items.value = data.items
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

const closeBatch = () => {
  showBatch.value = false
  batchError.value = ''
  namesText.value = ''
}

const submitBatch = async () => {
  batchError.value = ''
  const names = namesText.value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
  if (names.length === 0) {
    batchError.value = '请至少输入一个姓名'
    return
  }
  batchSubmitting.value = true
  try {
    const result = await rosterApi.batchCreate(names, batchYear.value)
    const accounts = result.created.map((c) => c.account).join('、')
    toast.success(`已创建 ${result.created.length} 人，初始密码 ${result.default_password}。账号：${accounts}`)
    closeBatch()
    await load()
  } catch (err) {
    batchError.value = err instanceof Error ? err.message : '创建失败'
  } finally {
    batchSubmitting.value = false
  }
}

useDebouncedWatch(keyword, () => {
  void load()
})

onMounted(async () => {
  try {
    classes.value = await classApi.list()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载班级列表失败，班级筛选不可用')
  }
  await load()
})
</script>
