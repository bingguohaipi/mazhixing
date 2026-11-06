import { ref } from 'vue'
import { petApi } from '@/api/pet'
import { usePetStore } from '@/stores/pet'
import type { PetPlayReaction } from '@/types/pet'
import { toast } from '@/utils/toast'

const reactionQuotes: Record<PetPlayReaction, string[]> = {
  jump: ['耶！', '跳高高～', '好开心！'],
  happy: ['嘻嘻～', '笑一个！', '太好玩啦～'],
  wiggle: ['扭扭～', '摇尾巴！', '再来一次！'],
}

const previewReactions: PetPlayReaction[] = ['jump', 'happy', 'wiggle']

function pickPreviewReaction(): PetPlayReaction {
  return previewReactions[Math.floor(Math.random() * previewReactions.length)]!
}

export function usePetPlay() {
  const petStore = usePetStore()
  const playReaction = ref<PetPlayReaction | null>(null)
  /** 每次互动 +1，强制 PetAvatar 重播 CSS 动画 */
  const playFxKey = ref(0)
  const playing = ref(false)
  const bubble = ref<string | null>(null)

  function bumpPlayFx(reaction: PetPlayReaction) {
    playReaction.value = reaction
    playFxKey.value += 1
  }

  function clearPlayFx(delayMs = 1600) {
    window.setTimeout(() => {
      playReaction.value = null
      bubble.value = null
    }, delayMs)
  }

  async function playWithPet() {
    const pet = petStore.activePet
    if (playing.value || !pet) return

    if (pet.satiety <= 0 || pet.state_hint === 'sleep') {
      bumpPlayFx('wiggle')
      bubble.value = '我好饿…先喂我一下吧～'
      toast.warning('小伙伴太饿了，先去商城喂点吃的吧')
      clearPlayFx(2000)
      return
    }

    bumpPlayFx(pickPreviewReaction())
    playing.value = true
    try {
      const result = await petApi.playWithActivePet()
      petStore.setActivePet(result.pet)
      bumpPlayFx(result.reaction)
      const lines = reactionQuotes[result.reaction]
      bubble.value = `${lines[Math.floor(Math.random() * lines.length)]} 心情 +${result.mood_delta}`
      clearPlayFx(1600)
    } catch (err) {
      playReaction.value = null
      toast.error(err instanceof Error ? err.message : '互动失败')
    } finally {
      playing.value = false
    }
  }

  return { playReaction, playFxKey, playing, bubble, playWithPet }
}
