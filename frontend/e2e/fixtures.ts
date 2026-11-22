import { test as base, type Page } from "@playwright/test";

import { PulseTraceApi } from "./helpers/api";
import { trackConsoleErrors } from "./helpers/assertions";
import { primeSession } from "./helpers/auth-browser";

export const E2E_API_URL = process.env.E2E_API_URL ?? "http://127.0.0.1:8000";

type E2EFixtures = {
  api: PulseTraceApi;
  logReady: { email: string; token: string; projectId: string; projectName: string };
  incidentReady: {
    email: string;
    token: string;
    projectId: string;
    projectName: string;
    incidentId: string;
    incidentTitle: string;
  };
  authedPage: Page;
};

export const test = base.extend<E2EFixtures>({
  api: async ({ request }, use) => {
    const api = new PulseTraceApi(request, E2E_API_URL);
    await api.assertReachable();
    await use(api);
  },

  logReady: async ({ api }, use, testInfo) => {
    const workspace = await api.createLogReadyWorkspace(testInfo.project.name);
    await use(workspace);
  },

  incidentReady: async ({ api }, use, testInfo) => {
    const workspace = await api.createIncidentReadyWorkspace(testInfo.project.name);
    await use(workspace);
  },

  authedPage: async ({ page, logReady }, use) => {
    trackConsoleErrors(page);
    await primeSession(page, logReady.token);
    await use(page);
  },
});

export { expect } from "@playwright/test";