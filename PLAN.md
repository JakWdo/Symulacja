# PLAN.md - Roadmap & Strategic Tasks

**Market Research SaaS** - Platforma do wirtualnych grup fokusowych z AI

**Ostatnia aktualizacja:** 2025-10-15 - Dostosowanie do rzeczywistego stanu projektu

---

## 🎯 Przegląd Stanu Projektu

**Status Ogólny:** 5.5/10 - DEVELOPMENT MODE (Docker down, testy nie przechodzą)

**Kluczowe Metryki:**
- Test Coverage: Unknown (380 testów zebranych, ale nie mogą działać - Docker services down)
- Architektura: 8.0/10 - Service Layer Pattern, Async/Await, nowa struktura RAG (3 serwisy)
- Security: 5.0/10 - GOOGLE_API_KEY w repozytorium, DEFAULT SECRET_KEY, DEBUG=True
- DevOps: 3.0/10 - Docker nie działa, brak CI/CD, brak monitoringu

**KRYTYCZNE PROBLEMY:**
- ❌ **Docker services nie działają** - postgres, redis, neo4j, api, frontend (0/5 running)
- ❌ **GOOGLE_API_KEY w .env** (exposed w git) - NATYCHMIASTOWA ROTACJA WYMAGANA
- ❌ **Testy nie mogą działać** - timeout bo brak działających dependencies
- ❌ **DOCKER.md usunięty** - ale jest DEVOPS.md i TROUBLESHOOTING.md

**Ostatnie Osiągnięcia (październik 2025):**
- [x] RAG System - Split na 3 serwisy (RAGDocumentService, RAGGraphService, RAGHybridSearchService) (data: 2025-10-15)
- [x] Hybrid Search - Optymalizacja (chunking 1000, reranking, RRF fusion) (data: 2025-10-14)
- [x] Security Fixes - 8 critical/high issues (bare except, indexes, sanitization) (data: 2025-10-14)
- [x] Graph Service - Archiwizacja legacy features (data: 2025-10-15)
- [x] Test Infrastructure - Factories, fixtures, 380 testów (data: 2025-10-15)
- [x] Documentation - DEVOPS.md, TROUBLESHOOTING.md, QUICKSTART.md (data: 2025-10-15)
- [x] **Segment-Based Persona Architecture** - Refactor z loose orchestration na structured segments (data: 2025-10-15)

---

## 🚨 TIER 0: IMMEDIATE FIXES (TODAY!)

### Critical Security (DO FIRST!)
- [ ] [Priority: 100] **ROTATE GOOGLE_API_KEY** - Key exposed w .env committed to git - NATYCHMIAST - 15min
  - Unieważnij AIzaSyDB92Edj_MGJsBuyK21J0gcupofvO1ZVQ8 w Google Cloud Console
  - Wygeneruj nowy klucz
  - Dodaj .env do .gitignore (jeśli nie ma)
  - Git commit z usunięciem klucza, ale NIE push starego history!
- [ ] [Priority: 100] **Git history cleanup** - Usuń GOOGLE_API_KEY ze wszystkich commitów (git filter-branch lub BFG) - 30min
- [ ] [Priority: 98] **Zmień SECRET_KEY** - "your_secret_key_here_change_in_production" to default placeholder - 5min

### Infrastructure (GET WORKING!)
- [ ] [Priority: 99] **Uruchom Docker services** - postgres, redis, neo4j, api, frontend (docker-compose up -d) - 10min
  - Diagnoza: dlaczego services są down
  - Fix: docker-compose.yml issues
  - Verify: docker-compose ps pokazuje 5/5 running
- [ ] [Priority: 95] **Inicjalizacja Neo4j indexes** - python scripts/init_neo4j_indexes.py (WYMAGANE dla RAG!) - 5min
- [ ] [Priority: 90] **Verify test suite** - python -m pytest tests/ -v (sprawdź czy 380 testów przechodzi) - 30min

---

## 🚨 TIER 1: PRODUCTION BLOCKERS (Week 1)

### Security & Dependencies
- [ ] [Priority: 95] Upgrade vulnerable dependencies (npm audit, pip-audit, fix CVEs) - 5h
- [ ] [Priority: 95] Docker secrets management (użyj Docker secrets lub AWS SSM zamiast .env) - 4h
- [ ] [Priority: 90] Validate SECRET_KEY at startup (check != default, length ≥32, entropy check) - 1h
- [ ] [Priority: 90] Disable DEBUG by default (raise error if DEBUG=True + ENVIRONMENT=production) - 30min

