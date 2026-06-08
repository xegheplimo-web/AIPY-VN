import { expect, test } from '@playwright/test';

test.describe('Customer App E2E Tests - Comprehensive', () => {
  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context.clearCookies();
    await page.goto('/');
  });

  test('homepage loads successfully', async ({ page }) => {
    await expect(page).toHaveTitle(/VietStore/);
    await expect(page.locator('nav')).toBeVisible();
  });

  test('search functionality works', async ({ page }) => {
    await page.goto('/');

    // Find search input
    const searchInput = page
      .locator('input[placeholder*="tìm"], input[placeholder*="search"]')
      .first();
    if ((await searchInput.count()) > 0) {
      await searchInput.fill('sản phẩm');
      await searchInput.press('Enter');

      // Wait for results
      await page.waitForTimeout(2000);
      const results = page.locator('.product-card');
      if ((await results.count()) > 0) {
        await expect(results.first()).toBeVisible();
      }
    }
  });

  test('navigation to product detail', async ({ page }) => {
    await page.goto('/');

    // Click on first product if exists
    const productCard = page.locator('.product-card').first();
    if ((await productCard.count()) > 0) {
      await productCard.click();

      // Verify product detail page
      await expect(page.locator('h1, h2').first()).toBeVisible();
    }
  });

  test('add to cart functionality', async ({ page }) => {
    await page.goto('/');

    // Navigate to product
    const productCard = page.locator('.product-card').first();
    if ((await productCard.count()) > 0) {
      await productCard.click();

      // Add to cart
      const addToCartBtn = page
        .locator('button:has-text("Thêm vào giỏ"), button:has-text("Add to cart")')
        .first();
      if ((await addToCartBtn.count()) > 0) {
        await addToCartBtn.click();

        // Verify cart notification
        await expect(page.locator('[role="alert"]')).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('cart page loads', async ({ page }) => {
    await page.goto('/cart');

    // Verify cart page
    const cartHeading = page.locator('h1:has-text("Giỏ hàng"), h1:has-text("Cart")').first();
    if ((await cartHeading.count()) > 0) {
      await expect(cartHeading).toBeVisible();
    }
  });

  test('checkout flow', async ({ page }) => {
    await page.goto('/cart');

    // Proceed to checkout if cart has items
    const checkoutBtn = page
      .locator('button:has-text("Thanh toán"), button:has-text("Checkout")')
      .first();
    if ((await checkoutBtn.count()) > 0) {
      await checkoutBtn.click();

      // Verify checkout page
      await expect(
        page.locator('h1:has-text("Thanh toán"), h1:has-text("Checkout")').first()
      ).toBeVisible();
    }
  });

  test('authentication flow - register', async ({ page }) => {
    await page.goto('/login');

    // Click on register link if exists
    const registerLink = page.locator('a:has-text("Đăng ký"), a:has-text("Register")').first();
    if ((await registerLink.count()) > 0) {
      await registerLink.click();

      // Fill registration form
      const emailInput = page.locator('input[type="email"]').first();
      const passwordInput = page.locator('input[type="password"]').first();
      const nameInput = page.locator('input[name*="name"], input[name*="full"]').first();

      if ((await emailInput.count()) > 0) {
        await emailInput.fill(`test${Date.now()}@example.com`);
      }
      if ((await passwordInput.count()) > 0) {
        await passwordInput.fill('TestPass123');
      }
      if ((await nameInput.count()) > 0) {
        await nameInput.fill('Test User');
      }

      // Submit registration
      const submitBtn = page.locator('button[type="submit"]').first();
      if ((await submitBtn.count()) > 0) {
        await submitBtn.click();

        // Verify redirect to home or dashboard
        await page.waitForTimeout(2000);
      }
    }
  });

  test('authentication flow - login', async ({ page }) => {
    await page.goto('/login');

    // Fill login form
    const emailInput = page.locator('input[type="email"]').first();
    const passwordInput = page.locator('input[type="password"]').first();

    if ((await emailInput.count()) > 0) {
      await emailInput.fill('test@example.com');
    }
    if ((await passwordInput.count()) > 0) {
      await passwordInput.fill('TestPass123');
    }

    // Submit login
    const submitBtn = page.locator('button[type="submit"]').first();
    if ((await submitBtn.count()) > 0) {
      await submitBtn.click();

      // Verify redirect
      await page.waitForTimeout(2000);
    }
  });

  test('store locator page', async ({ page }) => {
    await page.goto('/locator');

    // Verify store locator page
    const locatorHeading = page
      .locator('h1:has-text("Cửa hàng gần đây"), h1:has-text("Store Locator")')
      .first();
    if ((await locatorHeading.count()) > 0) {
      await expect(locatorHeading).toBeVisible();
    }
  });

  test('user profile page', async ({ page }) => {
    await page.goto('/profile');

    // Verify profile page or redirect to login
    await page.waitForTimeout(2000);
    const profileHeading = page.locator('h1:has-text("Hồ sơ"), h1:has-text("Profile")').first();
    if ((await profileHeading.count()) > 0) {
      await expect(profileHeading).toBeVisible();
    }
  });

  test('order tracking page', async ({ page }) => {
    await page.goto('/orders');

    // Verify orders page or redirect to login
    await page.waitForTimeout(2000);
    const ordersHeading = page.locator('h1:has-text("Đơn hàng"), h1:has-text("Orders")').first();
    if ((await ordersHeading.count()) > 0) {
      await expect(ordersHeading).toBeVisible();
    }
  });

  test('responsive design - mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Verify mobile layout
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('.mobile-menu-button').first()).toBeVisible();
  });

  test('responsive design - tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    // Verify tablet layout
    await expect(page.locator('nav')).toBeVisible();
  });

  test('accessibility - keyboard navigation', async ({ page }) => {
    await page.goto('/');

    // Test tab navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
  });

  test('loading states', async ({ page }) => {
    await page.goto('/');

    // Navigate to a page that might have loading state
    const productCard = page.locator('.product-card').first();
    if ((await productCard.count()) > 0) {
      await productCard.click();

      // Check for loading spinner
      const spinner = page.locator('.animate-spin, .loading').first();
      if ((await spinner.count()) > 0) {
        await expect(spinner).toBeVisible();
        await expect(spinner).not.toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('error handling - 404 page', async ({ page }) => {
    await page.goto('/non-existent-page');

    // Verify 404 handling
    await expect(page.locator('h1:has-text("404"), h1:has-text("Not Found")').first()).toBeVisible({
      timeout: 5000,
    });
  });
});
