# CLAUDE.md

Ten plik zawiera instrukcje dla Claude Code (claude.ai/code) podczas pracy z kodem w tym repozytorium.

## Output Style

**WAŻNE:** Dla tego projektu zawsze używaj output style **"edukacyjny"**.

Aktywuj go na początku każdej sesji poprzez wczytanie zawartości z:
`~/.claude/output-styles/edukacyjny.md`

Ten styl zapewnia:
- Konwersacyjny ton (jak kolega z zespołu)
- Edukacyjne wyjaśnienia ("dlaczego", nie tylko "co")
- Production-ready kod i dokumentacja
- Polski w komunikacji, angielski w kodzie

## Przegląd Projektu

Market Research SaaS - Platforma do wirtualnych grup fokusowych z AI wykorzystująca Google Gemini do generowania syntetycznych person i symulacji dyskusji badawczych. Wersja produkcyjna z pełną funkcjonalnością.

**Stack Technologiczny:**
- Backend: FastAPI (Python 3.11+), PostgreSQL + pgvector, Redis, Neo4j
- Frontend: React 18 + TypeScript, Vite, TanStack Query, Tailwind CSS
- AI: Google Gemini 2.5 (Flash/Pro) via LangChain
- Infrastruktura: Docker + Docker Compose

## Polecenia Deweloperskie

### Operacje Docker (Podstawowa Metoda Deweloperska)

**Architektura Docker:**
Projekt używa **multi-stage Docker builds** dla optymalnej wydajności:
- **Development**: Hot reload, volume mounts, instant starty
- **Production**: Zoptymalizowane images, nginx, gunicorn, brak dev tools

**Aktywne Kontenery:**
- `postgres` - PostgreSQL + pgvector
- `redis` - Redis (cache i session storage)
- `neo4j` - Neo4j (graf wiedzy)
- `api` - Backend FastAPI
- `frontend` - Frontend React + Vite

#### Development Environment

```bash
# Uruchom wszystkie serwisy (DEVELOPMENT)
docker-compose up -d

# Pierwsze uruchomienie (force rebuild po zmianach w Dockerfile)
docker-compose up -d --build

# Logi
docker-compose logs -f api
docker-compose logs -f frontend

# Restart serwisów (po zmianie kodu Python, jeśli hot reload nie działa)
docker-compose restart api
docker-compose restart frontend

# Przebuduj kontenery (po zmianie dependencies: requirements.txt, package.json)
docker-compose up --build -d

# Zatrzymaj wszystkie serwisy
docker-compose down

# Zatrzymaj i usuń wolumeny (USUWA DANE! Użyj dla czystego startu)
docker-compose down -v
```

**WAŻNE - Nowa Architektura:**
- ✅ **Instant starty**: Frontend NIE uruchamia `npm install` przy każdym `up` (node_modules cached w image)
- ✅ **Named volumes**: `frontend_node_modules` zapobiega konfliktom host vs container
- ✅ **Multi-stage builds**: ~50% mniejsze images, szybsze buildy dzięki layer caching
- ✅ **No duplication**: dependencies instalowane RAZ podczas build, nie przy każdym start

**Kiedy Rebuild?**
- ✅ Zmiana `requirements.txt` (Python deps) → `docker-compose up --build -d`
- ✅ Zmiana `package.json` (npm deps) → `docker-compose up --build -d`
- ✅ Zmiana `Dockerfile` → `docker-compose up --build -d`
- ❌ Zmiana kodu `.py` lub `.tsx` → NIE rebuild (hot reload działa)

#### Production Environment

```bash
# Deploy do produkcji
docker-compose -f docker-compose.prod.yml up -d --build

# Logi produkcyjne
docker-compose -f docker-compose.prod.yml logs -f

# Status serwisów
docker-compose -f docker-compose.prod.yml ps

# Zatrzymaj produkcję
docker-compose -f docker-compose.prod.yml down
```

**Production Features:**
- 🚀 **Frontend**: Nginx serving static build (~25MB image vs ~500MB dev)
- 🚀 **Backend**: Gunicorn z multiple workers (production ASGI server)
- 🔒 **Security**: Non-root users, resource limits, brak debug mode
- 📦 **Optimized**: Multi-stage builds, brak development dependencies
- 🔌 **Internal network**: Databases NIE exposed na host (tylko internal Docker network)

**PRZED DEPLOYEM DO PRODUKCJI:**
1. Skopiuj `.env.production.example` → `.env.production`
2. Wypełnij **WSZYSTKIE** env vars (SECRET_KEY, passwords, API keys)
3. Zmień hasła baz danych (POSTGRES_PASSWORD, NEO4J_PASSWORD)
4. Skonfiguruj ALLOWED_ORIGINS (tylko trusted domains)
5. Sprawdź checklist w `docker-compose.prod.yml`

### Migracje Bazy Danych (Alembic)

```bash
# Wykonaj migracje
docker-compose exec api alembic upgrade head

# Utwórz nową migrację
docker-compose exec api alembic revision --autogenerate -m "opis"

# Rollback jednej migracji
docker-compose exec api alembic downgrade -1

# Historia migracji
docker-compose exec api alembic history
```

### Inicjalizacja Neo4j (WYMAGANE dla RAG)

```bash
# Utwórz wymagane indeksy w Neo4j (vector + fulltext)
python scripts/init_neo4j_indexes.py

# Ten skrypt tworzy:
# 1. Vector index (rag_document_embeddings) - dla semantic search
# 2. Fulltext index (rag_fulltext_index) - dla keyword search

# WAŻNE: Uruchom ten skrypt PRZED pierwszym użyciem RAG!
```

### Testowanie

```bash
# Wszystkie testy
python -m pytest tests/ -v

# Z coverage
python -m pytest tests/ -v --cov=app --cov-report=html

# Konkretny plik testowy
python -m pytest tests/test_persona_generator.py -v

# Lista wszystkich testów
python -m pytest tests/ --collect-only
```

### Rozwój Frontendu

```bash
cd frontend

# Instalacja zależności
npm install

# Serwer deweloperski (standalone)
npm run dev

# Build produkcyjny
npm run build

# Podgląd build produkcyjnego
npm run preview

# Lint TypeScript
npm run lint
```

## Architektura

### Wzorzec Service Layer (Backend)

Backend wykorzystuje **architekturę zorientowaną na serwisy**, gdzie logika biznesowa jest oddzielona od endpointów API:

```
Endpointy API (app/api/*.py)
    ↓
Warstwa Serwisów (app/services/*_langchain.py)
    ↓
Modele/DB (app/models/*.py)
```

**Kluczowe Serwisy:**
- `PersonaGeneratorLangChain` - Generuje statystycznie reprezentatywne persony używając Gemini + statistical sampling (walidacja chi-kwadrat)
- `FocusGroupServiceLangChain` - Orkiestruje dyskusje grup fokusowych, przetwarza odpowiedzi równolegle
- `MemoryServiceLangChain` - System event sourcing z semantic search używając Google embeddings
- `DiscussionSummarizerService` - Podsumowania AI używając Gemini Pro
- `PersonaValidator` - Walidacja statystyczna rozkładów person
- `GraphService` - Analiza grafów wiedzy w Neo4j (koncepty, emocje, relacje)
- `SurveyResponseGenerator` - Generator odpowiedzi na ankiety syntetyczne

### System Pamięci i Kontekstu

Platforma używa **event sourcing** dla pamięci person:
1. Każda akcja/odpowiedź persony jest zapisywana jako niezmienny `PersonaEvent`
2. Eventy mają embeddingi (via Google Gemini) dla semantic search
3. Przy odpowiadaniu na pytania, pobierany jest kontekst z przeszłości via similarity search
4. Zapewnia spójność w wielopytaniowych dyskusjach

### Architektura Równoległego Przetwarzania