### New RAG Architecture Integration
- [ ] [Priority: 92] **Testy dla nowych serwisów RAG** - test_rag_document_service.py, test_rag_graph_service.py, test_rag_hybrid_search_service.py (sprawdź integrację) - 4h
- [ ] [Priority: 90] **Update API endpoints** - app/api/rag.py używa nowych serwisów (RAGDocumentService, RAGGraphService, RAGHybridSearchService) - 2h
- [ ] [Priority: 88] **Migration guide** - Dokumentacja migracji z monolitycznego rag_service.py do 3 serwisów - 1h

### CI/CD & Infrastructure
- [ ] [Priority: 95] GitHub Actions workflow (lint → test → security scan → build) - 8h
- [ ] [Priority: 85] Health check endpoints (/health/live, /health/ready, /health/startup) - 2h
- [ ] [Priority: 80] Automated backups (Postgres daily, Neo4j weekly, S3/local storage) - 4h

### Authentication & Authorization
- [ ] [Priority: 88] JWT token blacklist (Redis-based revocation, TTL = token expiration) - 6h
- [ ] [Priority: 85] Account lockout mechanism (5 failed attempts → 15min lockout, Redis counter) - 6h

---

## 🎯 TIER 2: OPTIMIZATION & STABILITY (Week 2-3)

### RAG System Stabilization
- [ ] [Priority: 85] **RAG integration tests end-to-end** - Test RAGDocumentService → RAGGraphService → RAGHybridSearchService workflow - 8h
- [ ] [Priority: 82] **Neo4j connection pooling** - Implement proper connection pool dla RAGGraphService (max_size=50, timeout=30s) - 3h
- [ ] [Priority: 80] **GraphRAG schema validation** - Ensure consistent node properties, improve fill-rate (target: 85%+) - 6h
- [ ] [Priority: 75] **RAG error handling** - Comprehensive error handling dla chunking, embeddings, graph construction failures - 4h

### AI/LLM Optimization
- [ ] [Priority: 80] **PersonaGenerator prompt compression** - 700 lines → 250 lines (reduce token usage ~55%) - 4h
- [ ] [Priority: 78] **LLM retry logic** - Exponential backoff, circuit breaker (3 retries, 60s cooldown) - 3h
- [ ] [Priority: 75] **Token usage tracking** - Log token consumption per request (persona generation, focus groups, RAG) - 2h

### Performance & Caching
- [ ] [Priority: 80] **Redis caching layer Phase 1** - Cache persona profiles (TTL: 24h), focus groups (TTL: 7d) - 8h
- [ ] [Priority: 75] **Redis caching layer Phase 2** - Cache RAG queries (TTL: 1h), hybrid search results - 6h
- [ ] [Priority: 70] **Connection pooling optimization** - SQLAlchemy (pool_size=20), Neo4j (max_size=50), Redis (max_connections=50) - 4h

### Testing & Quality
- [ ] [Priority: 75] **Test suite stability** - Fix timeout issues, ensure all 380 tests pass consistently - 4h
- [ ] [Priority: 72] **Fix flaky E2E tests** - test_e2e_full_workflow.py, test_e2e_survey_workflow.py (increase timeouts, add retries) - 2h
- [ ] [Priority: 68] **Test coverage analysis** - Identify untested code paths, prioritize critical paths - 3h

---

## 🔧 TIER 3: ENHANCEMENTS & POLISH (Week 4+)

### Code Quality & Refactoring
- [ ] [Priority: 65] **Refactor PersonaOrchestration** - Simplify persona_orchestration.py (lepszy error handling, logging) - 4h
- [ ] [Priority: 62] **Refactor _generate_personas_task** - Split 250 lines → 4 methods, reduce complexity (18 → <10) - 6h
- [ ] [Priority: 58] **Standardize error logging** - Structured JSON logs, correlation IDs, consistent log levels - 6h
- [ ] [Priority: 55] **Code quality metrics** - Setup SonarQube/CodeClimate, track complexity, duplication - 4h

### DevOps & Monitoring
- [ ] [Priority: 68] **Prometheus + Grafana setup** - Dashboards dla FastAPI metrics, DB, Redis, Neo4j, LLM tokens - 12h
- [ ] [Priority: 65] **Docker network isolation** - Separate networks: frontend, backend, database - 3h
- [ ] [Priority: 60] **Resource limits** - docker-compose CPU/memory limits, restart policies - 2h
- [ ] [Priority: 58] **Image vulnerability scanning** - Trivy w CI, fail on HIGH/CRITICAL CVEs - 6h

