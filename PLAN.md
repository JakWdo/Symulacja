# PLAN.md - Roadmap & Task Tracking

**WAŻNE:** Ten plik jest używany przez Claude Code do trackowania zadań i planowania rozwoju.

---

## 📋 Jak używać tego pliku?

### Dla Claude Code:
1. **Przed rozpoczęciem zadania** - Przeczytaj odpowiednią sekcję, sprawdź czy podobne zadanie nie istnieje
2. **Po zakończeniu zadania** - Zaznacz jako zrealizowane `[x]` i dodaj datę w formacie `(2025-10-14)`
3. **Dodawanie nowych zadań** - Grupuj według obszaru, dodaj do odpowiedniej sekcji "Priorities"
4. **Aktualizacja** - Aktualizuj ten plik przy każdej większej zmianie w projekcie

### Dla Developerów:
- Checklisty są pogrupowane według obszarów funkcjonalnych
- Priorytety znajdują się na końcu dokumentu (High/Medium/Low)
- Zrealizowane zadania pozostają w dokumencie (dla historii i trackowania postępu)

---

## 🗺️ Roadmap & Future Improvements

Plan rozwoju platformy z podziałem na obszary funkcjonalne.

## Docker & Infrastructure

### CI/CD Pipeline
- [ ] GitHub Actions workflow dla automated builds
- [ ] Automated testing w CI (pytest, unit + integration)
- [ ] Docker image builds i push do registry
- [ ] Automated deployment do staging environment
- [ ] Production deployment z manual approval gate

### Docker Registry
- [ ] Prywatny Docker registry (Harbor / AWS ECR / GCP Artifact Registry)
- [ ] Image signing dla security
- [ ] Vulnerability scanning (Trivy / Clair)
- [ ] Tag strategy (semver, git sha, latest)

### Kubernetes (jeśli planowane)
- [ ] Kubernetes manifests (Deployments, Services, ConfigMaps)
- [ ] Helm charts dla łatwiejszego deployment
- [ ] Horizontal Pod Autoscaling (HPA) bazowane na CPU/memory
- [ ] Ingress controller z SSL/TLS termination
- [ ] Persistent Volumes dla databases

### Monitoring & Observability
- [ ] Prometheus + Grafana w Docker Compose
- [ ] Application metrics (FastAPI requests, response times)
- [ ] Database metrics (Postgres, Redis, Neo4j)
- [ ] LLM API metrics (Gemini calls, token usage, costs)
- [ ] Alerting (email, Slack, PagerDuty) na critical events

### Health Checks
- [ ] Comprehensive health endpoints (/health/live, /health/ready)
- [ ] Database connection checks
- [ ] Redis connection checks
- [ ] Neo4j connection checks
- [ ] External API checks (Google Gemini availability)
- [ ] Startup probes dla slow-starting services

### Backups
- [ ] Automated Postgres backups (daily, retention policy)
- [ ] Neo4j backups (graph data)
- [ ] Redis persistence (RDB + AOF w production)
- [ ] Static files backups (avatary użytkowników)
- [ ] Backup restoration testing (monthly)
- [ ] Off-site backup storage (S3, GCS)

---

## Backend & API

### Performance Optimization
- [ ] Database query optimization (analyze slow queries)
- [ ] Connection pooling tuning (SQLAlchemy, Neo4j)
- [ ] Redis caching strategy (cache persona profiles, focus group results)
- [ ] Async batch processing dla bulk operations
- [ ] Background jobs dla long-running tasks (Celery / ARQ)

### API Enhancements
- [ ] API versioning strategy (v2 endpoints)
- [ ] Rate limiting per user/IP (Redis-based)
- [ ] Request/response compression (gzip)
- [ ] API key management dla external integrations
- [ ] Webhook support dla async notifications

### Error Handling
- [ ] Structured error responses (error codes, messages)
- [ ] Error tracking (Sentry integration)
- [ ] Retry logic dla transient failures (LLM API, database)
- [ ] Circuit breaker pattern dla external services
- [ ] Dead letter queue dla failed jobs

