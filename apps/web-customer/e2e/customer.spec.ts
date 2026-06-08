import { test, expect } from '@playwright/test';

test.describe('Customer App E2E Tests', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/VietStore/);
  });

  test('search functionality works', async ({ page }) => {
    await page.goto('/');
    
    // Find search input
    const searchInput = page.locator('input[placeholder*="tìm"]');
    await searchInput.fill('sản phẩm');
    
    // Submit search
    await searchInput.press('Enter');
    
    // Wait for results
    await expect(page.locator('.product-card').first()).toBeVisible();
  });

  test('navigation to product detail', async ({ page }) => {
    await page.goto('/');
    
    // Click on first product
    await page.locator('.product-card').first().click();
    
    // Verify product detail page
    await expect(page.locator('h1')).toBeVisible();
  });

  test('add to cart functionality', async ({ page }) => {
    await page.goto('/');
    
    // Navigate to product
    await page.locator('.product-card').first().click();
    
    // Add to cart
    await page.locator('button:has-text("Thêm vào giỏ")').click();
    
    // Verify cart notification
    await expect(page.locator('[role="alert"]')).toBeVisible();
  });

  test('cart page loads', async ({ page }) => {
    await page.goto('/cart');
    
    // Verify cart page
    await expect(page.locator('h1:has-text("Giỏ hàng")')).toBeVisible();
  });

  test('authentication flow', async ({ page }) => {
    await page.goto('/login');
    
    // Fill login form
    await page.locator('input[type="email"]').fill('test@example.com');
    await page.locator('input[type="password"]').fill('TestPass123');
    
    // Submit login
    await page.locator('button[type="submit"]').click();
    
    // Verify redirect to home
    await expect(page).toHaveURL('/');
  });
});
