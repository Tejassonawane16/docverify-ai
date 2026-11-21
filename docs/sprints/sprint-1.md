# Sprint 1 – Platform, accounts and roles

**Dates:** 4 – 12 November 2026  
**Sprint goal:** All five services start with one `docker compose up`, the CI pipeline is green,
and users can register, log in and get access according to their role.

## Sprint planning

| Issue | User story | Priority | Points | Branch / PR |
|---|---|---|---|---|
| – | Project setup: Docker Compose (5 services), CI pipeline, repository structure | Must | 5 | `feature/project-setup` |
| #1 | US-01 Register as applicant | Must | 2 | `feature/auth-roles-admin` |
| #2 | US-02 Log in and log out (lockout, token revocation) | Must | 3 | `feature/auth-roles-admin` |
| #3 | US-03 Admin creates staff accounts and assigns roles | Must | 3 | `feature/auth-roles-admin` |
| #19 | US-19 Audit log | Should | 3 | `feature/auth-roles-admin` |
| #21 | US-21 Delete my account and data (backend) | Should | 2 | `feature/auth-roles-admin` |
| | **Total planned** | | **18** | |

Capacity: about 12 hours, alongside lectures and part-time work.

## Technical decisions

| Decision | Reason |
|---|---|
| FastAPI + SQLAlchemy for the backend | Python is also used for the AI service (Phase 3); automatic OpenAPI docs |
| React + Vite, served by nginx | nginx also proxies `/api`, so frontend and API share one origin (no CORS issues) |
| PostgreSQL for data, Qdrant as vector database | Qdrant runs as its own container and is ready for the RAG pipeline |
| JWT bearer tokens with a deny-list on logout | Stateless API, but logout still invalidates the token (US-02 AC4) |
| Role read from the database on every request | Role changes take effect immediately (US-03 AC2) |
| Tests use SQLite | Fast, no database container needed in CI unit tests |
| Audit log without foreign keys, pseudonymous `user-<id>` | Entries survive account deletion (US-19, US-21) |

## Sprint review (12 Nov)

**Done (18 / 18 points):**

- `docker compose up --build` starts frontend, backend, ai-service, PostgreSQL and Qdrant.
- CI runs lint, tests, frontend build, Docker image build and a smoke test on every push and PR.
- Registration with password rules, login with a generic error message and lockout after 5 failed
  attempts in 10 minutes, logout that revokes the token.
- Role-based access (403 for wrong role), admin user management, read-only audit log, statistics.
- Login, registration and admin pages in the frontend.

**Demo:** register → log in → admin creates a reviewer → reviewer gets 403 on admin endpoints →
admin changes a role and the change applies on the next request → audit log shows every step.

## Retrospective

| What went well | What to improve | Action for Sprint 2 |
|---|---|---|
| CI from day one caught lint and test failures early | The first Docker build was slow | Keep Docker layers ordered: requirements before source code |
| Writing acceptance criteria as tests made "done" clear | Some issues were too large for one PR | Split work into smaller PRs per user story |
| | Email validation rejected `.local` addresses for the seed admin | Validate format at registration only; test edge cases earlier |