### Security & Compliance
- [ ] [Priority: 58] **API audit logging** - Log user_id, endpoint, method, timestamp, IP (retention: 90d) - 8h
- [ ] [Priority: 55] **MFA implementation** - TOTP 2FA, QR setup, backup codes - 12h
- [ ] [Priority: 52] **GDPR compliance checks** - Data retention policies, user data export/delete - 8h

### Features & UX
- [ ] [Priority: 55] **Persona quality dashboard** - Metrics: diversity, RAG usage, latency (Grafana) - 10h
- [ ] [Priority: 50] **Real-time progress indicators** - WebSocket/SSE dla persona generation, focus groups - 12h
- [ ] [Priority: 48] **Export functionality** - Export focus groups, personas to PDF/CSV/JSON - 8h

---

## 📊 Podział Zadań według Obszarów

**TIER 0 (CRITICAL):** 6 zadań - Security + Infrastructure (DO TODAY!)
**TIER 1 (BLOCKERS):** 12 zadań - Security, RAG Integration, CI/CD, Auth (Week 1)
**TIER 2 (OPTIMIZATION):** 13 zadań - RAG Stabilization, AI/LLM, Performance, Testing (Week 2-3)
**TIER 3 (ENHANCEMENTS):** 15 zadań - Code Quality, DevOps, Security, Features (Week 4+)

**Total:** 46 zadań strategicznych (3 tiers + critical)

---

## 🎯 Quick Wins (≤2h, High Impact)

Zadania do natychmiastowego wykonania:
1. **ROTATE GOOGLE_API_KEY** (15min) - Priority: 100
2. **Zmień SECRET_KEY** (5min) - Priority: 98
3. **Uruchom Docker** (10min) - Priority: 99
4. **Init Neo4j indexes** (5min) - Priority: 95
5. **Disable DEBUG by default** (30min) - Priority: 90
6. **Health check endpoints** (2h) - Priority: 85
7. **Resource limits in docker-compose** (2h) - Priority: 60
8. **Fix flaky E2E tests** (2h) - Priority: 72

**Total Quick Wins:** 8 zadań, ~4.5h całkowity czas

---

## 📈 Success Criteria

**TIER 0 (TODAY) - Basic Functionality:**
- ✅ GOOGLE_API_KEY rotated & removed from git history
- ✅ SECRET_KEY changed (not default)
- ✅ Docker services running (5/5: postgres, redis, neo4j, api, frontend)
- ✅ Neo4j indexes initialized
- ✅ Test suite runnable (380 tests collect without errors)

**TIER 1 (Week 1) - Production Blockers Resolved:**
- ✅ Zero HIGH/CRITICAL CVEs w dependencies
- ✅ All secrets managed securely (nie w .env w repo)
- ✅ SECRET_KEY validation at startup
- ✅ DEBUG disabled w production
- ✅ New RAG services (Document, Graph, HybridSearch) fully integrated & tested
- ✅ GitHub Actions CI/CD running (lint → test → build)
- ✅ Health check endpoints operational
- ✅ JWT blacklist implemented
- ✅ Account lockout mechanism working

**TIER 2 (Week 2-3) - Optimized & Stable:**
- ✅ All 380 tests passing consistently (no flaky tests)
- ✅ RAG end-to-end integration tests passing
- ✅ Neo4j connection pooling configured (no leaks)
- ✅ GraphRAG fill-rate ≥85%
- ✅ PersonaGenerator token usage -55% (compression)
- ✅ Redis caching operational (persona, focus groups, RAG queries)
- ✅ LLM retry logic + circuit breaker implemented
- ✅ Connection pooling optimized (DB, Neo4j, Redis)

**TIER 3 (Week 4+) - Production Excellence:**
- ✅ Code quality score 8.5/10+ (SonarQube/CodeClimate)
- ✅ Prometheus + Grafana dashboards live
- ✅ Docker network isolation complete
- ✅ Image vulnerability scanning in CI (Trivy)
- ✅ API audit logging operational (90d retention)
- ✅ MFA available for users
- ✅ GDPR compliance (data export/delete)
- ✅ Real-time progress indicators (WebSocket/SSE)

---

## 🗂️ Archiwum Zakończonych Zadań (ostatnie 30 dni)