Grupy fokusowe przetwarzają odpowiedzi person **równolegle** używając asyncio:
- Każda persona ma własny async task
- ~20 person × 4 pytania = ~2-5 minut (vs 40+ minut sekwencyjnie)
- Target: <3s per persona response, <30s total focus group time

### Schemat Bazy Danych

Główne modele:
- `User` - Użytkownicy systemu (autoryzacja JWT)
- `Project` - Kontener projektu badawczego
- `Persona` - Syntetyczna persona z demografią + psychologią (Big Five, Hofstede)
- `FocusGroup` - Sesja dyskusyjna łącząca persony z pytaniami
- `PersonaResponse` - Indywidualne odpowiedzi person
- `PersonaEvent` - Log event sourcing z embeddingami
- `Survey` - Ankiety z pytaniami (single/multiple choice, rating scale, open text)
- `SurveyResponse` - Odpowiedzi person na ankiety

## Konfiguracja i Środowisko

**Wymagane Zmienne Środowiskowe (.env):**

```bash
# Baza danych
DATABASE_URL=postgresql+asyncpg://market_research:password@postgres:5432/market_research_db

# AI (WYMAGANE!)
GOOGLE_API_KEY=your_gemini_api_key_here

# Modele
PERSONA_GENERATION_MODEL=gemini-2.5-flash
ANALYSIS_MODEL=gemini-2.5-pro
DEFAULT_MODEL=gemini-2.5-flash

# Redis & Neo4j
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password_change_in_prod

# Bezpieczeństwo (ZMIEŃ W PRODUKCJI!)
SECRET_KEY=change-me
ENVIRONMENT=development
DEBUG=true
```

**Ważne Ustawienia ([app/core/config.py](app/core/config.py)):**
- `TEMPERATURE=0.7` - Kreatywność LLM (0.0-1.0)
- `MAX_TOKENS=8000` - Maksymalna długość odpowiedzi (gemini-2.5 używa reasoning tokens!)
- `RANDOM_SEED=42` - Dla powtarzalności
- `MAX_RESPONSE_TIME_PER_PERSONA=3` - Cel wydajnościowy (sekundy)
- `MAX_FOCUS_GROUP_TIME=30` - Cel czasu całkowitego (sekundy)

**Konfiguracja RAG Hybrid Search:**
- `RAG_USE_HYBRID_SEARCH=True` - Włącz hybrid search (vector + keyword)
- `RAG_VECTOR_WEIGHT=0.7` - Waga vector search w RRF (0.0-1.0)
- `RAG_RRF_K=60` - Parametr wygładzania Reciprocal Rank Fusion
- `RAG_TOP_K=5` - Liczba top wyników z retrieval
- `RAG_CHUNK_SIZE=2000` - Rozmiar chunków tekstowych (znaki)
- `RAG_CHUNK_OVERLAP=400` - Overlap między chunkami

**Konfiguracja GraphRAG Node Properties:**
- `RAG_NODE_PROPERTIES_ENABLED=True` - Włącz bogate metadane węzłów grafu
- `RAG_EXTRACT_SUMMARIES=True` - Ekstrakcja summary dla każdego węzła (1 zdanie)
- `RAG_EXTRACT_KEY_FACTS=True` - Ekstrakcja key_facts (lista faktów)
- `RAG_RELATIONSHIP_CONFIDENCE=True` - Ekstrakcja confidence dla relacji (0.0-1.0)

## Punkty Dostępu API

- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Frontend: http://localhost:5173
- Neo4j Browser: http://localhost:7474

## Typowe Workflow Deweloperskie

### Testowanie Połączenia z Gemini API

```bash
# Sprawdź API key
docker-compose exec api printenv GOOGLE_API_KEY

# Testuj Gemini API bezpośrednio
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hi"}]}]}'
```

### Tworzenie Testowych Projektów via API

```bash
# Utwórz projekt
PROJECT_ID=$(curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test",
    "description": "Projekt testowy",
    "target_demographics": {
      "age_group": {"18-24": 0.5, "25-34": 0.5},
      "gender": {"Male": 0.5, "Female": 0.5}
    },
    "target_sample_size": 10
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Generuj persony
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/personas/generate" \
  -H "Content-Type: application/json" \
  -d '{"num_personas": 10, "adversarial_mode": false}'

# Listuj persony
curl "http://localhost:8000/api/v1/projects/$PROJECT_ID/personas"
```

### Proces Generowania Person

Generowanie person używa **hybrydowego AI + statistical sampling + RAG**:
1. Sample demografii z rozkładów docelowych (walidacja chi-kwadrat)
2. Sample Big Five personality traits (rozkład normalny wokół średnich populacyjnych)
3. Sample Hofstede cultural dimensions (bazowane na lokalizacji)
4. **RAG z Hybrid Search (zawsze aktywny)**:
   - **Vector search**: Semantic similarity przez Google Gemini embeddings
   - **Keyword search**: Lexical matching przez Neo4j fulltext index
   - **RRF Fusion**: Reciprocal Rank Fusion łączy oba wyniki (k=60)
   - Pobiera najbardziej relevantny kontekst z raportów o polskim społeczeństwie
5. Użyj Gemini do generacji realistycznej narracji profilu, tła, wartości z kontekstem RAG
6. Waliduj dopasowanie statystyczne finalnej kohorty
7. Waliduj zgodność wieku z opisem (ekstrakcja wieku z background_story)

**Polskie Realia:**
- Imiona i nazwiska: 60+ polskich imion męskich, 60+ żeńskich, 100+ nazwisk
- Dochody w złotówkach (PLN): od <3000 zł do >15000 zł netto miesięcznie
- Edukacja: polski system (podstawowe, zasadnicze zawodowe, średnie, policealne, wyższe)
- Lokalizacje: Warszawa, Kraków, Wrocław, Gdańsk, etc.
- Zawody: typowe dla polskiego rynku pracy
- Wartości i zainteresowania: zgodne z polską kulturą

**Dodatkowy Opis Grupy:**
- Użytkownik może dodać opis w AI Wizard (np. "Osoby zainteresowane ekologią")
- Opis jest przekazywany do promptu LLM i wpływa na cechy person

**Wydajność:** ~30-60s dla 20 person (Gemini Flash)

**Testowanie Hybrid Search:**
```bash
# Test RAG hybrid search (wymaga uruchomionego Neo4j + zaindeksowanych dokumentów)
python tests/manual/test_hybrid_search.py
```

## System Analizy Grafowej (Graf Wiedzy)

Platforma zawiera **automatyczny graf wiedzy** zbudowany w Neo4j, który dostarcza głębokich insightów z dyskusji grup fokusowych. Po zakończeniu każdej grupy fokusowej, system automatycznie ekstraktuje koncepty, emocje i relacje używając LLM.

### Architektura

**Przepływ Danych:**
1. Grupa fokusowa kończy się → Automatyczne budowanie grafu
2. LLM (Gemini Flash) ekstraktuje koncepty, emocje, sentiment z każdej odpowiedzi
3. Graf Neo4j tworzony z nodami: Personas, Concepts, Emotions
4. Relacje: MENTIONS, FEELS, AGREES_WITH, DISAGREES_WITH
5. Frontend pobiera i wizualizuje graf z zaawansowaną analityką

**Kluczowe Komponenty:**
- **Backend:** [app/services/graph_service.py](app/services/graph_service.py) - Integracja Neo4j z LangChain
- **API:** [app/api/graph_analysis.py](app/api/graph_analysis.py) - Endpointy RESTful
- **Frontend:** [frontend/src/components/panels/GraphAnalysisPanel.tsx](frontend/src/components/panels/GraphAnalysisPanel.tsx) - Wizualizacja 3D + insighty

### Dostępne Insighty Grafowe

