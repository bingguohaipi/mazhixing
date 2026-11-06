<template>
  <div
    v-if="open"
    class="practice-filter-popover absolute right-0 top-[calc(100%+6px)] z-50 w-[260px] border border-gray-200 bg-white p-3.5"
    role="dialog"
    aria-label="筛选班级"
    @click.stop
  >
    <div class="practice-filter-title">筛选</div>
    <div class="space-y-3">
      <label class="block">
        <span class="practice-filter-label">周几</span>
        <select v-model="draftWeekday" class="practice-filter-select">
          <option value="">全部</option>
          <option v-for="day in CLASS_WEEKDAYS" :key="day" :value="day">{{ day }}</option>
        </select>
      </label>
      <label class="block">
        <span class="practice-filter-label">编程语言</span>
        <select v-model="draftCourseType" class="practice-filter-select">
          <option value="">全部</option>
          <option v-for="lang in CLASS_COURSE_TYPES" :key="lang" :value="lang">{{ lang }}</option>
        </select>
      </label>
    </div>
    <div class="practice-filter-footer">
      <button type="button" class="practice-filter-btn-reset" @click="emit('reset')">重置</button>
      <button type="button" class="practice-filter-btn-apply" @click="emitApply">应用</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { CLASS_COURSE_TYPES } from '@/constants/class-course'
import { CLASS_WEEKDAYS } from '@/constants/class-weekday'

const props = defineProps<{
  open: boolean
  weekday: string
  courseType: string
}>()

const emit = defineEmits<{
  apply: [payload: { weekday: string; courseType: string }]
  reset: []
}>()

const draftWeekday = ref('')
const draftCourseType = ref('')

const syncDraftFromProps = () => {
  draftWeekday.value = props.weekday
  draftCourseType.value = props.courseType
}

watch(
  () => props.open,
  (open) => {
    if (open) syncDraftFromProps()
  },
)

const emitApply = () => {
  emit('apply', {
    weekday: draftWeekday.value,
    courseType: draftCourseType.value,
  })
}
</script>
