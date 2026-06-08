import { test, expect } from '@playwright/test';

test.describe('Owner App E2E Tests', () => {
  test('dashboard loads successfully', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('products page loads', async ({ page }) => {
    await page.goto('/products');
    await expect(page.locator('h1:has-text("Sản phẩm")')).toBeVisible();
  });

  test('orders page loads', async ({ page }) => {
    await page.goto('/orders');
    await expect(page.locator('h1:has-text("Đơn hàng")')).toBeVisible();
  });

  test('analytics page loads', async ({ page }) => {
    await page.goto('/analytics');
    await expect(page.locator('h1:has-text("Phân tích")')).toBeVisible();
  });
});