**1. Kluczowe Koncepty** - Najczęściej wspomniane tematy z sentimentem
```bash
GET /api/v1/graph/{focus_group_id}/concepts
```

**2. Kontrowersyjne Koncepty** - Polaryzujące tematy (wysoka wariancja sentymentu)
```bash
GET /api/v1/graph/{focus_group_id}/controversial
# Zwraca koncepty z podziałem na zwolenników vs krytyków
```

**3. Korelacje Trait-Opinion** - Różnice wiekowe/demograficzne w opiniach
```bash
GET /api/v1/graph/{focus_group_id}/correlations
# Pokazuje jak młodzi vs starsi uczestnicy czują o konceptach
```

**4. Rozkład Emocji** - Emocjonalne odpowiedzi uczestników
```bash
GET /api/v1/graph/{focus_group_id}/emotions
```

**5. Wpływowe Persony** - Najbardziej połączeni uczestnicy (thought leaders)
```bash
GET /api/v1/graph/{focus_group_id}/influential
```

### Przykład: Znajdowanie Polaryzujących Tematów

```bash
# Uruchom grupę fokusową
curl -X POST http://localhost:8000/api/v1/focus-groups/{id}/run

# Graf jest automatycznie budowany po zakończeniu

# Odpytaj kontrowersyjne koncepty
curl http://localhost:8000/api/v1/graph/{focus_group_id}/controversial
```

**Przykładowa Odpowiedź:**
```json
{
  "controversial_concepts": [
    {
      "concept": "Cena",
      "avg_sentiment": 0.1,
      "polarization": 0.85,
      "supporters": ["Anna Kowalska", "Jan Nowak"],
      "critics": ["Maria Wiśniewska", "Piotr Zieliński"],
      "total_mentions": 12
    }
  ]
}
```

### Zaawansowane Zapytania Cypher

System zawiera gotowe zapytania analityczne w [app/services/graph_service.py](app/services/graph_service.py):

- **Kontrowersyjne Koncepty:** `get_controversial_concepts()` - Używa odchylenia standardowego do znajdowania polaryzujących tematów
- **Korelacje Trait:** `get_trait_opinion_correlations()` - Segmentacja opinii bazowana na wieku
- **Analiza Wpływu:** `get_influential_personas()` - Liczenie połączeń w stylu PageRank

### Użycie na Frontendzie

Zakładka Graph Analysis pojawia się automatycznie po zakończeniu grupy fokusowej:

1. Nawiguj do Focus Group → zakładka "Graph Analysis"
2. Interaktywna wizualizacja 3D z kolorowanymi nodami:
   - 🔵 Niebieski = Persony
   - 🟣 Fioletowy = Koncepty
   - 🟠 Bursztynowy = Emocje
   - 🟢 Zielony = Pozytywny sentiment
   - 🔴 Czerwony = Negatywny sentiment
3. Sidebar pokazuje: Kluczowe Koncepty, Wpływowe Persony, Kontrowersyjne Tematy, Emocje, Korelacje Wiekowe
4. Kliknij nody aby eksplorować szczegóły
5. Użyj filtrów: Wszystkie, Pozytywne, Negatywne, Wysoki Wpływ

### Wydajność i Optymalizacja

- **Ekstrakcja LLM:** ~0.5-1s per response (Gemini Flash)
- **Budowa Grafu:** ~30-60s dla 20 person × 4 pytania
- **Frontend:** Limit 100 najsilniejszych połączeń dla wydajności
- **Caching:** 5-minutowy stale time na zapytania frontendowe

### Ręczna Budowa Grafu (jeśli potrzeba)

```bash
# Wymuś przebudowę grafu
curl -X POST http://localhost:8000/api/v1/graph/build/{focus_group_id}
```

## System GraphRAG z Bogatymi Metadanymi

Platforma wykorzystuje **GraphRAG** (Graph + Retrieval-Augmented Generation) do budowy grafu wiedzy z dokumentów źródłowych. System ekstraktuje nie tylko węzły i relacje, ale także **bogate metadane** używając `LLMGraphTransformer` z LangChain.

### Architektura GraphRAG

**Serwisy:**
- [app/services/rag_service.py](app/services/rag_service.py) - Główny serwis RAG
  - `RAGDocumentService` - Ingest dokumentów, budowa grafu, Graph RAG queries
  - `PolishSocietyRAG` - Hybrid search dla generatora person

**Przepływ Przetwarzania Dokumentu:**
1. **LOAD** - PyPDFLoader/Docx2txtLoader wczytuje dokument
2. **SPLIT** - RecursiveCharacterTextSplitter dzieli na chunki (2000 znaków, overlap 400)
3. **METADATA** - Dodanie doc_id, chunk_index, title, country
4. **GRAPH** - LLMGraphTransformer ekstraktuje graf z bogatymi właściwościami
5. **ENRICH** - `_enrich_graph_nodes()` wzbogaca metadane i waliduje jakość
6. **VECTOR** - Zapis chunków do Neo4j Vector Store z embeddingami

### Bogate Metadane Węzłów (Node Properties)

Każdy węzeł w grafie wiedzy zawiera następujące właściwości:

**Właściwości Treściowe:**
- `description` - Szczegółowy opis kontekstu i znaczenia (2-3 zdania)
- `summary` - Jednozdaniowe streszczenie najważniejszej informacji
- `key_facts` - Lista kluczowych faktów oddzielonych średnikami (min. 2-3 fakty)
- `source_context` - Bezpośredni cytat ze źródła (20-50 słów) dla weryfikowalności

**Właściwości Temporalne i Numeryczne:**
- `time_period` - Okres czasu jeśli istnieje (format: "2020" lub "2018-2023")
- `magnitude` - Dla wskaźników liczbowych, wartość z jednostką (np. "67%", "1.2 mln osób")

**Właściwości Jakościowe:**
- `confidence_level` - Pewność danych: "high" (bezpośrednie dane), "medium" (wnioski), "low" (spekulacje)

**Metadane Techniczne:**
- `doc_id` - UUID dokumentu źródłowego (KRYTYCZNE dla usuwania dokumentów)
- `chunk_index` - Indeks fragmentu w dokumencie
- `document_title` - Tytuł dokumentu
- `document_country` - Kraj dokumentu
- `document_year` - Rok dokumentu
- `processed_at` - Timestamp przetwarzania ISO 8601

### Bogate Metadane Relacji (Relationship Properties)

Każda relacja w grafie zawiera:

- `confidence` - Pewność relacji jako liczba 0.0-1.0 (string)
- `evidence` - Konkretny dowód z tekstu uzasadniający relację
- `strength` - Siła relacji: "strong" (bezpośrednia zależność), "moderate" (prawdopodobna), "weak" (możliwa)
- `doc_id`, `chunk_index` - Metadane techniczne

### Typy Węzłów w Grafie

System używa precyzyjnych typów węzłów:
- **Observation** - Konkretne obserwacje, fakty z badań
- **Indicator** - Wskaźniki liczbowe, statystyki, metryki
- **Demographic** - Grupy demograficzne, populacje
- **Trend** - Trendy czasowe, zmiany w czasie
- **Location** - Miejsca geograficzne
- **Cause** - Przyczyny zjawisk
- **Effect** - Skutki, konsekwencje

### Typy Relacji

- `DESCRIBES` - Opisuje cechę/właściwość
- `APPLIES_TO` - Dotyczy grupy/kategorii
- `SHOWS_TREND` - Pokazuje trend czasowy
- `LOCATED_IN` - Zlokalizowane w miejscu
- `CAUSED_BY` - Spowodowane przez
- `LEADS_TO` - Prowadzi do
- `COMPARES_TO` - Porównuje z

### Post-processing Metadanych