### Security
- [ ] API audit logging (who, what, when)
- [ ] RBAC (Role-Based Access Control) - admin, user, viewer roles
- [ ] API key rotation policy
- [ ] Input sanitization hardening
- [ ] OWASP Top 10 compliance audit
- [ ] Penetration testing

---

## AI & LLM

### Gemini API Optimization
- [ ] Token usage monitoring i cost tracking
- [ ] Caching dla powtarzalnych queries
- [ ] Fallback na mniejsze modele (Flash) jeśli Pro timeout
- [ ] Batch requests gdzie możliwe
- [ ] Prompt optimization dla mniejszych tokenów

### Multi-Model Support
- [ ] Abstrakcja LLM provider (LangChain już używany)
- [ ] Fallback na OpenAI GPT jeśli Gemini niedostępny
- [ ] A/B testing różnych modeli
- [ ] Model selection bazowane na task type (generation vs analysis)

### Persona Generation
- [ ] Więcej demographic categories (ethnicity, occupation, income brackets)
- [ ] International demographics (UK, US, Germany, etc.)
- [ ] Custom personality frameworks (MBTI, Enneagram)
- [ ] Persona templates library (zapisane profile)
- [ ] Import person z CSV/JSON

### Focus Groups
- [ ] Real-time streaming responses (WebSockets / SSE)
- [ ] Progress indicators (X of Y personas odpowiedziało)
- [ ] Retry pojedynczych person jeśli failed
- [ ] Focus group templates (pre-defined questions)
- [ ] Export transcripts (PDF, DOCX)

---

## RAG & Knowledge Graph

### RAG KLUCZOWE
- [ ] Stworzenie RAG settings, aby prompty do LLMGraphTransformer były dostosowane do raportu.

### Chunking & Context Optimization (ZREALIZOWANE 2025-10-14) ✅
- [x] Optymalizacja chunk_size (2000 → 1000 znaków) dla lepszej precyzji embeddings (2025-10-14)
- [x] Zwiększenie overlap (20% → 30%) dla lepszej ciągłości kontekstu (2025-10-14)
- [x] Zwiększenie TOP_K (5 → 8) dla kompensacji mniejszych chunków (2025-10-14)
- [x] Zwiększenie MAX_CONTEXT (5000 → 12000) zapobiegające truncation (2025-10-14)

### Reranking & Precision (ZREALIZOWANE 2025-10-14) ✅
- [x] Cross-encoder reranking dla precyzyjniejszego scoringu (2025-10-14)
- [x] Multilingual reranker (mmarco-mMiniLMv2) dla wsparcia polskiego (2025-10-14)
- [x] A/B testing framework (test_rag_ab_comparison.py) (2025-10-14)
- [x] RRF_K tuning tools (test_rrf_k_tuning.py) (2025-10-14)

### Hybrid Search Improvements
- [ ] BM25 keyword search zamiast fulltext (lepsze ranking)
- [ ] Query expansion (synonimy, related terms)
- [ ] Multi-query retrieval (generuj wiele queries z jednego pytania)

### Chunking Strategy (PRIORYTET ŚREDNI)
- [ ] **Semantic chunking** - Split bazując na semantic similarity, nie arbitrary char count
  - LangChain `SemanticChunker` lub custom implementation
  - Zachowuje tematyczną spójność chunków
  - Problem: Arbitrary char count często rozdziela ważne informacje
  - Rozwiązanie: Chunki są naturalnie spójne semantycznie

### Graph Node Enrichment (PRIORYTET ŚREDNI)
- [ ] **Improved graph node matching** - Cosine similarity zamiast word overlap dla enrichment
  - Obecny matching (word overlap) daje dużo false positives/negatives
  - Cosine similarity między chunk embedding a graph node properties
  - Albo TF-IDF scoring dla weighted matching
  - Zwiększ próg z >=2 matches → semantic threshold (cosine >0.7)

### Graph RAG Enhancements
- [ ] Community detection w grafie (clustery person/konceptów)
- [ ] Graph traversal queries (find paths between concepts)
- [ ] Temporal graph analysis (zmiany opinii w czasie)
- [ ] Entity linking (Wikipedia, DBpedia)

