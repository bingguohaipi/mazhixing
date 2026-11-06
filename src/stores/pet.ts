import { defineStore } from 'pinia'
import { ref } from 'vue'
import { petApi } from '@/api/pet'
import type { StudentPetActive, StudentPetSettings, StudentPointsSummary } from '@/types/pet'

export const usePetStore = defineStore('pet', () => {
  const points = ref<StudentPointsSummary | null>(null)
  const activePet = ref<StudentPetActive | null>(null)
  const settings = ref<StudentPetSettings | null>(null)
  const loading = ref(false)

  async function refreshPoints() {
    points.value = await petApi.getPoints()
  }

  async function refreshActivePet() {
    activePet.value = await petApi.syncPet()
  }

  async function refreshSettings() {
    settings.value = await petApi.getSettings()
  }

  async function bootstrap() {
    if (loading.value) return
    loading.value = true
    try {
      await Promise.all([refreshPoints(), refreshSettings(), refreshActivePet()])
    } finally {
      loading.value = false
    }
  }

  function setPointsBalance(balance: number) {
    if (points.value) {
      points.value = { ...points.value, balance }
    }
  }

  function setActivePet(pet: StudentPetActive | null) {
    activePet.value = pet
  }

  return {
    points,
    activePet,
    settings,
    loading,
    bootstrap,
    refreshPoints,
    refreshActivePet,
    refreshSettings,
    setPointsBalance,
    setActivePet,
  }
})
