# E2E Testing with Playwright

## Overview

This project uses Playwright for end-to-end testing of the VietStore customer web application. Playwright provides reliable, fast cross-browser testing for modern web apps.

## Setup

Playwright is already installed and configured. The test suite includes:

- **Chromium** - Chrome/Edge browser testing
- **Firefox** - Firefox browser testing  
- **WebKit** - Safari browser testing

## Running Tests

### Run all tests
```bash
cd apps/web-customer
pnpm test:e2e
```

### Run tests in UI mode (interactive)
```bash
pnpm test:e2e:ui
```

### Run tests in debug mode
```bash
pnpm test:e2e:debug
```

### Run tests for specific browser
```bash
# Chromium only
pnpm test:e2e --project=chromium

# Firefox only
pnpm test:e2e --project=firefox

# WebKit only
pnpm test:e2e --project=webkit
```

### View test report
```bash
pnpm test:e2e:report
```

## Test Structure

Tests are located in `apps/web-customer/e2e/`:

- `basic.spec.ts` - Basic page load and error handling tests

## Configuration

Playwright configuration is in `playwright.config.ts`:

- **Base URL**: `http://localhost:3000`
- **Auto-start**: Dev server starts automatically before tests
- **Parallel execution**: Tests run in parallel across browsers
- **Timeout**: 30 seconds per test
- **Retries**: 2 retries in CI, 0 locally

## Writing New Tests

Create a new test file in `e2e/` directory:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test('test description', async ({ page }) => {
    await page.goto('/');
    // Your test code here
    await expect(page.locator('selector')).toBeVisible();
  });
});
```

## Best Practices

1. **Use specific selectors**: Prefer data-testid, aria-label, or specific attributes over generic selectors
2. **Wait for elements**: Use `await expect(element).toBeVisible()` instead of fixed timeouts
3. **Test user flows**: Test complete user journeys, not just individual components
4. **Keep tests independent**: Each test should be able to run in isolation
5. **Use test.describe**: Group related tests together

## Troubleshooting

### Tests fail with "Missing Publishable Key"
This is expected in test environment. The test suite filters out Clerk authentication errors.

### Dev server not starting
Ensure port 3000 is available. The test suite auto-starts the dev server.

### Browser not installed
Run: `npx playwright install chromium`

## CI/CD Integration

The test suite is configured for CI/CD with:
- Single worker mode in CI
- Automatic retries
- HTML test reports
- Trace on retry for debugging

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright Config Reference](https://playwright.dev/docs/test-configuration)