### Graph Prompt Optimization (PRIORYTET ŚREDNI)
- [ ] **Graph prompt simplification** - Zmniejsz liczbę required properties dla lepszego fill-rate
  - Problem: Validation pokazuje >30% nodes bez pełnych metadanych
  - Obecne: 7 node properties + 3 relationship properties = LLM ma trudności
  - Rozwiązanie: Zmniejsz do must-have only (description, summary, confidence_level)
  - Albo two-pass approach: extract nodes → enrich properties w drugim LLM call
  - Lepiej mniej properties, ale wypełnione quality data

### Document Management
- [ ] Web scraping dla public reports
- [ ] OCR dla scanned PDFs
- [ ] Document versioning (track updates)
- [ ] Document expiration dates (auto-remove stale data)
- [ ] Multi-language support (Polish, English)

### Embeddings
- [ ] Multi-lingual embeddings (Polish + English)
- [ ] Fine-tuned embeddings dla domain-specific content
- [ ] Embeddings compression (quantization) dla mniejszych storage

### Advanced RAG Features (PRIORYTET NISKI - Eksperymentalne)
- [ ] **Dynamic TOP_K** - Dostosuj k w zależności od query complexity
  - LLM klasyfikuje query jako simple/medium/complex
  - Simple queries → TOP_K=5 (mniej noise)
  - Complex queries → TOP_K=12-15 (więcej kontekstu)
  - Wymaga query complexity classifier (może być prosty heuristic lub ML model)

- [ ] **Dimensionality reduction** - PCA z 3072 → 1024 wymiary dla Google embeddings
  - Może przyspieszyć vector search (mniejsze wektory = szybsze dot product)
  - Może obniżyć quality retrieval
  - Wymaga EXTENSIVE testing na production data
  - Trade-off: speed vs accuracy

- [ ] **Custom Polish cross-encoder** - Trenuj domain-specific reranker na polskich tekstach demograficznych
  - Obecny mmarco model jest multilingual ale generic
  - Custom model trenowany na polskich social research texts
  - Długoterminowy projekt (requires labeled query-document pairs)
  - Wymaga: 1000+ labeled pairs (query, relevant_doc, irrelevant_doc)

---

## Frontend

### UI/UX Improvements
- [ ] Dark mode persistence (localStorage)
- [ ] Keyboard shortcuts (hotkeys dla common actions)
- [ ] Drag & drop persona assignment do focus groups
- [ ] Bulk operations (select multiple personas, delete, export)
- [ ] Undo/redo dla edycji

### Real-Time Features
- [ ] WebSocket connection dla live updates
- [ ] Real-time collaboration (multiple users editing)
- [ ] Live focus group progress (streaming responses)
- [ ] Notifications system (toast, browser notifications)

### Visualization Enhancements
- [ ] Graph analysis: filtry (age, gender, sentiment)
- [ ] Graph analysis: zoom, pan, node selection
- [ ] Chart exports (PNG, SVG) dla wszystkich visualizations
- [ ] Interactive timelines (persona history)
- [ ] Comparison views (compare 2 focus groups side-by-side)

### Accessibility
- [ ] WCAG 2.1 AA compliance
- [ ] Screen reader support
- [ ] Keyboard navigation dla wszystkich features
- [ ] High contrast mode
- [ ] Font size controls

### Performance
- [ ] Code splitting (lazy load routes)
- [ ] Image optimization (avatary)
- [ ] Bundle size optimization (tree shaking)
- [ ] Service worker dla offline support
- [ ] PWA manifest (installable app)

---

## Testing

### Test Coverage
- [ ] Zwiększ coverage do 90%+ (obecnie ~80%)
- [ ] Property-based testing (Hypothesis) dla generators
- [ ] Mutation testing (mutmut) dla test quality
- [ ] Visual regression testing (Percy, Chromatic)

### E2E Testing
- [ ] Playwright / Cypress dla frontend E2E
- [ ] Critical user flows (signup → generate personas → run focus group)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile testing (responsive design)

### Performance Testing
- [ ] Load testing (Locust / k6) - 100 concurrent users
- [ ] Stress testing - find breaking point
- [ ] Spike testing - sudden traffic spikes
- [ ] Endurance testing - 24h load

