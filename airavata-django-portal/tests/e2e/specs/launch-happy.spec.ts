import { test, expect } from "../fixtures/auth";

test("launch a stub experiment via /workspace/launch", async ({ page }) => {
  await page.goto("/workspace/launch");
  await expect(page.getByPlaceholder(/Experiment name/i)).toBeVisible();

  await page.getByPlaceholder(/Experiment name/i).fill("e2e-stub");

  // Project picker — pick whatever's available (index 1 = first real option)
  const projectSelect = page.locator("select[data-test='exp-project']");
  await projectSelect.selectOption({ index: 1 });

  // App + interface (stub returns NAMD)
  await page.locator("[data-test='app-tile-namd']").click();
  await page.locator("[data-test='iface-card-run']").click();

  // Inputs
  // sim_dir is a dir; pick a storage and a path
  const storageSelects = page.locator("select").filter({ hasText: /My Home|Bridges/ });
  await storageSelects.first().selectOption({ index: 1 });
  await page.locator("input[data-test='file-path-sim_dir']").fill("/home/x/sim");
  await page.locator("input[data-test='scalar-steps']").fill("100");

  // Output: trajectory
  await page.locator("input[data-test='file-out-path-trajectory']").fill("/home/x/out.dcd");

  // Tab 2
  await page.locator("button[role='tab']").nth(1).click();
  await page.locator("select[data-test='cr']").selectOption("bridges-2");
  await page.locator("select[data-test='partition']").selectOption("RM");

  // Tab 3
  await page.locator("button[role='tab']").nth(2).click();
  await expect(page.locator("pre code")).toContainText("#!/bin/bash");
  await page.locator("button[data-test='launch']").click();

  await page.waitForURL(/\/workspace\/experiments\//);
});
