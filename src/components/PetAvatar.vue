<template>
  <div
    class="pet-avatar inline-flex items-center justify-center select-none"
    :class="[
      `pet-avatar--${displayStateHint}`,
      `pet-avatar--stage-${stage}`,
      { 'pet-avatar--animate': animate && !interaction },
      interaction ? `pet-avatar--play-${interaction}` : '',
    ]"
    :style="{ width: `${size}px`, height: `${size}px` }"
  >
    <svg
      :width="size"
      :height="size"
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      class="pet-avatar__svg"
      aria-hidden="true"
    >
      <g class="pet-avatar__body" :transform="bodyTransform">
        <g class="pet-avatar__figure">
        <ellipse cx="60" cy="108" :rx="28 * scale" ry="6" fill="#000" fill-opacity="0.08" />

        <ellipse
          v-if="stage === 'max'"
          cx="60"
          cy="52"
          rx="46"
          ry="10"
          fill="none"
          stroke="#FBBF24"
          stroke-width="2"
          opacity="0.85"
          class="pet-halo"
        />

        <!-- 橘小胖 -->
        <template v-if="assetKey === 'cat_orange'">
          <path d="M35 48 L28 32 L42 42 Z" fill="#E89545" stroke="#C96F2D" stroke-width="1.5" stroke-linejoin="round" />
          <path d="M85 48 L92 32 L78 42 Z" fill="#E89545" stroke="#C96F2D" stroke-width="1.5" stroke-linejoin="round" />
          <ellipse cx="60" cy="68" rx="38" ry="34" fill="#F4A460" stroke="#D97706" stroke-width="2" />
          <ellipse cx="60" cy="74" rx="22" ry="18" fill="#FFF7ED" />
          <ellipse cx="52" cy="66" rx="5" ry="6" fill="#1F2937" />
          <ellipse cx="68" cy="66" rx="5" ry="6" fill="#1F2937" />
          <circle cx="54" cy="64" r="1.5" fill="#FFF" />
          <circle cx="70" cy="64" r="1.5" fill="#FFF" />
          <g v-if="stateHint === 'sleep'">
            <line x1="48" y1="66" x2="56" y2="66" stroke="#1F2937" stroke-width="2" stroke-linecap="round" />
            <line x1="64" y1="66" x2="72" y2="66" stroke="#1F2937" stroke-width="2" stroke-linecap="round" />
          </g>
          <g v-else>
            <path d="M48 62 Q52 58 56 62" stroke="#1F2937" stroke-width="1.5" fill="none" stroke-linecap="round" />
            <path d="M64 62 Q68 58 72 62" stroke="#1F2937" stroke-width="1.5" fill="none" stroke-linecap="round" />
          </g>
          <ellipse cx="60" cy="76" rx="4" ry="3" fill="#FDA4AF" />
          <path
            v-if="displayHappy"
            d="M54 82 Q60 89 66 82"
            stroke="#C96F2D"
            stroke-width="2"
            fill="none"
            stroke-linecap="round"
          />
          <path
            v-else
            d="M56 79 Q60 82 64 79"
            stroke="#C96F2D"
            stroke-width="1.5"
            fill="none"
            stroke-linecap="round"
          />
          <line x1="42" y1="74" x2="30" y2="70" stroke="#D97706" stroke-width="2" stroke-linecap="round" />
          <line x1="78" y1="74" x2="90" y2="70" stroke="#D97706" stroke-width="2" stroke-linecap="round" />
        </template>

        <!-- 柯基豆 -->
        <template v-else-if="assetKey === 'dog_corgi'">
          <ellipse cx="38" cy="52" rx="14" ry="22" fill="#D4A574" stroke="#B45309" stroke-width="1.5" transform="rotate(-15 38 52)" />
          <ellipse cx="82" cy="52" rx="14" ry="22" fill="#D4A574" stroke="#B45309" stroke-width="1.5" transform="rotate(15 82 52)" />
          <ellipse cx="60" cy="70" rx="36" ry="30" fill="#FCD34D" stroke="#D97706" stroke-width="2" />
          <ellipse cx="60" cy="76" rx="20" ry="16" fill="#FFFBEB" />
          <ellipse cx="52" cy="68" rx="4.5" ry="5.5" fill="#1F2937" />
          <ellipse cx="68" cy="68" rx="4.5" ry="5.5" fill="#1F2937" />
          <circle cx="54" cy="66" r="1.5" fill="#FFF" />
          <ellipse cx="60" cy="74" rx="5" ry="4" fill="#1F2937" />
          <path v-if="stateHint === 'happy'" d="M54 82 Q60 88 66 82" stroke="#B45309" stroke-width="2" fill="none" stroke-linecap="round" />
          <path v-else-if="stateHint !== 'sleep'" d="M56 83 L64 83" stroke="#B45309" stroke-width="2" stroke-linecap="round" />
          <path v-if="stateHint === 'happy'" d="M62 80 Q68 84 72 79" fill="#F87171" />
        </template>

        <!-- 像素机 -->
        <template v-else-if="assetKey === 'robot_pixel'">
          <rect x="32" y="38" width="56" height="52" rx="8" fill="#38BDF8" stroke="#0284C7" stroke-width="2" />
          <rect x="38" y="44" width="44" height="28" rx="4" fill="#0EA5E9" />
          <rect x="44" y="52" width="10" height="10" rx="1" fill="#4ADE80" class="pet-blink" />
          <rect x="66" y="52" width="10" height="10" rx="1" fill="#4ADE80" class="pet-blink" />
          <rect x="52" y="68" width="16" height="4" rx="1" fill="#0369A1" />
          <line x1="60" y1="38" x2="60" y2="28" stroke="#64748B" stroke-width="3" stroke-linecap="round" />
          <circle cx="60" cy="26" r="4" fill="#F472B6" class="pet-pulse" />
          <rect x="28" y="58" width="8" height="16" rx="2" fill="#7DD3FC" stroke="#0284C7" stroke-width="1" />
          <rect x="84" y="58" width="8" height="16" rx="2" fill="#7DD3FC" stroke="#0284C7" stroke-width="1" />
          <rect x="44" y="90" width="12" height="8" rx="2" fill="#64748B" />
          <rect x="64" y="90" width="12" height="8" rx="2" fill="#64748B" />
        </template>

        <!-- 云端幼龙 -->
        <template v-else-if="assetKey === 'dragon_cloud'">
          <path d="M28 72 Q20 58 32 52 Q24 44 38 48" fill="#A78BFA" stroke="#7C3AED" stroke-width="1.5" stroke-linejoin="round" />
          <path d="M92 72 Q100 58 88 52 Q96 44 82 48" fill="#C4B5FD" stroke="#7C3AED" stroke-width="1.5" stroke-linejoin="round" />
          <ellipse cx="60" cy="72" rx="34" ry="28" fill="#8B5CF6" stroke="#6D28D9" stroke-width="2" />
          <ellipse cx="60" cy="78" rx="18" ry="14" fill="#EDE9FE" />
          <ellipse cx="52" cy="70" rx="5" ry="6" fill="#1F2937" />
          <ellipse cx="68" cy="70" rx="5" ry="6" fill="#1F2937" />
          <circle cx="54" cy="68" r="1.5" fill="#FFF" />
          <circle cx="70" cy="68" r="1.5" fill="#FFF" />
          <path d="M60 42 L64 28 L68 42 Z" fill="#FDE047" stroke="#CA8A04" stroke-width="1" />
          <ellipse cx="60" cy="80" rx="3" ry="2" fill="#F472B6" />
          <path v-if="stateHint === 'happy'" d="M54 86 Q60 92 66 86" stroke="#5B21B6" stroke-width="2" fill="none" />
          <circle cx="78" cy="62" r="3" fill="#FDE047" opacity="0.9" class="pet-sparkle" />
          <circle cx="42" cy="64" r="2" fill="#FDE047" opacity="0.7" class="pet-sparkle pet-sparkle--delay" />
        </template>

        <!-- 未知 -->
        <template v-else>
          <circle cx="60" cy="65" r="32" fill="#E5E7EB" stroke="#9CA3AF" stroke-width="2" />
          <text x="60" y="72" text-anchor="middle" font-size="28">🐾</text>
        </template>

        <g v-if="stage === 'growth'" class="pet-avatar__decor">
          <path
            d="M44 84 Q60 90 76 84 L76 88 Q60 94 44 88 Z"
            fill="#1890FF"
            opacity="0.9"
          />
        </g>
        <g v-else-if="stage === 'mature' || stage === 'max'" class="pet-avatar__decor">
          <path
            d="M40 82 Q60 92 80 82 L84 86 Q60 98 36 86 Z"
            fill="#EF4444"
            stroke="#B91C1C"
            stroke-width="1"
          />
          <path d="M36 86 L28 96 L32 88 Z" fill="#DC2626" />
          <path d="M84 86 L92 96 L88 88 Z" fill="#DC2626" />
        </g>
        <g v-if="stage === 'max'" class="pet-avatar__decor">
          <path
            d="M60 34 L62 40 L68 40 L63 44 L65 50 L60 46 L55 50 L57 44 L52 40 L58 40 Z"
            fill="#FBBF24"
            stroke="#D97706"
            stroke-width="0.5"
            class="pet-crown"
          />
        </g>
        </g>
      </g>
    </svg>
    <span
      v-if="showStageLabel"
      class="absolute -bottom-1 left-1/2 -translate-x-1/2 text-[9px] px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 whitespace-nowrap font-medium"
    >
      {{ stageLabel }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PetPlayReaction, PetStateHint } from '@/types/pet'
