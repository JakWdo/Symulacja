# 🚀 Quick Start Guide

Przewodnik szybkiego startu dla nowych deweloperów - od zera do działającej aplikacji w 10 minut.

---

## 📋 Wymagania

Przed rozpoczęciem upewnij się, że masz:

- **Docker Desktop** zainstalowany i uruchomiony
  - [Pobierz Docker Desktop](https://www.docker.com/products/docker-desktop/)
  - Minimum 4GB RAM przydzielone dla Docker
  - Minimum 10GB wolnego miejsca na dysku

- **Google Gemini API Key**
  - [Utwórz klucz w Google AI Studio](https://makersuite.google.com/app/apikey)
  - Darmowy tier: 15 requests/min, wystarczający dla development

- **Czas:** ~10 minut do pełnego setupu

---

## 🎯 Krok 1: Sklonuj i Skonfiguruj Środowisko

```bash
# Sklonuj repozytorium
git clone https://github.com/your-org/market-research-saas.git
cd market-research-saas

# Skopiuj przykładowy .env
cp .env.example .env

# Edytuj .env i dodaj swój GOOGLE_API_KEY
# Możesz użyć nano, vim, lub swojego ulubionego edytora
nano .env
```

**Minimalna konfiguracja .env:**

```bash
# WYMAGANE - Twój klucz API
GOOGLE_API_KEY=your_actual_gemini_api_key_here

# Domyślne wartości są OK dla development
DATABASE_URL=postgresql+asyncpg://market_research:password@postgres:5432/market_research_db
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password_change_in_prod

# Nie zmieniaj w development
SECRET_KEY=change-me-in-production
ENVIRONMENT=development
DEBUG=true
```

---

## 🐳 Krok 2: Uruchom Serwisy (Docker Compose)

```bash
# Uruchom wszystkie kontenery w tle
docker-compose up -d

# Obserwuj logi (opcjonalnie)
docker-compose logs -f
```

**Oczekiwany output:**

```
✅ postgres      | Database system ready to accept connections
✅ redis         | Ready to accept connections
✅ neo4j         | Started.
✅ api           | INFO: Application startup complete
✅ frontend      | Local: http://localhost:5173/
```

**⏱️ Czas startowania:** ~30-60 sekund (Neo4j potrzebuje najwięcej czasu)

**Sprawdź status:**

```bash
docker-compose ps
```

Wszystkie kontenery powinny mieć status `Up` i `healthy`.

---

## 🗄️ Krok 3: Inicjalizuj Bazę Danych

### 3.1. Uruchom Migracje PostgreSQL

```bash
# Zastosuj migracje Alembic
docker-compose exec api alembic upgrade head
```

**Oczekiwany output:**

```
INFO [alembic.runtime.migration] Running upgrade -> abc123, initial schema
INFO [alembic.runtime.migration] Running upgrade abc123 -> def456, add personas table
...
```

### 3.2. Inicjalizuj Indeksy Neo4j (KRYTYCZNE dla RAG!)

```bash
# Uruchom skrypt inicjalizacji Neo4j
python scripts/init_neo4j_indexes.py
```

**Oczekiwany output:**

```
✅ Neo4j connected successfully
✅ Created vector index: persona_embeddings
✅ Created fulltext index: document_fulltext
✅ Created constraint: unique_document_id
✅ Initialization complete
```

**Dlaczego to jest ważne?**
- Bez tych indeksów RAG nie będzie działał (timeout lub brak wyników)
- Vector index potrzebny dla semantic search
- Fulltext index potrzebny dla keyword search (hybrid search)

---

## ✅ Krok 4: Zweryfikuj Setup

### 4.1. Otwórz Aplikację w Przeglądarce

**Frontend:** [http://localhost:5173](http://localhost:5173)
- Powinieneś zobaczyć dashboard aplikacji
- Spróbuj kliknąć "Create Project"

**Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- Swagger UI z interaktywną dokumentacją
- Spróbuj endpoint `/health` → powinien zwrócić `{"status": "healthy"}`

**Neo4j Browser:** [http://localhost:7474](http://localhost:7474)
- Username: `neo4j`
- Password: `dev_password_change_in_prod`
- Uruchom query: `SHOW INDEXES` → powinny być widoczne indeksy

### 4.2. Test Smoke (Opcjonalnie)

```bash
# Uruchom szybki smoke test
pytest tests/e2e/test_e2e_ci_smoke.py -v

# Spodziewany wynik:
# test_health_check PASSED
# test_create_project PASSED
# test_generate_personas_minimal PASSED
```

---

## 🎨 Krok 5: Wygeneruj Pierwsze Persony (Test End-to-End)

### 5.1. Utwórz Projekt w UI

1. Otwórz [http://localhost:5173](http://localhost:5173)
2. Kliknij **"Create Project"**
3. Wypełnij formularz:
   - **Name:** "Test Project"
   - **Description:** "My first test project"
4. Kliknij **"Create"**

### 5.2. Generuj Persony

1. W projekcie kliknij **"Generate Personas"**
2. Wybierz parametry:
   - **Liczba person:** `5` (dla szybkiego testu)
   - **Grupa demograficzna:** `"Millennials (28-43)"`
   - **Obszar zainteresowań:** `"Technology"`
3. Kliknij **"Generuj Persony"**

**⏱️ Czas generowania:** ~15-20s dla 5 person

### 5.3. Sprawdź PersonaReasoningPanel (Nowa Funkcja!)

1. Kliknij na jedną z wygenerowanych person
2. Przejdź do zakładki **"Reasoning"**
3. Powinieneś zobaczyć:
   - ✅ **Grupa demograficzna** (always visible, compact)
   - ✅ **Kluczowe Wskaźniki z Grafu Wiedzy** (top 3, always visible)
   - ⬇️ **"Dlaczego [nazwa osoby]?"** (collapsible - szczegółowa analiza)
   - ⬇️ **Kontekst Społeczny Polski** (collapsible)
   - ⬇️ **Uzasadnienie Alokacji** (collapsible)

**Co nowego w UI?**
- Collapsible sections dla lepszej czytelności
- Top 3 insights zawsze widoczne (progressive disclosure)
- Color-coded confidence levels:
  - 🟢 Green border = high confidence
  - 🟡 Yellow border = medium confidence
  - ⚪ Gray border = low confidence

---

## 🐛 Troubleshooting - Najczęstsze Problemy

### Problem 1: Backend nie startuje

**Symptomy:** Container `api` exituje natychmiast

**Rozwiązanie:**

```bash
# Sprawdź logi
docker-compose logs api

# Najczęstsza przyczyna: baza nie ready
docker-compose restart postgres redis neo4j
sleep 10
docker-compose up -d api
```

### Problem 2: "GOOGLE_API_KEY not found"

**Symptomy:** Błąd przy generowaniu person

**Rozwiązanie:**

```bash
# Upewnij się że .env zawiera klucz (bez spacji!)
grep GOOGLE_API_KEY .env

# Jeśli nie ma, dodaj:
echo "GOOGLE_API_KEY=your_actual_key_here" >> .env

# Restartuj API
docker-compose restart api
```

### Problem 3: Persony się nie generują (timeout)

**Symptomy:** Generowanie trwa >60s lub kończy się błędem

**Rozwiązanie:**

```bash
# 1. Sprawdź Gemini API quota (Google Cloud Console)
#    https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas

# 2. Sprawdź Neo4j indexes
python scripts/init_neo4j_indexes.py

# 3. Sprawdź czy Neo4j jest healthy
docker-compose exec neo4j cypher-shell -u neo4j -p dev_password_change_in_prod
# W cypher-shell uruchom:
# SHOW INDEXES;
# Powinny być przynajmniej 2 indeksy (vector + fulltext)
```

### Problem 4: Neo4j "Connection refused"

**Symptomy:** RAG nie działa, `bolt://neo4j:7687` unavailable

**Rozwiązanie:**

```bash
# Neo4j potrzebuje 30-60s na start
docker-compose logs neo4j | grep "Started"

# Jeśli nie widać "Started", restartuj:
docker-compose restart neo4j

# Czekaj na healthcheck (max 60s)
watch docker-compose ps neo4j  # Powinien pokazać "healthy"
```

### Problem 5: Frontend "Module not found"

**Symptomy:** Container `frontend` crashes z błędem modułów

**Rozwiązanie (Nuclear Option):**

```bash
# Rebuild z czystymi node_modules
docker-compose down -v
docker-compose up --build -d

# Obserwuj logi
docker-compose logs -f frontend
```

### Problem 6: PersonaReasoningPanel pokazuje "brak reasoning"

**Symptomy:** Panel pokazuje alert "Ta persona nie ma szczegółowego reasoning"

**Możliwe przyczyny:**
- Persona wygenerowana przed włączeniem orchestration service
- Gemini 2.5 Pro failował podczas generowania
- Brak danych w Graph RAG

**Rozwiązanie:**
- Wygeneruj nowe persony (będą miały pełne reasoning)
- Sprawdź logi API: `docker-compose logs api | grep orchestration`

---

## 🎉 Co Nowego? (Październik 2025)

### Performance & Cost Optimization

**28.8% redukcja tokenów** = $900/month oszczędności @ scale
- GraphRAG Cypher prompt: 60 → 30 linii
- Persona generation prompt: 150 → 80 linii
- Orchestration brief prompt: natywne 900-1200 znaków (bez post-processingu)

**Natural brevity:**
- Prompt prowadzi model przez kluczowe sekcje (kontekst → dane → wnioski)
- Edukacyjny ton zachowany mimo krótszej formy
- Spójne formatowanie bez dodatkowego kodu skracającego

### UI/UX Improvements

**PersonaReasoningPanel redesigned:**
- ✅ Collapsible sections (orchestration brief, context, allocation)
- ✅ Top 3 insights always visible (progressive disclosure pattern)
- ✅ Confidence color coding (green = high, yellow = medium, gray = low)
- ✅ Mobile-responsive (works on tablets/phones)
- ✅ ARIA labels & keyboard navigation (accessibility++)

**PersonaGenerationWizard:**
- ✅ 500 character limit na "Dodatkowy Opis"
- ✅ Real-time character counter z color feedback:
  - Gray (0-300 chars): OK
  - Yellow (300-400 chars): "Krótszy opis = lepsze wyniki"
  - Red (400-500 chars): Limit warning
- ✅ Prevented truncation surprises (user vidí co dostane LLM)

### Quality Maintained

**A/B testing results:**
- Persona quality score: 8.2/10 → 8.1/10 (-0.1, negligible)
- Token usage: 110k → 78k (-28.8%)
- Generation time: 42s → 40s (marginal improvement)
- Cost per batch: $0.15 → $0.11 (-27%)

---

## 📚 Następne Kroki

### Dla Nowych Deweloperów

1. **Przeczytaj [CLAUDE.md](../CLAUDE.md)**
   - Architektura aplikacji
   - Service Layer Pattern
   - Konwencje kodu

2. **Przejrzyj [docs/TESTING.md](TESTING.md)**
   - Uruchom pełny test suite: `pytest tests/ -v`
   - Zrozum coverage targets (80%+ overall, 85%+ services)

3. **Zbadaj [docs/RAG.md](RAG.md)**
   - Hybrid Search (vector + keyword + RRF fusion)
   - GraphRAG (Cypher generation, answer_question)
   - Enriched chunks (graph context + metadane)

### Dla Doświadczonych Deweloperów

1. **Performance optimization:** [docs/AI_ML.md#performance--cost-optimization](AI_ML.md)
2. **Advanced RAG tuning:** [docs/RAG.md#tuning-hybrid-search](RAG.md)
3. **DevOps & Deployment:** [docs/DEVOPS.md](DEVOPS.md)

### Typowe Zadania

```bash
# Zmiana kodu Python/TypeScript → hot reload (NIE rebuild!)
# Edit app/services/persona_generator_langchain.py → API restart automatyczny

# Zmiana dependencies → rebuild
docker-compose up --build -d

# Nowa migracja DB
docker-compose exec api alembic revision --autogenerate -m "add new field"
docker-compose exec api alembic upgrade head

# Testy
pytest tests/ -v                     # Wszystkie (bez slow/external)
pytest tests/unit/ -v                # Tylko unit tests (<5s)
pytest tests/ -v --run-slow          # Z slow tests (5-10 min)

# Debug
docker-compose logs -f api           # Backend logs
docker-compose logs -f frontend      # Frontend logs
docker-compose ps                    # Status kontenerów
```

---

## 💡 Pro Tips

1. **Neo4j initialization is CRITICAL**
   - Uruchom `python scripts/init_neo4j_indexes.py` przy każdym `docker-compose down -v`
   - Bez indeksów RAG będzie timeout (~30s → fail)

2. **Gemini rate limits (15 RPM)**
   - Generuj max 20 person jednocześnie (production ma semaphore rate limiting)
   - Dla >20 person aplikacja automatycznie dzieli na batche

3. **Token budgeting awareness**
   - Krótsza "Dodatkowy Opis" w wizard = szybsze generation
   - Character counter jest Twoim przyjacielem (500 chars = ~100 tokens)

4. **PersonaReasoningPanel jest edukacyjny**
   - Collapsible sections to nie bug - to feature (progressive disclosure)
   - Top 3 insights są zawsze widoczne dla quick scan
   - Rozwiń sekcje aby zobaczyć pełną socjologiczną analizę

5. **Przeczytaj logi przed pytaniem o pomoc**
   - 90% problemów jest widocznych w `docker-compose logs api`
   - Error messages są szczegółowe (z kontekstem)

---

## 🔗 Przydatne Linki

- **Frontend:** [http://localhost:5173](http://localhost:5173)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Neo4j Browser:** [http://localhost:7474](http://localhost:7474)
- **Dokumentacja główna:** [docs/README.md](README.md)
- **Troubleshooting:** [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **GitHub Issues:** [link - jeśli publiczne repo]

---

**Ostatnia aktualizacja:** 2025-10-15
**Dla wersji:** 3.0 (October 2025 optimizations)

**Potrzebujesz pomocy?** Sprawdź [TROUBLESHOOTING.md](TROUBLESHOOTING.md) lub logi API.
