# Progress

Commit after every class. Tag every Friday: `git tag week-N && git push origin week-N`.

## Week 1 (tag week-1 by Fri 23 Oct)
- [ ] Repo created from the Examate template and registered on the form
- [ ] README top section filled from my project card
- [ ] /health runs locally
- [ ] docs/QUESTIONS.md: 10 real questions
- [ ] 50+ pages collected, DATASET.md filled, sample in data/sample/
- [ ] Tag week-1 pushed

## Week 2 (tag week-2 by Fri 30 Oct)
- [ ] POST /chat calls an LLM and returns structured JSON
- [ ] Streaming, timeouts, retry and a fallback model
- [ ] Cost log + GET /usage
- [ ] Docker Compose (API + Postgres/pgvector) runs
- [ ] CI green, live link in README
- [ ] Tag week-2 pushed

## Week 3 (tag week-3 by Fri 6 Nov)
- [ ] Parser keeps page numbers and headings
- [ ] 500+ pages chunked, embedded and stored in pgvector
- [ ] POST /ask answers with [document, page] citations
- [ ] docs/EVAL_v0.md with my 10 questions scored
- [ ] Tag week-3 pushed

## Daily log
| Date | What I did today | Commit |
|---|---|---|
| | | |

## Week 2 summary (Sessions 5 and 6)

- Session 5: streaming /chat over SSE, safe retries, fallback model, cost log per call, /usage endpoint.
- Session 6: /ready readiness route (checks Postgres, returns 503 if down), Dockerfile, docker-compose with API + pgvector, .dockerignore.
- /health is liveness (no database call); /ready is readiness (database reachable).
- Secrets: .env is never committed; compose sets DATABASE_URL for local development only.
- CI: GitHub Actions runs ruff and pytest. Fixed an import error by using python -m pytest.
- Tests: 15 passing locally and on GitHub.
- Run locally: docker compose up --build, then GET /health and GET /ready.
- Stop everything: docker compose down (add -v to also delete the database volume).
- Lesson: an image is the built package, a container is a running copy of it.
