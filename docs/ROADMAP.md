# PLAN.md - Roadmap Techniczny i Priorytety

**Wersja:** 1.0
**Data:** 2025-11-03
**Status:** Production-Ready MVP

## Spis Treści

1. [Przegląd Architektury](#1-przegląd-architektury)
2. [Aktualny Stan](#2-aktualny-stan)
3. [Priorytety Techniczne](#3-priorytety-techniczne)
4. [Roadmap Funkcjonalności](#4-roadmap-funkcjonalności)
5. [Dług Techniczny](#5-dług-techniczny)
6. [Strategia Skalowania](#6-strategia-skalowania)
7. [Koordynacja Zespołu](#7-koordynacja-zespołu)

---

## 1. Przegląd Architektury

Szczegółowa dokumentacja techniczna znajduje się w:
- **Backend**: [docs/architecture/backend.md](../architecture/backend.md) - API, service layer, database
- **AI/ML**: [docs/architecture/ai_ml.md](../architecture/ai_ml.md) - LLM, RAG, prompts
- **Infrastructure**: [docs/architecture/infrastructure.md](../architecture/infrastructure.md) - Docker, Cloud Run, CI/CD
- **QA**: [docs/operations/qa_testing.md](../operations/qa_testing.md) - Testy, coverage, benchmarki

**Stack**: FastAPI + SQLAlchemy (async) + PostgreSQL + Neo4j + Redis + LangChain + Google Gemini 2.5
**Wzorce**: Service Layer, Event Sourcing, Hybrid RAG, Centralized Config (`config/*.yaml`)

---

## 2. Aktualny Stan

### Metryki Codebase (Stan: 2025-11-03)

| Metryka | Wartość | Status |
|---------|---------|--------|
| **Lines of Code (LOC)** | ~20,000 | Moderate |
| API Endpoints | 60+ | Comprehensive |
| Service Modules | 30+ | Well-organized |
| Database Models | 16 | Complete |
| LLM Prompts | 25+ | Extensive |
| **Test Coverage** | 87% | ✅ Excellent |
| Test Functions | 444 | ✅ Strong |
| **Performance** | | |
| - Persona Gen (20) | ~45s | ✅ Target <60s |
| - Focus Group (20×4) | ~2 min | ✅ Target <3 min |
| - RAG Query | ~280ms | ✅ Target <350ms |
| - API P90 Latency | ~380ms | ✅ Target <500ms |

### Główne Osiągnięcia

✅ **Produkcyjny Backend**: 60+ endpoints, async-first, event sourcing
✅ **Hybrydowy System RAG**: Vector + keyword + graph search
✅ **Study Designer Chat**: Konwersacyjne projektowanie badań (LangGraph, 7 etapów)
✅ **Wysoka Jakość**: 87% test coverage, 444 testy
✅ **Wydajność**: Wszystkie SLA targets spełnione
✅ **CI/CD**: Automated deployment w 7-12 min
✅ **Infrastruktura**: Cloud Run serverless, auto-scaling

### Obecne Ograniczenia

⚠️ **Brak RBAC**: Wszyscy użytkownicy mają pełny dostęp (security risk)
⚠️ **Brak Team Features**: Nie ma sharingu projektów ani collaboration
⚠️ **Brak Export PDF/DOCX**: Users nie mogą eksportować raportów
⚠️ **Brak Payments**: Stripe integration do zrobienia
⚠️ **Brak Multi-LLM**: Tylko Gemini (vendor lock-in risk)

---

## 3. Priorytety Techniczne

### 🔴 P0: Krytyczne (Q4 2024 - M0-3)

**1. RBAC Implementation** (5-7 dni)
- Role-based access control (Admin, Researcher, Viewer)
- Lokalizacja: `app/core/security.py`, `app/middleware/rbac.py`
- Dependencies: Migration `users.role`
- Success: Viewer read-only, Researcher CRUD, Admin user management

**2. Stripe Payment Integration** (5-7 dni)
- Checkout flow + subscription + webhooks
- Lokalizacja: `app/api/payments.py`, `app/services/billing/`
- Dependencies: Stripe account, Secret Manager
- Success: Subscribe Pro ($49/mo), auto-upgrade, webhook handling

**3. Export PDF/DOCX** (3-5 dni)
- Generate PDF reports (personas, focus groups, surveys)
- Lokalizacja: `app/services/export/`, `app/api/export.py`
- Dependencies: WeasyPrint, python-docx
- Success: Export z charts, watermark dla free

**4. Multi-user/Team Accounts** (7-10 dni)
- Share projects, invite teammates, activity log
- Lokalizacja: `app/models/team.py`, `app/api/teams.py`, `app/services/teams/`
- Dependencies: Migration teams table
- Success: Create team, invite members, shared projects, activity log

### 🟠 P1: Wysokie (Q1 2025 - M4-6)

**5. Multi-LLM Provider Support** (5-7 dni)
- Abstraction layer + OpenAI + Anthropic
- Lokalizacja: `app/services/shared/llm_router.py`, `config/models.yaml`
- Fallback chain, cost-based routing, performance tracking

**6. Advanced RAG: Semantic Chunking** (5-7 dni)
- sentence-transformers chunking zamiast fixed-size
- Lokalizacja: `app/services/rag/chunking.py`
- 30-40% accuracy improvement, overlapping chunks, metadata enrichment

**7. API Rate Limiting per User/Tier** (2-3 dni)
- Rate limits based on subscription tier
- Lokalizacja: `app/middleware/rate_limiter.py`
- Free: 10 gen/day, Pro: unlimited, 429 responses

**8. Enhanced Monitoring & Alerting** (3-5 dni)
- Cloud Monitoring dashboards + PagerDuty
- Lokalizacja: `app/middleware/metrics.py`
- Dashboards, alerts (error rate >5%, downtime), weekly cost reports

### 🟡 P2: Średnie (Q2 2025 - M7-9)

**9. Journey Mapping Visualization** (7-10 dni)
- Visualize persona lifecycle (awareness → purchase → retention)
- Lokalizacja: `frontend/src/components/JourneyMap/`, `app/services/journey/`
- Dependencies: D3.js/Mermaid.js, 4-6 stage journey, touchpoints, emotions, export PNG/PDF

**10. Custom Knowledge Base Upload** (5-7 dni)
- Upload PDFs/CSVs → RAG index → use in generation
- Lokalizacja: `app/services/rag/document_upload.py`, `app/api/knowledge_base.py`
- Per-project knowledge bases, extract + chunk + embed

**11. Real-time Collaboration** (10-14 dni)
- Multiple users editing simultaneously
- Lokalizacja: `app/websocket/collaboration.py`
- Dependencies: WebSocket w Cloud Run, Redis pub/sub, live updates, conflict resolution

**12. Mobile-Responsive Design** (5-7 dni)
- Responsive breakpoints, mobile-first components
- Lokalizacja: `frontend/src/components/`, Tailwind config
- 320px width support, touch-friendly (44px buttons), hamburger menu

### 🟢 P3: Niskie (Q3-Q4 2025 - M10-12)

**13. CRM Integrations** (7-10 dni per integration)
- Export personas/insights do Salesforce, HubSpot
- Lokalizacja: `app/services/integrations/`, `app/api/integrations.py`
- OAuth flow, push personas as Contacts, insights as Notes

**14. Keyboard Shortcuts & Power User Features** (3-5 dni)
- Command palette (Cmd+K), keyboard shortcuts
- Lokalizacja: `frontend/src/hooks/useKeyboardShortcuts.ts`
- Cmd+N (new project), Cmd+P (generate), Cmd+F (search)

**15. White-label Branding** (7-10 dni)
- Custom logo, colors, domain
- Lokalizacja: `app/services/branding/`, `frontend/src/theme/`
- Enterprise tier ($99/mo extra), custom domain

**16. API Public Access** (10-14 dni)
- Public REST API + webhooks + developer portal
- Lokalizacja: `app/api/v2/`, docs portal
- API keys, rate limiting (1000 req/day free), webhooks

---

## 4. Roadmap Funkcjonalności

### Q4 2024 (M0-3): MVP Launch

**Cel**: Product-Market Fit Validation
**Target**: 100 users, 15 paying, NPS 30+

| Feature | Priority | Effort | Owner | Status |
|---------|----------|--------|-------|--------|
| RBAC | P0 | 5-7d | Backend | TODO |
| Stripe Payments | P0 | 5-7d | Backend | TODO |
| Export PDF/DOCX | P0 | 3-5d | Backend | TODO |
| Team Accounts | P0 | 7-10d | Backend | TODO |
| Enhanced Monitoring | P1 | 3-5d | DevOps | TODO |

**Deliverables:**
- [x] Core features stable (personas, focus groups, surveys)
- [ ] RBAC implemented
- [ ] Payment flow working
- [ ] Export functionality
- [ ] Team features MVP

---

### Q1 2025 (M4-6): Growth Acceleration

**Cel**: Scale Proven Channels
**Target**: 500 users, 70 paying, $16k MRR

| Feature | Priority | Effort | Owner | Status |
|---------|----------|--------|-------|--------|
| Multi-LLM Support | P1 | 5-7d | AI/ML | TODO |
| Semantic Chunking | P1 | 5-7d | AI/ML | TODO |
| API Rate Limiting | P1 | 2-3d | Backend | TODO |
| Journey Mapping | P2 | 7-10d | Full-stack | TODO |
| Custom Knowledge Base | P2 | 5-7d | Backend + AI/ML | TODO |

**Deliverables:**
- [ ] Multi-LLM provider abstraction
- [ ] Advanced RAG features
- [ ] Journey mapping visualization
- [ ] Tier-based rate limiting
- [ ] Upload own research data

---

### Q2 2025 (M7-9): Enterprise Readiness

**Cel**: Enterprise Customers
**Target**: 1200 users, 175 paying, 5 enterprise, $42k MRR

| Feature | Priority | Effort | Owner | Status |
|---------|----------|--------|-------|--------|
| Real-time Collaboration | P2 | 10-14d | Full-stack | TODO |
| Mobile Responsive | P2 | 5-7d | Frontend | TODO |
| CRM Integrations (Salesforce) | P3 | 7-10d | Backend | TODO |
| SSO/SAML | P1 | 5-7d | Backend | TODO |
| White-label Branding | P3 | 7-10d | Full-stack | TODO |

**Deliverables:**
- [ ] Multi-user editing (WebSocket)
- [ ] Mobile-first redesign
- [ ] Salesforce integration
- [ ] Enterprise SSO
- [ ] White-label dla agencies

---

### Q3-Q4 2025 (M10-12): Ecosystem & Scale

**Cel**: API Platform + International Expansion
**Target**: 2500 users, 330 paying, 10 enterprise, $80k MRR

| Feature | Priority | Effort | Owner | Status |
|---------|----------|--------|-------|--------|
| Public API + Webhooks | P3 | 10-14d | Backend | TODO |
| Developer Portal | P3 | 5-7d | Frontend | TODO |
| Keyboard Shortcuts | P3 | 3-5d | Frontend | TODO |
| GraphRAG Query Optimization | P1 | 5-7d | AI/ML | TODO |
| International (English) | P1 | 10-14d | Full-stack | TODO |

**Deliverables:**
- [ ] Public REST API v2
- [ ] Developer docs + SDKs
- [ ] Webhooks dla integrations
- [ ] Power user features
- [ ] English version (international launch)

---

## 5. Dług Techniczny

### 🔴 Krytyczne (Adresować w M0-3)

**1. Brak Staging Environment**
- **Problem**: Wszystkie testy na production (ryzyko downtime)
- **Impact**: High (production incidents, user-facing bugs)
- **Solution**: Setup staging w GCP (separate Cloud Run service + database)
- **Effort**: 2-3 dni
- **Owner**: DevOps

**2. Database Migration Testing**
- **Problem**: Migracje nie są testowane przed production (recent incident)
- **Impact**: High (downtime risk przy każdym deploy)
- **Solution**:
  - Staging environment (gdzie testować migracje)
  - Rollback procedure documented
  - Migration checklist (manual approval w CI/CD)
- **Effort**: 1-2 dni
- **Owner**: DevOps

**3. Brak Automated Rollback**
- **Problem**: Jeśli deployment failuje, manual rollback (5-10 min downtime)
- **Impact**: Medium-High (downtime, lost revenue)
- **Solution**: Cloud Run automatic rollback on health check failure
- **Effort**: 1 dzień
- **Owner**: DevOps

### 🟠 Ważne (Adresować w M4-6)

**4. N+1 Query Problem w Endpoints** (2-3 dni)
- Fetch related data w loops → slow performance
- Solution: `selectinload()` / `joinedload()` w SQLAlchemy
- Owner: Backend

**5. Neo4j Connection Leaks** (1-2 dni)
- Connections nie zawsze zamykane → memory leak
- Solution: Context manager `async with neo4j_connection.session()`
- Owner: Backend

**6. Missing Indexes** (1 dzień)
- Slow queries (>500ms) przez brak indexów
- Solution: Add indexes based on `pg_stat_statements` analysis
- Owner: Backend

**7. LLM Retry Logic** (1-2 dni)
- Inconsistent retry → transient failures
- Solution: Centralized retry decorator w `app/services/shared/llm_utils.py`
- Owner: AI/ML

### 🟡 Pożądane (Adresować w M7-12)

**8. Large Service Files** (3-5 dni)
- 800 LOC service files → maintainability issues
- Solution: Split into smaller modules
- Owner: Backend

**9. Frontend Bundle Size** (3-5 dni)
- 2.5MB bundle → slow load
- Solution: Code splitting, lazy loading, tree shaking
- Owner: Frontend

**10. E2E Tests Coverage** (5-7 dni)
- Tylko 12 testów E2E
- Solution: Add 10+ E2E tests w Playwright
- Owner: QA

---

## 6. Strategia Skalowania

### Database Scaling (PostgreSQL)

**Current**: Cloud SQL db-f1-micro (0.6GB RAM, shared CPU) - $10/mo

**Scaling Path:**

| Users | Tier | CPU | RAM | Storage | Cost/mo | When |
|-------|------|-----|-----|---------|---------|------|
| 0-100 | db-f1-micro | Shared | 0.6GB | 10GB | $10 | Now |
| 100-1k | db-g1-small | 1 vCPU | 1.7GB | 50GB | $50-60 | M6 |
| 1k-10k | db-n1-standard-2 | 2 vCPU | 7.5GB | 200GB | $170 | M12 |
| 10k-100k | db-n1-standard-4 + HA | 4 vCPU | 15GB | 500GB | $600 | Y2 |

**Optimization Strategies:**
- **Connection pooling**: Increase `pool_size` 10 → 20 → 50
- **Read replicas**: Offload analytics queries (when needed at 10k+ users)
- **Partitioning**: Partition `persona_events`, `usage_logs` by month
- **Archival**: Move old data (>90 days) to BigQuery ($0.02/GB storage vs $0.17/GB)

### Neo4j Scaling (Graph Database)

**Current**: Neo4j AuraDB Free (50k nodes, 2GB) - $0/mo

**Scaling Path:**

| Users | Tier | Nodes | RAM | Cost/mo | When |
|-------|------|-------|-----|---------|------|
| 0-500 | Free | 50k | 2GB | $0 | Now |
| 500-5k | Professional | 500k | 8GB | $65 | M8-10 |
| 5k-50k | Professional Plus | 5M | 32GB | $240 | M15-18 |
| 50k+ | Enterprise | Custom | Custom | $1000+ | Y3+ |

**Optimization Strategies:**
- **Prune old nodes**: Delete RAG chunks dla deleted projects
- **Optimize Cypher queries**: Add LIMIT, use indexes
- **Batch writes**: Bulk insert zamiast single-node creates

### Redis Scaling (Cache)

**Current**: Upstash Free (10k req/day, 256MB) - $0/mo

**Scaling Path:**

| Users | Tier | Requests/day | Memory | Cost/mo | When |
|-------|------|--------------|--------|---------|------|
| 0-100 | Free | 10k | 256MB | $0 | Now |
| 100-1k | Pay-as-you-go | 100k | 1GB | $10 | M6 |
| 1k-10k | Standard | 1M | 5GB | $50 | M12 |
| 10k+ | Cloud Memorystore | Unlimited | 10-50GB | $100-500 | Y2 |

**Migration to Cloud Memorystore (gdy Upstash limits exceeded):**
- Better latency (~5ms vs ~20ms Upstash)
- VPC peering (secure, no public internet)
- No request limits
- Cost: $0.049/GB/hour = ~$35/mo dla 1GB

### Cloud Run Scaling (Compute)

**Current**: 2 vCPU, 4Gi RAM, max 5 instances - $5-10/mo

**Scaling Path:**

| Users | Instances | CPU | Memory | Cost/mo | When |
|-------|-----------|-----|--------|---------|------|
| 0-100 | 0-2 | 2 vCPU | 4Gi | $5-10 | Now |
| 100-1k | 0-5 | 2 vCPU | 4Gi | $50-80 | M6 |
| 1k-10k | 0-20 | 2 vCPU | 4Gi | $200-400 | M12 |
| 10k+ | 0-50 | 4 vCPU | 8Gi | $1000-2000 | Y2 |

**Optimization Strategies:**
- **CPU/Memory right-sizing**: Test 2Gi memory (może wystarczyć dla non-LLM endpoints)
- **Min instances**: Set `--min-instances=1` when traffic consistent (avoid cold starts)
- **Request concurrency**: Increase from 80 → 100 (reduce instance count)

### Cost Projections

| Users | Infrastructure | LLM API | Total/mo | Cost per User |
|-------|----------------|---------|----------|---------------|
| 100 | $50 | $20 | $70 | $0.70 |
| 1,000 | $200 | $150 | $350 | $0.35 |
| 10,000 | $1,500 | $1,000 | $2,500 | $0.25 |
| 100,000 | $12,000 | $8,000 | $20,000 | $0.20 |

**Key Insight**: Economics of scale działają - cost per user spada 75% (z $0.70 → $0.20)

---

## 7. Koordynacja Zespołu

### Struktura Zespołu (Recommended)

**Phase 1 (M0-6): 2-3 osoby**
- 1x Full-stack Developer (Founder) - 100% allocation
- 1x Backend/AI Engineer (Part-time) - 50% allocation
- DevOps: Outsourced lub Founder (10% time)

**Phase 2 (M7-12): 4-5 osób**
- 1x CTO/Tech Lead (Founder)
- 1x Backend Engineer (Full-time)
- 1x Frontend Engineer (Full-time)
- 1x AI/ML Engineer (Full-time)
- DevOps: Shared resource lub platform engineer (50% time)

**Phase 3 (M13-24): 8-10 osób**
- 1x CTO
- 2x Backend Engineers
- 2x Frontend Engineers
- 1x AI/ML Engineer
- 1x DevOps Engineer (Full-time)
- 1x QA Engineer (Full-time)
- 1x Product Manager (manage roadmap, prioritization)

### Development Workflow

**Sprint Planning (2-week sprints):**
1. Monday Week 1: Review roadmap, select features, assign owners, create GitHub Issues
2. Daily Standups (async w Slack): Yesterday, today, blockers
3. Friday Week 2: Demo, metrics review, retro, plan next sprint

**Code Review:**
- Min 1 approval (2 dla critical)
- Tests (>85%), docs updated, performance tested, security reviewed, linting passed

**Deployment:**
1. Merge PR → CI/CD triggers
2. Monitor w #deployments
3. Smoke tests + 15 min monitoring
4. Rollback if issues

**Communication:**
- Slack: #general, #engineering, #deployments, #alerts, #support, #metrics
- Weekly: Monday sprint planning, Wednesday tech sync, Friday demo
- Monthly: Business review, roadmap update

**Documentation:**
- ADRs dla major decisions
- API docs (auto-generated)
- Runbooks dla incydentów
- Onboarding guide

---

## 8. Metryki Sukcesu

### Technical KPIs (Quarterly Targets)

| Metric | Q4 2024 | Q1 2025 | Q2 2025 | Target |
|--------|---------|---------|---------|--------|
| **Performance** | | | | |
| API P95 Latency | <500ms | <400ms | <350ms | <300ms |
| Persona Gen (20) | <60s | <50s | <45s | <40s |
| Focus Group (20×4) | <3min | <2.5min | <2min | <90s |
| **Quality** | | | | |
| Test Coverage | 87% | 88% | 90% | 90%+ |
| Production Bugs | <5/mo | <3/mo | <2/mo | <1/mo |
| **Reliability** | | | | |
| Uptime | 99.5% | 99.7% | 99.9% | 99.9%+ |
| Deployment Success | 90% | 95% | 98% | 99%+ |
| MTTR (incidents) | <30min | <20min | <15min | <10min |

### Engineering Velocity

| Metric | Target | Tracking |
|--------|--------|----------|
| Features Shipped | 3-5 per sprint | GitHub milestones |
| Code Review Time | <24h | GitHub PR metrics |
| Deployment Frequency | 3-5x per week | Cloud Build logs |
| Lead Time (commit→prod) | <2h | DORA metrics |

---

## 9. Risk Management

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Gemini API outage** | Medium | High | Multi-LLM fallback (OpenAI, Anthropic) [Q1 2025] |
| **Cloud Run downtime** | Low | Critical | Multi-region deployment [Q3 2025], automatic rollback [Q4 2024] |
| **Database connection exhaustion** | Medium | High | Connection pooling optimization [Q4 2024], scale up tier [M6] |
| **Neo4j free tier limit exceeded** | High | Medium | Monitor node count weekly, upgrade to Professional gdy 80% limit [~M8] |
| **Security breach** | Low | Critical | RBAC [Q4 2024], security audit [Q1 2025], penetration testing [Q2 2025] |
| **Key developer leaves** | Low | High | Documentation (ADRs, runbooks), knowledge sharing (pair programming), backup engineers |

### Dependency Risks

| Dependency | Risk | Mitigation |
|------------|------|------------|
| **Google Gemini** | Vendor lock-in | Multi-LLM abstraction [Q1 2025] |
| **Neo4j AuraDB** | Costly at scale | Evaluate alternatives (PostgreSQL + pgvector) [Q3 2025] |
| **Cloud Run** | Price increases | Container portability (Kubernetes option) [Q4 2025] |
| **LangChain** | Breaking changes | Pin versions, thorough testing, contribute to project |

---

## 10. Podsumowanie & Następne Kroki

### Aktualny Status ✅
- **MVP Ready**: Core features stable, 87% test coverage, all performance SLAs met
- **Infrastructure**: Serverless Cloud Run, auto-scaling, 7-12 min deployments
- **AI/ML**: Hybrid RAG working, 25+ prompts, statistical validation
- **Documentation**: Comprehensive (BACKEND_ARCHITECTURE.md, AI_ML_ARCHITECTURE.md, QA_DOCUMENTATION.md)

### Krytyczne Priorytety (M0-3) 🔴
1. **RBAC** - Security & enterprise readiness (5-7 dni)
2. **Stripe Payments** - Revenue generation (5-7 dni)
3. **Export PDF/DOCX** - #1 user request (3-5 dni)
4. **Team Accounts** - Corporate blocker (7-10 dni)

### Q1 2025 Focus 🎯
- Multi-LLM support (vendor diversification)
- Advanced RAG (semantic chunking)
- Journey mapping (differentiation feature)
- Enhanced monitoring (faster incident response)

### Long-term Vision (2025) 🚀
- **Q2**: Enterprise-ready (SSO, white-label, CRM integrations)
- **Q3**: API Platform (public API, webhooks, developer ecosystem)
- **Q4**: International expansion (English version, multi-currency)

---

**Ostatnia Aktualizacja**: 2025-11-03
**Wersja**: 1.1 (skondensowana z 769 → 553 linii)
**Maintainer**: Engineering Team

**Pytania lub sugestie?** Otwórz issue w GitHub lub discuss w #engineering Slack channel.
