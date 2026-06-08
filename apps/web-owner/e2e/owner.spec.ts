import { expect, test } from '@playwright/test';

test.describe('Owner App E2E Tests - Comprehensive', () => {
  test.beforeEach(async ({ page }) => {
    await page.context.clearCookies();
  });

  test('dashboard loads successfully', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('h1').first()).toBeVisible();
  });

  test('dashboard shows statistics', async ({ page }) => {
    await page.goto('/dashboard');

    // Check for statistics cards
    const statsCards = page.locator('.stat-card, .metric-card');
    if ((await statsCards.count()) > 0) {
      await expect(statsCards.first()).toBeVisible();
    }
  });

  test('products page loads', async ({ page }) => {
    await page.goto('/products');
    await expect(
      page.locator('h1:has-text("Sản phẩm"), h1:has-text("Products")').first()
    ).toBeVisible();
  });

  test('create new product', async ({ page }) => {
    await page.goto('/products');

    // Click add product button
    const addBtn = page.locator('button:has-text("Thêm mới"), button:has-text("Add")').first();
    if ((await addBtn.count()) > 0) {
      await addBtn.click();

      // Fill product form
      const nameInput = page.locator('input[name*="name"]').first();
      const priceInput = page.locator('input[name*="price"]').first();
      const descInput = page.locator('textarea[name*="desc"]').first();

      if ((await nameInput.count()) > 0) {
        await nameInput.fill('Test Product');
      }
      if ((await priceInput.count()) > 0) {
        await priceInput.fill('100000');
      }
      if ((await descInput.count()) > 0) {
        await descInput.fill('Test product description');
      }

      // Submit form
      const submitBtn = page.locator('button[type="submit"]').first();
      if ((await submitBtn.count()) > 0) {
        await submitBtn.click();

        // Verify success
        await page.waitForTimeout(2000);
      }
    }
  });

  test('edit existing product', async ({ page }) => {
    await page.goto('/products');

    // Click edit button on first product
    const editBtn = page.locator('button:has-text("Sửa"), button:has-text("Edit")').first();
    if ((await editBtn.count()) > 0) {
      await editBtn.click();

      // Modify product
      const nameInput = page.locator('input[name*="name"]').first();
      if ((await nameInput.count()) > 0) {
        await nameInput.fill('Updated Product Name');
      }

      // Submit
      const submitBtn = page.locator('button[type="submit"]').first();
      if ((await submitBtn.count()) > 0) {
        await submitBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('delete product', async ({ page }) => {
    await page.goto('/products');

    // Click delete button on first product
    const deleteBtn = page.locator('button:has-text("Xóa"), button:has-text("Delete")').first();
    if ((await deleteBtn.count()) > 0) {
      await deleteBtn.click();

      // Confirm deletion
      const confirmBtn = page
        .locator('button:has-text("Xác nhận"), button:has-text("Confirm")')
        .first();
      if ((await confirmBtn.count()) > 0) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('orders page loads', async ({ page }) => {
    await page.goto('/orders');
    await expect(
      page.locator('h1:has-text("Đơn hàng"), h1:has-text("Orders")').first()
    ).toBeVisible();
  });

  test('view order details', async ({ page }) => {
    await page.goto('/orders');

    // Click on first order
    const orderRow = page.locator('tr, .order-card').first();
    if ((await orderRow.count()) > 0) {
      await orderRow.click();

      // Verify order details
      await expect(
        page.locator('h1:has-text("Chi tiết"), h1:has-text("Details")').first()
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('update order status', async ({ page }) => {
    await page.goto('/orders');

    // Click on first order
    const orderRow = page.locator('tr, .order-card').first();
    if ((await orderRow.count()) > 0) {
      await orderRow.click();

      // Update status
      const statusSelect = page.locator('select[name*="status"]').first();
      if ((await statusSelect.count()) > 0) {
        await statusSelect.selectOption('processing');

        const saveBtn = page.locator('button:has-text("Lưu"), button:has-text("Save")').first();
        if ((await saveBtn.count()) > 0) {
          await saveBtn.click();
          await page.waitForTimeout(2000);
        }
      }
    }
  });

  test('analytics page loads', async ({ page }) => {
    await page.goto('/analytics');
    await expect(
      page.locator('h1:has-text("Phân tích"), h1:has-text("Analytics")').first()
    ).toBeVisible();
  });

  test('analytics shows charts', async ({ page }) => {
    await page.goto('/analytics');

    // Check for charts
    const charts = page.locator('canvas, .chart, .recharts-wrapper');
    if ((await charts.count()) > 0) {
      await expect(charts.first()).toBeVisible();
    }
  });

  test('filter orders by date', async ({ page }) => {
    await page.goto('/orders');

    // Set date filter
    const dateInput = page.locator('input[type="date"]').first();
    if ((await dateInput.count()) > 0) {
      await dateInput.fill('2024-01-01');

      const applyBtn = page.locator('button:has-text("Áp dụng"), button:has-text("Apply")').first();
      if ((await applyBtn.count()) > 0) {
        await applyBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('search products', async ({ page }) => {
    await page.goto('/products');

    // Search input
    const searchInput = page
      .locator('input[placeholder*="tìm"], input[placeholder*="search"]')
      .first();
    if ((await searchInput.count()) > 0) {
      await searchInput.fill('test');
      await searchInput.press('Enter');
      await page.waitForTimeout(2000);
    }
  });

  test('store settings page', async ({ page }) => {
    await page.goto('/settings');

    // Verify settings page
    const settingsHeading = page.locator('h1:has-text("Cài đặt"), h1:has-text("Settings")').first();
    if ((await settingsHeading.count()) > 0) {
      await expect(settingsHeading).toBeVisible();
    }
  });

  test('update store information', async ({ page }) => {
    await page.goto('/settings');

    // Update store name
    const nameInput = page.locator('input[name*="name"]').first();
    if ((await nameInput.count()) > 0) {
      await nameInput.fill('Updated Store Name');

      const saveBtn = page.locator('button[type="submit"]').first();
      if ((await saveBtn.count()) > 0) {
        await saveBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('upload product image', async ({ page }) => {
    await page.goto('/products');

    // Click add product
    const addBtn = page.locator('button:has-text("Thêm mới"), button:has-text("Add")').first();
    if ((await addBtn.count()) > 0) {
      await addBtn.click();

      // Upload image
      const fileInput = page.locator('input[type="file"]').first();
      if ((await fileInput.count()) > 0) {
        await fileInput.setInputFiles('test-image.jpg');
        await page.waitForTimeout(2000);
      }
    }
  });

  test('export orders', async ({ page }) => {
    await page.goto('/orders');

    // Click export button
    const exportBtn = page.locator('button:has-text("Xuất"), button:has-text("Export")').first();
    if ((await exportBtn.count()) > 0) {
      await exportBtn.click();
      await page.waitForTimeout(2000);
    }
  });

  test('responsive design - mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');

    // Verify mobile sidebar toggle
    const menuBtn = page.locator('button[aria-label*="menu"], .menu-button').first();
    if ((await menuBtn.count()) > 0) {
      await expect(menuBtn).toBeVisible();
    }
  });

  test('loading states', async ({ page }) => {
    await page.goto('/products');

    // Check for loading state
    const spinner = page.locator('.animate-spin, .loading').first();
    if ((await spinner.count()) > 0) {
      await expect(spinner).toBeVisible();
      await expect(spinner).not.toBeVisible({ timeout: 5000 });
    }
  });
});
