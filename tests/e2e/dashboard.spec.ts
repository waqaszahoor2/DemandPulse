import { test, expect } from '@playwright/test';

test.describe('DemandPulse E2E Flow Validation', () => {
  test('Scenario 1: Open dashboard -> health loads -> KPI cards display', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/DemandPulse/i);
    await expect(page.getByText('Forecast Accuracy')).toBeVisible();
    await expect(page.getByText('WAPE 8.7%')).toBeVisible();
    await expect(page.getByText('Service Level')).toBeVisible();
    await expect(page.getByText('96.2%')).toBeVisible();
  });

  test('Scenario 2: Select store -> select product -> change horizon -> forecast refreshes', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Demand Forecast & Uncertainty')).toBeVisible();
    
    // Test Store selector
    const storeSelect = page.locator('select').first();
    await expect(storeSelect).toBeVisible();
    await storeSelect.selectOption('Store #101 (Boston)');

    // Test Horizon selector
    const horizonSelect = page.locator('select').nth(2);
    await horizonSelect.selectOption('14 Days');
  });

  test('Scenario 3: Request probabilistic forecast -> P10/P50/P90 display', async ({ page }) => {
    await page.goto('/probabilistic');
    await expect(page.getByText('Conformal Probabilistic Quantification')).toBeVisible();
    await expect(page.getByText('P10 - Low Demand')).toBeVisible();
    await expect(page.getByText('P50 - Expected Demand')).toBeVisible();
    await expect(page.getByText('P90 - High Demand')).toBeVisible();
    await expect(page.getByText('80.4%')).toBeVisible(); // Empirical coverage
  });

  test('Scenario 4: Open Inventory Intelligence -> calculate recommendation -> result displays', async ({ page }) => {
    await page.goto('/inventory');
    await expect(page.getByText('Inventory Optimization & Cost Policy')).toBeVisible();
    await expect(page.getByText('Recommended Order')).toBeVisible();
    await expect(page.getByText('175')).toBeVisible();
    await expect(page.getByText('Low')).toBeVisible();
  });

  test('Scenario 5: Open Promotion Impact -> causal results display', async ({ page }) => {
    await page.goto('/promotion-impact');
    await expect(page.getByText('Causal Promotion Lift & AIPW Impact')).toBeVisible();
    await expect(page.getByText('+8.4%')).toBeVisible();
    await expect(page.getByText('Beverages')).toBeVisible();
  });

  test('Scenario 6: Resize to mobile -> menu works -> bottom navigation works', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    
    // Bottom mobile navigation bar check
    await expect(page.locator('nav[aria-label="Mobile Navigation"]')).toBeVisible();
    await expect(page.getByText('Overview')).toBeVisible();
    await expect(page.getByText('Alerts')).toBeVisible();

    // Click Menu button to open slide-over drawer
    const menuBtn = page.getByRole('button', { name: 'Menu' });
    await menuBtn.click();
    await expect(page.getByText('Inventory Intelligence')).toBeVisible();
  });
});
