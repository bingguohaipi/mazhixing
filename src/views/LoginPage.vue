<template>
  <div class="login-dark" ref="loginContainer" @mousemove="handleMouseMove" @mouseleave="handleMouseLeave">
    <!-- 星星背景 -->
    <span v-for="(star, idx) in stars" :key="idx" class="star" :style="star.style">{{ star.keyword }}</span>
    
    <div class="login-card" ref="loginCard">
      <div class="logo-row">
        <div class="logo-icon">码</div>
        <span class="brand-name">码智星</span>
      </div>

      <!-- 步骤1：选择身份 -->
      <div v-if="authStep === 'select'">
        <h2 class="role-select-title">请选择身份</h2>
        <div class="role-card" :class="{ selected: selectedRole === 'teacher' }" @click="selectRole('teacher')">
          <span class="role-icon">👨‍🏫</span>
          <div class="role-info">
            <div class="role-name">教师</div>
            <div class="role-desc">题库管理 · 作业布置 · 学情分析</div>
          </div>
          <span class="role-arrow">›</span>
        </div>
        <div class="role-card" :class="{ selected: selectedRole === 'student' }" @click="selectRole('student')">
          <span class="role-icon">🧑‍💻</span>
          <div class="role-info">
            <div class="role-name">学生</div>
            <div class="role-desc">在线做题 · 沙箱判题 · 错题本</div>
          </div>
          <span class="role-arrow">›</span>
        </div>
        <div class="role-card" :class="{ selected: selectedRole === 'parent' }" @click="selectRole('parent')">
          <span class="role-icon">👨‍👩‍👧</span>
          <div class="role-info">
            <div class="role-name">家长</div>
            <div class="role-desc">学情概览 · 学习报告 · 家校互通</div>
          </div>
          <span class="role-arrow">›</span>
        </div>
        <div class="role-card" :class="{ selected: selectedRole === 'admin' }" @click="selectRole('admin')">
          <span class="role-icon">🛡️</span>
          <div class="role-info">
            <div class="role-name">管理员</div>
            <div class="role-desc">公共题库 · 用户管理 · 建议中心</div>
          </div>
          <span class="role-arrow">›</span>
        </div>
      </div>

      <!-- 步骤2：登录/注册表单 -->
      <div v-else style="min-height: 400px;">
        <button class="back-btn" @click="backToRoleSelect">← 返回选择身份</button>
        <h2 class="login-title">{{ currentRoleMeta.name }}登录</h2>
        <p class="login-subtitle">
          {{ selectedRole === 'student' ? '使用老师分配的账号登录，昵称可在个人中心设置' : '欢迎回到码智星' }}
        </p>

        <!-- Tab：学生不显示注册 -->
        <div class="tab-row" v-if="currentRoleMeta.canRegister">
          <button :class="{ active: authTab === 'login' }" @click="switchAuthTab('login')">登录</button>
          <button :class="{ active: authTab === 'register' }" @click="switchAuthTab('register')">注册</button>
        </div>

        <!-- 登录表单 -->
        <div v-if="authTab === 'login'">
          <div class="form-group">
            <label class="form-label">{{ currentRoleMeta.loginField }}</label>
            <input
              :type="selectedRole === 'teacher' || selectedRole === 'parent' ? 'tel' : 'text'"
              class="form-input"
              :class="{ error: loginErrors.field1 }"
              v-model="loginForm.field1"
              :placeholder="currentRoleMeta.loginPlaceholder"
              @blur="validateLoginField('field1')"
              @input="clearLoginError('field1')"
            >
            <div class="form-error" :class="{ show: loginErrors.field1 }">{{ loginErrors.field1Msg }}</div>
          </div>
          <div class="form-group">
            <label class="form-label">密码</label>
            <PasswordInput
              v-model="loginForm.field2"
              input-class="form-input"
              :has-error="loginErrors.field2"
              :placeholder="selectedRole === 'student' ? '请输入密码（默认123456）' : '请输入密码'"
              autocomplete="current-password"
              @blur="validateLoginField('field2')"
              @update:model-value="clearLoginError('field2')"
            />
            <div class="form-error" :class="{ show: loginErrors.field2 }">{{ loginErrors.field2Msg }}</div>
          </div>
          <div class="student-hint" v-if="selectedRole === 'student'">
            💡 账号由老师分配，初始密码 <b>123456</b>。登录后可在<b>个人中心</b>修改昵称（需文明用语）、头像与密码。
          </div>
          <div class="flex items-center justify-between text-xs mb-4">
            <label class="flex items-center gap-1.5 text-gray-400 cursor-pointer">
              <input type="checkbox" v-model="rememberMe" class="rounded"> 记住我
            </label>
            <a href="#" class="text-indigo-400 hover:text-indigo-300" v-if="selectedRole === 'teacher' || selectedRole === 'parent'" @click.prevent="showForgotPwdModal = true">忘记密码？</a>
          </div>
          <button class="login-btn" :disabled="submitting" @click="doLogin">{{ submitting ? '登录中...' : '登 录' }}</button>
          <div v-if="formError" class="form-error show" style="margin-top: 12px; text-align: center;">{{ formError }}</div>
        </div>

        <!-- 注册表单 -->
        <div v-if="authTab === 'register' && currentRoleMeta.canRegister">
          <div class="form-group">
            <label class="form-label">手机号</label>
            <input type="tel" class="form-input" :class="{ error: registerErrors.phone }" v-model="registerForm.phone" :placeholder="`请输入${currentRoleMeta.name}手机号码`" @blur="validateRegField('phone')" @input="clearRegError('phone')">
            <div class="form-error" :class="{ show: registerErrors.phone }">{{ registerErrors.phoneMsg }}</div>
          </div>
          <div class="form-group">
            <label class="form-label">验证码</label>
            <div class="code-row">
              <input type="text" class="form-input" :class="{ error: registerErrors.code }" v-model="registerForm.code" placeholder="请输入6位验证码" @blur="validateRegField('code')" @input="clearRegError('code')">
              <button class="code-btn" @click="sendCode" :disabled="codeCountdown > 0">{{ codeCountdown > 0 ? `${codeCountdown}s后重发` : '获取验证码' }}</button>
            </div>
            <div class="form-error" :class="{ show: registerErrors.code }">{{ registerErrors.codeMsg }}</div>
          </div>
          <div class="form-group">
            <label class="form-label">设置密码</label>
            <PasswordInput
              v-model="registerForm.pwd"
              input-class="form-input"
              :has-error="registerErrors.pwd"
              placeholder="6-20位，包含字母和数字"
              autocomplete="new-password"
              @blur="validateRegField('pwd')"
              @update:model-value="clearRegError('pwd')"
            />
            <div class="form-error" :class="{ show: registerErrors.pwd }">{{ registerErrors.pwdMsg }}</div>
          </div>
          <div class="form-group">
            <label class="form-label">确认密码</label>
            <PasswordInput
              v-model="registerForm.pwd2"
              input-class="form-input"
              :has-error="registerErrors.pwd2"
              placeholder="请再次输入密码"
              autocomplete="new-password"
              @blur="validateRegField('pwd2')"
              @update:model-value="clearRegError('pwd2')"
            />
            <div class="form-error" :class="{ show: registerErrors.pwd2 }">{{ registerErrors.pwd2Msg }}</div>
          </div>
          <button class="login-btn" :disabled="submitting" @click="doRegister">{{ submitting ? '注册中...' : '注 册' }}</button>
          <div v-if="formError" class="form-error show" style="margin-top: 12px; text-align: center;">{{ formError }}</div>
        </div>
      </div>

      <p class="footer-text">登录即同意 <a href="#">《用户服务协议》</a> 和 <a href="#">《隐私政策》</a></p>
    </div>

    <ForgotPwdModal
      v-if="showForgotPwdModal"
      :role="selectedRole === 'parent' ? 'parent' : 'teacher'"
      @close="showForgotPwdModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import ForgotPwdModal from '@/components/ForgotPwdModal.vue'