Funkcja `_enrich_graph_nodes()` automatycznie:
1. Dodaje `doc_id` i `chunk_index` do każdego węzła i relacji
2. Waliduje jakość metadanych (sprawdza czy summary i description nie są puste)
3. Dodaje timestamp przetwarzania
4. Normalizuje formaty danych:
   - `confidence_level`: wymusza "high", "medium", "low"
   - `confidence` w relacjach: waliduje 0.0-1.0, clamp do zakresu
   - `strength`: wymusza "strong", "moderate", "weak"
   - `magnitude`: konwertuje do string
5. Loguje ostrzeżenia jeśli >30% węzłów nie ma pełnych metadanych

### Graph RAG Queries

System generuje zapytania Cypher używając LLM, które wykorzystują nowe właściwości:

**Przykładowe Zapytania:**
```cypher
-- Znajdź największe wskaźniki
MATCH (n:Indicator)
WHERE n.magnitude IS NOT NULL
RETURN n.summary, n.magnitude, n.source_context
ORDER BY toFloat(split(n.magnitude, '%')[0]) DESC

-- Znajdź pewne fakty o temacie X
MATCH (n:Observation)
WHERE n.summary CONTAINS 'X' AND n.confidence_level = 'high'
RETURN n.description, n.key_facts, n.source_context

-- Jak X wpływa na Y? (silne relacje)
MATCH (cause)-[r:LEADS_TO]->(effect)
WHERE cause.summary CONTAINS 'X' AND effect.summary CONTAINS 'Y'
  AND r.strength = 'strong'
RETURN cause.summary, r.evidence, effect.summary, r.confidence

-- Trendy w latach 2020-2023
MATCH (n:Trend)
WHERE n.time_period >= '2020' AND n.time_period <= '2023'
RETURN n.summary, n.description, n.magnitude, n.time_period
ORDER BY n.time_period
```

**Funkcja `_generate_cypher_query()`:**
- LLM tłumaczy pytanie użytkownika na zapytanie Cypher
- Prompt systemowy zawiera szczegółowe instrukcje jak wykorzystać właściwości węzłów
- Automatyczne filtrowanie po `confidence_level`, `strength`, `time_period`, `magnitude`
- Zawsze zwraca `source_context` dla weryfikowalności

### API Graph RAG

**Ingest Dokumentu:**
```bash
POST /api/v1/rag/documents
{
  "file": <PDF/DOCX file>,
  "title": "Raport o polskim społeczeństwie 2023",
  "country": "Poland",
  "date": "2023"
}
```

**Odpytywanie Graph RAG:**
```bash
POST /api/v1/rag/query
{
  "question": "Jakie są największe wskaźniki ubóstwa w Polsce?"
}
```

**Odpowiedź:**
```json
{
  "answer": "Według raportów...",
  "graph_context": [
    {
      "indicator": "Stopa ubóstwa relatywnego",
      "magnitude": "17.3%",
      "summary": "Odsetek osób żyjących poniżej granicy ubóstwa relatywnego",
      "description": "Wskaźnik ubóstwa relatywnego w Polsce wyniósł 17.3% w 2022 roku...",
      "key_facts": "17.3% populacji; wzrost o 1.2% r/r; najwyższy w grupie 65+",
      "source_context": "Według GUS, stopa ubóstwa relatywnego wyniosła 17.3% w 2022...",
      "confidence_level": "high",
      "time_period": "2022"
    }
  ],
  "vector_context": [...],
  "cypher_query": "MATCH (n:Indicator) WHERE n.magnitude IS NOT NULL..."
}
```

### Wydajność i Optymalizacja

- **Ekstrakcja LLM:** ~2-5s per chunk (Gemini Flash)
- **Budowa Grafu:** ~1-3 min dla dokumentu 50-page PDF
- **Post-processing:** ~0.5-1s (walidacja + normalizacja)
- **Graph RAG Query:** ~2-4s (Cypher generation + execution + LLM answer)

### Schemas Pydantic

[app/schemas/graph.py](app/schemas/graph.py) zawiera modele:
- `NodeProperties` - Bogate metadane węzła (wszystkie właściwości)
- `RelationshipProperties` - Metadane relacji
- `GraphNode` - Rozszerzony o `properties: Optional[NodeProperties]`
- `GraphLink` - Rozszerzony o `properties: Optional[RelationshipProperties]`

### Testowanie GraphRAG

```bash
# Test pełnego pipeline ingest + Graph RAG
python -m pytest tests/test_rag_graph_properties.py -v

# Ręczne testowanie hybrid search
python tests/manual/test_hybrid_search.py

# Ręczne testowanie Graph RAG query
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Jakie są kluczowe trendy demograficzne w Polsce?"}'
```

## Konwencje Kodu

- Wszystkie serwisy używają **async/await** pattern (FastAPI + SQLAlchemy async)
- Abstrakcje LangChain używane wszędzie (`ChatGoogleGenerativeAI`, `ChatPromptTemplate`, etc.)
- Docstringi w języku polskim (istniejąca konwencja)
- Type hints wymagane dla wszystkich funkcji
- Stałe zdefiniowane w [app/core/constants.py](app/core/constants.py)

## Rozwiązywanie Problemów

### Backend nie startuje
```bash
docker-compose logs api  # Sprawdź błędy
docker-compose restart api postgres
```

### Puste odpowiedzi person
Sprawdź [app/services/focus_group_service_langchain.py](app/services/focus_group_service_langchain.py) - upewnij się że `max_tokens` jest wystarczająco wysoki dla gemini-2.5 reasoning tokens (powinno być 2048+)

### Błędy połączenia z bazą
```bash
docker-compose ps  # Weryfikuj że postgres jest healthy
docker-compose down -v && docker-compose up -d  # Opcja nuklearna (usuwa dane)
docker-compose exec api alembic upgrade head
```

### Wywołania API frontendu failują
Sprawdź że Vite proxy jest poprawnie skonfigurowane w [frontend/vite.config.ts](frontend/vite.config.ts) - powinno proxy `/api` do `http://api:8000`

### Neo4j nie startuje
```bash
docker-compose logs neo4j
docker-compose restart neo4j
curl http://localhost:7474  # Sprawdź połączenie
```

## Struktura Plików

