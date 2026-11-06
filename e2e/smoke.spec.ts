import { expect, test } from '@playwright/test'

async function loginAsTeacher(page: import('@playwright/test').Page) {
  await page.goto('/login')
  await page.locator('.role-card').filter({ hasText: '教师' }).click()
  await page.getByPlaceholder('请输入教师注册手机号').fill('13800138000')
  await page.getByPlaceholder('请输入密码').fill('Teacher123')
  await page.getByRole('button', { name: '登 录' }).click()
  await expect(page).toHaveURL(/teacher/)
}

test.describe('smoke', () => {
  test('teacher can open question bank', async ({ page }) => {
    await loginAsTeacher(page)
    await page.goto('/teacher/questions')
    await expect(page.getByRole('heading', { name: '题库管理' })).toBeVisible()
    await expect(page.getByRole('button', { name: '批量导入' })).toBeVisible()
  })

  test('teacher can open analytics page', async ({ page }) => {
    await loginAsTeacher(page)
    await page.goto('/teacher/analytics')
    await expect(page.getByRole('heading', { name: '学情分析' })).toBeVisible()
    await expect(page.getByRole('button', { name: '错题汇总' })).toBeVisible()
  })

  test('login page renders role cards', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByText('请选择身份')).toBeVisible()
    await expect(page.getByText('教师')).toBeVisible()
    await expect(page.getByText('学生')).toBeVisible()
    await expect(page.getByText('家长')).toBeVisible()
  })
})
