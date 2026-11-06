import { z } from 'zod'

const testCaseSchema = z.object({
  input_data: z.string(),
  expected_output: z.string(),
  is_sample: z.boolean().default(false),
  sort_order: z.number().int().default(0),
})

export const problemFormSchema = z
  .object({
    title: z.string().trim().min(1, '请输入题目标题').max(200, '标题最多 200 字'),
    description: z.string().trim().min(1, '请输入题目描述'),
    languages: z
      .array(z.enum(['Python', 'C++']))
      .min(1)
      .max(2)
      .default(['Python', 'C++'])
      .refine((arr) => new Set(arr).size === arr.length, '语言不可重复'),
    difficulty: z.enum(['入门', '简单', '中等', '困难']),
    knowledge_points: z.array(z.string().trim().min(1)).min(1, '请至少选择一个知识点'),
    sample_input: z.string().optional(),
    sample_output: z.string().optional(),
    reference_answer: z.string().optional(),
    time_limit_ms: z.number().int().min(100).max(10000),
    memory_limit_mb: z.number().int().min(1).max(256),
    test_cases: z.array(testCaseSchema).min(1, '至少配置一组测试用例'),
    image_urls: z.array(z.string()).max(5, '题目插图最多 5 张').optional().default([]),
  })
  .superRefine((data, ctx) => {
    const validCases = data.test_cases.filter((item) => item.expected_output.trim())
    if (validCases.length === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: '至少配置一组有效测试用例（期望输出不能为空；无输入题可将输入留空）',
        path: ['test_cases'],
      })
    }
  })

export type ProblemFormValues = z.infer<typeof problemFormSchema>

export function formatZodErrors(error: z.ZodError): string {
  return error.issues[0]?.message ?? '表单校验失败'
}