```
market-research-saas/
├── app/                              # Backend (FastAPI)
│   ├── api/                          # Endpointy REST API
│   │   ├── auth.py                  # Autoryzacja JWT
│   │   ├── projects.py              # Zarządzanie projektami
│   │   ├── personas.py              # Generowanie person
│   │   ├── focus_groups.py          # Grupy fokusowe
│   │   ├── surveys.py               # Ankiety syntetyczne
│   │   ├── analysis.py              # Analizy AI
│   │   ├── graph_analysis.py        # Analiza grafowa Neo4j
│   │   ├── rag.py                   # RAG endpoints
│   │   ├── settings.py              # Ustawienia użytkownika i profil
│   │   └── dependencies.py          # Zależności FastAPI
│   ├── core/                         # Konfiguracja
│   │   ├── config.py                # Ustawienia aplikacji
│   │   ├── constants.py             # Stałe
│   │   └── security.py              # Bezpieczeństwo i JWT
│   ├── db/                           # Baza danych
│   │   ├── session.py               # Sesje SQLAlchemy
│   │   └── base.py                  # Base model
│   ├── models/                       # Modele SQLAlchemy (ORM)
│   │   ├── user.py                  # Model użytkownika
│   │   ├── project.py               # Model projektu
│   │   ├── persona.py               # Model persony
│   │   ├── focus_group.py           # Model grupy fokusowej
│   │   ├── survey.py                # Model ankiety
│   │   ├── persona_events.py        # Model eventów
│   │   └── rag_document.py          # Model dokumentów RAG
│   ├── schemas/                      # Pydantic schemas (API validation)
│   │   ├── project.py
│   │   ├── persona.py
│   │   ├── focus_group.py
│   │   ├── survey.py
│   │   ├── graph.py
│   │   ├── rag.py
│   │   └── settings.py              # Schemas dla ustawień
│   ├── services/                     # Logika biznesowa
│   │   ├── persona_generator_langchain.py       # Generator person
│   │   ├── focus_group_service_langchain.py     # Orkiestracja dyskusji
│   │   ├── survey_response_generator.py         # Generator odpowiedzi ankiet
│   │   ├── discussion_summarizer.py             # AI podsumowania
│   │   ├── memory_service_langchain.py          # System pamięci
│   │   ├── persona_validator.py                 # Walidacja statystyczna
│   │   ├── graph_service.py                     # Graf wiedzy Neo4j
│   │   └── rag_service.py                       # RAG hybrid search + GraphRAG
│   └── main.py                       # Aplikacja FastAPI
├── frontend/                         # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── components/              # Komponenty React
│   │   │   ├── layout/             # Layout i nawigacja
│   │   │   ├── panels/             # Panele funkcjonalne
│   │   │   └── ui/                 # Komponenty UI (shadcn/ui)
│   │   ├── contexts/               # React Context (auth)
│   │   ├── hooks/                  # Custom hooks
│   │   ├── lib/                    # API client & utilities
│   │   │   ├── api.ts             # API client functions
│   │   │   └── avatar.ts          # Avatar utility functions
│   │   ├── store/                  # Zustand store
│   │   ├── types/                  # TypeScript types
│   │   └── App.tsx
│   ├── vite.config.ts
│   └── package.json
├── alembic/                          # Migracje bazy danych
│   └── versions/                    # Pliki migracji (12 migrations)
├── docs/                             # Dokumentacja techniczna
│   ├── README.md                    # Indeks dokumentacji
│   ├── TESTING.md                   # Dokumentacja testów (208 testów)
│   └── RAG.md                       # System RAG: Hybrid Search + GraphRAG
├── static/                           # Pliki statyczne
│   └── avatars/                     # Uploadowane avatary użytkowników
├── data/                             # Dane aplikacji (ignorowane w git)
│   └── documents/                   # Dokumenty RAG (PDFs)
├── tests/                            # Testy (208 testów)
│   ├── unit/                        # Testy jednostkowe (~150 testów, <5s)
│   │   ├── test_core_config_security.py
│   │   ├── test_persona_generator.py
│   │   ├── test_focus_group_service.py
│   │   ├── test_graph_service.py
│   │   ├── test_survey_response_generator.py
│   │   ├── test_memory_service_langchain.py
│   │   ├── test_discussion_summarizer_service.py
│   │   ├── test_persona_validator_service.py
│   │   ├── test_critical_paths.py
│   │   ├── test_analysis_api.py
│   │   ├── test_graph_analysis_api.py
│   │   ├── test_auth_api.py
│   │   ├── test_main_api.py
│   │   └── test_models.py
│   ├── integration/                 # Testy integracyjne (~35 testów, 10-30s)
│   │   ├── test_auth_api_integration.py
│   │   ├── test_projects_api_integration.py
│   │   ├── test_personas_api_integration.py
│   │   ├── test_focus_groups_api_integration.py
│   │   ├── test_surveys_api_integration.py
│   │   └── test_settings_api_integration.py
│   ├── e2e/                         # Testy end-to-end (~4 testy, 2-5 min)
│   │   ├── test_e2e_full_workflow.py
│   │   ├── test_e2e_survey_workflow.py
│   │   └── test_e2e_graph_analysis.py
│   ├── performance/                 # Testy wydajności (~5 testów, 5-10 min)
│   │   └── test_performance.py
│   ├── error_handling/              # Testy błędów (~9 testów, 5-10s)
│   │   └── test_error_handling.py
│   ├── manual/                      # Testy manualne (nie są w test suite)
│   │   └── test_hybrid_search.py   # Manual RAG hybrid search test
│   └── conftest.py                  # Shared fixtures
├── scripts/                          # Skrypty pomocnicze
│   ├── README.md                    # Dokumentacja skryptów
│   ├── init_db.py                   # Inicjalizacja bazy danych
│   └── init_neo4j_indexes.py        # Inicjalizacja indeksów Neo4j
├── docker-compose.yml                # Docker development environment
├── docker-compose.prod.yml           # Docker production environment
├── Dockerfile                        # Backend multi-stage Dockerfile
├── .dockerignore                     # Backend Docker ignore rules
├── frontend/
│   ├── Dockerfile                   # Frontend multi-stage Dockerfile
│   ├── nginx.conf                   # Nginx config dla production
│   └── .dockerignore                # Frontend Docker ignore rules
├── docker-entrypoint.sh              # Docker entrypoint script (migrations)
├── start.sh                          # Quick start script
├── requirements.txt                  # Zależności Python
├── .env.example                      # Development environment template
├── .env.production.example           # Production environment template
├── .gitignore                        # Git ignore rules
├── pytest.ini                        # Pytest configuration
├── alembic.ini                       # Alembic configuration
├── README.md                         # Dokumentacja użytkownika
└── CLAUDE.md                         # Ten plik - dokumentacja deweloperska
```

## Funkcjonalności

### 0. Zarządzanie Kontem i Ustawienia (Settings)

**Lokalizacja:**
- Backend: [app/api/settings.py](app/api/settings.py), [app/schemas/settings.py](app/schemas/settings.py)
- Frontend: [frontend/src/components/Settings.tsx](frontend/src/components/Settings.tsx)
- Utilities: [frontend/src/lib/avatar.ts](frontend/src/lib/avatar.ts)

**Funkcjonalności:**
- **Profil użytkownika** - GET/PUT `/api/v1/settings/profile`
  - Edycja: full_name, role, company
  - Model User rozszerzony o: avatar_url, role, company, plan, is_verified, last_login_at, deleted_at
- **Avatar management** - POST/DELETE `/api/v1/settings/avatar`
  - Upload: JPG, PNG, WEBP (max 2MB)
  - Walidacja: PIL Image validation, size check
  - Storage: `static/avatars/` directory (automatycznie tworzony)
  - Auto-cleanup starych avatarów przy upload nowego
- **Statystyki konta** - GET `/api/v1/settings/stats`
  - Liczby: projects, personas, focus groups, surveys
  - Plan użytkownika (free/pro/enterprise)
- **Usuwanie konta** - DELETE `/api/v1/settings/account`
  - Soft delete (ustawia deleted_at, is_active=false)
  - Zachowuje dane dla compliance i audytu
- **Dark/Light mode** - frontend theme system
  - Theme toggle w Settings panel
  - Persistence w localStorage
  - System theme detection

**Notification Settings (przygotowane na przyszłość):**
Model User zawiera pola:
- email_notifications_enabled
- discussion_complete_notifications
- weekly_reports_enabled
- system_updates_notifications

**Static Files Serving:**
```python
# app/main.py
app.mount("/static", StaticFiles(directory="static"), name="static")
```
Katalog `static/avatars/` automatycznie tworzony przy starcie ([app/api/settings.py](app/api/settings.py:37)).

**Frontend Utilities:**
```typescript
// frontend/src/lib/avatar.ts
getAvatarUrl(avatarUrl?: string): string // Konwersja relatywnych URL do pełnych
getInitials(name?: string): string       // Inicjały dla avatar fallback
```

**Wydajność:**
- Avatar upload: <500ms (walidacja + zapis)
- Profile update: <100ms
- Stats query: <200ms (4 count queries)

### 1. Generowanie Person
- Rozkłady demograficzne (wiek, płeć, edukacja, dochód, lokalizacja)
- Cechy psychologiczne (Big Five personality traits)
- Wymiary kulturowe (Hofstede dimensions)
- Walidacja statystyczna (test chi-kwadrat)
- Wydajność: ~30-60s dla 20 person