### Październik 2025
- [x] RAG monolith split (3 serwisy: Document, Graph, HybridSearch) (data: 2025-10-15)
- [x] Hybrid Search optimization (chunking, reranking, RRF tuning) (data: 2025-10-14)
- [x] Security fixes (8 issues: bare except, indexes, sanitization) (data: 2025-10-14)
- [x] Graph service archiving (legacy features do archived/) (data: 2025-10-15)
- [x] Test infrastructure (factories, fixtures, 58 test files) (data: 2025-10-15)
- [x] Documentation restructure (docs/: AI_ML, DEVOPS, RAG, TESTING, README) (data: 2025-10-15)
- [x] Persona orchestration service (persona_orchestration.py) (data: 2025-10-15)
- [x] A/B testing framework dla RAG (test_rag_ab_comparison.py, test_rrf_k_tuning.py) (data: 2025-10-14)
- [x] Security headers middleware (HSTS, CSP, X-Frame-Options) (data: 2025-10-14)
- [x] Database indexes on foreign keys (personas.project_id, focus_groups.project_id) (data: 2025-10-14)
- [x] **Segment-Based Persona Architecture** (data: 2025-10-15)
  - ✅ Nowe schematy: DemographicConstraints, SegmentDefinition (app/schemas/persona.py)
  - ✅ Orchestration: _generate_segment_name, _generate_segment_context, _filter_graph_insights_for_segment
  - ✅ Generator: generate_persona_from_segment z ENFORCE demographics (age, gender, education, income)
  - ✅ Database: segment_id, segment_name columns w tabeli personas
  - ✅ Frontend: Hero Segment Header + Validation Alert w PersonaReasoningPanel.tsx
  - ✅ Documentation: Kompletna sekcja w docs/AI_ML.md (1900+ linii)
  - Impact: Rozwiązuje problem niezgodności persona ↔ brief (HARD constraints zamiast string prompts)

---

## 📚 Dokumentacja i Kontekst

**Główne pliki dokumentacji:**
- `README.md` - User-facing quick start
- `CLAUDE.md` - Instrukcje dla Claude Code (architecture, patterns, troubleshooting)
- `docs/README.md` - Indeks dokumentacji technicznej
- `docs/TESTING.md` - Test suite (208 testów, markery, fixtures, performance)
- `docs/RAG.md` - Hybrid Search + GraphRAG (architektura, optymalizacje, tuning)
- `docs/AI_ML.md` - AI/LLM system (persona generation, quality metrics)
- `docs/DEVOPS.md` - DevOps practices (CI/CD, monitoring, deployment)

**Architecture Patterns:**
- Service Layer Pattern (API → Services → Models)
- Async/Await dla I/O operations
- Event Sourcing dla persona memory
- Hybrid Search (Vector + Keyword + RRF)
- Parallel Processing (asyncio.gather dla LLM calls)

**Tech Stack:**
- Backend: FastAPI, PostgreSQL+pgvector, Redis, Neo4j
- AI: Google Gemini 2.5 (Flash/Pro) via LangChain
- Frontend: React 18, TypeScript, Vite, TanStack Query, Tailwind
- Infrastructure: Docker, Docker Compose

---

## 🔄 Workflow Zarządzania Planem

**Gdy wprowadzasz zmiany:**
1. Zaznacz ukończone zadania `[x]` i dodaj datę `(data: YYYY-MM-DD)`
2. Przenieś ukończone zadania do sekcji "Archiwum" jeśli >30 dni
3. Dodaj nowe zadania z priorytetu (Priority: 1-100)
4. Utrzymuj 20-30 aktywnych zadań (TIER 1-3)
5. Usuwaj/konsoliduj zadania o niskim priorytecie (<45)

**Format zadania:**
```markdown
- [ ] [Priority: XX] Krótki opis (szczegóły, lokalizacja) - estymat
```

**Priorytety:**
- 90-100: Critical (production blockers)
- 75-89: High (optimization, performance)
- 60-74: Medium (quality, testing)
- 45-59: Low (enhancements, nice-to-have)
- <45: Backlog (rozważyć usunięcie)

---
---

## 🚨 CRITICAL ALERTS

**IMMEDIATE ACTION REQUIRED:**
1. **GOOGLE_API_KEY EXPOSED** - AIzaSyDB92Edj_MGJsBuyK21J0gcupofvO1ZVQ8 in .env committed to git
   - Unieważnij w Google Cloud Console → Credentials
   - Wygeneruj nowy klucz z IP restrictions
   - Usuń z git history: `git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env' --prune-empty --tag-name-filter cat -- --all`
   - Force push: `git push origin --force --all`

2. **DOCKER SERVICES DOWN** - 0/5 services running
   - Run: `docker-compose up -d`
   - Check: `docker-compose ps`
   - Logs: `docker-compose logs -f`

3. **TESTY NIE DZIAŁAJĄ** - Timeout bo brak dependencies
   - Po uruchomieniu Docker: `python -m pytest tests/ -v`

---

**Liczba aktywnych zadań:** 46 (TIER 0-3)
**Ostatnia aktualizacja:** 2025-10-15 (pełna restrukturyzacja, focus na critical issues)
