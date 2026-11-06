import { describe, expect, it } from 'vitest'
import { validateSubmissionCodeClient } from '@/utils/submission-code'

describe('validateSubmissionCodeClient', () => {
  it('rejects empty code', () => {
    expect(validateSubmissionCodeClient('  ', 'Python')).toBe('请勿提交空代码')
  })

  it('rejects dangerous python calls', () => {
    const code = "import os\nos.system('ls')\nprint('hello world test')"
    expect(validateSubmissionCodeClient(code, 'Python')).toContain('不允许')
  })

  it('accepts normal solution', () => {
    const code = 'a = input()\nprint(int(a) + 1)\n'
    expect(validateSubmissionCodeClient(code, 'Python')).toBeNull()
  })
})