### 2. Grupy Fokusowe
- Równoległe przetwarzanie odpowiedzi person (asyncio)
- System pamięci (kontekst rozmowy, event sourcing)
- Spójność odpowiedzi między pytaniami
- Semantic search w historii (pgvector)
- Wydajność: ~2-5 min dla 20 person × 4 pytania

### 3. Ankiety Syntetyczne
- 4 typy pytań: Single choice, Multiple choice, Rating scale, Open text
- Drag & drop builder ankiet
- AI-powered responses (Gemini)
- Równoległe przetwarzanie
- Analiza demograficzna (podział według wieku, płci, wykształcenia, dochodu)
- Wizualizacje (bar charts, pie charts)
- Wydajność: ~1-3s per persona, <60s total

### 4. Analiza Grafowa (Neo4j)
- Graf wiedzy: Personas, Concepts, Emotions
- Relacje: MENTIONS, FEELS, AGREES_WITH, DISAGREES_WITH
- Kluczowe koncepty z sentimentem
- Kontrowersyjne tematy (wysoka polaryzacja)
- Wpływowe persony (PageRank-style)
- Korelacje demograficzne (wiek vs opinie)
- Rozkład emocji
- Wizualizacja 3D (React Three Fiber)
- Wydajność: ~30-60s dla 20 person × 4 pytania

### 5. Analizy AI
- Executive summaries (Gemini 2.5 Pro/Flash)
- Key insights i recommendations
- Sentiment analysis
- Idea score (0-100)
- Consensus level (0-1)

## Testowanie

```bash
# Wszystkie testy
python -m pytest tests/ -v

# Z coverage
python -m pytest tests/ -v --cov=app --cov-report=html

# Konkretny test
python -m pytest tests/test_persona_generator.py -v

# Critical paths
python -m pytest tests/test_critical_paths.py -v
```

**Dostępne testy (134 testy):**
- `test_core_config_security.py` - konfiguracja i bezpieczeństwo (6 testów: settings singleton, password hashing, JWT, API key encryption)
- `test_persona_generator.py` - generowanie person
- `test_focus_group_service.py` - orkiestracja grup fokusowych
- `test_graph_service.py` - analiza grafowa Neo4j
- `test_survey_response_generator.py` - ankiety syntetyczne
- `test_memory_service_langchain.py` - system pamięci
- `test_discussion_summarizer_service.py` - AI podsumowania
- `test_persona_validator_service.py` - walidacja statystyczna
- `test_critical_paths.py` - end-to-end critical paths (9 testów: demographic distributions, Big Five traits, chi-square validation, performance metrics, event sourcing)
- `test_api_integration.py` - integracja API
- `test_auth_api.py` - autoryzacja i JWT
- `test_main_api.py` - główne endpointy
- `test_models.py` - modele bazy danych

## Bezpieczeństwo

- **JWT Authentication** - wszystkie chronione endpointy wymagają tokena
- **Password hashing** - bcrypt dla haseł użytkowników
- **CORS** - konfigurowalny via ALLOWED_ORIGINS
- **Secret key** - MUSI być zmieniony w produkcji
- **Environment-based config** - różne ustawienia dla dev/prod

## Architektura Docker

**📖 PEŁNA DOKUMENTACJA:** [docs/DOCKER.md](docs/DOCKER.md)

### Szybki Przegląd

**Multi-Stage Builds:**
- Backend: 850MB → 450MB (builder + runtime stages)
- Frontend: 500MB → 25MB production (deps + builder + dev + production stages)

**Key Features:**
- Instant frontend starty (30-60s → <2s) - node_modules cached w image
- Named volume `frontend_node_modules` zapobiega konfliktom
- Hot reload działa out-of-the-box
- Development (docker-compose.yml) vs Production (docker-compose.prod.yml)

**Podstawowe Komendy:**
```bash
# Development
docker-compose up -d              # Start
docker-compose up --build -d      # Rebuild (po zmianie requirements.txt / package.json)
docker-compose logs -f api        # Logi

# Production
docker-compose -f docker-compose.prod.yml up -d --build
```

**Więcej:** Zobacz [docs/DOCKER.md](docs/DOCKER.md) dla pełnej dokumentacji architektury, troubleshooting, i best practices.

## Produkcja

### Ważne Zmiany dla Produkcji

1. **Zmień SECRET_KEY** - wygeneruj bezpieczny klucz
2. **Zmień hasła baz danych** - PostgreSQL, Neo4j
3. **Skonfiguruj ALLOWED_ORIGINS** - tylko zaufane domeny
4. **Wyłącz DEBUG** - ustaw DEBUG=false
5. **Użyj HTTPS** - dla wszystkich połączeń
6. **Backup bazy** - regularny backup PostgreSQL i Neo4j
7. **Monitoring** - logi, metryki, alerty
8. **Rate limiting** - ogranicz requests per IP
9. **Google API quota** - monitoruj użycie Gemini API

### Generowanie Secret Key

```bash
# Wygeneruj bezpieczny secret key
openssl rand -hex 32
```

## Wsparcie

W razie problemów:
1. Sprawdź logi: `docker-compose logs -f api`
2. Sprawdź dokumentację API: http://localhost:8000/docs
3. Przeczytaj README.md
4. Otwórz issue w repozytorium

---

# SIGHT-SPECIFIC: Zasady Deweloperskie

## Jakość Kodu - Production-Ready Standard

### Wymagania Kodu

**1. Enterprise-Grade Architecture**
- ✅ **SOLID principles** - stosuj gdzie sensowne (nie over-engineer)
- ✅ **DRY** - unikaj duplikacji, ale bez przesady z abstrakcją
- ✅ **Design patterns** - używaj gdy rozwiązują realny problem
- ✅ **Type safety** - pełne type hints we wszystkich funkcjach
- ✅ **Error handling** - comprehensive exception handling z informacyjnymi messages
- ✅ **Security** - input validation, sanitization, proper auth/authz
- ✅ **Performance** - optymalizacje, caching, asyncio dla I/O-bound
- ✅ **Maintainability** - kod czytelny dla innych developerów

**2. Dokumentacja Production-Ready**
- ✅ **API Documentation** - pełne docstringi w stylu Google/NumPy
- ✅ **Inline comments** - wyjaśniają "dlaczego", nie "co"
- ✅ **Type hints** - wszystkie funkcje, metody, zmienne
- ✅ **Examples** - przykłady użycia w docstringach dla public API
- ✅ **Edge cases** - dokumentacja corner cases
- ✅ **Performance notes** - Big-O complexity dla algorytmów

**3. Testowanie Enterprise**
- ✅ **Unit tests** - coverage >80% dla critical paths
- ✅ **Integration tests** - testowanie współpracy komponentów
- ✅ **Edge cases** - nietypowe scenariusze
- ✅ **Error scenarios** - błędne input/wyjątki
- ✅ **Performance tests** - dla krytycznych ścieżek (jeśli stosowne)
- ✅ **Fixtures** - reusable test data, mocks, stubs

**4. Code Review Standards**

Przed commitem upewnij się że:
- ✅ Kod przechodzi linting (ruff, pylint, mypy)
- ✅ Wszystkie testy przechodzą
- ✅ Coverage nie spadł
- ✅ Dokumentacja jest aktualna
- ✅ Brak TODO/FIXME w production code
- ✅ Performance jest akceptowalne
- ✅ Security best practices zachowane

---

## Architecture Patterns dla Sight

### Kontekst
Sight to platforma do wirtualnych grup fokusowych z AI:
- **Backend**: FastAPI + PostgreSQL (pgvector) + Redis + Neo4j
- **Frontend**: React 18 + TypeScript + TanStack Query
- **AI**: Google Gemini (Flash/Pro) via LangChain
- **Stack**: Async-first, event sourcing, hybrid search

### 1. Service Layer Pattern

**Filozofia:** Logika biznesowa oddzielona od endpointów API.

