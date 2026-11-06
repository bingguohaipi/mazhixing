export type PetLevelStage = 'baby' | 'growth' | 'mature' | 'max'

export function getPetLevelStage(level: number): PetLevelStage {
  const lv = Math.max(1, Math.min(20, Math.floor(level)))
  if (lv >= 20) return 'max'
  if (lv >= 13) return 'mature'
  if (lv >= 6) return 'growth'
  return 'baby'
}

export function getPetLevelScale(stage: PetLevelStage): number {
  switch (stage) {
    case 'baby':
      return 0.78
    case 'growth':
      return 0.92
    case 'mature':
      return 1
    case 'max':
      return 1.08
    default:
      return 1
  }
}

export function getPetLevelStageLabel(stage: PetLevelStage): string {
  switch (stage) {
    case 'baby':
      return '幼体'
    case 'growth':
      return '成长期'
    case 'mature':
      return '成熟期'
    case 'max':
      return '满级'
  }
}
