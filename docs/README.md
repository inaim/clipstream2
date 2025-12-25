# 📚 ClipStream Documentation Hub

All of the deep-dive guides, runbooks, and historical notes have been relocated
to this `docs/` directory so contributors have a single place to look for
reference material. Anything that still mentions Supabase or legacy service
dependencies was updated or archived—every doc listed below now reflects the
SurrealDB-first, multi-modal ClipStream stack.

## 🔎 Document Map

| File | Focus |
| --- | --- |
| `ARCHITECTURE.md` | System diagrams, data flows, and infra topology |
| `BACKEND_FIXES_COMPLETE.md` | Source-of-truth for backend migration + health checklist |
| `BACKEND_FRONTEND_INTEGRATION.md` | Contract between FastAPI + React clients (REST + GraphQL) |
| `CLOUD_RUN_DEPLOYMENT.md` | Google Cloud Run build + deploy playbook |
| `COMPLETE_SYSTEM_SUMMARY.md` | Executive summary of every subsystem |
| `CONTRIBUTING.md` | Contributor onboarding, coding standards, governance |
| `FRONTEND_MOBILE_API_GUIDE.md` | Mobile + web client API usage (SurrealDB adapter examples) |
| `IMPLEMENTATION_SUMMARY.md` | Point-in-time implementation state + open work |
| `MOBILE_APPS_COMPLETE.md` | Native mobile build + release process |
| `MOBILE_READY.md` | Mobile UX + performance acceptance criteria |
| `PRODUCTION_DEPLOYMENT.md` | Step-by-step production rollout + smoke checks |
| `Paragraph_article.md` | Narrative overview of the CDN/IPFS hybrid demo |
| `SCOPING_BETA.md` | MVP and beta scope, KPIs, and gating criteria |
| `SUPABASE_TO_SURREALDB_MIGRATION.md` | Historical record of the Supabase → SurrealDB cut-over |
| `TESTING_GUIDE.md` | Detailed manual + automated test plans |

## 🧭 How to Use the Hub

1. **Start with `COMPLETE_SYSTEM_SUMMARY.md`** for context, then dive into the
   architecture or integration docs that match your task.
2. **Use `FRONTEND_MOBILE_API_GUIDE.md`** when wiring up clients—examples now
   call the SurrealDB-backed REST APIs via the compatibility layer in
   `frontend/src/lib/surrealdb.ts`.
3. **Follow `TESTING_GUIDE.md` together with the new mobile-to-publish E2E test
   harness** (see the top-level README) whenever you need to validate uploads,
   LLM/MCP verification, and publishing state transitions.
4. **Check `PRODUCTION_DEPLOYMENT.md` or `CLOUD_RUN_DEPLOYMENT.md`** depending
   on whether you are targeting self-hosted clusters or Google Cloud.

If you spot drift or missing topics, open an issue or PR that updates the
appropriate file in this directory so everything stays centralized.