```
API Endpoints (app/api/*.py)
    ↓ (thin layer: validation, routing, error handling)
Service Layer (app/services/*_langchain.py)
    ↓ (thick layer: business logic, orchestration)
Models/DB (app/models/*.py) + External APIs
```

**Zasady:**
- Endpoints są cienkie - tylko validation, response formatting, error handling
- Serwisy są grube - cała logika biznesowa, orchestration, external calls
- Jeden serwis = jedna odpowiedzialność (SRP)
- Serwisy są async - używają `async/await` dla I/O
- Dependency injection - serwisy dostają dependencies przez constructor

**Przykład:**
```python
# ❌ ZŁE - logika w endpoincie
@router.post("/personas/generate")
async def generate_personas(request: GenerateRequest):
    # 200 linii logiki tutaj...
    pass

# ✅ DOBRE - endpoint cienki, serwis gruby
@router.post("/personas/generate")
async def generate_personas(
    request: GenerateRequest,
    service: PersonaGeneratorLangChain = Depends(get_persona_service)
):
    """Generate synthetic personas for project."""
    try:
        personas = await service.generate_personas(
            demographics=request.demographics,
            sample_size=request.sample_size
        )
        return {"personas": personas, "count": len(personas)}
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

### 2. Async/Await Patterns

Sight robi **dużo I/O** (LLM, DB, Redis, Neo4j). Async jest krytyczny dla wydajności.

**Kiedy używać async:**
- ✅ LLM API calls (Gemini)
- ✅ Database queries (PostgreSQL, Neo4j)
- ✅ Redis operations
- ✅ HTTP requests (external APIs)
- ✅ File I/O (PDF loading dla RAG)

**Kiedy NIE używać:**
- ❌ CPU-bound operations (numpy, chi-square test)
- ❌ Synchronous libraries (legacy code)

**Pattern: Równoległe Przetwarzanie**
```python
# ✅ DOBRE - równoległe generowanie odpowiedzi
async def run_focus_group(personas: List[Persona], questions: List[str]):
    """
    Performance: 20 person × 4 pytania = ~2-5 min (vs 40+ min sekwencyjnie)
    Target: <3s per persona, <30s total per question
    """
    for question in questions:
        tasks = [generate_response(persona, question) for persona in personas]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions per-persona (nie fail całej grupy)
        for persona, response in zip(personas, responses):
            if isinstance(response, Exception):
                logger.error(f"Persona {persona.id} failed: {response}")
                continue
            await save_response(persona, question, response)
```

**Pattern: Timeouts**
```python
# ✅ DOBRE - timeout per persona
async def generate_response_with_timeout(persona: Persona, question: str):
    """Timeout aby jedna wolna persona nie blokowała grupy."""
    try:
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=settings.MAX_RESPONSE_TIME_PER_PERSONA
        )
        return response
    except asyncio.TimeoutError:
        logger.warning(f"Persona {persona.id} timeout")
        raise
```

### 3. Event Sourcing Pattern

Sight używa **event sourcing** dla pamięci person:
- Każda akcja/odpowiedź = immutable `PersonaEvent`
- Eventy mają embeddingi dla semantic search
- Przy odpowiadaniu pobieramy kontekst via similarity search

**Dlaczego?**
- ✅ Audyt trail - widzimy całą historię
- ✅ Time travel - odtworzenie stanu w dowolnym momencie
- ✅ Semantic search - inteligentne wyszukiwanie kontekstu
- ✅ Konsystencja - persona pamięta poprzednie odpowiedzi

**Pattern:**
```python
# 1. Zapisz event z embeddingiem
async def save_persona_event(
    persona_id: UUID,
    event_type: str,
    content: str,
    embedding_service: GoogleGenerativeAIEmbeddings
):
    """Zapisuje event z embeddingiem dla semantic search."""
    embedding = await embedding_service.aembed_query(content)

    event = PersonaEvent(
        persona_id=persona_id,
        event_type=event_type,
        content=content,
        embedding=embedding,  # pgvector
        timestamp=datetime.utcnow()
    )
    await db.add(event)
    await db.commit()

# 2. Pobierz releantny kontekst
async def get_relevant_context(
    persona_id: UUID,
    current_question: str,
    top_k: int = 5
) -> List[str]:
    """Semantic search w historii persony."""
    query_embedding = await embedding_service.aembed_query(current_question)

    # Semantic search (pgvector <=> operator)
    results = await db.execute(
        select(PersonaEvent)
        .where(PersonaEvent.persona_id == persona_id)
        .order_by(PersonaEvent.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )

    return [event.content for event in results.scalars()]
```

### 4. GraphRAG Pattern (Hybrid Search)

Sight używa **hybrid search** (vector + keyword) dla RAG:
- **Vector search**: semantic similarity (embeddings)
- **Keyword search**: lexical matching (fulltext index)
- **RRF fusion**: Reciprocal Rank Fusion łączy wyniki

**Dlaczego hybrid?**
- ✅ Vector - rozumie semantykę, synonimy
- ✅ Keyword - precyzyjne dopasowanie exact matches
- ✅ RRF - best of both worlds

**Pattern:**
```python
async def hybrid_search_rag(
    query: str,
    top_k: int = 5,
    vector_weight: float = 0.7
) -> List[Document]:
    """
    Hybrid search: vector + keyword + RRF fusion.
    Performance: ~100-200ms dla 1000 docs
    """
    # 1. Vector search
    query_embedding = await embeddings.aembed_query(query)
    vector_results = await neo4j_vector_index.similarity_search(
        query_embedding, k=top_k * 2
    )

    # 2. Keyword search
    keyword_results = await neo4j_fulltext_index.search(query, limit=top_k * 2)

    # 3. RRF Fusion
    fused_results = reciprocal_rank_fusion(
        [vector_results, keyword_results],
        k=settings.RAG_RRF_K,
        weights=[vector_weight, 1 - vector_weight]
    )

    return fused_results[:top_k]
```

### 5. Long-Running Operations Pattern

Sight ma długie operacje (20 person = 30-60s, focus group = 2-5 min).

**Opcje:**
1. Sync blocking ❌ - user czeka, timeout
2. Async with polling ✅ - background job + frontend polling
3. WebSockets ✅ - real-time updates (TODO)

**Current Pattern:**
```python
# Backend: Background task z statusem
@router.post("/focus-groups/{id}/run")
async def run_focus_group(
    focus_group_id: UUID,
    background_tasks: BackgroundTasks
):
    """Frontend polluje status via GET /focus-groups/{id}/status"""
    await update_focus_group_status(focus_group_id, "running")
    background_tasks.add_task(run_focus_group_task, focus_group_id)
    return {"status": "started", "id": focus_group_id}

# Frontend: Polling z TanStack Query
const { data } = useQuery({
  queryKey: ['focus-group-status', id],
  queryFn: () => api.getFocusGroupStatus(id),
  refetchInterval: (data) =>
    data?.status === 'running' ? 2000 : false, // Poll co 2s
  staleTime: 0
})
```

### 6. Frontend State Management

**Stack:** React Query (TanStack Query) + Zustand

- ✅ **Server state** (personas, focus groups) → React Query
- ✅ **UI state** (modals, filters) → Zustand
- ✅ **Form state** → React Hook Form

**Dlaczego React Query?**
- Automatic caching (stale-while-revalidate)
- Background refetching
- Optimistic updates
- Request deduplication

```typescript
// ✅ DOBRE - React Query dla server state
const usePersonas = (projectId: string) => {
  return useQuery({
    queryKey: ['personas', projectId],
    queryFn: () => api.getPersonas(projectId),
    staleTime: 5 * 60 * 1000, // 5 min cache
  })
}

// Mutation z optimistic update
const useGeneratePersonas = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.generatePersonas,
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries(['personas', variables.projectId])
    }
  })
}
```

### 7. Error Handling Pattern

**Hierarchia błędów:**
```
Domain Exceptions (app/exceptions.py)
    ↓
