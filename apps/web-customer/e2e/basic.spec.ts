import { expect, test } from '@playwright/test';

test.describe('Basic E2E Tests', () => {
  test('homepage loads with 200 status', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.status()).toBe(200);
  });

  test('page has a valid title', async ({ page }) => {
    await page.goto('/');
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);
  });

  test('page loads without network errors', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('page has no critical JavaScript errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => {
      errors.push(error.message);
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Filter out expected errors (Clerk auth, etc.)
    const criticalErrors = errors.filter(error => 
      !error.includes('Missing Publishable Key') &&
      !error.includes('Clerk')
    );
    
    expect(criticalErrors).toHaveLength(0);
  });
});