import PasswordInput from '@/components/PasswordInput.vue'

const router = useRouter()
const authStore = useAuthStore()

const showForgotPwdModal = ref(false)

const loginContainer = ref<HTMLElement | null>(null)
const loginCard = ref<HTMLElement | null>(null)
const authStep = ref<'select' | 'form'>('select')
const selectedRole = ref<'teacher' | 'student' | 'parent' | 'admin'>('teacher')
const authTab = ref<'login' | 'register'>('login')
const rememberMe = ref(false)
const codeCountdown = ref(0)
const submitting = ref(false)
const formError = ref('')

const roleMeta = reactive({
  teacher: { name: '教师', loginField: '手机号', loginPlaceholder: '请输入教师注册手机号', canRegister: true },
  student: { name: '学生', loginField: '账号', loginPlaceholder: '请输入老师分配的账号（如 stu2024001）', canRegister: false },
  parent: { name: '家长', loginField: '手机号', loginPlaceholder: '请输入家长注册手机号', canRegister: true },
  admin: { name: '管理员', loginField: '账号', loginPlaceholder: '请输入管理员账号', canRegister: false },
})

// 当前角色的元数据
const currentRoleMeta = computed(() => roleMeta[selectedRole.value])

const loginFieldUsesPhone = computed(
  () => selectedRole.value === 'teacher' || selectedRole.value === 'parent',
)

