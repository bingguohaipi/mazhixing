<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between flex-wrap gap-3">
      <div class="flex items-center gap-2">
        <h1 class="text-lg font-semibold text-gray-900">学情分析</h1>
        <div class="flex rounded-lg border border-gray-200 overflow-hidden text-sm">
          <button
            class="px-3 py-1.5"
            :class="activeTab === 'analytics' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
            @click="activeTab = 'analytics'"
          >
            学情数据
          </button>
          <button
            class="px-3 py-1.5"
            :class="activeTab === 'wrong-summary' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
            @click="switchToWrongSummary"
          >
            错题汇总
          </button>
          <button
            class="px-3 py-1.5"
            :class="activeTab === 'leaderboard' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
            @click="switchToLeaderboard"
          >
            班级排行榜
          </button>
        </div>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <ToolbarSelect
          v-model="selectedClassId"
          :options="classSelectOptions"
          wrapper-class="min-w-[140px]"
          @change="onClassChange"
        />
        <template v-if="activeTab === 'analytics' || activeTab === 'wrong-summary'">
          <ToolbarSelect
            v-model="selectedHomeworkId"
            :options="homeworkSelectOptions"
            wrapper-class="max-w-[180px] w-[180px]"
            @change="onFilterChange"
          />
          <ToolbarSelect
            v-model="period"
            :options="periodSelectOptions"
            @change="onFilterChange"
          />
          <button
            v-if="activeTab === 'analytics'"
            class="toolbar-field-light rounded-lg border border-gray-200 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50"
            :disabled="exporting"
            @click="handleExport"
          >
            {{ exporting ? '导出中...' : '导出报告' }}
          </button>
          <button
            v-if="activeTab === 'wrong-summary'"
            class="toolbar-field-light rounded-lg border border-gray-200 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50"
            :disabled="exportingWrong"
            @click="handleExportWrong"
          >
            {{ exportingWrong ? '导出中...' : '导出错题汇总' }}
          </button>
        </template>
      </div>
    </div>

    <div v-if="loading" class="p-6 text-center text-gray-500">加载中...</div>

    <div v-else-if="!selectedClassId" class="p-6 text-center text-gray-500">
      暂无班级数据，请先创建班级
    </div>

    <!-- 学情 Tab -->
    <div v-else-if="activeTab === 'analytics' && analytics" class="p-6 space-y-6">
      <div class="grid grid-cols-4 gap-4">
        <div class="bg-white rounded-xl p-5 border border-gray-100">
          <div class="text-sm text-gray-500 mb-1">作业完成率</div>
          <div class="text-3xl font-bold text-gray-900">{{ analytics.completion_rate }}%</div>
          <div class="text-xs text-gray-400 mt-1">班级 {{ analytics.student_count }} 人</div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100">
          <div class="text-sm text-gray-500 mb-1">平均正确率</div>
          <div class="text-3xl font-bold text-indigo-600">{{ analytics.average_accuracy }}%</div>
          <div class="text-xs text-gray-400 mt-1">不含补交数据</div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100">
          <div class="text-sm text-gray-500 mb-1">总提交次数</div>
          <div class="text-3xl font-bold text-gray-900">{{ analytics.total_submissions }}</div>
          <div class="text-xs text-gray-400 mt-1">有效提交</div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100">
          <div class="text-sm text-gray-500 mb-1">补交次数</div>
          <div class="text-3xl font-bold text-amber-500">{{ analytics.late_submission_count }}</div>
          <div class="text-xs text-gray-400 mt-1">单独统计</div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-6">
        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <h3 class="font-semibold text-gray-900 mb-4">知识点掌握分布</h3>
          <div v-if="analytics.knowledge_points.length === 0" class="text-sm text-gray-500 py-8 text-center">
            暂无做题记录
          </div>
          <KnowledgeBarChart v-else :items="analytics.knowledge_points" />
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-5">
          <div class="mb-4 flex items-baseline justify-between gap-2">
            <h3 class="font-semibold text-gray-900">每日提交趋势</h3>
            <span v-if="submissionTrend" class="text-xs text-gray-500">{{ trendGranularityHint }}</span>
          </div>
          <div v-if="trendLoading" class="py-16 text-center text-sm text-gray-500">加载中...</div>
          <TrendBarChart
            v-else-if="submissionTrend"
            :key="submissionTrend.range"
            :items="submissionTrend.items"
            :chart-type="submissionTrend.chart_type"
          />
          <div class="analytics-trend-range mt-4">
            <button
              v-for="opt in SUBMISSION_TREND_RANGE_OPTIONS"
              :key="opt.value"
              type="button"
              class="analytics-trend-range-btn"
              :class="{ 'is-active': trendRange === opt.value }"
              @click="onTrendRangeChange(opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <h3 class="font-semibold text-gray-900 mb-4">高频错题 TOP</h3>
        <div v-if="analytics.top_wrong_problems.length === 0" class="text-sm text-gray-500 py-6 text-center">
          太棒了，暂无错题
        </div>
        <table v-else class="w-full text-sm">
          <thead class="text-gray-500 border-b border-gray-100">
            <tr class="text-left">
              <th class="pb-2 font-medium">题目</th>
              <th class="pb-2 font-medium">知识点</th>
              <th class="pb-2 font-medium">错误次数</th>
              <th class="pb-2 font-medium w-24"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="item in analytics.top_wrong_problems" :key="item.problem_id">
              <td class="py-3">
                <button
                  type="button"
                  class="text-left text-indigo-600 hover:underline"
                  @click="openWrongCodes(item.problem_id, item.title)"
                >
                  #{{ item.problem_id }} {{ item.title }}
                </button>
              </td>
              <td class="py-3 text-gray-500">{{ item.knowledge_point || '-' }}</td>
              <td class="py-3 text-red-500 font-medium">{{ item.wrong_count }}</td>
              <td class="py-3 flex flex-wrap items-center gap-x-3 gap-y-1">
                <button type="button" class="text-indigo-600 hover:underline" @click="openProblemPreview(item.problem_id)">
                  查看题目
                </button>
                <button type="button" class="text-indigo-600 hover:underline" @click="openWrongCodes(item.problem_id, item.title)">
                  查看代码
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <h3 class="font-semibold text-gray-900 mb-4">需关注学生</h3>
        <div v-if="analytics.attention_students.length === 0" class="text-sm text-gray-500 py-6 text-center">
          暂无需要特别关注的学生
        </div>
        <table v-else class="w-full text-sm">
          <thead class="text-gray-500 border-b border-gray-100">
            <tr class="text-left">
              <th class="pb-2 font-medium">学生</th>
              <th class="pb-2 font-medium">近几次作业得分</th>
              <th class="pb-2 font-medium">薄弱知识点</th>
              <th class="pb-2 font-medium">建议</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="student in analytics.attention_students" :key="student.student_id">
              <td class="py-3">{{ student.student_name }}</td>
              <td class="py-3 text-red-500">{{ student.recent_scores }}</td>
              <td class="py-3">
                <span
                  v-for="point in student.weak_knowledge_points"
                  :key="point"
                  class="badge mr-1 bg-amber-100 text-amber-700"
                >
                  {{ point }}
                </span>
              </td>
              <td class="py-3 text-gray-500">{{ student.suggestion }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <h3 class="font-semibold text-gray-900 mb-1">学生提交统计</h3>
        <p class="text-xs text-gray-500 mb-4">按学生姓名汇总有效提交（不含补交；排除 CE）</p>
        <div v-if="!analytics.student_submission_stats?.length" class="text-sm text-gray-500 py-6 text-center">
          还没有做题记录，快去完成作业吧
        </div>
        <table v-else class="w-full text-sm">
          <thead class="text-gray-500 border-b border-gray-100">
            <tr class="text-left">
              <th class="pb-2 font-medium">学生</th>
              <th class="pb-2 font-medium">有效提交</th>
              <th class="pb-2 font-medium">AC</th>
              <th class="pb-2 font-medium">正确率</th>
              <th class="pb-2 font-medium">涉及题数</th>
              <th class="pb-2 font-medium">最近提交</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="(row, idx) in analytics.student_submission_stats" :key="idx">
              <td class="py-3 font-medium">{{ row.student_name }}</td>
              <td class="py-3">{{ row.submission_count }}</td>
              <td class="py-3 text-green-700">{{ row.ac_count }}</td>
              <td class="py-3">{{ row.accuracy_rate }}%</td>
              <td class="py-3">{{ row.problems_attempted }}</td>
              <td class="py-3 text-gray-500">
                {{ row.last_submitted_at ? formatTime(row.last_submitted_at) : '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="analytics.late_submission_stats?.length" class="bg-white rounded-xl border border-gray-100 p-5">
        <h3 class="font-semibold text-gray-900 mb-4">补交统计（按学生）</h3>
        <table class="w-full text-sm">
          <thead class="text-gray-500 border-b border-gray-100">
            <tr class="text-left">
              <th class="pb-2 font-medium">学生</th>
              <th class="pb-2 font-medium">补交次数</th>
              <th class="pb-2 font-medium">AC</th>
              <th class="pb-2 font-medium">正确率</th>
              <th class="pb-2 font-medium">涉及题数</th>
              <th class="pb-2 font-medium">最近提交</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="(row, idx) in analytics.late_submission_stats" :key="idx">
              <td class="py-3 font-medium">{{ row.student_name }}</td>
              <td class="py-3">{{ row.submission_count }}</td>
              <td class="py-3">{{ row.ac_count }}</td>
              <td class="py-3">{{ row.accuracy_rate }}%</td>
              <td class="py-3">{{ row.problems_attempted }}</td>
              <td class="py-3 text-gray-500">
                {{ row.last_submitted_at ? formatTime(row.last_submitted_at) : '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 错题汇总 Tab -->
    <div v-else-if="activeTab === 'wrong-summary' && wrongSummary" class="p-6 space-y-6">
      <div class="grid grid-cols-4 gap-4">
        <div class="bg-white rounded-xl p-5 border border-gray-100">
          <div class="text-sm text-gray-500 mb-1">错题提交总数</div>
          <div class="text-3xl font-bold text-red-500">{{ wrongSummary.total_wrong_submissions }}</div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100">
          <div class="text-sm text-gray-500 mb-1">涉及题目数</div>
          <div class="text-3xl font-bold text-gray-900">{{ wrongSummary.problem_count }}</div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100">
          <div class="text-sm text-gray-500 mb-1">班级人数</div>
          <div class="text-3xl font-bold text-gray-900">{{ wrongSummary.student_count }}</div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100">
          <div class="text-sm text-gray-500 mb-1">统计周期</div>
          <div class="text-xl font-bold text-indigo-600">{{ periodLabel }}</div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 p-4 flex flex-wrap gap-3 items-center">
        <ToolbarSelect
          v-model="wrongKnowledgeFilter"
          :options="wrongKnowledgeSelectOptions"
          placeholder="全部知识点"
          wrapper-class="max-w-xs"
          @change="loadWrongSummary"
        />
        <input
          v-model="wrongProblemKeyword"
          type="search"
          placeholder="搜索题目（题号或标题）"
          class="input-light-bg px-3 py-1.5 text-sm border border-gray-200 rounded-lg min-w-[200px] flex-1 max-w-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <input
          v-model="wrongStudentKeyword"
          type="search"
          placeholder="搜索学生真实姓名"
          class="input-light-bg px-3 py-1.5 text-sm border border-gray-200 rounded-lg min-w-[160px] flex-1 max-w-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <h3 class="font-semibold text-gray-900 mb-1">班级错题汇总</h3>
        <p class="text-xs text-gray-400 mb-4">统计周期内仍有错误且尚未 AC 的提交；已订正（AC）的不计入</p>
        <div v-if="wrongSummary.problems.length === 0" class="text-sm text-gray-500 py-8 text-center">
          太棒了，暂无错题
        </div>
        <div v-else-if="filteredWrongProblems.length === 0" class="text-sm text-gray-500 py-8 text-center">
          未找到匹配的错题或学生
        </div>
        <table v-else class="w-full text-sm">
          <thead class="text-gray-500 border-b border-gray-100">
            <tr class="text-left">
              <th class="pb-2 font-medium">题目</th>
              <th class="pb-2 font-medium">知识点</th>
              <th class="pb-2 font-medium">错误次数</th>
              <th class="pb-2 font-medium">涉及学生</th>
              <th class="pb-2 font-medium w-40"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <template v-for="item in filteredWrongProblems" :key="item.problem_id">
              <tr>
                <td class="py-3">
                  <button
                    type="button"
                    class="text-left text-indigo-600 hover:underline"
                    @click="openWrongCodes(item.problem_id, item.title)"
                  >
                    #{{ item.problem_id }} {{ item.title }}
                  </button>
                </td>
                <td class="py-3 text-gray-500">{{ item.knowledge_point || '-' }}</td>
                <td class="py-3 text-red-500 font-medium">{{ item.wrong_count }}</td>
                <td class="py-3">{{ visibleWrongStudents(item).length }} 人</td>
                <td class="py-3 flex flex-wrap items-center gap-x-3 gap-y-1">
                  <button
                    type="button"
                    class="text-indigo-600 hover:underline"
                    @click="toggleWrongProblemStudents(item.problem_id)"
                  >
                    {{ expandedWrongProblemIds.has(item.problem_id) ? '收起学生' : '查看学生' }}
                  </button>
                  <button type="button" class="text-indigo-600 hover:underline" @click="openProblemPreview(item.problem_id)">
                    查看题目
                  </button>
                  <button
                    type="button"
                    class="text-indigo-600 hover:underline"
                    @click="openWrongCodes(item.problem_id, item.title)"
                  >
                    查看代码
                  </button>
                </td>
              </tr>
              <tr v-if="expandedWrongProblemIds.has(item.problem_id)">
                <td colspan="5" class="pb-4 pt-0 px-0">
                  <div class="mx-3 rounded-lg border border-gray-100 bg-gray-50/80 overflow-hidden">
                    <table class="w-full text-xs">
                      <thead class="text-gray-500 border-b border-gray-100 bg-gray-50">
                        <tr class="text-left">
                          <th class="px-3 py-2 font-medium">真实姓名</th>
                          <th class="px-3 py-2 font-medium">展示名</th>
                          <th class="px-3 py-2 font-medium">错误次数</th>
                          <th class="px-3 py-2 font-medium">最近状态</th>
                          <th class="px-3 py-2 font-medium">最近错误时间</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-gray-100 bg-white">
                        <tr v-for="student in visibleWrongStudents(item)" :key="student.student_id">
                          <td class="px-3 py-2 font-medium text-gray-900">{{ student.real_name || '—' }}</td>
                          <td class="px-3 py-2 text-gray-600">{{ student.student_name }}</td>
                          <td class="px-3 py-2 text-red-500">{{ student.wrong_count }}</td>
                          <td class="px-3 py-2">{{ student.last_status }}</td>
                          <td class="px-3 py-2 text-gray-500">{{ formatTime(student.last_error_at) }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 排行榜 Tab -->
    <div v-else-if="activeTab === 'leaderboard' && leaderboard" class="p-6 space-y-6">
      <div class="bg-white rounded-xl border border-gray-100 p-4 text-sm text-gray-500">
        计分规则：正确率 × 70% + 相对耗时 × 30%；补交与错题不计入排名
      </div>
      <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500">
            <tr class="text-left">
              <th class="px-4 py-3 font-medium">排名</th>
              <th class="px-4 py-3 font-medium">学生昵称</th>
              <th class="px-4 py-3 font-medium">真实姓名</th>
              <th class="px-4 py-3 font-medium">完成题数</th>
              <th class="px-4 py-3 font-medium">正确率</th>
              <th class="px-4 py-3 font-medium">综合得分</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="entry in leaderboard.entries" :key="entry.student_id">
              <td class="px-4 py-3">
                <span class="font-bold" :class="entry.rank <= 3 ? 'text-amber-500' : 'text-gray-500'">
                  {{ entry.rank }}
                </span>
              </td>
              <td class="px-4 py-3 font-medium text-gray-900">{{ entry.nickname || '—' }}</td>
              <td class="px-4 py-3 text-gray-600">{{ entry.real_name || '—' }}</td>
              <td class="px-4 py-3 text-gray-600">{{ entry.completed_problems }}</td>
              <td class="px-4 py-3 text-gray-600">{{ entry.accuracy_rate }}%</td>
              <td class="px-4 py-3 font-semibold text-indigo-600">{{ entry.total_score }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="leaderboard.entries.length === 0" class="text-sm text-gray-500 py-12 text-center">
          暂无排名数据
        </div>
      </div>
    </div>

    <TeacherWrongCodeModal
      v-if="wrongCodeTarget && selectedClassId"
      :class-id="selectedClassId"
      :problem-id="wrongCodeTarget.problemId"
      :title="wrongCodeTarget.title"
      :period="period"
      :homework-id="selectedHomeworkId"
      @close="wrongCodeTarget = null"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import TeacherWrongCodeModal from '@/components/TeacherWrongCodeModal.vue'
import ToolbarSelect from '@/components/ToolbarSelect.vue'

const KnowledgeBarChart = defineAsyncComponent(
  () => import('@/components/charts/KnowledgeBarChart.vue'),
)
const TrendBarChart = defineAsyncComponent(
  () => import('@/components/charts/TrendBarChart.vue'),
)
import { usePageDwell } from '@/composables/usePageDwell'
import { analyticsApi } from '@/api/analytics'
import { classApi } from '@/api/classes'
import { homeworkApi } from '@/api/homework'
import { leaderboardApi } from '@/api/leaderboard'
import { toast } from '@/utils/toast'
import { trackEvent } from '@/utils/tracker'
import { formatShanghaiDateTime } from '@/utils/datetime'
import { SUBMISSION_TREND_RANGE_OPTIONS } from '@/constants/submission-trend-range'
import type {
  AnalyticsPeriod,
  ClassAnalytics,
  ClassWrongProblemDetail,
  ClassWrongSummary,
  SubmissionTrendRange,
  SubmissionTrendResponse,
  WrongSummaryStudentBrief,
} from '@/types/analytics'
import type { ClassListItem } from '@/types/class'
import type { HomeworkListItem } from '@/types/homework'
import type { LeaderboardResponse } from '@/types/leaderboard'

usePageDwell('analytics_dwell', '/teacher/analytics', 'teacher')

const router = useRouter()

const loading = ref(true)
const exporting = ref(false)
const exportingWrong = ref(false)
const activeTab = ref<'analytics' | 'wrong-summary' | 'leaderboard'>('analytics')
const classes = ref<ClassListItem[]>([])
const allHomeworks = ref<HomeworkListItem[]>([])
const selectedClassId = ref<number | null>(null)
const selectedHomeworkId = ref<number | null>(null)
const period = ref<AnalyticsPeriod>('week')
const analytics = ref<ClassAnalytics | null>(null)
const submissionTrend = ref<SubmissionTrendResponse | null>(null)
const trendRange = ref<SubmissionTrendRange>('7d')
const trendLoading = ref(false)
const wrongSummary = ref<ClassWrongSummary | null>(null)
const leaderboard = ref<LeaderboardResponse | null>(null)
const wrongKnowledgeFilter = ref('')
const wrongProblemKeyword = ref('')
const wrongStudentKeyword = ref('')
const expandedWrongProblemIds = ref<Set<number>>(new Set())
const wrongCodeTarget = ref<{ problemId: number; title: string } | null>(null)

const classHomeworks = computed(() => {
  if (!selectedClassId.value) return []
  return allHomeworks.value.filter((hw) => hw.class_ids.includes(selectedClassId.value!))
})

const classSelectOptions = computed(() =>
  classes.value.map((cls) => ({ value: cls.id, label: cls.name })),
)

const homeworkSelectOptions = computed(() => [
  { value: null, label: '全部作业' },
  ...classHomeworks.value.map((hw) => ({ value: hw.id, label: hw.title })),
])

const periodSelectOptions = [
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
  { value: 'semester', label: '本学期' },
] as const

const wrongKnowledgeSelectOptions = computed(() => [
  { value: '', label: '全部知识点' },
  ...wrongKnowledgeOptions.value.map((kp) => ({ value: kp, label: kp })),
])

const periodLabel = computed(() => {
  if (period.value === 'month') return '本月'
  if (period.value === 'semester') return '本学期'
  return '本周'
})

const trendGranularityHint = computed(() => {
  const granularity = submissionTrend.value?.granularity
  if (granularity === 'week') return '按周统计'
  if (granularity === 'month') return '按月统计'
  return '按日统计'
})

const wrongKnowledgeOptions = computed(() => {
  const set = new Set<string>()
  for (const item of wrongSummary.value?.problems ?? []) {
    if (item.knowledge_point) set.add(item.knowledge_point)
  }
  return [...set]
})

const wrongStudentMatches = (student: WrongSummaryStudentBrief, keyword: string): boolean => {
  const needle = keyword.trim().toLowerCase()
  if (!needle) return true
  const fields = [student.real_name, student.student_name].filter(Boolean) as string[]
  return fields.some((field) => field.toLowerCase().includes(needle))
}

const wrongProblemMatches = (item: ClassWrongProblemDetail): boolean => {
  const problemNeedle = wrongProblemKeyword.value.trim().toLowerCase()
  const studentNeedle = wrongStudentKeyword.value.trim().toLowerCase()

  const problemOk =
    !problemNeedle
    || item.title.toLowerCase().includes(problemNeedle)
    || String(item.problem_id).includes(problemNeedle)

  if (!studentNeedle) return problemOk

  const hasStudent = item.students.some((student) => wrongStudentMatches(student, studentNeedle))
  return problemOk && hasStudent
}

const filteredWrongProblems = computed(() =>
  (wrongSummary.value?.problems ?? []).filter((item) => wrongProblemMatches(item)),
)

const visibleWrongStudents = (item: ClassWrongProblemDetail): WrongSummaryStudentBrief[] => {
  const studentNeedle = wrongStudentKeyword.value.trim()
  if (!studentNeedle) return item.students
  return item.students.filter((student) => wrongStudentMatches(student, studentNeedle))
}

const toggleWrongProblemStudents = (problemId: number) => {
  const next = new Set(expandedWrongProblemIds.value)
  if (next.has(problemId)) {
    next.delete(problemId)
  } else {
    next.add(problemId)
  }
  expandedWrongProblemIds.value = next
}

const resetWrongSummaryFilters = () => {
  wrongProblemKeyword.value = ''
  wrongStudentKeyword.value = ''
  expandedWrongProblemIds.value = new Set()
}

const formatTime = (iso: string) => formatShanghaiDateTime(iso)

const loadSubmissionTrend = async () => {
  if (!selectedClassId.value) return
  trendLoading.value = true
  try {
    submissionTrend.value = await analyticsApi.getSubmissionTrend(
      selectedClassId.value,
      trendRange.value,
      selectedHomeworkId.value ?? undefined,
    )
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载提交趋势失败')
  } finally {
    trendLoading.value = false
  }
}

const onTrendRangeChange = async (range: SubmissionTrendRange) => {
  if (trendRange.value === range) return
  trendRange.value = range
  await loadSubmissionTrend()
}

const loadAnalytics = async () => {
  if (!selectedClassId.value) return
  loading.value = true
  try {
    const homeworkId = selectedHomeworkId.value ?? undefined
    const [analyticsData, trendData] = await Promise.all([
      analyticsApi.getClassAnalytics(selectedClassId.value, period.value, homeworkId),
      analyticsApi.getSubmissionTrend(selectedClassId.value, trendRange.value, homeworkId),
    ])
    analytics.value = analyticsData
    submissionTrend.value = trendData
    trackEvent({
      event_name: 'analytics_view',
      page: '/teacher/analytics',
      module: 'teacher',
      detail: `class=${selectedClassId.value},homework=${selectedHomeworkId.value ?? 'all'}`,
    })
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载学情失败')
  } finally {
    loading.value = false
  }
}

const loadWrongSummary = async () => {
  if (!selectedClassId.value) return
  loading.value = true
  expandedWrongProblemIds.value = new Set()
  try {
    wrongSummary.value = await analyticsApi.getClassWrongSummary(
      selectedClassId.value,
      period.value,
      selectedHomeworkId.value ?? undefined,
      wrongKnowledgeFilter.value || undefined,
    )
    trackEvent({
      event_name: 'wrong_summary_view',
      page: '/teacher/analytics',
      module: 'teacher',
      detail: `class=${selectedClassId.value}`,
    })
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载错题汇总失败')
  } finally {
    loading.value = false
  }
}

const loadLeaderboard = async () => {
  if (!selectedClassId.value) return
  loading.value = true
  try {
    leaderboard.value = await leaderboardApi.getClassForTeacher(selectedClassId.value)
    trackEvent({
      event_name: 'leaderboard_view',
      page: '/teacher/analytics',
      module: 'teacher',
      detail: `class=${selectedClassId.value}`,
    })
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载排行榜失败')
  } finally {
    loading.value = false
  }
}

const switchToWrongSummary = async () => {
  activeTab.value = 'wrong-summary'
  await loadWrongSummary()
}

const switchToLeaderboard = async () => {
  activeTab.value = 'leaderboard'
  await loadLeaderboard()
}

const onFilterChange = async () => {
  if (activeTab.value === 'wrong-summary') {
    await loadWrongSummary()
  } else {
    await loadAnalytics()
  }
}

const onClassChange = async () => {
  selectedHomeworkId.value = null
  wrongKnowledgeFilter.value = ''
  resetWrongSummaryFilters()
  if (activeTab.value === 'leaderboard') {
    await loadLeaderboard()
  } else if (activeTab.value === 'wrong-summary') {
    await loadWrongSummary()
  } else {
    await loadAnalytics()
  }
}

const openWrongCodes = (problemId: number, title: string) => {
  if (!selectedClassId.value) return
  wrongCodeTarget.value = { problemId, title }
}

const openProblemPreview = (problemId: number) => {
  void router.push(`/teacher/coding/${problemId}`)
}

const handleExportWrong = async () => {
  if (!selectedClassId.value) return
  exportingWrong.value = true
  try {
    const blob = await analyticsApi.exportWrongSummary(
      selectedClassId.value,
      period.value,
      selectedHomeworkId.value ?? undefined,
      wrongKnowledgeFilter.value || undefined,
    )
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `错题汇总_${wrongSummary.value?.class_name || '班级'}.csv`
    link.click()
    URL.revokeObjectURL(url)
    toast.success('错题汇总导出成功')
    trackEvent({
      event_name: 'wrong_summary_export',
      page: '/teacher/analytics',
      module: 'teacher',
      detail: `class=${selectedClassId.value}`,
    })
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '导出失败')
  } finally {
    exportingWrong.value = false
  }
}

const handleExport = async () => {
  if (!selectedClassId.value) return
  exporting.value = true
  try {
    const blob = await analyticsApi.exportReport(
      selectedClassId.value,
      period.value,
      selectedHomeworkId.value ?? undefined,
    )
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `学情报告_${analytics.value?.class_name || '班级'}.csv`
    link.click()
    URL.revokeObjectURL(url)
    toast.success('报告导出成功')
    trackEvent({
      event_name: 'analytics_export',
      page: '/teacher/analytics',
      module: 'teacher',
      detail: `class=${selectedClassId.value}`,
    })
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  try {
    const [classList, homeworkList] = await Promise.all([
      classApi.list(),
      homeworkApi.list(),
    ])
    classes.value = classList
    allHomeworks.value = homeworkList
    if (classes.value.length > 0) {
      selectedClassId.value = classes.value[0].id
      await loadAnalytics()
    } else {
      loading.value = false
    }
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载班级失败')
    loading.value = false
  }
})
</script>
