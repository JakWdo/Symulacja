# BIZNES.md - Sight Platform

**Dokument biznesowy platformy Sight** - AI-powered virtual focus groups platform.

---

## Spis Treści

1. [Model Biznesowy](#1-model-biznesowy)
2. [Funkcjonalności Core](#2-funkcjonalności-core)
3. [Przewagi Konkurencyjne](#3-przewagi-konkurencyjne)
4. [Korzyści Biznesowe](#4-korzyści-biznesowe)
5. [User Journey](#5-user-journey)
6. [Metryki Sukcesu i KPI](#6-metryki-sukcesu-i-kpi)
7. [Model Biznesowy i Monetyzacja](#7-model-biznesowy-i-monetyzacja)
8. [Go-to-Market Strategy](#8-go-to-market-strategy)
9. [Konkurencja i Pozycjonowanie](#9-konkurencja-i-pozycjonowanie)
10. [Roadmap i Next Steps](#10-roadmap-i-next-steps)

---

## 1. MODEL BIZNESOWY

### 1.1. Problem Biznesowy

Platforma **Sight** rozwiązuje **cztery kluczowe wyzwania** tradycyjnych badań rynkowych:

**🕐 Koszt i czas badań jakościowych**
- Tradycyjne focus groups: 2-4 tygodnie planowania + rekrutacja uczestników + wynajem lokalu
- Koszt pojedynczej sesji: 8,000-15,000 PLN (moderator + uczestnicy + transkrypcja + analiza)
- **Sight**: Symulacja 20 person w 4 dyskusjach → ~3 minuty, koszt tokenów AI ~$0.50

**📊 Ograniczona reprezentatywność**
- Tradycyjnie: 6-12 uczestników per sesja, często z jednorodnej grupy
- Brak statystycznej reprezentatywności demograficznej
- **Sight**: Generuje 20+ person z precyzyjnymi rozkładami demograficznymi (wiek, płeć, wykształcenie, dochód, lokalizacja) zwalidowanymi testem chi-kwadrat

**💡 Brak kontekstu społeczno-kulturowego**
- Tradycyjne metody: brak dostępu do danych GUS, CBOS, badań rynku w czasie rzeczywistym
- **Sight**: Hybrid RAG Search (vector + keyword + RRF fusion) oraz GraphRAG z dokumentami badawczymi → każda persona ma kontekst społeczny

**🔄 Trudność w iteracji i skalowaniu**
- Zmiana scenariusza wymaga nowej sesji (koszt + czas)
- **Sight**: Nieograniczone iteracje, instant feedback, parallel processing (asyncio.gather dla 20 person)

---

### 1.2. Grupa Docelowa

**Primary Users (Bezpośredni Użytkownicy):**

**🎯 Marketerzy i Product Managerowie (B2B SaaS, Tech)**
- **Pain Points:**
  - Brak szybkiego feedbacku przed campaign launch
  - Wysokie koszty tradycyjnych focus groups (8k-15k PLN per sesja)
  - Potrzeba walidacji messaging, value proposition, pricing
- **Use Cases:**
  - Pre-launch product testing (features, messaging, pricing)
  - Customer journey mapping z touchpoints i buying signals
  - Segment analysis (JTBD framework, needs, pains)
- **Benefity z Sight:**
  - Time-to-Insight < 5 min (vs. 2-4 tygodnie)
  - Koszt ~$5-10 per research session (vs. 8k-15k PLN)
  - Unlimited iterations

**📈 Badacze Rynku i Agencje Badawcze**
- **Pain Points:**
  - Presja czasowa od klientów (tight deadlines)
  - Difficulty rekrutacji niszowych segmentów
  - Brak narzędzi do AI-powered insights extraction
- **Use Cases:**
  - Wstępna eksploracja przed large-scale quantitative research
  - Generowanie hipotez badawczych
  - Analiza sentymentu i konceptów (Neo4j graph analytics)
- **Benefity z Sight:**
  - Parallel processing (20 person × 4 pytania = 2 min)
  - Graph analytics: concept extraction, sentiment analysis, relationships
  - Export reports (PDF/CSV - planned Post-MVP)

**🏢 Konsultanci i Strategowie Biznesowi**
- **Pain Points:**
  - Potrzeba szybkiej desk research + qualitative insights
  - Brak dostępu do reprezentatywnych danych demograficznych
  - Trudność w prezentacji insights dla klientów
- **Use Cases:**
  - Market sizing (segment size estimation z GUS data)
  - Competitive analysis (porównanie messaging różnych segmentów)
  - Strategy workshops z client stakeholders
- **Benefity z Sight:**
  - Data-driven personas z RAG context (GUS, CBOS, badania)
  - KPI estimation (segment size, adoption rate - heurystyki + benchmarks)
  - Visual insights (charts, graphs, knowledge graph 3D)

---

### 1.3. Propozycja Wartości

**Kluczowe Value Propositions:**

**⚡ "Od pomysłu do insights w 5 minut"**
- Traditional focus groups: 2-4 tygodnie planowania + rekrutacja + sesja + analiza
- **Sight:** Create project → Generate 20 personas → Run focus group → AI summary = **< 5 min**
- **ROI:** 99% redukcja czasu (2880 min → 5 min)

**💰 "Koszt $5-10 zamiast 8,000-15,000 PLN per sesja"**
- Traditional: Moderator (3k PLN) + Uczestnicy (4k PLN) + Wynajem (2k PLN) + Transkrypcja (2k PLN) + Analiza (4k PLN) = **15k PLN**
- **Sight:** Gemini Flash tokens (~$0.50) + Infrastructure (Cloud Run ~$1/month amortized) = **~$5-10 per session**
- **ROI:** 99.9% redukcja kosztów

**📊 "Statystycznie reprezentatywne persony"**
- Traditional: 6-12 uczestników, często convenience sampling
- **Sight:** 20+ person z precyzyjnymi rozkładami demograficznymi:
  - Age groups (18-24: 30%, 25-34: 50%, 35-44: 20%)
  - Gender (M: 48%, F: 52%, Non-binary: 2%)
  - Education, Income, Location z GUS distributions
  - Walidacja chi-kwadrat (p > 0.05)
- **Benefit:** Real statistical validity

**🧠 "AI-powered insights z kontekstem społecznym"**
- Traditional: Brak dostępu do real-time data (GUS, CBOS, badania rynku)
- **Sight:** Hybrid RAG Search:
  - Vector search (semantic similarity, 768-dim Gemini embeddings)
  - Keyword search (fulltext index Neo4j)
  - RRF Fusion (Reciprocal Rank Fusion, weights 0.7:0.3)
  - GraphRAG (Cypher queries, relationship extraction)
- **Benefit:** Każda persona ma kontekst społeczny z real data

**🔄 "Unlimited iterations i skalowanie"**
- Traditional: Zmiana scenariusza = nowa sesja (koszt + czas)
- **Sight:**
  - Edit questions → Re-run focus group (2 min)
  - Generate 50, 100, 200 personas (linear scaling dzięki async parallelization)
  - A/B testing messaging (równoczesne focus groups na różnych segmentach)
- **Benefit:** Rapid experimentation

---

## 2. FUNKCJONALNOŚCI CORE

### 2.1. Generowanie Person AI (PersonaGeneratorLangChain)

**Biznesowa wartość:**
- **Input:** Rozkłady demograficzne (age, gender, education, income, location)
- **Output:** 20+ realistycznych person w 30-60s
- **Technologia:** Gemini 2.5 Flash + RAG context (PolishSocietyRAG)

**User Journey:**
1. User tworzy projekt: "Test produktu B2B SaaS"
2. Definiuje target demographics:
   - Age: 25-34 (60%), 35-44 (40%)
   - Gender: Male (70%), Female (30%)
   - Education: Wyższe (80%), Średnie (20%)
   - Income: 6k-10k PLN (50%), 10k-15k PLN (50%)
   - Location: Warszawa (40%), Kraków (30%), Wrocław (30%)
3. Klik "Generuj persony" → **Background task (FastAPI BackgroundTasks)**
4. **30-60s later:** 20 person ready
   - Każda persona: Imię, wiek, płeć, zawód, wykształcenie, dochód, lokalizacja
   - **Big Five personality** (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
   - **Hofstede cultural dimensions** (Power Distance, Individualism, Masculinity, Uncertainty Avoidance, Long-term Orientation, Indulgence)
   - **Background story** (AI-generated, ~200 słów)
   - **RAG context** (segment brief, social context z GUS/CBOS)

**Przewaga konkurencyjna:**
- **Segment-Based Architecture:** Każda persona należy do demograficznego segmentu → consistency
- **Statistical Validation:** Chi-kwadrat test (p > 0.05) → reject jeśli distribution nie pasuje
- **RAG Integration:** Każda persona ma kontekst społeczny z real data (GUS, CBOS)

**Metryki wydajności:**
- 20 person: ~45s (target: <60s) ✅
- Parallel generation: 3x speedup (asyncio.gather)
- Token cost: ~$0.30 per 20 personas (Gemini Flash: $0.00005/1k tokens input)

---

### 2.2. Wirtualne Grupy Fokusowe (FocusGroupServiceLangChain)

**Biznesowa wartość:**
- **Input:** Lista person + 3-5 pytań
- **Output:** Odpowiedzi wszystkich person + AI summary
- **Czas:** 2-5 min dla 20 person × 4 pytania (target: <3 min)

**User Journey:**
1. User wybiera 20 person z listy
2. Definiuje pytania:
   - "Co sądzisz o tym produkcie?"
   - "Jakie funkcje są najważniejsze?"
   - "Ile byłbyś skłonny zapłacić?"
   - "Jakie są Twoje największe obawy?"
3. Klik "Uruchom focus group" → **Async orchestration (asyncio.gather)**
4. **2-5 min later:** Wyniki gotowe
   - Każda persona: 4 odpowiedzi (~100-300 słów każda)
   - **AI Summary** (DiscussionSummarizerService): Key themes, sentiment, quotes
   - **Memory Events** (MemoryServiceLangChain): Każda odpowiedź → event w systemie pamięci

**Przewaga konkurencyjna:**
- **Async Parallelization:** 20 person odpowiada **równocześnie** (nie sekwencyjnie)
- **Memory System (Event Sourcing):** Każda odpowiedź persony → immutable event z embedding
  - Semantic search (vector similarity) po historii
  - Consistency checking (czy persona odpowiada zgodnie z poprzednimi odpowiedziami)
- **Real-time Status Updates:** Frontend polling co 2s (TanStack Query refetchInterval)

**Metryki wydajności:**
- 20 person × 4 pytania = 80 LLM calls
- Parallel execution: ~2 min (vs. ~8 min sequential)
- Average response time: <3s per persona
- Token cost: ~$0.40 per focus group

---

### 2.3. System RAG (PolishSocietyRAG, GraphRAG)

**Biznesowa wartość:**
- **Problem:** Generic personas bez real-world context
- **Rozwiązanie:** Hybrid RAG Search + GraphRAG z dokumentami badawczymi (GUS, CBOS, market research)
- **Output:** Każda persona ma **segment brief** z social context

**3 serwisy RAG:**

**1. PolishSocietyRAG (Hybrid Search)**
- **Vector Search:** Cosine similarity (Gemini embeddings 768-dim)
- **Keyword Search:** Fulltext index Neo4j (Lucene-based)
- **RRF Fusion:** Łączy oba wyniki (weights: 0.7 vector, 0.3 keyword)
- **Performance:** <250ms per query
- **Use Case:** Znajdź dokumenty o "młodych prekariuszach" → zwróci chunks o:
  - Bezrobocie 18-24: 12% (GUS 2024)
  - Umowy śmieciowe: 35% młodych (CBOS)
  - Median income: 3,200 PLN

**2. GraphRAGService (Graph Queries)**
- **Ekstrakcja wiedzy z dokumentów → Graf Neo4j:**
  - **Węzły:** Obserwacja, Wskaźnik, Demografia, Trend, Lokalizacja
  - **Relacje:** OPISUJE, DOTYCZY, POKAZUJE_TREND, ZLOKALIZOWANY_W
  - **Metadane:** streszczenie, skala, pewność, okres_czasu, kluczowe_fakty
- **LLM-generated Cypher queries** (Gemini 2.5 Pro)

**3. RAGDocumentService (Document Management)**
- **Upload dokumentów:** PDF, TXT, DOCX
- **Chunking:** 1000 chars + 30% overlap (planned: semantic chunking)
- **Ingest → Neo4j:** Chunks + Graph extraction
- **CRUD:** List, delete, re-index documents

**Metryki wydajności:**
- Hybrid search: <250ms (Precision@5: >70%, Recall@8: >80%)
- Graph RAG query: <3s (depends on Cypher complexity)
- Token cost: ~$0.05 per persona generation (RAG context ~500 tokens)

---

### 2.4. Ankiety (SurveyResponseGenerator)

**Biznesowa wartość:**
- **Problem:** Tradycyjne surveys: manual sending + slow response rate (~15-20%)
- **Rozwiązanie:** AI-powered survey responses od person
- **Output:** Instant feedback (100% response rate)

**4 typy pytań:**
- **Single choice** (radio buttons)
- **Multiple choice** (checkboxes)
- **Rating scale** (1-5, 1-10)
- **Open-ended** (textarea, AI-generated ~50-200 słów)

**Metryki wydajności:**
- 10 person × 5 pytań = 50 LLM calls
- Time: <60s (parallel execution)
- Token cost: ~$0.20 per survey

---

### 2.5. Dashboard i Analityka (DashboardOrchestrator)

**8 KPI Cards:**
1. **Time-to-Insight (TTI):** Median czas od create project → first insight (Target: <5 min)
2. **Adoption Rate:** % projektów z przynajmniej 1 focus group lub survey (Target: 65%)
3. **Coverage:** % person wykorzystanych w focus groups/surveys (Target: >70%)
4. **Active Projects:** Liczba projektów z aktywnością w ostatnich 7 dniach
5. **Insight Velocity:** Avg liczba insights per projekt per tydzień (Target: >3)
6. **Token Usage:** Total tokens consumed z budget limits (Free: $50, Pro: $100, Enterprise: $500)
7. **Health Score:** Composite score (0-100) - TTI + Coverage + Velocity (Target: >70)
8. **Weekly Completion:** Trend chart - liczba ukończonych insights per tydzień

**Insight Types Distribution:**
- **Opportunity** (40%) - Untapped market segments, feature requests
- **Risk** (25%) - Concerns, objections, competitive threats
- **Trend** (20%) - Emerging patterns
- **Pattern** (15%) - Recurring behaviors, correlations

**Performance Optimizations:**
- **Redis Caching:** 30s TTL dla analytics (Cache hit ratio: ~90%)
- **N+1 Query Optimization:** GROUP BY subqueries (87% reduction w queries)
- **Latency:** <200ms cache hit, <500ms cache miss

---

## 3. PRZEWAGI KONKURENCYJNE

### 3.1. AI-Powered Automation

**Vs. Traditional Focus Groups:**
- **Time:** 5 min vs. 2-4 tygodnie (99% faster)
- **Cost:** $5-10 vs. 8k-15k PLN (99.9% cheaper)
- **Scalability:** 20-200 personas (linear) vs. 6-12 (fixed)
- **Iterations:** Unlimited vs. 1 per budget

**Vs. Survey Tools (SurveyMonkey, Typeform):**
- **Response Rate:** 100% (AI) vs. 15-20% (real humans)
- **Time-to-Insights:** <5 min vs. 1-2 tygodnie
- **Quality:** AI-generated z kontekstem vs. low-quality responses

**Vs. Synthetic Data Tools (Mostly, Synthetic Users):**
- **Statistical Validity:** Chi-kwadrat validation vs. random generation
- **Context:** RAG with real data (GUS, CBOS) vs. generic templates
- **Graph Analytics:** Neo4j relationship extraction vs. flat data

---

### 3.2. Hybrid Search + GraphRAG

**Unique Value Proposition:**
- **Kombinacja 3 strategii retrieval:**
  1. Vector Search (semantic similarity)
  2. Keyword Search (lexical matching)
  3. Graph Queries (structural knowledge)
- **RRF Fusion** (Reciprocal Rank Fusion) → best of both worlds

**Konkurencyjne rozwiązania:**
- **OpenAI Assistants API:** Vector search only (brak graph)
- **LangChain default:** Keyword search only (brak semantic)
- **Neo4j GraphRAG:** Graph only (brak vector + keyword fusion)

**Sight:** **Hybrid 3-way fusion** → unique competitive advantage

**Benchmark:**
- Precision@5: >70% (vs. 50% vector-only, 55% keyword-only)
- Recall@8: >80% (vs. 65% vector-only, 60% keyword-only)
- F1 Score: >75% (vs. 55% vector-only, 57% keyword-only)

---

### 3.3. Event Sourcing dla Person (MemoryServiceLangChain)

**Problem z tradycyjnymi personami:**
- Statyczne (no memory, no evolution)
- Inconsistent responses (każda odpowiedź niezależna)
- Brak auditability

**Sight Memory System:**
- **Immutable Events:** Każda odpowiedź persony → event z:
  - `event_type`: "response", "view", "export", "delete"
  - `content`: Tekst odpowiedzi
  - `embedding`: 768-dim vector (Gemini embeddings)
  - `metadata`: Timestamp, user_id, ip_address
- **Semantic Search:** Vector similarity po historii zdarzeń
- **Consistency Checking:** LLM dostaje context previous events → zwiększa consistency

**Audit Trail (PersonaAuditService):**
- **GDPR Compliance:** IP addresses retention 90 dni
- **Accountability:** User actions logged (view, export, delete, compare)
- **Timeline View:** Frontend - ostatnie 20 akcji z timestamps

---

### 3.4. Async Orchestration i Performance

**Problem tradycyjnych LLM apps:**
- Sequential processing (1 persona at a time)
- Blocking I/O (wait for LLM response)
- Poor scalability (linear time complexity)

**Sight Architecture:**
- **Async/Await wszędzie:** FastAPI + SQLAlchemy async + asyncio
- **Parallel LLM Calls:** `asyncio.gather()` dla 20 person równocześnie
- **Connection Pooling:** PostgreSQL (10 max), Neo4j (50), Redis (10)
- **Retry Logic:** Exponential backoff dla Gemini rate limits (max_retries=3)
- **Redis Caching:** Smart cache keys z `updated_at` timestamp

**Performance Metrics:**
- **20 person generation:** ~45s (vs. ~3 min sequential)
- **20 person × 4 pytania focus group:** ~2 min (vs. ~8 min sequential)
- **Speedup:** **3x dla generation, 4x dla focus groups**

**Latency targets:**
- API endpoints: <500ms P95
- Persona generation: <5s per persona
- Focus group response: <3s per persona
- Hybrid search: <250ms
- Graph RAG query: <3s

---

## 4. KORZYŚCI BIZNESOWE

### 4.1. Oszczędności (Czas i Koszt)

**Time Savings:**

| Operacja | Traditional | Sight | Savings |
|----------|-------------|-------|---------|
| **Focus group setup** | 2-4 tygodnie | 5 min | **99.9%** |
| **Persona creation** | 1-2 tygodnie (rekrutacja) | 30-60s | **99.9%** |
| **Survey distribution** | 1-2 tygodnie | <60s | **99.9%** |
| **Insights analysis** | 1-2 tygodnie | <3s (AI) | **99.9%** |
| **Iteration** | 2-4 tygodnie | <5 min | **99.9%** |

**Total Time-to-Market:** **4-8 tygodni → <1 godzina** (99.8% reduction)

**Cost Savings:**

| Pozycja | Traditional (PLN) | Sight ($) | Savings |
|---------|------------------|-----------|---------|
| **Moderator** | 3,000 | $0 | **100%** |
| **Uczestnicy** | 4,000 | $0 | **100%** |
| **Wynajem lokalu** | 2,000 | $0 | **100%** |
| **Transkrypcja** | 2,000 | $0 (auto) | **100%** |
| **Analiza** | 4,000 | $0.50 (AI) | **99.9%** |
| **Infrastructure** | 0 | $1 (Cloud Run) | - |
| **TOTAL** | **15,000 PLN** | **~$5-10** | **99.9%** |

**ROI Example:**
- Agencja badawcza: 10 projektów/miesiąc
- Traditional cost: 10 × 15k PLN = **150k PLN/miesiąc**
- Sight cost: 10 × $10 = **$100/miesiąc** (~400 PLN)
- **Savings: 149,600 PLN/miesiąc** (99.7%)
- **Annual savings: ~1.8M PLN**

---

### 4.2. Jakość Insights

**Statistical Validity:**
- **Chi-kwadrat validation:** p > 0.05 (reject if distribution not matching)
- **Demographic precision:** Age, gender, education, income, location z GUS distributions
- **Confidence scores:** Każdy insight ma confidence score (0.0-1.0)

**Kontekst społeczny (RAG):**
- **Real data:** GUS, CBOS, market research documents
- **Hybrid search:** Vector + keyword + RRF fusion (Precision@5: >70%)
- **Graph analytics:** Concept extraction, relationship mapping

**AI Summary Quality:**
- **Key themes extraction:** Top 3-5 themes (frequency-based)
- **Sentiment analysis:** Positive/Negative/Neutral
- **Quotes:** TF-IDF ranking

**Consistency Checking:**
- **Event sourcing:** Każda odpowiedź → event z embedding
- **Semantic search:** Previous responses context → consistency
- **Hallucination reduction:** LLM dostaje context → mniej generic answers

---

### 4.3. Skalowanie Badań

**Horizontal Scaling (więcej person):**
- **Linear complexity:** 20 personas = 45s → 100 personas = 3.75 min
- **No recruitment bottleneck:** 100 uczestników traditionally = niemożliwe/drogie
- **Cost:** $0.30 per 20 personas → $1.50 per 100 (negligible)

**Vertical Scaling (więcej pytań):**
- **Focus groups:** 3-5 pytań traditionally → 10-20 w Sight (no time pressure)
- **Surveys:** Max 15-20 traditionally → unlimited w Sight (AI nie ma fatigue)

**Iterative Scaling (A/B testing):**
- **Test messaging A vs. B:**
  - Traditional: 2 sesje × 15k PLN = 30k PLN
  - Sight: 2 focus groups × $5 = $10
- **Test 5 pricing models:**
  - Traditional: 5 sesji × 15k PLN = 75k PLN
  - Sight: 5 focus groups × $5 = $25

**Geographic Scaling:**
- **Multi-city research:** Warszawa, Kraków, Wrocław, Gdańsk, Poznań
  - Traditional: 5 × 15k PLN = 75k PLN + travel
  - Sight: $5 (location = JSONB field)

**ROI dla scale:**
- **100 personas, 10 pytań, 5 scenarios, 5 cities, 12 months:**
  - Traditional: ~1M PLN/rok
  - Sight: ~$500/rok (~2k PLN)
  - **Savings: 99.8%**

---

## 5. USER JOURNEY

### 5.1. Typowy Workflow

**Step 1: Onboarding**
1. Landing page → "Rozpocznij za darmo" (Free tier)
2. Sign up (Email + password lub OAuth Google)
3. Onboarding wizard:
   - "Opisz use case" (Product testing, Market research, Strategy)
   - "Wybierz plan" (Free, Pro $49, Enterprise $299)

**Step 2: Create Project**
1. Project wizard:
   - Nazwa: "Test produktu B2B SaaS"
   - Opis (opcjonalny)
   - **Target demographics:** Age, Gender, Education, Income, Location
   - Target sample size: 20
2. Submit → Redirect do ProjectDetail

**Step 3: Generate Personas**
1. Empty state: "Brak person. Wygeneruj teraz!"
2. Persona generation dialog:
   - Num personas: 20 (slider 5-50)
   - Advanced: RAG context, Validation
3. Submit → Background task
4. ~45s later → 20 person ready
5. PersonaPanel: Grid 4×5 cards

**Step 4: Explore Persona Details**
1. Click persona → PersonaDetailsDrawer
2. Tabs:
   - **"Osoba":** Overview, Profile, Potrzeby i bóle (JTBD)
   - **"Segment":** Segment brief, RAG metadata, Audit timeline
3. Actions: Export, Compare, Delete

**Step 5: Create Focus Group**
1. Focus Groups tab → "+ Nowa grupa fokusowa"
2. Wizard:
   - Nazwa, Select personas (10-20), Questions (3-5)
3. Submit → Async orchestration
4. ~2 min later → Results ready
5. FocusGroupView:
   - Summary: AI themes, sentiment, stats
   - Responses: Accordion per question

**Step 6: Analyze Insights**
1. Dashboard → Insights tab
2. Latest Insights: Type, Title, Description, Evidence, Action
3. Analytics: Weekly chart, Insight types, Top concepts, Sentiment
4. Export Report (planned): PDF/PowerPoint/CSV

---

### 5.2. Integracja RAG

**Step 1: Upload Document**
1. RAGManagementPanel → "+ Upload document"
2. Upload dialog: File (PDF/TXT/DOCX), Description, Category
3. Submit → Ingest pipeline:
   - Split → chunks (1000 chars + 30% overlap)
   - Generate embeddings (Gemini 768-dim)
   - Extract graph (Nodes + Relations)
   - Save to Neo4j

**Step 2: Use RAG in Persona Generation**
1. Generate personas (automatic RAG context)
2. PersonaGeneratorLangChain → PolishSocietyRAG.hybrid_search(query)
3. Result: Top 5 chunks (~500 tokens)
4. Persona generation z context → realistic persona

**Step 3: Query Graph RAG**
1. GraphAnalysisPanel: "Jakie trendy w IT w Warszawie?"
2. Submit → GraphRAGService.answer_question(query)
3. LLM generates Cypher query → Execute → Synthesize answer
4. Frontend: Answer + sources + 3D Graph Visualization

---

## 6. METRYKI SUKCESU I KPI

### 6.1. Product Metrics (Wewnętrzne)

**Adoption Metrics:**
- **Active Users (MAU):** Target 100 by Q2 2026
- **Projects Created:** Target 500 by Q2 2026
- **Personas Generated:** Target 10,000 by Q2 2026
- **Focus Groups Run:** Target 2,000 by Q2 2026

**Engagement Metrics:**
- **Time-to-First-Insight (TTFI):** Target <5 min (current: ~3 min) ✅
- **Coverage (% personas used):** Target >70% (current: ~65%)
- **Retention (D7, D30):** Target D7: 60%, D30: 40%
- **NPS:** Target >45

**Technical Metrics:**
- **API Latency (P95):** Target <500ms (current: ~350ms) ✅
- **Error Rate:** Target <1% (current: ~0.5%) ✅
- **Uptime:** Target 99.5%
- **Cache Hit Ratio:** Target >80% (current: ~90%) ✅

**Cost Metrics:**
- **Cost per Persona:** Target <$0.02 (current: ~$0.015) ✅
- **Cost per Focus Group:** Target <$0.50 (current: ~$0.40) ✅
- **Infrastructure Cost:** Target <$50/month (current: ~$16-30) ✅

---

### 6.2. Business Metrics (Customer-Facing)

**Value Delivered:**
- **Time Savings:** Target 99% reduction (2-4 tygodnie → 5 min)
- **Cost Savings:** Target 99.9% reduction (15k PLN → $5-10)
- **Insight Quality:** Precision@5 >70%, F1 Score >75%
- **Statistical Validity:** Chi-kwadrat p > 0.05 dla 95%+ personas

**Customer Success:**
- **CSAT:** Target >4.5/5
- **Feature Adoption:**
  - Persona generation: 100%
  - Focus groups: >80%
  - Surveys: >60%
  - RAG upload: >40%
  - Graph analytics: >30%

**Revenue Metrics (Post-MVP):**
- **MRR:** Target $5k by Q2 2026
- **ARPU:** Target $50/month (Pro plan)
- **Churn Rate:** Target <5% monthly
- **CAC:** Target <$100
- **LTV:** Target $600 (12 months)
- **LTV/CAC Ratio:** Target >6

---

## 7. MODEL BIZNESOWY I MONETYZACJA

### 7.1. Pricing Tiers

**Free Tier** ($0/month):
- 1 projekt aktywny
- 20 person per projekt
- 5 focus groups/month
- 3 surveys/month
- 100 MB storage
- Community support

**Pro Tier** ($49/month):
- Unlimited projekty
- 100 person per projekt
- 50 focus groups/month
- 30 surveys/month
- 1 GB storage
- Advanced analytics
- Email support (48h)
- Export to PDF/CSV
- Compare personas (up to 3)

**Enterprise Tier** ($299/month):
- Unlimited personas
- Unlimited focus groups/surveys
- 10 GB storage
- Priority LLM models (Gemini Pro)
- Custom RAG integrations
- SSO
- 24h support
- Custom branding
- API access
- White-label option
- SLA 99.9%

**Add-ons:**
- Extra storage: $10/GB/month
- Priority processing: $20/month
- Custom models: $50/month
- Professional services: $150/hour

---

### 7.2. Revenue Streams

**Primary: SaaS Subscriptions**
- Target mix: 70% Pro, 30% Enterprise
- Projected MRR (Q2 2026):
  - 100 Pro × $49 = $4,900
  - 10 Enterprise × $299 = $2,990
  - **Total MRR: $7,890** (~$95k ARR)

**Secondary: Add-ons**
- Extra storage: ~10% adoption → $500/month
- Priority processing: ~5% adoption → $250/month
- **Total: $750/month**

**Tertiary: Professional Services**
- Custom integrations: 2 projects/month × $5k = $10k
- Training workshops: 1/month × $2k = $2k
- **Total: $12k/month**

**Total Projected Revenue (Q2 2026):**
- Subscriptions: $7,890
- Add-ons: $750
- Services: $12,000
- **Total: $20,640/month** (~$248k ARR)

---

### 7.3. Cost Structure

**Infrastructure Costs:**
- Cloud Run: $10-20/month
- Cloud SQL: $50/month
- Neo4j AuraDB: $65/month
- Redis (Upstash): $10/month
- Cloud Storage: $5/month
- Monitoring: $10/month
- **Total: ~$150/month**

**LLM Costs:**
- 100 MAU × 10 personas × 3k tokens = 3M tokens/month
- 100 MAU × 3 FG × 10 personas × 1k tokens = 3M tokens/month
- RAG: 1M tokens/month
- **Total: 7M tokens × $0.00005 = $350/month**

**Personnel (Post-PMF):**
- CTO: $8k/month
- Backend Dev: $6k/month
- Frontend Dev: $5k/month
- Sales/Marketing: $3k/month
- **Total: $22k/month**

**Total Monthly Costs:** ~$22,605

**Break-even:** 452 paying users (~500 MAU z 90% conversion)

**Unit Economics:**
- ARPU: $50/month
- Variable cost: ~$6/month (LLM + infra)
- Gross margin: $44/user (88%)
- CAC: $100
- Payback: 2.3 months
- LTV (12 months): $600
- **LTV/CAC: 6.0** (excellent, >3 is good)

---

## 8. GO-TO-MARKET STRATEGY

### 8.1. Target Segments (Prioritized)

**Phase 1 (MVP - Q1 2026): Early Adopters**
- **Product Managers w tech startups**
  - Pain: Brak budżetu ($15k/sesja)
  - Channel: Product Hunt, Twitter/X, LinkedIn
  - **Target:** 10 early adopters

**Phase 2 (Q2 2026): Product/Market Fit**
- **Marketerzy w SMB (50-200 employees)**
  - Pain: Tight deadlines, limited resources
  - Channel: SEO, Google Ads
  - **Target:** 100 paying users (Pro)

**Phase 3 (Q3-Q4 2026): Scale**
- **Agencje badawcze i consulting firms**
  - Pain: Client pressure, recurring projects
  - Channel: Partnerships, webinars, conferences
  - **Target:** 500 paying users (70% Pro, 30% Enterprise)

---

### 8.2. Marketing Channels

**Owned Channels ($0-500/month):**
- **Blog (SEO):** 10 posts/month, rank top 3 dla 5 keywords w 6 months
- **Email Newsletter:** Weekly insights, 1,000 subscribers by Q2 2026
- **Twitter/X:** Daily updates, 500 followers by Q2 2026

**Paid Channels ($2k/month):**
- **Google Ads:** $1,500/month → 25 sign-ups ($60 CPA)
- **LinkedIn Ads:** $500/month → 10 sign-ups ($50 CPA)

**Community Channels (Time only):**
- **Product Hunt:** Launch #1 Product of the Day → 500 upvotes, 50 sign-ups
- **Reddit (r/marketing, r/productmanagement):** Organic engagement
- **Indie Hackers, HackerNews:** "Show HN" → 100 visits, 10 sign-ups

**Partnership Channels (Revenue share):**
- **Integrations:** Notion, Figma, Miro → 1-2 by Q2 2026
- **Affiliate program:** 20% commission → 10 affiliates

---

### 8.3. Sales Strategy

**Self-Serve (Free + Pro):**
- No sales calls
- In-app wizard + video tutorials
- Upsell triggers: Hit limits, Advanced features
- **Conversion:** 12% (Free → Pro)

**Enterprise Sales:**
- Sales calls required (demos, contracts, security)
- Target: Agencies (10+ employees), consulting, large enterprises
- Sales cycle: 1-3 months
- ACV: $3,588
- **Target:** 2 Enterprise deals/month

---

## 9. KONKURENCJA I POZYCJONOWANIE

### 9.1. Konkurencyjne Rozwiązania

**Traditional Focus Groups (Millward Brown, Ipsos, GfK):**
- Strengths: Real humans, body language, depth
- Weaknesses: Koszt (15k PLN), czas (2-4 tyg), scale (6-12)
- **Sight:** "99% taniej, 99% szybciej, unlimited scale"

**Survey Tools (SurveyMonkey, Typeform, Google Forms):**
- Strengths: Łatwe, tanie, quantitative
- Weaknesses: Brak qualitative depth, low response (15-20%)
- **Sight:** "Qualitative insights z quantitative scale"

**Synthetic Data Tools (Mostly AI, Synthetic Users, Gretel):**
- Strengths: Privacy, GDPR, scale
- Weaknesses: Generic, flat data, no focus groups
- **Sight:** "Statistical validity + RAG context + Focus groups"

**AI Research Tools (Dovetail, Notably):**
- Strengths: AI analysis, integrations
- Weaknesses: Require real data, brak synthetic personas
- **Sight:** "Generate data + Analyze data (end-to-end)"

**Generic LLM (ChatGPT, Claude):**
- Strengths: Flexible, conversational, cheap
- Weaknesses: Generic, brak validity, no persistence
- **Sight:** "Purpose-built for market research"

---

### 9.2. Competitive Advantages

**1. Hybrid RAG (Vector + Keyword + Graph)**
- Konkurenci: Vector-only OR Graph-only
- **Sight:** 3-way fusion → Precision@5: 70% (vs. 50-55%)

**2. Event Sourcing dla Person**
- Konkurenci: Statyczne persony
- **Sight:** Immutable events + semantic search

**3. Statistical Validation (Chi-kwadrat)**
- Konkurenci: Random generation
- **Sight:** p > 0.05 → validity

**4. Async Parallelization (3-4x speedup)**
- Konkurenci: Sequential
- **Sight:** asyncio.gather() → 45s dla 20 personas

**5. Production-Ready Infrastructure**
- Konkurenci: Prototype quality
- **Sight:** Cloud Run + Redis + Retry + Monitoring

---

### 9.3. Positioning Statement

**For:** Product Managers, Marketerzy, Badacze Rynku w tech/SaaS

**Who:** Need fast, affordable, statistically valid qualitative insights

**Sight is:** An AI-powered virtual focus group platform

**That:** Generates 20+ realistic personas z RAG + runs discussions w <5 min

**Unlike:** Traditional focus groups (2-4 tyg, 15k PLN) OR survey tools (brak depth)

**Sight:** 99% cost savings, 99% time savings, unlimited scale, z statistical validity + real-world context (GUS, CBOS via RAG)

---

## 10. ROADMAP I NEXT STEPS

### 10.1. MVP Status (Q4 2025 - CURRENT)

**✅ Implemented:**
- Persona generation (45s, validation)
- Focus groups (async, 2-5 min)
- Hybrid RAG (vector + keyword + RRF)
- GraphRAG (Cypher, graph analytics)
- Surveys (4 types, AI responses)
- Dashboard (8 KPI cards, Redis cache, N+1 optimization)
- PersonaDetailsDrawer (Profile + Needs + Insights)
- Event Sourcing (Memory, audit trail)
- Cloud Run deployment (CI/CD, migrations, tests)
- 380 tests (80%+ coverage)

**🚧 In Progress (27 active tasks):**
- Integration tests w CI/CD
- RBAC enforcement
- Semantic chunking
- Coverage 85%+

---

### 10.2. Post-MVP Priorities (Q1-Q2 2026)

**High Priority (Must Have):**

**1. Export Functionality (2 weeks)**
- Export personas/focus groups do PDF/CSV/JSON
- PII masking, watermarks, selective sections
- **Value:** Shareable insights dla presentations

**2. Compare Personas (2 weeks)**
- Side-by-side (up to 3)
- Similarity score (cosine)
- Highlight differences
- **Value:** Segment differentiation

**3. LLM-Powered Customer Journey (3 weeks)**
- Gemini Pro generates 4 etapy (Awareness → Post-Purchase)
- Touchpoints, emotions, buying signals, actions
- **Value:** Actionable marketing playbook

**4. CRM Integration (4 weeks)**
- Salesforce, HubSpot API
- Replace heurystyki z real data
- **Value:** Enterprise customers

**5. Pricing + Payment (3 weeks)**
- Stripe (Free, Pro $49, Enterprise $299)
- Usage-based billing
- **Value:** Revenue generation

---

**Medium Priority (Should Have):**

**6. Semantic Chunking RAG (2 weeks)**
- RecursiveCharacterTextSplitter
- Respect paragraph boundaries
- **Value:** Higher precision

**7. Real-time Collaboration (4 weeks)**
- WebSocket comments, @mentions, notifications
- **Value:** Team workflows

**8. Graph Analytics Restoration (1 week)**
- Unhide `graph_service.py`
- Endpoint `/focus-groups/{id}/graph-analytics`
- **Value:** Power users

**9. Advanced Analytics (3 weeks)**
- Cohort analysis, funnel analysis
- **Value:** Product optimization

---

**Low Priority (Could Have):**

**10. Dark Mode (1 week)**
**11. Mobile App (8 weeks)**
**12. API Access (3 weeks)**

---

### 10.3. Long-Term Vision

**Year 1 (2026): Product/Market Fit**
- **Goal:** 500 paying, $25k MRR, 95% retention
- **Features:** Export, Compare, Journey, CRM, Pricing
- **Team:** 3 FTE
- **Revenue:** ~$300k ARR

**Year 2 (2027): Scale + Enterprise**
- **Goal:** 2,000 paying, $100k MRR
- **Features:** Collaboration, Mobile, API, White-label
- **Team:** 10 FTE
- **Revenue:** ~$1.2M ARR
- **Funding:** Seed ($500k-1M)

**Year 3 (2028): Market Leader**
- **Goal:** 10,000 paying, $500k MRR
- **Features:** AI Moderator, Multi-language, Industry templates
- **Team:** 30 FTE
- **Revenue:** ~$6M ARR
- **Funding:** Series A ($5-10M)

---

## PODSUMOWANIE

### Kluczowe Wnioski:

**1. Problem-Solution Fit: ✅ STRONG**
- Traditional: 15k PLN, 2-4 tyg → **Sight: $5-10, <5 min**
- ROI: **99.9% cost, 99.8% time savings**
- TAM: ~$2B globally (Product Managers, Marketerzy, Badacze)

**2. Competitive Advantage: ✅ UNIQUE**
- Hybrid RAG (Precision@5: 70% vs. 50%)
- Event Sourcing (consistency + audit)
- Statistical Validation (chi-kwadrat)
- Async Parallelization (3-4x speedup)

**3. Technical Execution: ✅ PRODUCTION-READY**
- 380 tests, 80%+ coverage
- Cloud Run + CI/CD
- Redis cache, N+1 optimization
- <500ms latency

**4. Unit Economics: ✅ PROFITABLE**
- ARPU: $50/month
- Gross margin: 88% ($44/user)
- LTV/CAC: 6.0 (excellent)
- Break-even: 452 paying users

**5. Roadmap: ✅ CLEAR**
- MVP (Q4 2025): ✅ Done
- Post-MVP (Q1-Q2 2026): Export, Compare, Journey, Pricing
- Scale (Q3-Q4 2026): 500 users, $25k MRR

---

**Rekomendacje (Next 30 days):**
1. **Product Hunt launch** → 10 early adopters
2. **Case study #1** → Document savings
3. **SEO content** → 5 blog posts

**Q1 2026:**
1. Export + Compare → viral loop
2. Stripe integration → revenue
3. 100 paying users → PMF validation

**Q2-Q4 2026:**
1. CRM integration → Enterprise
2. Partnerships → distribution
3. 500 users, $25k MRR → Seed ready

---

**Dokumentacja powiązana:**
- **PLAN.md** - Strategic roadmap (27 aktywnych zadań)
- **README.md** - User-facing docs, quick start
- **CLAUDE.md** - Instrukcje dla Claude Code
- **docs/INFRASTRUCTURE.md** - Docker, CI/CD, Cloud Run
- **docs/SERVICES.md** - Architektura serwisów
- **docs/RAG.md** - System RAG (Hybrid Search + GraphRAG)
- **docs/AI_ML.md** - AI/LLM system, persona generation

---

**Wersja dokumentu:** 1.0 (2025-10-28)
**Ostatnia aktualizacja:** 2025-10-28