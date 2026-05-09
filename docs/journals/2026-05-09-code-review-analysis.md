# Code Review Analysis — 2026-05-09

## Scope

Full codebase audit: 60 Python files, ~5.3K LOC, FastAPI + Mezon SDK + PostgreSQL.

**Method:** Scout → 3 parallel code-reviewers → adversarial review → synthesis

**Result:** 40/40 tests passed, all key files compile OK

---

## Findings Summary

### Critical (10 — Block Production)
1. **Button ID authorization bypass** — Any user can access/edit/delete any resource via crafted button IDs (no ownership check, sequential IDs trivial to guess)
2. **Path traversal in Word export** — User-controlled `expert_name` and `order_id` used directly in filenames without sanitization
3. **SQL injection via ILIKE** — `f"%{name}%"` in repository query, no wildcard escaping
4. **CORS wildcard with credentials** — `allow_origins=["*"]` + `allow_credentials=True` enables CSRF
5. **No API authentication** — `/api/v1/bot/status` publicly accessible
6. **Soft-delete filter bypass** — `get_by_id()`, `find_by_name()`, `find_by_id_number()` return deleted records
7. **Vietnamese text converter DoS** — No upper bound on number input, extreme values cause OOM
8. **Unvalidated button ID parsing** — 14 instances of `int(button_id.split(":")[1])` without try/except
9. **Race condition in contract recalculation** — Concurrent updates can overwrite totals, no row locking
10. **Database pool without timeouts** — No `pool_recycle`, `pool_timeout`, or statement timeout

### Important (8 — Fix Before Next Phase)
11. Expert handler 1907 LOC (9.5x over limit)
12. N+1 query in contract repository
13. Generic exception catching (19 instances)
14. Form tracker memory leak risk (in-memory, no eviction)
15. No rate limiting (API + bot commands)
16. Secrets in .env.example
17. Missing database error handling (no IntegrityError/OperationalError handling)
18. Insecure default host (0.0.0.0)

### Minor (9 — Technical Debt)
19. No request ID tracking
20. Logging too simplistic
21. Health check incomplete
22. Missing composite indexes
23. No OpenAPI schema validation
24. S3 upload errors silently swallowed
25. Word export uses sync operations
26. Test coverage gaps
27. No graceful shutdown

---

## Decisions Made

| Question | Decision |
|----------|----------|
| Deployment environment | Docker |
| Expected concurrent users | <20 |
| PII compliance requirements | Not a concern |
| Mezon API rate limit docs | Not needed |
| Form state persistence | **Should persist** across restarts (needs DB/Redis, not memory) |
| Third-party audit required | **Yes** |
| Template_HDCG.docx Jinja2 safety | **Safe** (escaped variables) |
| Button events authenticated by Mezon | **No** — confirms authorization bypass severity |

---

## Action Items

### Immediate (Before Production)
1. Add authorization checks on all button handlers — verify `event.user_id` owns resource
2. Sanitize user-controlled inputs used in file paths (Word export)
3. Escape LIKE wildcards or use parameterized queries
4. Fix CORS to use specific allowed origins
5. Add API authentication middleware
6. Add soft-delete filter to all repository queries
7. Add upper bound to Vietnamese text converter
8. Wrap button ID parsing in try/except
9. Add row-level locking to contract recalculation
10. Configure database pool timeouts

### Short Term
- Modularize `expert.py` (1907 LOC → ~5 files)
- Fix N+1 query with `selectinload()`
- Add structured error handling
- Implement form state persistence (DB or Redis)
- Add rate limiting (slowapi or token bucket)

### Backlog
- Request ID tracking
- Structured logging with rotation
- Composite database indexes
- Async Word export
- Test coverage for repositories and error paths
- Graceful shutdown handling

---

## Technical Debt Noted

- **expert.py**: 1907 LOC, 9.5x over 200 LOC limit — highest priority refactor
- **Form tracker**: In-memory with no eviction — will OOM on long-running bot
- **Generic exception catching**: 19 instances mask real errors
- **Test coverage**: Only acceptance + Word export tests (40 total), no repository/handler_manager/error path tests