const loginForm = reactive({ field1: '', field2: '' })
const loginErrors = reactive({ field1: false, field1Msg: '', field2: false, field2Msg: '' })

const registerForm = reactive({ phone: '', code: '', pwd: '', pwd2: '' })
const registerErrors = reactive({ phone: false, phoneMsg: '', code: false, codeMsg: '', pwd: false, pwdMsg: '', pwd2: false, pwd2Msg: '' })

// ===== 星星背景动画 =====
interface StarData {
  keyword: string
  style: any
  baseX: number
  baseY: number
  swaySpeed: number
  swayAmpX: number
  swayAmpY: number
  phase: number
  fontSize: number
  opacity: number
  curX: number
  curY: number
  attractUntil: number
}

const stars = ref<StarData[]>([])
let animationId: number | null = null
let time = 0
let mouseX = -9999
let mouseY = -9999
let hasMouse = false

const ATTRACT_RADIUS = 120
const ATTRACT_STRENGTH = 0.12
const FOLLOW_DURATION = 1000

const KEYWORDS = [
  'def','class','import','from','return','if','else','elif','for','while',
  'try','except','with','as','lambda','yield','print','True','False','None',
  'self','in','not','and','or','is','global','pass','break','continue',
  'range','len','int','str','list','dict','set','tuple','input','open',
  'int','char','float','double','bool','void','struct','public','private',
  'protected','return','if','else','for','while','do','switch','case',
  'break','continue','new','delete','this','nullptr','true','false','const',
  'static','virtual','override','template','typename','namespace','using',
  'std','cout','cin','vector','string','map','auto','include','iostream'
]
const KW_COLORS = ['#4FC3F7','#FFD54F','#81C784','#4DD0E1','#BA68C8','#FF8A65','#AED581','#E57373']

