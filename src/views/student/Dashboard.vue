<template>
  <div>
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <h1 class="text-lg font-semibold text-gray-900">我的工作台</h1>
        <span class="badge bg-green-100 text-green-700">学生端</span>
      </div>
      <div class="flex items-center gap-3">
        <div v-if="overview?.class_rank" class="text-sm text-gray-500">
          班级排名：<span class="font-bold text-indigo-600">第{{ overview.class_rank }}名</span>
        </div>
        <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-sm font-medium text-blue-700">
          {{ auth.displayName.charAt(0) }}
        </div>
      </div>
    </div>

    <div v-if="loading" class="p-6 text-center text-gray-500">加载中...</div>

    <div v-else-if="overview" class="p-6 space-y-6">
      <div class="grid grid-cols-4 gap-4">
        <div class="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-5 text-white">
          <div class="text-sm opacity-80 mb-1">已完成题目</div>
          <div class="text-3xl font-bold">{{ overview.completed_problems }}</div>
          <div class="text-xs opacity-70 mt-1">本周 +{{ overview.week_new_problems }}</div>
        </div>
        <div class="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-5 text-white">
          <div class="text-sm opacity-80 mb-1">正确率</div>
          <div class="text-3xl font-bold">{{ overview.accuracy }}%</div>
          <div class="text-xs opacity-70 mt-1">班级平均 {{ overview.class_avg_accuracy }}%</div>
        </div>
        <div class="bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl p-5 text-white">
          <div class="text-sm opacity-80 mb-1">连续打卡</div>
          <div class="text-3xl font-bold">{{ overview.streak_days }}天</div>
          <div class="text-xs opacity-70 mt-1">继续保持</div>
        </div>
        <div class="bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl p-5 text-white">
          <div class="text-sm opacity-80 mb-1">待复习错题</div>
          <div class="text-3xl font-bold">{{ overview.wrong_pending_count }}</div>
          <div class="text-xs opacity-70 mt-1">点击查看错题本</div>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-6">
        <div class="col-span-2 space-y-6">
          <div class="bg-white rounded-xl border border-gray-100 p-5">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-gray-900">待完成作业</h3>
              <span class="badge bg-amber-100 text-amber-700">{{ pendingHomework.length }}份待交</span>
            </div>
            <div v-if="pendingHomework.length === 0" class="text-center py-6 text-gray-500 text-sm">
              暂无作业，请等待老师布置
            </div>
            <div v-else class="dashboard-panel-scroll dashboard-panel-scroll--homework space-y-3">
              <div
                v-for="hw in pendingHomework"
                :key="hw.id"
                class="flex items-center justify-between p-3 rounded-lg"
                :class="hw.progress ? 'bg-amber-50 border border-amber-100' : 'bg-gray-50'"
              >
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-gray-900">{{ hw.title }}</span>
                    <span
                      v-if="hw.has_unread_update"
                      class="badge bg-indigo-100 text-indigo-700 text-xs"
                    >
                      有更新
                    </span>
                  </div>
                  <div class="text-sm text-gray-500 mt-0.5">
                    {{ hw.class_name }} · {{ hw.problem_count }}道题 · {{ hw.progress || '未开始' }}
                  </div>
                </div>
                <div class="text-right">
                  <div class="text-sm font-medium" :class="hw.progress ? 'text-amber-600' : 'text-gray-500'">
                    {{ formatDeadline(hw.end_time) }}
                  </div>
                  <button
                    class="mt-1 px-3 py-1 bg-indigo-600 text-white text-xs rounded-lg"
                    @click="router.push(`/student/homework/${hw.id}`)"
                  >
                    {{ hw.progress && !hw.progress.startsWith('0/') ? '继续做' : '开始做' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl border border-gray-100 p-5">
            <h3 class="font-semibold text-gray-900 mb-4">我的学习进度</h3>
            <div v-if="overview.knowledge_progress.length === 0" class="text-sm text-gray-500 py-6 text-center">
              还没有做题记录，快去完成作业吧
            </div>
            <div v-else class="space-y-3">
              <div v-for="progress in overview.knowledge_progress" :key="progress.name">
                <div class="flex justify-between text-sm mb-1">
                  <span>{{ progress.name }}</span>
                  <span :class="getStatusClass(progress.status)">{{ progress.status }}</span>
                </div>
                <div class="student-kp-progress-track">
                  <div
                    class="student-kp-progress-fill"
                    :style="{ width: progress.mastery_rate + '%' }"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="bg-white rounded-xl border border-gray-100 p-5">
            <h3 class="font-semibold text-gray-900 mb-3">我的小伙伴</h3>
            <div v-if="petStore.activePet" class="space-y-3">
              <div class="flex items-center gap-3">
                <button
                  type="button"
                  class="shrink-0 rounded-xl hover:bg-gray-50 p-1 transition cursor-pointer"
                  title="点击逗小伙伴玩"
                  @click="playWithPet"
                >
                  <PetAvatar
                    :key="playFxKey"
                    :asset-key="petStore.activePet.asset_key"
                    :size="72"
                    :level="petStore.activePet.level"
                    :state-hint="petStore.activePet.state_hint"
                    :interaction="playReaction"
                    show-stage-label
                  />
                </button>
                <div class="flex-1 min-w-0">
                  <div class="font-medium text-gray-900">{{ petStore.activePet.name }}</div>
                  <div class="text-xs text-gray-500">Lv.{{ petStore.activePet.level }} · 点击头像互动</div>
                </div>
              </div>
              <div>
                <div class="flex justify-between text-xs text-gray-500 mb-1"><span>饱食</span><span>{{ petStore.activePet.satiety }}</span></div>
                <div class="h-1.5 bg-gray-100 rounded-full"><div class="h-full bg-amber-400 rounded-full" :style="{ width: petStore.activePet.satiety + '%' }" /></div>
              </div>
              <div>
                <div class="flex justify-between text-xs text-gray-500 mb-1"><span>心情</span><span>{{ petStore.activePet.mood }}</span></div>
                <div class="h-1.5 bg-gray-100 rounded-full"><div class="h-full bg-pink-400 rounded-full" :style="{ width: petStore.activePet.mood + '%' }" /></div>
              </div>
              <div>
                <div class="flex justify-between text-xs text-gray-500 mb-1"><span>经验</span><span>{{ petStore.activePet.exp }}/{{ petStore.activePet.exp_to_next || '满' }}</span></div>
                <div class="h-1.5 bg-gray-100 rounded-full"><div class="h-full bg-indigo-500 rounded-full" :style="{ width: expPercent }" /></div>
              </div>
              <RouterLink to="/student/pet-shop" class="block text-center text-sm py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">去喂养</RouterLink>
            </div>
            <div v-else class="text-center py-4 text-sm text-gray-500">
              <p class="mb-3">还没有小伙伴，完成题目赚积分去领养吧</p>
              <RouterLink to="/student/pet-shop" class="inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm">去商城</RouterLink>
            </div>
            <p v-if="petStore.settings && !petStore.settings.desktop_pet_enabled" class="text-xs text-gray-400 mt-3 text-center">
              桌面伙伴已隐藏，可在个人中心开启
            </p>
          </div>

          <NoticeFeedPanel />

          <div class="bg-white rounded-xl border border-gray-100 p-5">
            <h3 class="font-semibold text-gray-900 mb-4">错题本</h3>
            <div class="text-center mb-4">
              <div class="text-4xl font-bold text-red-500">{{ overview.wrong_pending_count }}</div>
              <div class="text-sm text-gray-500">道待复习</div>
            </div>
            <button
              class="w-full py-2 text-sm text-indigo-600 border border-indigo-200 rounded-lg hover:bg-indigo-50"
              @click="router.push('/student/wrong')"
            >
              去复习 →
            </button>
          </div>

          <div class="bg-white rounded-xl border border-gray-100 p-5">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-gray-900">班级排行榜</h3>
              <button class="text-xs text-indigo-600 hover:underline" @click="router.push('/student/leaderboard')">
                查看全部
              </button>
            </div>
            <div v-if="overview.leaderboard_preview.length === 0" class="text-sm text-gray-500 text-center py-4">
              暂无排名
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="rank in overview.leaderboard_preview"
                :key="rank.student_id"
                class="flex items-center gap-2 text-sm"
                :class="rank.is_me ? 'leaderboard-me-row p-1.5 rounded-lg' : ''"
              >
                <span class="w-5 font-bold" :class="rank.is_me ? 'text-indigo-600' : rank.rank === 1 ? 'text-amber-500' : 'text-gray-400'">
                  {{ rank.rank }}
                </span>
                <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs bg-blue-100 text-blue-700">
                  {{ rank.display_name.charAt(0) }}
                </div>
                <span class="flex-1" :class="rank.is_me ? 'font-medium' : ''">
                  {{ rank.display_name }}
                  <span v-if="rank.is_me" class="text-xs text-gray-500">（我）</span>
                </span>
                <span class="text-gray-500">{{ rank.completed_problems }}题</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { usePetPlay } from '@/composables/usePetPlay'
import { usePetStore } from '@/stores/pet'
import { useRouter } from 'vue-router'
import NoticeFeedPanel from '@/components/NoticeFeedPanel.vue'
import { homeworkApi } from '@/api/homework'
import { studentDashboardApi } from '@/api/student-dashboard'
import { useAuthStore } from '@/stores/auth'
import type { StudentHomeworkItem } from '@/types/homework'
import type { StudentDashboardOverview } from '@/types/student-dashboard'

const router = useRouter()
const auth = useAuthStore()
const petStore = usePetStore()
const { playReaction, playFxKey, playWithPet } = usePetPlay()

const expPercent = computed(() => {
  const p = petStore.activePet
  if (!p || !p.exp_to_next) return '100%'
  return `${Math.min(100, Math.round((p.exp / p.exp_to_next) * 100))}%`
})

const loading = ref(true)
const overview = ref<StudentDashboardOverview | null>(null)
const allHomework = ref<StudentHomeworkItem[]>([])

const pendingHomework = computed(() =>
  allHomework.value.filter((hw) => hw.status === '进行中' || hw.status === '未开始'),
)

const formatDeadline = (iso: string) => {
  const date = new Date(iso)
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadData = async () => {
  loading.value = true
  try {
    const [dashboard, homework] = await Promise.all([
      studentDashboardApi.getOverview(),
      homeworkApi.listMy().catch(() => [] as StudentHomeworkItem[]),
    ])
    overview.value = dashboard
    allHomework.value = homework
  } catch {
    overview.value = null
    allHomework.value = []
  } finally {
    loading.value = false
  }
}

const getStatusClass = (status: string) => {
  if (status === '已掌握') return 'text-green-600'
  if (status === '学习中') return 'text-amber-600'
  return 'text-gray-400'
}

onMounted(() => {
  void petStore.bootstrap()
  void loadData()
})
</script>
