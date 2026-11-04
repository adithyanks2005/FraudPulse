# Progress

Commit after every class. Tag every Friday: `git tag week-N && git push origin week-N`.

## Week 1 (tag week-1 by Fri 23 Oct) — COMPLETED
- [x] Repo created from the Examate template and registered on the form
- [x] README top section filled from my project card (resolved merge conflicts)
- [x] /health and /ready run locally (pytest and local HTTP requests pass)
- [x] docs/QUESTIONS.md: 10 project-specific questions written with preliminary page mappings
- [x] 50+ pages collected, DATASET.md filled, sample in data/sample/ (171-page RBI FSR June 2025 collected, 5-page sample committed)
- [x] Tag week-1 pushed

## Week 2 (tag week-2 by Fri 30 Oct) — COMPLETED
- [x] LLM calls working with a fallback model (`app/llm/` provider architecture, SSE streaming, failover handling)
- [x] Usage endpoint exposes token usage and estimated cost (`app/cost.py`, `app/usage.py`, `GET /usage`)
- [x] /health and /ready run in Docker and are ready for deployment
- [x] CI checks pass on every push (13 unit tests pass, Ruff check and formatting clean)
- [x] DESIGN.md documents API endpoints and database tables (PostgreSQL + pgvector schema)
- [x] Tag week-2 pushed

## Week 3 (tag week-3 by Fri 6 Nov)
- [ ] Parser keeps page numbers and headings
- [ ] 500+ pages chunked, embedded and stored in pgvector
- [ ] POST /ask answers with [document, page] citations
- [ ] docs/EVAL_v0.md with my 10 questions scored
- [ ] Tag week-3 pushed

## Daily log
| Date | What I did today | Commit |
|---|---|---|
| 2026-10-23 | Created repository from Examate template, setup FastAPI /health endpoint, wrote initial project card and 10 research questions in docs/QUESTIONS.md. | `week-1` |
| 2026-10-30 | Deployed containerized health check, configured GitHub Actions CI pipeline, and initiated LLM and usage reporting architecture. | `week-2` |
| 2026-11-04 | Implemented complete LLM provider layer with streaming and fallback models (`app/llm`), cost logging and daily usage aggregation (`/usage`), created `DESIGN.md`, resolved README conflict, downloaded 171-page official RBI Financial Stability Report (June 2025) with 5-page sample, updated DATASET.md and manifest, and verified 13 pytest tests and Ruff linting pass. | `de135e1` |
