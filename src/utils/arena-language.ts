export type ArenaLanguage = 'Python' | 'C++'

export const ARENA_LANGUAGES: ArenaLanguage[] = ['Python', 'C++']

const STORAGE_KEY = 'mzx_arena_language'

export function getStoredArenaLanguage(): ArenaLanguage | null {
  const raw = sessionStorage.getItem(STORAGE_KEY)
  if (raw === 'Python' || raw === 'C++') return raw
  return null
}

export function setStoredArenaLanguage(lang: ArenaLanguage): void {
  sessionStorage.setItem(STORAGE_KEY, lang)
}

export function clearStoredArenaLanguage(): void {
  sessionStorage.removeItem(STORAGE_KEY)
}

export function parseArenaLanguage(value: unknown): ArenaLanguage | null {
  if (value === 'Python' || value === 'C++') return value
  return null
}