### Chaos Engineering
- [ ] Simulated database failures
- [ ] Network latency injection
- [ ] LLM API failures
- [ ] OOM (Out of Memory) scenarios

---

## Data & Analytics

### User Analytics
- [ ] Usage tracking (Mixpanel, Amplitude)
- [ ] Funnel analysis (signup → first focus group)
- [ ] Cohort analysis (user retention)
- [ ] Feature adoption rates

### Application Analytics
- [ ] Persona generation statistics (distributions, demographics)
- [ ] Focus group metrics (duration, personas count, questions)
- [ ] LLM API usage (tokens, costs, models)
- [ ] Error rates i tipos per endpoint

### Business Intelligence
- [ ] Dashboard dla key metrics
- [ ] Revenue tracking (jeśli płatne plany)
- [ ] Churn prediction (ML model)
- [ ] Customer lifetime value (LTV)

---

## Compliance & Legal

### GDPR
- [ ] Data retention policies (auto-delete po X miesięcy)
- [ ] Right to erasure (user deletion flow)
- [ ] Data portability (export user data)
- [ ] Consent management (cookies, tracking)
- [ ] Privacy policy updates

### Terms of Service
- [ ] ToS acceptance flow
- [ ] ToS versioning (track changes)
- [ ] Age verification (13+ / 18+)

### Audit Trails
- [ ] User action logging (CRUD operations)
- [ ] Admin action logging
- [ ] Data access logs (kto, co, kiedy)
- [ ] Log retention policy

---

## Internationalization

### Multi-Language Support
- [ ] i18n framework (react-i18next)
- [ ] Polish, English, German translations
- [ ] Language selection w UI
- [ ] LLM prompts w native language
- [ ] Date/time formatting per locale

### Regional Demographics
- [ ] Polish demographics (już jest)
- [ ] UK demographics
- [ ] US demographics
- [ ] German demographics

---

## Integrations

### Export Formats
- [ ] PDF reports (focus group transcripts)
- [ ] DOCX exports (Microsoft Word)
- [ ] Excel exports (survey results, demographics)
- [ ] PowerPoint exports (charts, summaries)

### External APIs
- [ ] Slack integration (notifications)
- [ ] Microsoft Teams integration
- [ ] Zapier webhooks
- [ ] REST API dla third-party integrations

### Import Sources
- [ ] Import personas z CSV
- [ ] Import survey questions z Google Forms
- [ ] Import documents z Google Drive, Dropbox

---

## Scalability

### Database Sharding
- [ ] Postgres sharding strategy (by tenant/user)
- [ ] Read replicas dla query load distribution
- [ ] Connection pooling optimization (PgBouncer)

### Caching Strategy
- [ ] Redis caching layers (L1: in-memory, L2: Redis, L3: DB)
- [ ] Cache invalidation strategy (TTL, manual)
- [ ] Cache warming dla popular queries

### Async Processing
- [ ] Message queue (RabbitMQ / Redis Queue)
- [ ] Background workers (Celery)
- [ ] Job scheduling (APScheduler / Celery Beat)
- [ ] Distributed task execution

---

## Priorities

### High Priority (Next 3 months)
- Monitoring & Observability
- CI/CD Pipeline
- Real-time focus group updates (WebSockets)
- Test coverage improvements
- ✅ RAG optimization (chunking, reranking, A/B testing) - DONE 2025-10-14

### Medium Priority (3-6 months)
- Multi-model LLM support
- Frontend performance optimization
- API rate limiting
- **RAG Chunking Strategy** - Semantic chunking implementation (split by semantic similarity)
- **Graph Node Enrichment** - Improved matching (cosine similarity vs word overlap)
- **Graph Prompt Optimization** - Simplification dla lepszego fill-rate (zmniejsz required properties)

### Low Priority (6-12 months)
- Kubernetes migration (jeśli potrzebne)
- Multi-language i18n
- Advanced analytics dashboard
- Third-party integrations
- **Advanced RAG Features** - Dynamic TOP_K, dimensionality reduction (PCA), custom Polish cross-encoder

---

*Last updated: 2025-10-14*
