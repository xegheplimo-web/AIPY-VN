import { test, expect } from '@playwright/test';

test.describe('Admin App E2E Tests', () => {
  test('dashboard loads successfully', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('stores page loads', async ({ page }) => {
    await page.goto('/stores');
    await expect(page.locator('h1:has-text("Cửa hàng")')).toBeVisible();
  });

  test('users page loads', async ({ page }) => {
    await page.goto('/users');
    await expect(page.locator('h1:has-text("Người dùng")')).toBeVisible();
  });

  test('reports page loads', async ({ page }) => {
    await page.goto('/reports');
    await expect(page.locator('h1:has-text("Báo cáo")')).toBeVisible();
  });
});