import { getPetLevelScale, getPetLevelStage, getPetLevelStageLabel } from '@/utils/petLevelStage'

const props = withDefaults(
  defineProps<{
    assetKey: string
    size?: number
    level?: number
    stateHint?: PetStateHint
    interaction?: PetPlayReaction | null
    animate?: boolean
    showStageLabel?: boolean
  }>(),
  {
    size: 88,
    level: 1,
    stateHint: 'idle',
    interaction: null,
    animate: true,
    showStageLabel: false,
  },
)

const displayHappy = computed(
  () => props.stateHint === 'happy' || props.interaction === 'happy' || props.interaction === 'jump',
)
const displayStateHint = computed((): PetStateHint => {
  if (props.interaction || displayHappy.value) return 'happy'
  return props.stateHint
})

const stage = computed(() => getPetLevelStage(props.level))
const scale = computed(() => getPetLevelScale(stage.value))
const stageLabel = computed(() => getPetLevelStageLabel(stage.value))

/** SVG 以 (60,72) 为脚底中心缩放，幼体更小、满级略大 */
const bodyTransform = computed(() => {
  const s = scale.value
  return `translate(60 72) scale(${s}) translate(-60 -72)`
})
</script>

<style scoped>
.pet-avatar--animate .pet-avatar__figure {
  animation: pet-float 2.8s ease-in-out infinite;
  transform-box: fill-box;
  transform-origin: 60px 72px;
}

