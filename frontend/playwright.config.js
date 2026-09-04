import {defineConfig, devices} from "@playwright/test";

export default defineConfig({
    testDir: "./tests/e2e",
    timeout: 30000,
    fullyParallel: false,
    reporter: "list",
    use: {
        baseURL: "http://localhost:5173",
        browserName: "chromium",
        trace: "retain-on-failure",
    },
    projects: [
        {
            name: "chromium",
            use: {
                ...devices["Desktop Chrome"],
            },
        },
    ],
});