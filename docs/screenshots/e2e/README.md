# E2E screenshots

Playwright writes **real browser captures** here when `npm run test:e2e` succeeds (`captureE2e` helper).

| File | Source test |
|------|-------------|
| `dashboard.png` | `workflows.spec.ts` |
| `dashboard-projects-list.png` | `projects.spec.ts` |
| `incident-explorer.png` | `incidents.spec.ts` |
| `incident-detail.png` | `incidents.spec.ts` |
| `rca-candidates.png` | `rca.spec.ts` |
| `rca-evidence.png` | `rca.spec.ts` |
| `investigation-report.png` | `rca.spec.ts` |
| `dashboard-overview-responsive.png` | `responsive.spec.ts` |

Regenerate: Postgres + API on port 8000, then `cd frontend && npm run test:e2e`.