.pet-avatar--sleep .pet-avatar__figure {
  animation: pet-float 4s ease-in-out infinite;
  transform-origin: 60px 72px;
}

.pet-avatar--happy .pet-avatar__figure {
  animation: pet-wiggle 1.2s ease-in-out infinite;
  transform-origin: 60px 72px;
}

.pet-avatar--play-jump .pet-avatar__figure {
  animation: pet-jump 0.55s ease-out;
  transform-origin: 60px 72px;
}

.pet-avatar--play-wiggle .pet-avatar__figure {
  animation: pet-wiggle 0.65s ease-in-out;
  transform-origin: 60px 72px;
}

.pet-avatar--play-happy .pet-avatar__figure {
  animation: pet-hop 0.5s ease-out;
  transform-origin: 60px 72px;
}

@keyframes pet-jump {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  45% {
    transform: translateY(-16px) scale(1.06);
  }
}

@keyframes pet-hop {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes pet-float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

@keyframes pet-wiggle {
  0%,
  100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(-3deg) translateY(-3px);
  }
  75% {
    transform: rotate(3deg) translateY(-3px);
  }
}

.pet-blink {
  animation: pet-blink 3s step-end infinite;
}

@keyframes pet-blink {
  0%,
  92%,
  100% {
    opacity: 1;
  }
  96% {
    opacity: 0.2;
  }
}

.pet-pulse {
  animation: pet-pulse 1.5s ease-in-out infinite;
}

@keyframes pet-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.pet-sparkle {
  animation: pet-sparkle 2s ease-in-out infinite;
}

.pet-sparkle--delay {
  animation-delay: 0.8s;
}

@keyframes pet-sparkle {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.7;
  }
  50% {
    transform: scale(1.3);
    opacity: 1;
  }
}

.pet-halo {
  animation: pet-halo 2.5s ease-in-out infinite;
}

@keyframes pet-halo {
  0%,
  100% {
    opacity: 0.65;
    stroke-width: 2;
  }
  50% {
    opacity: 1;
    stroke-width: 2.5;
  }
}

.pet-crown {
  animation: pet-sparkle 1.8s ease-in-out infinite;
}

.pet-avatar {
  position: relative;
}

.pet-avatar__svg {
  overflow: visible;
}
</style>
