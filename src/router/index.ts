import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/auth'
import { trackError, trackPageView } from '@/utils/tracker'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: UserRole[]
    guestOnly?: boolean
    title?: string
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginPage.vue'),
    meta: { guestOnly: true, title: '登录' },
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    children: [
      { path: '', redirect: () => {
        const auth = useAuthStore()
        return auth.isAuthenticated ? auth.homeRoute : '/login'
      }},
      {
        path: 'teacher/dashboard',
        name: 'teacher-dashboard',
        component: () => import('@/views/teacher/Dashboard.vue'),
        meta: { requiresAuth: true, roles: ['teacher'], title: '教师工作台' },
      },
      {
        path: 'teacher/questions',
        name: 'teacher-questions',
        component: () => import('@/views/teacher/Question.vue'),
        meta: { requiresAuth: true, roles: ['teacher'], title: '公共题库' },
      },
      {
        path: 'teacher/my-questions',
        name: 'teacher-my-questions',
        component: () => import('@/views/teacher/MyQuestions.vue'),
        meta: { requiresAuth: true, roles: ['teacher'], title: '自有题库' },
      },
      {
        path: 'teacher/coding/:problemId',
        name: 'teacher-coding',
        component: () => import('@/views/student/Coding.vue'),
        meta: { requiresAuth: true, roles: ['teacher'], title: '题目预览' },
      },
      {
        path: 'teacher/homework',
        name: 'teacher-homework',
        component: () => import('@/views/teacher/Homework.vue'),
        meta: { requiresAuth: true, roles: ['teacher'], title: '作业管理' },
      },
      {
        path: 'teacher/roster',
        name: 'teacher-roster',
        component: () => import('@/views/teacher/StudentRoster.vue'),
        meta: { requiresAuth: true, roles: ['teacher'], title: '学生名单' },
      },
      {
        path: 'teacher/classes',
        name: 'teacher-classes',
        component: () => import('@/views/teacher/Class.vue'),
        meta: { requiresAuth: true, roles: ['teacher'], title: '班级管理' },
      },
      {
        path: 'teacher/classes/create',
        name: 'teacher-create-class',
        component: () => import('@/views/teacher/CreateClass.vue'),
        meta: { requiresAuth: true, roles: ['teacher'], title: '创建班级' },
      },
      {
        path: 'teacher/classes/:id',
        name: 'teacher-class-detail',
        component: () => import('@/views/teacher/ClassDetail.vue'),
        meta: { requiresAuth: true, roles: ['teacher'], title: '班级详情' },
      },
      {
        path: 'teacher/analytics',
        name: 'teacher-analytics',
        component: () => import('@/views/teacher/Analytics.vue'),
        meta: { requiresAuth: true, roles: ['teacher'], title: '学情分析' },
      },
      {
        path: 'teacher/profile',
        name: 'teacher-profile',
        component: () => import('@/views/teacher/Profile.vue'),
        meta: { requiresAuth: true, roles: ['teacher'], title: '个人中心' },
      },
      {
        path: 'teacher/students',
        name: 'teacher-students',
        redirect: '/teacher/roster',
      },
      {
        path: 'teacher/export',
        redirect: '/teacher/dashboard',
      },
      {
        path: 'teacher/prep-tools',
        redirect: '/teacher/dashboard',
      },
      {
        path: 'admin/dashboard',
        name: 'admin-dashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { requiresAuth: true, roles: ['admin'], title: '管理后台' },
      },
      {
        path: 'admin/users',
        name: 'admin-users',
        component: () => import('@/views/admin/Users.vue'),
        meta: { requiresAuth: true, roles: ['admin'], title: '用户管理' },
      },
      {
        path: 'admin/public-problems',
        name: 'admin-public-problems',
        component: () => import('@/views/admin/PublicProblems.vue'),
        meta: { requiresAuth: true, roles: ['admin'], title: '公共题库' },
      },
      {
        path: 'admin/coding/:problemId',
        name: 'admin-coding',
        component: () => import('@/views/student/Coding.vue'),
        meta: { requiresAuth: true, roles: ['admin'], title: '题目预览' },
      },
      {
        path: 'admin/suggestions',
        name: 'admin-suggestions',
        component: () => import('@/views/SuggestionsPage.vue'),
        meta: { requiresAuth: true, roles: ['admin'], title: '建议中心' },
      },
      {
        path: 'admin/suggestions/:id',
        name: 'admin-suggestion-detail',
        component: () => import('@/views/SuggestionDetailPage.vue'),
        meta: { requiresAuth: true, roles: ['admin'], title: '留言详情' },
      },
      {
        path: 'admin/pet-shop',
        name: 'admin-pet-shop',
        component: () => import('@/views/admin/PetShop.vue'),
        meta: { requiresAuth: true, roles: ['admin'], title: '宠物商城配置' },
      },
      {
        path: 'admin/knowledge-points',
        name: 'admin-knowledge-points',
        component: () => import('@/views/admin/KnowledgePoints.vue'),
        meta: { requiresAuth: true, roles: ['admin'], title: '知识点管理' },
      },
      {
        path: 'suggestions',
        name: 'suggestions',
        component: () => import('@/views/SuggestionsPage.vue'),
        meta: { requiresAuth: true, roles: ['teacher', 'student', 'parent', 'admin'], title: '建议' },
      },
      {
        path: 'suggestions/:id',
        name: 'suggestion-detail',
        component: () => import('@/views/SuggestionDetailPage.vue'),
        meta: { requiresAuth: true, roles: ['teacher', 'student', 'parent', 'admin'], title: '留言详情' },
      },
      {
        path: 'student/dashboard',
        name: 'student-dashboard',
        component: () => import('@/views/student/Dashboard.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '学生工作台' },
      },
      {
        path: 'student/questions',
        name: 'student-questions',
        component: () => import('@/views/student/Questions.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '题库' },
      },
      {
        path: 'student/questions/topic/:slug',
        name: 'student-question-topic',
        component: () => import('@/views/student/QuestionTopic.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '知识点练习' },
      },
      {
        path: 'student/homework/:id',
        name: 'student-homework-detail',
        component: () => import('@/views/student/HomeworkDetail.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '作业详情' },
      },
      {
        path: 'student/coding/:problemId',
        name: 'student-coding',
        component: () => import('@/views/student/Coding.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '在线做题' },
      },
      {
        path: 'student/wrong',
        name: 'student-wrong',
        component: () => import('@/views/student/Wrong.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '错题本' },
      },
      {
        path: 'student/leaderboard',
        name: 'student-leaderboard',
        component: () => import('@/views/student/Leaderboard.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '班级排行榜' },
      },
      {
        path: 'student/arena',
        name: 'student-arena',
        component: () => import('@/views/student/Arena.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '擂台' },
      },
      {
        path: 'student/arena/problems/:problemId',
        name: 'student-arena-problem',
        component: () => import('@/views/student/ArenaProblem.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '擂台详情' },
      },
      {
        path: 'student/analytics',
        name: 'student-analytics',
        component: () => import('@/views/student/Analytics.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '个人学情' },
      },
      {
        path: 'student/profile',
        name: 'student-profile',
        component: () => import('@/views/student/Profile.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '个人中心' },
      },
      {
        path: 'student/pet-shop',
        name: 'student-pet-shop',
        component: () => import('@/views/student/PetShop.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '宠物商城' },
      },
      {
        path: 'student/points',
        name: 'student-points',
        component: () => import('@/views/student/Points.vue'),
        meta: { requiresAuth: true, roles: ['student'], title: '积分明细' },
      },
      {
        path: 'parent',
        component: () => import('@/layouts/ParentLayout.vue'),
        meta: { requiresAuth: true, roles: ['parent'] },
        children: [
          { path: '', redirect: { name: 'parent-overview' } },
          {
            path: 'overview',
            name: 'parent-overview',
            component: () => import('@/views/parent/Overview.vue'),
            meta: { requiresAuth: true, roles: ['parent'], title: '学情总览' },
          },
          {
            path: 'trends',
            name: 'parent-trends',
            component: () => import('@/views/parent/Trends.vue'),
            meta: { requiresAuth: true, roles: ['parent'], title: '学习趋势' },
          },
          {
            path: 'weak-points',
            name: 'parent-weak-points',
            component: () => import('@/views/parent/WeakPoints.vue'),
            meta: { requiresAuth: true, roles: ['parent'], title: '薄弱知识点' },
          },
          {
            path: 'wrong-top',
            name: 'parent-wrong-top',
            component: () => import('@/views/parent/WrongTop.vue'),
            meta: { requiresAuth: true, roles: ['parent'], title: '高频错题' },
          },
          {
            path: 'wrong-book',
            name: 'parent-wrong-book',
            component: () => import('@/views/parent/WrongBook.vue'),
            meta: { requiresAuth: true, roles: ['parent'], title: '子女错题' },
          },
          {
            path: 'profile',
            name: 'parent-profile',
            component: () => import('@/views/parent/Profile.vue'),
            meta: { requiresAuth: true, roles: ['parent'], title: '个人中心' },
          },
        ],
      },
      {
        path: 'parent/dashboard',
        redirect: '/parent/overview',
      },
    ],
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@/views/ForbiddenPage.vue'),
    meta: { title: '无权限' },
  },
  {
    path: '/network-error',
    name: 'network-error',
    component: () => import('@/views/NetworkErrorPage.vue'),
    meta: { title: '网络异常' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundPage.vue'),
    meta: { title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (auth.user === null && localStorage.getItem('mzx_access_token')) {
    await auth.fetchMe()
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return auth.homeRoute
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (to.meta.roles && auth.role && !to.meta.roles.includes(auth.role)) {
    trackError('forbidden_access', `path=${to.fullPath},role=${auth.role}`, to.path)
    return '/403'
  }

  return true
})

router.afterEach((to) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 码智星`
  }
  if (to.name && to.name !== 'login') {
    trackPageView(to.path, to.meta.roles?.[0])
  }
})

export default router
