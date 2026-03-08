import { test, expect } from '@playwright/test'

test.describe('Auth', () => {
  test('landing page shows login', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()
    await expect(page.getByPlaceholder(/email/i)).toBeVisible()
  })

  test('register then login', async ({ page }) => {
    await page.goto('/register')
    await page.getByPlaceholder(/email/i).fill('e2e@example.com')
    await page.getByPlaceholder(/password/i).fill('E2EPassword123')
    await page.getByRole('button', { name: /register/i }).click()
    await expect(page).toHaveURL('/')
    await page.getByPlaceholder(/email/i).fill('e2e@example.com')
    await page.getByPlaceholder(/password/i).fill('E2EPassword123')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByText('Dashboard')).toBeVisible()
  })
})
