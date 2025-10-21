# PLAN.md - Strategic Roadmap

Strategiczny roadmap projektu Sight. Utrzymujemy 20-30 najważniejszych zadań pogrupowanych według obszarów. Priorytety według MoSCoW: **High** (Must Have - blokuje inne zadania, security, production bugs), **Medium** (Should Have - ważne features, performance), **Low** (Could Have - nice-to-have, technical debt).

**Ostatnia aktualizacja:** 2025-10-21

---

## 🚀 Infrastructure & CI/CD

### High Priority

- [ ] **[High]** Add integration tests to CI/CD pipeline
  Obecnie tylko unit tests (240). Dodać ~30 integration tests z PostgreSQL/Neo4j dla core workflows (persona generation, focus groups). Target: 270+ tests total. Wymaga: pytest fixtures + Docker services w Cloud Build.

- [ ] **[High]** Fix race condition w KPI calculation (Redis lock)
  Concurrent calculations dla tej samej persony nadpisują swoje wyniki. Implementować distributed locking via Redis (`SETNX` key + TTL). Service: `PersonaKPIService:134-156`.

- [ ] **[High]** Implement automatic rollback w CI/CD
  Obecnie smoke tests failują ale deployment pozostaje broken. Dodać step 9 w cloudbuild.yaml: rollback do poprzedniej rewizji (`gcloud run services update-traffic --to-revisions=PREVIOUS=100`).

### Medium Priority

- [ ] **[Medium]** Setup Cloud Run custom domain
  Mapować custom domain (np. `app.sight.ai`) do Cloud Run service. Wymaga: weryfikacja domeny w Google Search Console, Cloud Run domain mapping, SSL cert (auto przez Google).

- [ ] **[Medium]** Migrate db-migrate job to use DATABASE_URL_SYNC
  Obecnie używa async driver (`asyncpg`) w sync context alembic. Stworzyć osobny `DATABASE_URL_SYNC` secret z `psycopg2` driver dla cleanszych migrations.

- [ ] **[Medium]** Add Cloud Monitoring alerts
  Skonfigurować alerty dla: error rate >1%, latency P95 >5s, Cloud SQL CPU >80%, Neo4j connection failures >5/min. Notification channel: email + Slack webhook.

### Low Priority

- [ ] **[Low]** Migrate to GitHub Actions (optional)
  Cloud Build działa dobrze, ale GitHub Actions ma lepszą integrację z repo (PR comments, checks API). Evaluate: czy warto migrować? Cost: GitHub free tier vs Cloud Build free 120min/day.

- [ ] **[Low]** Implement blue-green deployment
  Obecnie rolling deployment z health checks. Blue-green pozwoli na instant rollback (traffic switch). Wymaga: dwa Cloud Run services + Cloud Load Balancer.

---

## 🔧 Backend & API

### High Priority

- [ ] **[High]** Add RBAC enforcement do /personas endpoints
  Obecnie `/personas/{id}/details` nie sprawdza user role. Production wymaga: Viewer+ dla read, Editor+ dla mutations. Decorator: `@require_role("viewer")`.

- [ ] **[High]** Fix DB session leak w background tasks
  `asyncio.create_task` dla audit logging używa `self.db` która może być już closed. Stworzyć nową AsyncSession w task. Service: `PersonaAuditService:87-95`.

### Medium Priority

- [ ] **[Medium]** Optimize token usage w PersonaJourneyService
  Obecnie ~6000 tokens (max_tokens). Redukcja do ~2000: trim prompt, reduce RAG context 4000→500 chars, remove JSON schema (use structured output). Savings: ~67% tokens.

- [ ] **[Medium]** Add rate limiting per user
  Obecnie global rate limit (slowapi). Dodać per-user limits: 100 req/hour dla Free tier, 1000 req/hour dla Pro. Storage: Redis counter z TTL.

- [ ] **[Medium]** Implement Redis caching dla PersonaDetailsResponse
  Obecnie każdy request robi DB queries. Cache full response w Redis (TTL 5min). Cache hit <50ms vs miss <500ms. Key: `persona_details:{id}:{version}`.

### Low Priority

- [ ] **[Low]** Add missing `cac_ltv_ratio` field
  Frontend używa tego pola ale backend schema go nie zwraca. Dodać do `KPISnapshot` + calculation w `PersonaKPIService`. Formula: `cac / ltv * 100`.

