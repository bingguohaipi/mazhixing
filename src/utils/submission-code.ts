const MAX_CODE_LENGTH = 64_000
const MIN_MEANINGFUL_LENGTH = 8

const pythonForbidden = [
  /\bos\s*\.\s*system\s*\(/i,
  /\bsubprocess\b/i,
  /\beval\s*\(/i,
  /\bexec\s*\(/i,
  /\b__import__\s*\(/i,
]

const cppForbidden = [/\bsystem\s*\(/i, /\bfork\s*\(/i, /\bpopen\s*\(/i]

const stripForMeaningful = (code: string, language: 'Python' | 'C++'): string => {
  if (language === 'Python') {
    const noTriple = code.replace(/"""[\s\S]*?"""|'''[\s\S]*?'''/g, ' ')
    const noLine = noTriple.replace(/#.*/g, ' ')
    return noLine.replace(/\s+/g, '')
  }
  const noBlock = code.replace(/\/\*[\s\S]*?\*\//g, ' ')
  const noLine = noBlock.replace(/\/\/.*/g, ' ')
  return noLine.replace(/\s+/g, '')
}

export const validateSubmissionCodeClient = (
  code: string,
  language: 'Python' | 'C++',
): string | null => {
  const stripped = code.trim()
  if (!stripped) return '请勿提交空代码'
  if (code.length > MAX_CODE_LENGTH) return '代码过长，请精简后重新提交'
  if (stripForMeaningful(stripped, language).length < MIN_MEANINGFUL_LENGTH) {
    return '代码内容过少，请编写完整解题逻辑后再提交'
  }
  const patterns = language === 'Python' ? pythonForbidden : cppForbidden
  if (patterns.some((p) => p.test(stripped))) {
    return '代码包含不允许的系统调用，请修改后重试'
  }
  return null
}
