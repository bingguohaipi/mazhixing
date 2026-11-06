<template>
  <Teleport to="body">
    <div
      v-if="showPet && pet && !minimized"
      ref="elRef"
      class="desktop-pet fixed z-[900] select-none"
      :class="isDraggingPet ? 'cursor-grabbing' : 'cursor-pointer'"
      :style="{ left: `${pos.x}px`, top: `${pos.y}px` }"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerCancel"
      @dblclick.prevent="panelOpen = true"
    >
      <div
        v-if="bubble"
        class="absolute -top-10 left-1/2 -translate-x-1/2 whitespace-nowrap bg-white border border-gray-200 text-xs px-2 py-1 rounded-lg shadow-sm pointer-events-none z-10"
      >
        {{ bubble }}
      </div>
      <div class="w-[88px] h-[88px] flex items-center justify-center mx-auto">
        <PetAvatar
          v-if="pet"
          :key="playFxKey"
          :asset-key="pet.asset_key"
          :size="80"
          :level="pet.level"
          :state-hint="pet.state_hint"
          :interaction="playReaction"
        />
      </div>
      <div class="text-center text-[10px] text-gray-700 mt-1 font-medium drop-shadow-sm pointer-events-none">
        {{ pet.name }} Lv.{{ pet.level }}
      </div>
    </div>

    <div
      v-else-if="showPet && pet && minimized"
      class="fixed bottom-4 right-4 z-[900] w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-lg cursor-pointer"
      @click="minimized = false"
    >
      🐾
    </div>

    <aside
      v-if="panelOpen && pet"
      class="fixed top-0 right-0 h-full w-[min(360px,100vw)] bg-white border-l border-gray-200 shadow-xl z-[950] p-5"
    >
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-900">{{ pet.name }}</h2>
        <button type="button" class="text-gray-400 hover:text-gray-600" @click="panelOpen = false">✕</button>
      </div>
      <div
        class="flex justify-center mb-4 cursor-pointer rounded-xl hover:bg-gray-50 py-2 transition"
        role="button"
        aria-label="逗小伙伴玩"
        @click="onPetClick"
      >
        <PetAvatar
          :key="`panel-${playFxKey}`"
          :asset-key="pet.asset_key"
          :size="140"
          :level="pet.level"
          :state-hint="pet.state_hint"
          :interaction="playReaction"
          show-stage-label
        />
      </div>
      <div class="space-y-3 text-sm">
        <div>
          <div class="flex justify-between text-gray-600 mb-1"><span>饱食</span><span>{{ pet.satiety }}</span></div>
          <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div class="h-full bg-amber-400" :style="{ width: `${pet.satiety}%` }" />
          </div>
        </div>
        <div>
          <div class="flex justify-between text-gray-600 mb-1"><span>心情</span><span>{{ pet.mood }}</span></div>
          <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div class="h-full bg-pink-400" :style="{ width: `${pet.mood}%` }" />
          </div>
        </div>
        <div>
          <div class="flex justify-between text-gray-600 mb-1">
            <span>经验</span><span>{{ pet.exp }}/{{ pet.exp_to_next || 'MAX' }}</span>
          </div>
          <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-indigo-500"
              :style="{ width: pet.exp_to_next ? `${(pet.exp / pet.exp_to_next) * 100}%` : '100%' }"
            />
          </div>
        </div>
      </div>
      <p class="text-xs text-gray-400 mt-4 text-center">轻点悬浮的小伙伴会跳起来；拖走可换位置，心情会慢慢下降，记得常互动或喂养哦</p>
      <div class="mt-4 flex flex-col gap-2">
        <RouterLink to="/student/pet-shop" class="btn-primary text-center py-2 rounded-lg text-sm" @click="panelOpen = false">
          去商城 / 喂养
        </RouterLink>
        <button type="button" class="text-sm text-gray-500" @click="minimized = true; panelOpen = false">收起小伙伴</button>
      </div>
    </aside>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePetPlay } from '@/composables/usePetPlay'
import { usePetStore } from '@/stores/pet'
import PetAvatar from '@/components/PetAvatar.vue'

const petStore = usePetStore()
const route = useRoute()

const DRAG_THRESHOLD_PX = 10

const pos = ref({ x: 0, y: 0 })
const pointerSession = ref(false)
const isDraggingPet = ref(false)
const dragOffset = ref({ x: 0, y: 0 })
const pointerStart = ref({ x: 0, y: 0 })
const panelOpen = ref(false)
const minimized = ref(false)
const elRef = ref<HTMLElement | null>(null)
const { playReaction, playFxKey, bubble, playWithPet } = usePetPlay()

