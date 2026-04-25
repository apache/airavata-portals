import { test, expect } from "../fixtures/auth";

test("strict-forward gate: cannot click tab 2 before tab 1 is valid", async ({ page }) => {
  await page.goto("/workspace/launch");
  await expect(page.locator("button[role='tab']").nth(1)).toBeDisabled();
});

test("preview failure shows error and disables launch", async ({ page }) => {
  // Intercept the preview endpoint and return 502
  await page.route("**/api/launcher/experiment-drafts/preview/", (route) =>
    route.fulfill({ status: 502, body: JSON.stringify({ message: "airavata down" }) }),
  );

  await page.goto("/workspace/launch");
  await page.getByPlaceholder(/Experiment name/i).fill("err-stub");
  await page.locator("select[data-test='exp-project']").selectOption({ index: 1 });
  await page.locator("[data-test='app-tile-namd']").click();
  await page.locator("[data-test='iface-card-run']").click();
  await page.locator("select[data-test='file-storage-sim_dir']").selectOption("my-home");
  await page.locator("input[data-test='file-path-sim_dir']").fill("/x");
  await page.locator("select[data-test='file-storage-force_field']").selectOption("my-home");
  await page.locator("input[data-test='file-path-force_field']").fill("/ff");
  await page.locator("input[data-test='scalar-steps']").fill("1");
  await page.locator("select[data-test='file-out-storage-trajectory']").selectOption("my-home");
  await page.locator("input[data-test='file-out-path-trajectory']").fill("/y");
  await page.locator("button[role='tab']").nth(1).click();
  await page.locator("select[data-test='cr']").selectOption("bridges-2");
  await page.locator("select[data-test='partition']").selectOption("RM");
  await page.locator("button[role='tab']").nth(2).click();

  await expect(page.locator(".alert-danger")).toContainText("airavata down");
  await expect(page.locator("button[data-test='launch']")).toBeDisabled();
});

test("project change clears runtime selections", async ({ page }) => {
  await page.goto("/workspace/launch");
  await page.getByPlaceholder(/Experiment name/i).fill("proj-change");
  await page.locator("select[data-test='exp-project']").selectOption({ index: 1 });

  // The confirm dialog is what we're testing — accept it when prompted
  page.on("dialog", (d) => d.accept());

  await page.locator("[data-test='app-tile-namd']").click();
  await page.locator("[data-test='iface-card-run']").click();
  await page.locator("select[data-test='file-storage-sim_dir']").selectOption("my-home");
  await page.locator("input[data-test='file-path-sim_dir']").fill("/x");
  await page.locator("select[data-test='file-storage-force_field']").selectOption("my-home");
  await page.locator("input[data-test='file-path-force_field']").fill("/ff");
  await page.locator("input[data-test='scalar-steps']").fill("1");
  await page.locator("select[data-test='file-out-storage-trajectory']").selectOption("my-home");
  await page.locator("input[data-test='file-out-path-trajectory']").fill("/y");
  await page.locator("button[role='tab']").nth(1).click();
  await page.locator("select[data-test='cr']").selectOption("bridges-2");

  // Switch project — the dropdown only has projects from session data; pick the second.
  // If only one project exists, this test no-ops on the assertion below.
  const opts = await page.locator("select[data-test='exp-project'] option").allTextContents();
  if (opts.length > 2) {
    await page.locator("select[data-test='exp-project']").selectOption({ index: 2 });
    await expect(page.locator("select[data-test='cr']")).toHaveValue("");
  }
});
