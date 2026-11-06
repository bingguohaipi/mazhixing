const DRAFT_PREFIX = 'draft_'

export const getDraftKey = (userId: number, problemId: number, language: 'Python' | 'C++'): string =>
  `${DRAFT_PREFIX}${userId}_${problemId}_${language}`

export const loadDraft = (userId: number, problemId: number, language: 'Python' | 'C++'): string | null => {
  return localStorage.getItem(getDraftKey(userId, problemId, language))
}

/** 将旧版单键草稿迁移到对应语言键，避免切换语言时串稿。 */
export const migrateLegacyDraft = (
  userId: number,
  problemId: number,
  fallbackLanguage: 'Python' | 'C++',
): void => {
  const legacyKey = `${DRAFT_PREFIX}${userId}_${problemId}`
  const legacy = localStorage.getItem(legacyKey)
  if (!legacy) return
  const hasPy = localStorage.getItem(getDraftKey(userId, problemId, 'Python')) !== null
  const hasCpp = localStorage.getItem(getDraftKey(userId, problemId, 'C++')) !== null
  if (hasPy || hasCpp) {
    localStorage.removeItem(legacyKey)
    return
  }
  const looksCpp =
    legacy.includes('#include') || legacy.includes('using namespace std') || legacy.includes('int main(')
  const target: 'Python' | 'C++' = looksCpp ? 'C++' : fallbackLanguage
  localStorage.setItem(getDraftKey(userId, problemId, target), legacy)
  localStorage.removeItem(legacyKey)
}

export const saveDraft = (userId: number, problemId: number, language: 'Python' | 'C++', code: string): void => {
  localStorage.setItem(getDraftKey(userId, problemId, language), code)
}

export const clearDraft = (userId: number, problemId: number, language: 'Python' | 'C++'): void => {
  localStorage.removeItem(getDraftKey(userId, problemId, language))
  localStorage.removeItem(`${DRAFT_PREFIX}${userId}_${problemId}`)
}

const looksLikeCpp = (source: string): boolean =>
  /#include\s*[<"]|using namespace std|int main\s*\(/.test(source)

const looksLikePython = (source: string): boolean =>
  /\bprint\s*\(|for\s+\w+\s+in\s+range\b|def\s+\w+\s*\(/.test(source)

const isPythonStarterComment = (source: string): boolean =>
  /在此编写\s*Python/i.test(source) && !looksLikeCpp(source)

const isCppStarterTemplate = (source: string): boolean =>
  source.includes('#include') && source.includes('int main')

/** 丢弃与所选语言明显不符的草稿（例如 Python 下却存了 C++ 模板）。 */
export const draftForLanguage = (raw: string | null, language: 'Python' | 'C++'): string | null => {
  if (raw === null || !raw.trim()) return null
  const cpp = looksLikeCpp(raw)
  const py = looksLikePython(raw)
  if (language === 'Python' && (isCppStarterTemplate(raw) || (cpp && !py))) return null
  if (language === 'C++' && (isPythonStarterComment(raw) || (py && !cpp))) return null
  return raw
}

export const getDefaultCode = (language: 'Python' | 'C++'): string => {
  if (language === 'Python') {
    return '# 在此编写 Python 代码\n'
  }
  return `#include <iostream>
using namespace std;

int main() {
    
    return 0;
}
`
}