onMounted(() => {
  // 创建星星
  for (let i = 0; i < 90; i++) {
    const fontSize = Math.random() * 12 + 11
    const baseX = Math.random() * 100
    const baseY = Math.random() * 100
    const opacity = Math.random() * 0.5 + 0.25
    const color = KW_COLORS[Math.floor(Math.random() * KW_COLORS.length)]
    const swaySpeed = Math.random() * 0.02 + 0.008
    const swayAmpX = Math.random() * 12 + 4
    const swayAmpY = Math.random() * 6 + 2
    const phase = Math.random() * Math.PI * 2
    const keyword = KEYWORDS[Math.floor(Math.random() * KEYWORDS.length)]
    
    stars.value.push({
      keyword,
      baseX,
      baseY,
      swaySpeed,
      swayAmpX,
      swayAmpY,
      phase,
      fontSize,
      opacity,
      curX: 0,
      curY: 0,
      attractUntil: 0,
      style: {
        fontSize: fontSize + 'px',
        left: baseX + '%',
        top: baseY + '%',
        opacity: opacity,
        color: color,
        textShadow: `0 0 8px ${color}80`,
        transition: 'font-size 0.3s, opacity 0.3s'
      }
    })
  }
  
  // 读取记住的账号
  ;['teacher', 'student', 'parent'].forEach(role => {
    const saved = localStorage.getItem('mzx_remember_' + role)
    if (saved) {
      // 存储但不自动填充，等用户选择身份后再填
    }
  })
  
  // 启动动画
  animate()
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
})

const handleMouseMove = (e: MouseEvent) => {
  if (!loginContainer.value) return
  const rect = loginContainer.value.getBoundingClientRect()
  mouseX = e.clientX - rect.left
  mouseY = e.clientY - rect.top
  hasMouse = true
  
  // 检测鼠标是否在登录卡片范围内
  if (loginCard.value) {
    const cr = loginCard.value.getBoundingClientRect()
    const inCard = e.clientX >= cr.left && e.clientX <= cr.right && e.clientY >= cr.top && e.clientY <= cr.bottom
    if (inCard) {
      stars.value.forEach(s => { s.attractUntil = 0 })
      return
    }
  }
  
  // 吸附半径内的星星
  const now = performance.now()
  const w = loginContainer.value.clientWidth
  const h = loginContainer.value.clientHeight
  
  stars.value.forEach(s => {
    if (s.attractUntil > now) return
    const px = (s.baseX / 100) * w
    const py = (s.baseY / 100) * h
    const d = Math.sqrt((mouseX - px) ** 2 + (mouseY - py) ** 2)
    if (d < ATTRACT_RADIUS) {
      s.attractUntil = now + FOLLOW_DURATION
    }
  })
}

const handleMouseLeave = () => {
  hasMouse = false
  stars.value.forEach(s => { s.attractUntil = 0 })
}

const animate = () => {
  time += 1
  const now = performance.now()
  
  if (!loginContainer.value) {
    animationId = requestAnimationFrame(animate)
    return
  }
  
  const w = loginContainer.value.clientWidth
  const h = loginContainer.value.clientHeight
  
  stars.value.forEach(s => {
    // 基础摆动
    const swayX = Math.sin(time * s.swaySpeed + s.phase) * s.swayAmpX
    const swayY = Math.cos(time * s.swaySpeed * 0.7 + s.phase) * s.swayAmpY
    
    const basePxX = (s.baseX / 100) * w
    const basePxY = (s.baseY / 100) * h
    
    const isFollowing = s.attractUntil > now && hasMouse
    
    if (isFollowing) {
      // 跟随鼠标
      const targetOffsetX = mouseX - basePxX
      const targetOffsetY = mouseY - basePxY
      s.curX += (targetOffsetX - s.curX) * ATTRACT_STRENGTH
      s.curY += (targetOffsetY - s.curY) * ATTRACT_STRENGTH
    } else {
      // 缓慢归位
      s.curX += (0 - s.curX) * 0.03
      s.curY += (0 - s.curY) * 0.03
    }
    
    // 更新样式
    s.style.transform = `translate(${s.curX + swayX}px, ${s.curY + swayY}px)`
    
    if (isFollowing) {
      s.style.fontSize = (s.fontSize * 1.5) + 'px'
      s.style.opacity = Math.min(1, s.opacity + 0.35)
    } else {
      s.style.fontSize = s.fontSize + 'px'
      s.style.opacity = s.opacity
    }
  })
  
  animationId = requestAnimationFrame(animate)
}

