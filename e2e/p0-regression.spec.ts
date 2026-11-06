import { expect, test } from '@playwright/test'

test.describe('P0 regression', () => {
  test('403 page renders standard copy', async ({ page }) => {
    await page.goto('/403')
    await expect(page.getByText('暂无权限访问该页面')).toBeVisible()
  })

  test('network error page renders standard copy', async ({ page }) => {
    await page.goto('/network-error')
    await expect(page.getByText('网络连接异常，请检查网络后重试')).toBeVisible()
  })

  test('student analytics route exists', async ({ page }) => {
    await page.goto('/login')
    await page.locator('.role-card').filter({ hasText: '学生' }).click()
    await page.getByPlaceholder('请输入学号').fill('stu2024001')
    await page.getByPlaceholder('请输入密码').fill('123456')
    await page.getByRole('button', { name: '登 录' }).click()
    await page.goto('/student/analytics')
    await expect(page.getByRole('heading', { name: '个人学情中心' })).toBeVisible()
  })
})