const pet = computed(() => petStore.activePet)
const settings = computed(() => petStore.settings)

const isCoding = computed(() => route.path.includes('/student/coding'))

const showPet = computed(() => {
  if (!settings.value?.desktop_pet_enabled || !pet.value) return false
  if (isCoding.value) return false
  return true
})

function loadPosition() {
  const key = `pet_position_${petStore.activePet?.id ?? 'default'}`
  const raw = localStorage.getItem(key)
  if (raw) {
    try {
      const parsed = JSON.parse(raw) as { x: number; y: number }
      pos.value = parsed
      return
    } catch {
      /* ignore */
    }
  }
  pos.value = { x: window.innerWidth - 120, y: window.innerHeight - 160 }
}

function savePosition() {
  const key = `pet_position_${petStore.activePet?.id ?? 'default'}`
  localStorage.setItem(key, JSON.stringify(pos.value))
}

function snapToEdge() {
  const w = 100
  const h = 120
  const mid = pos.value.x + w / 2
  pos.value.x = mid < window.innerWidth / 2 ? 16 : window.innerWidth - w - 16
  pos.value.y = Math.min(Math.max(pos.value.y, 64), window.innerHeight - h - 16)
  savePosition()
}

function onPointerDown(e: PointerEvent) {
  if (e.button !== 0) return
  pointerSession.value = true
  isDraggingPet.value = false
  pointerStart.value = { x: e.clientX, y: e.clientY }
  dragOffset.value = { x: e.clientX - pos.value.x, y: e.clientY - pos.value.y }
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  if (!pointerSession.value) return
  const dx = e.clientX - pointerStart.value.x
  const dy = e.clientY - pointerStart.value.y
  if (!isDraggingPet.value) {
    if (Math.hypot(dx, dy) <= DRAG_THRESHOLD_PX) return
    isDraggingPet.value = true
  }
  pos.value = {
    x: e.clientX - dragOffset.value.x,
    y: e.clientY - dragOffset.value.y,
  }
}

function finishPointer(e: PointerEvent) {
  if (!pointerSession.value) return
  const el = e.currentTarget as HTMLElement
  if (el.hasPointerCapture(e.pointerId)) {
    el.releasePointerCapture(e.pointerId)
  }
  const wasTap = !isDraggingPet.value
  pointerSession.value = false
  isDraggingPet.value = false
  if (wasTap) {
    void playWithPet()
  } else {
    snapToEdge()
  }
}

function onPointerUp(e: PointerEvent) {
  finishPointer(e)
}

function onPointerCancel(e: PointerEvent) {
  pointerSession.value = false
  isDraggingPet.value = false
  const el = e.currentTarget as HTMLElement
  if (el.hasPointerCapture(e.pointerId)) {
    el.releasePointerCapture(e.pointerId)
  }
}

function onPetClick() {
  void playWithPet()
}

let syncTimer: ReturnType<typeof setInterval> | null = null
let walkTimer: ReturnType<typeof setInterval> | null = null

function startWalkLoop() {
  if (walkTimer) clearInterval(walkTimer)
  walkTimer = setInterval(() => {
    if (!pet.value || pointerSession.value || isDraggingPet.value) return
    if (isCoding.value && settings.value?.silent_while_coding) return
    if (pet.value.state_hint === 'sleep') return
    const dx = (Math.random() - 0.5) * 40
    const dy = (Math.random() - 0.5) * 24
    pos.value = {
      x: Math.min(Math.max(pos.value.x + dx, 8), window.innerWidth - 108),
      y: Math.min(Math.max(pos.value.y + dy, 64), window.innerHeight - 140),
    }
  }, 8000)
}

onMounted(() => {
  loadPosition()
  syncTimer = setInterval(() => {
    void petStore.refreshActivePet()
  }, 60000)
  startWalkLoop()
})

onUnmounted(() => {
  if (syncTimer) clearInterval(syncTimer)
  if (walkTimer) clearInterval(walkTimer)
})

watch(
  () => petStore.activePet?.id,
  () => loadPosition(),
)
</script>

<style scoped>
.desktop-pet {
  touch-action: none;
  filter: drop-shadow(0 4px 12px rgb(0 0 0 / 0.12));
}
.btn-primary {
  background: #1890ff;
  color: #fff;
}
</style>