- [ ] **[Low]** Refactor serwisów do domain folders
  Niektóre serwisy jeszcze w `app/services/` zamiast `app/services/<domain>/`. Przenieść: `PersonaMessagingService` → `personas/`, `AnalyticsService` → `analytics/`.

---

## 🤖 AI & RAG

### High Priority

- [ ] **[High]** Implement semantic chunking dla RAG
  Obecnie fixed-size chunks (1000 chars + 30% overlap). Semantic chunking respektuje sentence/paragraph boundaries. Libraries: LangChain `RecursiveCharacterTextSplitter` z sentence tokenizer.

### Medium Priority

- [ ] **[Medium]** Optimize hybrid search weights
  Obecnie vector:keyword = 0.7:0.3. A/B test różnych wag (0.5:0.5, 0.8:0.2, 0.6:0.4). Metryka: precision@5 dla test queries.

- [ ] **[Medium]** Implement LLM-powered customer journey generation
  PersonaDetailsService generuje 4 etapy journey z touchpoints, emocjami, buying signals. Model: Gemini 2.5 Pro. Output: structured (CustomerJourney Pydantic schema).

- [ ] **[Medium]** Add graph analytics do archived services
  `app/services/archived/graph_service.py` - concept/emotion extraction z focus groups. Restore: unhide z UI, dodać endpoint `/focus-groups/{id}/graph-analytics`.

### Low Priority