// ===== 登录/注册逻辑 =====
const selectRole = (role: 'teacher' | 'student' | 'parent' | 'admin') => {
  selectedRole.value = role
  setTimeout(() => {
    authStep.value = 'form'
    authTab.value = 'login'
    
    // 读取记住的账号
    const savedAccount = localStorage.getItem('mzx_remember_' + role)
    if (savedAccount) {
      loginForm.field1 = savedAccount
      rememberMe.value = true
    } else {
      loginForm.field1 = ''
      rememberMe.value = false
    }
    loginForm.field2 = ''
    clearLoginError('field1')
    clearLoginError('field2')
  }, 150)
}

const backToRoleSelect = () => {
  authStep.value = 'select'
}

const switchAuthTab = (tab: 'login' | 'register') => {
  authTab.value = tab
}

const validateLoginField = (field: 'field1' | 'field2') => {
  if (field === 'field1') {
    // 空值不报错，只清除错误
    if (!loginForm.field1) {
      clearLoginError('field1')
      return false
    }
    if (loginFieldUsesPhone.value && !/^1[3-9]\d{9}$/.test(loginForm.field1)) {
      loginErrors.field1 = true
      loginErrors.field1Msg = '请输入正确的11位手机号码'
      return false
    }
    if (!loginFieldUsesPhone.value && loginForm.field1.trim().length < 2) {
      loginErrors.field1 = true
      loginErrors.field1Msg = '请输入有效账号'
      return false
    }
    loginErrors.field1 = false
  } else if (field === 'field2') {
    // 空值不报错
    if (!loginForm.field2) {
      clearLoginError('field2')
      return false
    }
    loginErrors.field2 = false
  }
  return true
}

const clearLoginError = (field: 'field1' | 'field2') => {
  if (field === 'field1') {
    loginErrors.field1 = false
    loginErrors.field1Msg = ''
  } else {
    loginErrors.field2 = false
    loginErrors.field2Msg = ''
  }
}

const doLogin = async () => {
  formError.value = ''
  if (!loginForm.field1) {
    loginErrors.field1 = true
    loginErrors.field1Msg = loginFieldUsesPhone.value ? '请输入手机号' : '请输入账号'
  }
  if (!loginForm.field2) {
    loginErrors.field2 = true
    loginErrors.field2Msg = '请输入密码'
  }
  if (!loginForm.field1 || !loginForm.field2) return

  const valid1 = validateLoginField('field1')
  const valid2 = validateLoginField('field2')
  if (!valid1 || !valid2) return

  if (rememberMe.value) {
    localStorage.setItem('mzx_remember_' + selectedRole.value, loginForm.field1)
  } else {
    localStorage.removeItem('mzx_remember_' + selectedRole.value)
  }

  submitting.value = true
  try {
    await authStore.login({
      account: loginForm.field1,
      password: loginForm.field2,
      role: selectedRole.value,
    })
    await router.push(authStore.homeRoute)
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '登录失败，请重试'
  } finally {
    submitting.value = false
  }
}

