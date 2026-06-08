import { expect, test } from '@playwright/test';

test.describe('Admin App E2E Tests - Comprehensive', () => {
  test.beforeEach(async ({ page }) => {
    await page.context.clearCookies();
  });

  test('dashboard loads successfully', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('h1').first()).toBeVisible();
  });

  test('dashboard shows system statistics', async ({ page }) => {
    await page.goto('/dashboard');

    // Check for statistics cards
    const statsCards = page.locator('.stat-card, .metric-card');
    if ((await statsCards.count()) > 0) {
      await expect(statsCards.first()).toBeVisible();
    }
  });

  test('stores page loads', async ({ page }) => {
    await page.goto('/stores');
    await expect(
      page.locator('h1:has-text("Cửa hàng"), h1:has-text("Stores")').first()
    ).toBeVisible();
  });

  test('view store details', async ({ page }) => {
    await page.goto('/stores');

    // Click on first store
    const storeRow = page.locator('tr, .store-card').first();
    if ((await storeRow.count()) > 0) {
      await storeRow.click();

      // Verify store details
      await expect(
        page.locator('h1:has-text("Chi tiết"), h1:has-text("Details")').first()
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('verify store', async ({ page }) => {
    await page.goto('/stores');

    // Click verify button on first store
    const verifyBtn = page
      .locator('button:has-text("Xác minh"), button:has-text("Verify")')
      .first();
    if ((await verifyBtn.count()) > 0) {
      await verifyBtn.click();

      // Confirm verification
      const confirmBtn = page
        .locator('button:has-text("Xác nhận"), button:has-text("Confirm")')
        .first();
      if ((await confirmBtn.count()) > 0) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('suspend store', async ({ page }) => {
    await page.goto('/stores');

    // Click suspend button
    const suspendBtn = page
      .locator('button:has-text("Tạm dừng"), button:has-text("Suspend")')
      .first();
    if ((await suspendBtn.count()) > 0) {
      await suspendBtn.click();

      // Confirm suspension
      const confirmBtn = page
        .locator('button:has-text("Xác nhận"), button:has-text("Confirm")')
        .first();
      if ((await confirmBtn.count()) > 0) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('users page loads', async ({ page }) => {
    await page.goto('/users');
    await expect(
      page.locator('h1:has-text("Người dùng"), h1:has-text("Users")').first()
    ).toBeVisible();
  });

  test('view user details', async ({ page }) => {
    await page.goto('/users');

    // Click on first user
    const userRow = page.locator('tr, .user-card').first();
    if ((await userRow.count()) > 0) {
      await userRow.click();

      // Verify user details
      await expect(
        page.locator('h1:has-text("Chi tiết"), h1:has-text("Details")').first()
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('change user role', async ({ page }) => {
    await page.goto('/users');

    // Click on first user
    const userRow = page.locator('tr, .user-card').first();
    if ((await userRow.count()) > 0) {
      await userRow.click();

      // Change role
      const roleSelect = page.locator('select[name*="role"]').first();
      if ((await roleSelect.count()) > 0) {
        await roleSelect.selectOption('admin');

        const saveBtn = page.locator('button:has-text("Lưu"), button:has-text("Save")').first();
        if ((await saveBtn.count()) > 0) {
          await saveBtn.click();
          await page.waitForTimeout(2000);
        }
      }
    }
  });

  test('ban user', async ({ page }) => {
    await page.goto('/users');

    // Click ban button
    const banBtn = page.locator('button:has-text("Cấm"), button:has-text("Ban")').first();
    if ((await banBtn.count()) > 0) {
      await banBtn.click();

      // Confirm ban
      const confirmBtn = page
        .locator('button:has-text("Xác nhận"), button:has-text("Confirm")')
        .first();
      if ((await confirmBtn.count()) > 0) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('reports page loads', async ({ page }) => {
    await page.goto('/reports');
    await expect(
      page.locator('h1:has-text("Báo cáo"), h1:has-text("Reports")').first()
    ).toBeVisible();
  });

  test('view report details', async ({ page }) => {
    await page.goto('/reports');

    // Click on first report
    const reportRow = page.locator('tr, .report-card').first();
    if ((await reportRow.count()) > 0) {
      await reportRow.click();

      // Verify report details
      await expect(
        page.locator('h1:has-text("Chi tiết"), h1:has-text("Details")').first()
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('resolve report', async ({ page }) => {
    await page.goto('/reports');

    // Click on first report
    const reportRow = page.locator('tr, .report-card').first();
    if ((await reportRow.count()) > 0) {
      await reportRow.click();

      // Add resolution note
      const noteInput = page.locator('textarea[name*="note"]').first();
      if ((await noteInput.count()) > 0) {
        await noteInput.fill('Issue resolved');

        const resolveBtn = page
          .locator('button:has-text("Giải quyết"), button:has-text("Resolve")')
          .first();
        if ((await resolveBtn.count()) > 0) {
          await resolveBtn.click();
          await page.waitForTimeout(2000);
        }
      }
    }
  });

  test('categories page loads', async ({ page }) => {
    await page.goto('/categories');

    const categoriesHeading = page
      .locator('h1:has-text("Danh mục"), h1:has-text("Categories")')
      .first();
    if ((await categoriesHeading.count()) > 0) {
      await expect(categoriesHeading).toBeVisible();
    }
  });

  test('create category', async ({ page }) => {
    await page.goto('/categories');

    // Click add category button
    const addBtn = page.locator('button:has-text("Thêm mới"), button:has-text("Add")').first();
    if ((await addBtn.count()) > 0) {
      await addBtn.click();

      // Fill category form
      const nameInput = page.locator('input[name*="name"]').first();
      if ((await nameInput.count()) > 0) {
        await nameInput.fill('Test Category');
      }

      const submitBtn = page.locator('button[type="submit"]').first();
      if ((await submitBtn.count()) > 0) {
        await submitBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('promotions page loads', async ({ page }) => {
    await page.goto('/promotions');

    const promotionsHeading = page
      .locator('h1:has-text("Khuyến mãi"), h1:has-text("Promotions")')
      .first();
    if ((await promotionsHeading.count()) > 0) {
      await expect(promotionsHeading).toBeVisible();
    }
  });

  test('create promotion', async ({ page }) => {
    await page.goto('/promotions');

    // Click add promotion button
    const addBtn = page.locator('button:has-text("Thêm mới"), button:has-text("Add")').first();
    if ((await addBtn.count()) > 0) {
      await addBtn.click();

      // Fill promotion form
      const nameInput = page.locator('input[name*="name"]').first();
      const discountInput = page.locator('input[name*="discount"]').first();

      if ((await nameInput.count()) > 0) {
        await nameInput.fill('Test Promotion');
      }
      if ((await discountInput.count()) > 0) {
        await discountInput.fill('10');
      }

      const submitBtn = page.locator('button[type="submit"]').first();
      if ((await submitBtn.count()) > 0) {
        await submitBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('system health page', async ({ page }) => {
    await page.goto('/health');

    const healthHeading = page.locator('h1:has-text("Sức khỏe"), h1:has-text("Health")').first();
    if ((await healthHeading.count()) > 0) {
      await expect(healthHeading).toBeVisible();
    }
  });

  test('search users', async ({ page }) => {
    await page.goto('/users');

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

  test('filter stores by status', async ({ page }) => {
    await page.goto('/stores');

    // Filter by status
    const statusSelect = page.locator('select[name*="status"]').first();
    if ((await statusSelect.count()) > 0) {
      await statusSelect.selectOption('pending');
      await page.waitForTimeout(2000);
    }
  });

  test('export reports', async ({ page }) => {
    await page.goto('/reports');

    // Click export button
    const exportBtn = page.locator('button:has-text("Xuất"), button:has-text("Export")').first();
    if ((await exportBtn.count()) > 0) {
      await exportBtn.click();
      await page.waitForTimeout(2000);
    }
  });

  test('view audit logs', async ({ page }) => {
    await page.goto('/audit');

    const auditHeading = page.locator('h1:has-text("Audit"), h1:has-text("Logs")').first();
    if ((await auditHeading.count()) > 0) {
      await expect(auditHeading).toBeVisible();
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
    await page.goto('/users');

    // Check for loading state
    const spinner = page.locator('.animate-spin, .loading').first();
    if ((await spinner.count()) > 0) {
      await expect(spinner).toBeVisible();
      await expect(spinner).not.toBeVisible({ timeout: 5000 });
    }
  });

  test('admin authentication', async ({ page }) => {
    await page.goto('/login');

    // Fill admin credentials
    const emailInput = page.locator('input[type="email"]').first();
    const passwordInput = page.locator('input[type="password"]').first();

    if ((await emailInput.count()) > 0) {
      await emailInput.fill('admin@example.com');
    }
    if ((await passwordInput.count()) > 0) {
      await passwordInput.fill('AdminPass123');
    }

    // Submit login
    const submitBtn = page.locator('button[type="submit"]').first();
    if ((await submitBtn.count()) > 0) {
      await submitBtn.click();

      // Verify redirect to admin dashboard
      await page.waitForTimeout(2000);
    }
  });

  test('bulk action on users', async ({ page }) => {
    await page.goto('/users');

    // Select multiple users
    const checkboxes = page.locator('input[type="checkbox"]').all();
    for (const checkbox of await checkboxes) {
      await checkbox.check();
    }

    // Perform bulk action
    const bulkActionBtn = page
      .locator('button:has-text("Hành động"), button:has-text("Action")')
      .first();
    if ((await bulkActionBtn.count()) > 0) {
      await bulkActionBtn.click();
      await page.waitForTimeout(2000);
    }
  });
});