- [ ] **[Low]** Evaluate cross-encoder dla reranking
  Obecnie RRF fusion bez reranking. Cross-encoder (sentence-transformers) może improve precision. Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`. Latency: +100-200ms.

- [ ] **[Low]** Implement dynamic TOP_K dla RAG queries
  Obecnie fixed TOP_K=5. Dynamic TOP_K based on query complexity: simple queries → 3 chunks, complex → 8 chunks. Heuristic: query length + keyword count.

---

## 💻 Frontend

### Medium Priority

- [ ] **[Medium]** Add loading states do PersonaDetailsDrawer
  Obecnie brak skeleton loader podczas fetch. Dodać: 6 skeleton cards dla KPI, skeleton dla Big Five progress bars, skeleton dla audit timeline.

- [ ] **[Medium]** Implement compare personas feature
  Porównaj do 3 person side-by-side. Highlight differences, similarity score (cosine similarity embeddings). Shareable URL z 30-day expiry.

- [ ] **[Medium]** Add export functionality (PDF/CSV/JSON)
  PersonaDetailsDrawer dropdown: Export as PDF/CSV/JSON. PDF: watermark + PII masking (Admin może unmask). CSV: flat structure dla Excel.

### Low Priority

- [ ] **[Low]** Implement real-time collaboration (WebSocket)
  Comments na personie, @mentions z email notifications, tasks assigned do person. Status workflow: draft/active/archived/needs_review.

- [ ] **[Low]** Add dark mode toggle
  Tailwind dark mode classes. Toggle w settings page. Persistence: localStorage + Zustand store.

---

## 🧪 Testing & Quality

### High Priority

- [ ] **[High]** Increase coverage 80% → 85%
  Obecnie 80% overall. Target 85%+. Focus: uncovered branches w services, error handling paths, edge cases. Tool: `pytest --cov-report=html` → review `htmlcov/`.

- [ ] **[High]** Add e2e tests dla persona details MVP
  Brak e2e coverage dla PersonaDetailsDrawer. Scenarios: open drawer → verify KPI cards, delete persona → verify cascade, export persona → verify PDF content.

### Medium Priority

- [ ] **[Medium]** Setup pytest-xdist dla parallel test execution
  Obecnie unit tests ~60-90s sequential. Z `-n auto` (parallel): ~20-30s. Speedup 3x. Wymaga: thread-safe fixtures.

- [ ] **[Medium]** Add performance regression tests
  Benchmark kluczowych operations: persona generation, focus group, hybrid search. Fail jeśli >10% slowdown vs baseline. Tool: pytest-benchmark.

---

## 📚 Documentation

### Medium Priority

- [ ] **[Medium]** Add deployment runbook
  Step-by-step guide dla common operations: rollback deployment, update secrets, scale Cloud Run, debug failed build. Format: checklist + commands.

- [ ] **[Medium]** Create API changelog
  Track breaking changes, deprecations, new endpoints. Format: CHANGELOG.md z semantic versioning + migration guides.

### Low Priority

- [ ] **[Low]** Add architecture decision records (ADR)
  Dokumentuj kluczowe decyzje: dlaczego Cloud Run (not GKE), dlaczego Gemini (not OpenAI), dlaczego Neo4j (not PostgreSQL for graphs). Format: `docs/adr/001-cloud-run.md`.

---

## ✅ Completed (Last 30 days)

- [x] **Build test-runner Docker image for CI/CD** (2025-10-21)
  Zbudowano i wrzucono test-runner:latest do Artifact Registry (670MB z dependencies). Naprawia failed Cloud Builds (image not found error). Przyspiesza unit tests: 5min → <60s.

- [x] **Add retry logic for Gemini API rate limits** (2025-10-21)
  Dodano max_retries=3 do build_chat_model() w app/services/shared/clients.py. LangChain automatycznie obsługuje exponential backoff (1s → 2s → 4s). Zwiększa reliability przy rate-limited API calls.

- [x] **CRITICAL FIX: CORS blocking all API requests** (2025-10-21)
  Disabled CORS for production (same-origin deployment). Frontend i backend na tym samym origin = no CORS needed. Added API smoke test (test 5) w CI/CD. Removed ALLOWED_ORIGINS wildcard (FastAPI nie wspiera).

- [x] **Automated database migrations w CI/CD** (2025-10-21)
  Cloud Run Job `db-migrate` uruchamia `alembic upgrade head` przed każdym deployment. Zero-downtime migrations. Blocking step w pipeline.

- [x] **Neo4j indexes initialization po deploy** (2025-10-21)
  Cloud Run Job `neo4j-init` tworzy vector indexes automatycznie. Non-blocking (app działa bez RAG dopóki indexes się nie utworzą).

- [x] **Startup probe i enhanced healthcheck** (2025-10-21)
  `/startup` endpoint weryfikuje połączenia do PostgreSQL, Redis, Neo4j. Cloud Run czeka na healthy status przed routing traffic.

- [x] **Unit tests w CI/CD (blocking)** (2025-10-21)
  240+ unit tests wykonują się w Cloud Build. Linting (ruff), type checking (mypy), security scan (bandit). Deployment blokowany jeśli tests failują.

- [x] **Smoke tests po deployment - 5 tests** (2025-10-21)
  5 smoke tests weryfikują: /health, /startup, /docs, frontend SPA, API endpoint. Informują o broken deployment (brak automatic rollback - TODO).

- [x] **Docker image optimization** (2025-10-16)
  Multi-stage builds, layer caching, redukcja rozmiaru 84% (55GB → 11GB). Czas budowania -67%. Security: 54 CVE naprawione.

- [x] **Persona Details MVP** (2025-10-16)
  PersonaDetailsDrawer z 3 zakładkami: Overview (KPI cards), Profile (demografia + Big Five), Insights (RAG metadata + audit log). CRUD operations + audit trail.

- [x] **Service layer reorganization** (2025-10-20)
  Serwisy pogrupowane w domain folders: `personas/`, `focus_groups/`, `rag/`, `surveys/`. Import: `from app.services.personas import ...`.

- [x] **Documentation consolidation** (2025-10-21)
  DEPLOYMENT.md + DEVOPS.md → INFRASTRUCTURE.md (narracyjny styl). Archiwizacja PERFORMANCE_OPTIMIZATIONS.md. Stworzenie PLAN.md.

---

## 📊 Priority Summary

**Total Tasks:** 27 active + 9 completed

**By Priority:**
- High: 8 tasks (30%)
- Medium: 14 tasks (52%)
- Low: 5 tasks (18%)

**By Area:**
- Infrastructure & CI/CD: 8 tasks
- Backend & API: 6 tasks
- AI & RAG: 6 tasks
- Frontend: 5 tasks
- Testing & Quality: 4 tasks
- Documentation: 3 tasks

**Next Sprint Focus:**
1. Integration tests w CI/CD (Infrastructure)
2. RBAC enforcement (Backend)
3. Semantic chunking RAG (AI)
4. Coverage 85%+ (Testing)

---

**Uwaga:** Plan jest dynamiczny. Aktualizuj po każdym istotnym commit. Usuwaj completed tasks starsze niż 30 dni. Limit: 30 active tasks.