const validateRegField = (field: 'phone' | 'code' | 'pwd' | 'pwd2') => {
  if (field === 'phone') {
    // 空值不报错
    if (!registerForm.phone) {
      clearRegError('phone')
      return false
    }
    if (!/^1[3-9]\d{9}$/.test(registerForm.phone)) {
      registerErrors.phone = true
      registerErrors.phoneMsg = '请输入正确的11位手机号码'
      return false
    }
    registerErrors.phone = false
  } else if (field === 'code') {
    // 空值不报错
    if (!registerForm.code) {
      clearRegError('code')
      return false
    }
    if (!/^\d{6}$/.test(registerForm.code)) {
      registerErrors.code = true
      registerErrors.codeMsg = '验证码为6位数字'
      return false
    }
    registerErrors.code = false
  } else if (field === 'pwd') {
    // 空值不报错
    if (!registerForm.pwd) {
      clearRegError('pwd')
      return false
    }
    if (registerForm.pwd.length < 6 || registerForm.pwd.length > 20) {
      registerErrors.pwd = true
      registerErrors.pwdMsg = '密码长度为6-20位'
      return false
    }
    if (!/[a-zA-Z]/.test(registerForm.pwd) || !/\d/.test(registerForm.pwd)) {
      registerErrors.pwd = true
      registerErrors.pwdMsg = '密码需同时包含字母和数字'
      return false
    }
    registerErrors.pwd = false
    if (registerForm.pwd2) validateRegField('pwd2')
  } else if (field === 'pwd2') {
    // 空值不报错
    if (!registerForm.pwd2) {
      clearRegError('pwd2')
      return false
    }
    if (registerForm.pwd2 !== registerForm.pwd) {
      registerErrors.pwd2 = true
      registerErrors.pwd2Msg = '两次密码输入不一致'
      return false
    }
    registerErrors.pwd2 = false
  }
  return true
}

const clearRegError = (field: 'phone' | 'code' | 'pwd' | 'pwd2') => {
  if (field === 'phone') {
    registerErrors.phone = false
    registerErrors.phoneMsg = ''
  } else if (field === 'code') {
    registerErrors.code = false
    registerErrors.codeMsg = ''
  } else if (field === 'pwd') {
    registerErrors.pwd = false
    registerErrors.pwdMsg = ''
  } else if (field === 'pwd2') {
    registerErrors.pwd2 = false
    registerErrors.pwd2Msg = ''
  }
}

const doRegister = async () => {
  formError.value = ''
  if (!registerForm.phone) {
    registerErrors.phone = true
    registerErrors.phoneMsg = '请输入手机号'
  }
  if (!registerForm.code) {
    registerErrors.code = true
    registerErrors.codeMsg = '请输入验证码'
  }
  if (!registerForm.pwd) {
    registerErrors.pwd = true
    registerErrors.pwdMsg = '请设置密码'
  }
  if (!registerForm.pwd2) {
    registerErrors.pwd2 = true
    registerErrors.pwd2Msg = '请确认密码'
  }
  if (!registerForm.phone || !registerForm.code || !registerForm.pwd || !registerForm.pwd2) return

  const valid1 = validateRegField('phone')
  const valid2 = validateRegField('code')
  const valid3 = validateRegField('pwd')
  const valid4 = validateRegField('pwd2')
  if (!valid1 || !valid2 || !valid3 || !valid4) return

  if (selectedRole.value === 'student' || selectedRole.value === 'admin') return

  submitting.value = true
  try {
    await authStore.register({
      phone: registerForm.phone,
      code: registerForm.code,
      password: registerForm.pwd,
      role: selectedRole.value as 'teacher' | 'parent',
    })
    registerForm.phone = ''
    registerForm.code = ''
    registerForm.pwd = ''
    registerForm.pwd2 = ''
    authTab.value = 'login'
    formError.value = ''
    alert(`${roleMeta[selectedRole.value].name}注册成功！请使用手机号+密码登录。`)
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '注册失败，请重试'
  } finally {
    submitting.value = false
  }
}

const sendCode = async () => {
  if (!registerForm.phone || !/^1[3-9]\d{9}$/.test(registerForm.phone)) {
    alert('请输入正确的手机号')
    return
  }
  if (selectedRole.value === 'student') return

  try {
    const result = await authApi.sendCode({
      phone: registerForm.phone,
      purpose: 'register',
      role: selectedRole.value,
    })
    codeCountdown.value = 60
    const timer = setInterval(() => {
      codeCountdown.value--
      if (codeCountdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
    if (result.dev_code) {
      alert(`验证码已发送（开发环境验证码：${result.dev_code}）`)
    } else {
      alert('验证码已发送')
    }
  } catch (err) {
    alert(err instanceof Error ? err.message : '验证码发送失败')
  }
}
</script>

<style scoped>
/* 样式已在 main.css 中定义 */
</style>