Service Layer (catch & transform)
    ↓
API Layer (FastAPI exception handlers)
    ↓
Frontend (error boundaries + toast notifications)
```

**Pattern:**
```python
# 1. Custom domain exceptions
class PersonaGenerationError(Exception):
    """Rzucany gdy generowanie person failuje."""
    pass

# 2. Service layer - rzuca domain exceptions
async def generate_personas(...):
    try:
        personas = await llm.generate(...)
    except LangChainError as e:
        raise PersonaGenerationError(f"Failed: {e}")

# 3. API layer - transform do HTTP
@router.post("/personas/generate")
async def generate_personas_endpoint(...):
    try:
        personas = await service.generate_personas(...)
        return {"personas": personas}
    except PersonaGenerationError as e:
        raise HTTPException(status_code=500, detail={
            "error": "generation_failed",
            "message": str(e),
            "retry": True
        })

# 4. Frontend - structured handling
if (error?.response?.data?.error === 'generation_failed') {
  toast.error(error.response.data.message, {
    action: { label: 'Retry', onClick: () => mutate(vars) }
  })
}
```

---

## Common Pitfalls & Solutions

### 1. N+1 Queries Problem

**Problem:** Ładowanie person + responses = N+1 queries

```python
# ❌ ZŁE - N+1 queries
personas = await db.execute(select(Persona).where(...))
for persona in personas:
    responses = await db.execute(
        select(PersonaResponse).where(PersonaResponse.persona_id == persona.id)
    )

# ✅ DOBRE - 2 queries total
from sqlalchemy.orm import selectinload

personas = await db.execute(
    select(Persona)
    .where(...)
    .options(selectinload(Persona.responses))
)
```

### 2. LLM Token Limit Overflow

**Problem:** Gemini ma limit tokenów. Context może być za długi.

**Solution:** Truncate context inteligentnie

```python
async def prepare_context_for_llm(
    persona: Persona,
    question: str,
    max_tokens: int = 6000
):
    """
    Priorytet:
    1. Current question (zawsze)
    2. Persona profile (zawsze)
    3. Recent events (newest first, truncate if needed)
    4. RAG context (most relevant)
    """
    def count_tokens(text: str) -> int:
        return len(text) // 4  # Approximation

    context_parts = []
    token_count = 0

    # Must-have parts
    context_parts.append(f"Question: {question}")
    token_count += count_tokens(question)

    context_parts.append(f"Profile: {persona.background_story}")
    token_count += count_tokens(persona.background_story)

    # Optional: recent events (truncate if needed)
    events = await get_recent_events(persona.id, limit=10)
    for event in events:
        event_tokens = count_tokens(event.content)
        if token_count + event_tokens > max_tokens:
            break
        context_parts.append(event.content)
        token_count += event_tokens

    return "\n\n".join(context_parts)
```

### 3. Memory Leaks w Async Code

**Problem:** Nie cancelled tasks mogą leakować memory.

**Solution:** Proper cleanup z `asyncio.TaskGroup`

```python
# ✅ DOBRE - automatic cleanup jeśli jeden task failuje
async def run_focus_group_safe(personas: List[Persona], question: str):
    """TaskGroup canceluje pozostałe tasks jeśli jeden failuje."""
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(generate_response(persona, question))
            for persona in personas
        ]
    return [task.result() for task in tasks]
```

### 4. Race Conditions w Event Sourcing

**Problem:** Dwa równoległe requesty zapisują eventy = race condition.

**Solution:** Redis lock

```python
from redis import asyncio as aioredis

async def save_event_with_lock(persona_id: UUID, event: PersonaEvent):
    """Redis lock zapobiega race conditions."""
    lock_key = f"persona_lock:{persona_id}"

    async with aioredis.from_url(settings.REDIS_URL) as redis:
        lock = redis.lock(lock_key, timeout=5)
        async with lock:
            await db.add(event)
            await db.commit()
```

### 5. Neo4j Connection Pool Exhaustion

**Problem:** Dużo równoległych queries = pool exhaustion.

**Solution:** Connection pooling + retry logic

```python
from neo4j import AsyncGraphDatabase

class Neo4jService:
    def __init__(self):
        self._driver = None

    async def get_driver(self):
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_pool_size=50,
                connection_timeout=5.0
            )
        return self._driver

    async def close(self):
        if self._driver:
            await self._driver.close()
```

### 6. Frontend: Stale Data po Mutation

**Problem:** User generuje persony, lista nie refreshuje się.

**Solution:** Invalidate queries

```typescript
const useGeneratePersonas = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.generatePersonas,
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['personas', variables.projectId]
      })
    }
  })
}
```

### 7. Chi-Square Test Fails dla Małych Próbek

**Problem:** Chi-square nie jest reliable dla n < 10.

**Solution:** Fallback + warning

```python
def validate_demographics(
    personas: List[Persona],
    target_demographics: Dict,
    sample_size: int
):
    if sample_size < 10:
        logger.warning("Sample size too small for chi-square. Using percentage match.")
        return validate_percentage_match(personas, target_demographics, tolerance=0.1)

    chi_square, p_value = calculate_chi_square(personas, target_demographics)
    if p_value < 0.05:
        raise StatisticalValidationError(f"Demographics don't match (p={p_value:.4f})")
    return True
```

---

## Production Checklist

### Pre-Deploy

**Backend:**
- [ ] Wszystkie testy przechodzą (208 tests)
- [ ] Coverage >80% dla critical paths
- [ ] Migrations up-to-date (`alembic upgrade head`)
- [ ] Neo4j indexes utworzone (`python scripts/init_neo4j_indexes.py`)
- [ ] Secrets w env vars (nie w .env!)
- [ ] CORS tylko dla prod domains
- [ ] Rate limiting włączony
- [ ] Logging level = INFO
- [ ] Health check działa (`/health`)
- [ ] Connection pooling skonfigurowany
- [ ] LLM rate limits monitorowane

**Frontend:**
- [ ] Build działa (`npm run build`)
- [ ] No console.errors w prod
- [ ] Env vars skonfigurowane
- [ ] Error boundaries na miejscu
- [ ] Loading states dla long ops
- [ ] Toast notifications dla errors

**Infrastructure:**
- [ ] PostgreSQL backups skonfigurowane
- [ ] Redis persistence włączona (AOF/RDB)
- [ ] Neo4j backups skonfigurowane
- [ ] SSL/TLS dla wszystkich połączeń
- [ ] Firewall rules ustawione
- [ ] Monitoring/alerting skonfigurowany

**Security:**
- [ ] JWT secret zmieniony
- [ ] Database passwords zmienione
- [ ] CORS tylko trusted domains
- [ ] Rate limiting per IP + user
- [ ] OWASP Top 10 checked

**Performance:**
- [ ] Database indexes utworzone
- [ ] N+1 queries fixed
- [ ] Caching skonfigurowany
- [ ] Async/await wszędzie dla I/O
- [ ] Connection pooling dla external services

### Post-Deploy Verification

**Smoke tests:**
- [ ] Login działa
- [ ] Tworzenie projektu działa
- [ ] Generowanie person działa (test 1-2)
- [ ] Mini focus group działa (2 persony, 1 pytanie)
- [ ] Graph analysis działa
- [ ] RAG search działa

**Performance checks:**
- [ ] API response <500ms dla GET
- [ ] Persona generation <5s per persona
- [ ] Focus group <30s per question (20 personas)
- [ ] DB query time <100ms

**Monitoring:**
- [ ] Error rate <1%
- [ ] CPU usage <70%
- [ ] Memory stable (no leaks)
- [ ] DB connections <80% pool
- [ ] LLM calls within quota
