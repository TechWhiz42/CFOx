import {expect, test} from "@playwright/test";

test("registers, logs in, and opens dashboard", async ({page}) => {
    const timestamp = Date.now();
    const email = `e2e-${timestamp}@example.com`;
    const password = "StrongPassword123";

    await page.goto("/");

    await page.getByRole("button", {
        name: /create account/i,
    }).click();

    await page
        .getByRole("textbox", {
            name: "Email",
            exact: true,
        })
        .fill(email);

    await page
        .getByRole("textbox", {
            name: "Password",
            exact: true,
        })
        .fill(password);

    await page
        .getByRole("textbox", {
            name: "Confirm password",
            exact: true,
        })
        .fill(password);

    await page.getByRole("button", {
        name: /^create account$/i,
    }).click();

    await expect(
        page.getByRole("heading", {
            name: /financial overview/i,
        })
    ).toBeVisible({
        timeout: 15000,
    });

    await expect(
        page.getByText(email)
    ).toBeVisible();
});