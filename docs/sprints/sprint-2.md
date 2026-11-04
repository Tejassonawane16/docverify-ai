# Sprint 2 – Documents and human review

**Dates:** 13 – 22 November 2026  
**Sprint goal:** Applicants upload documents and follow their status; reviewers work through a
dashboard and make the final decision; applicants see feedback and upload corrected versions.

## Sprint planning

| Issue | User story | Priority | Points | Branch / PR |
|---|---|---|---|---|
| #4 | US-04 Upload documents (PDF/JPG/PNG, 10 MB, private storage) | Must | 5 | `feature/documents-and-review` |
| #5 | US-05 See the status of each document | Must | 2 | `feature/documents-and-review` |
| #6 | US-06 Read the reason and upload a corrected version | Should | 3 | `feature/documents-and-review` |
| #13 | US-13 Reviewer dashboard with filters and sorting | Must | 5 | `feature/documents-and-review` |
| #14 | US-14 Detail view: original document next to the report | Must | 3 | `feature/documents-and-review` |
| #15 | US-15 Final decision with comment | Must | 3 | `feature/documents-and-review` |
| #21 | US-21 Delete my account (frontend) | Should | 1 | `feature/documents-and-review` |
| – | README, sprint documentation | Must | 2 | `docs/phase-2-documentation` |
| | **Total planned** | | **24** | |

## Sprint review (22 Nov)

**Done (24 / 24 points):**

- Upload checked by file extension **and** file signature (a renamed `.exe` is rejected), size limit,
  random file names, files only downloadable through the API after an access check.
- Status per document: Uploaded, Processing, In review, Verified, Needs more information, Rejected.
- Version history: a corrected upload creates version 2 and keeps version 1.
- Reviewer dashboard: filter by status, search by applicant, sort by date or AI confidence.
- Detail view with the original PDF/image, a placeholder for the AI report (Phase 3), decision history.
- Decisions require a comment when rejecting, asking for information or overriding the AI.
- Applicants can delete their account and all files.

**Demo (end-to-end):** applicant uploads a transcript → reviewer asks for more information →
applicant sees the message and uploads version 2 → admin checks the audit log.

**Test status:** 35 backend tests, 3 AI-service tests, 9 frontend tests; CI green on `main`.

**Not done / moved to Phase 3:** AI recommendation, confidence score and report (US-07 – US-12)
are shown as placeholders; the fields already exist in the data model and the dashboard.

## Retrospective

| What went well | What to improve | Action for Phase 3 |
|---|---|---|
| The data model already has fields for the AI result, so Phase 3 can plug in | No automated browser (E2E) tests yet | Add Playwright E2E tests to CI (needed in Phase 4) |
| Small, focused PRs were easy to review | Manual testing of uploads took time | Create a set of synthetic test documents early (also needed in Phase 4) |
| Branch protection kept `main` green | | |
