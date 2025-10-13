# CLAUDE.md

Ten plik zawiera instrukcje dla Claude Code (claude.ai/code) podczas pracy z kodem w tym repozytorium.

## Przegląd Projektu

Market Research SaaS - Platforma do wirtualnych grup fokusowych z AI wykorzystująca Google Gemini do generowania syntetycznych person i symulacji dyskusji badawczych. Wersja produkcyjna z pełną funkcjonalnością.

**Stack Technologiczny:**
- Backend: FastAPI (Python 3.11+), PostgreSQL + pgvector, Redis, Neo4j
- Frontend: React 18 + TypeScript, Vite, TanStack Query, Tailwind CSS
- AI: Google Gemini 2.5 (Flash/Pro) via LangChain
- Infrastruktura: Docker + Docker Compose

## Polecenia Deweloperskie

### Operacje Docker (Podstawowa Metoda Deweloperska)

**Aktywne Kontenery:**
- `postgres` - PostgreSQL + pgvector
- `redis` - Redis (cache i session storage)
- `neo4j` - Neo4j (graf wiedzy)
- `api` - Backend FastAPI
- `frontend` - Frontend React + Vite

```bash
# Uruchom wszystkie serwisy
docker-compose up -d

# Logi
docker-compose logs -f api
docker-compose logs -f frontend

# Restart serwisów
docker-compose restart api
docker-compose restart frontend

# Przebuduj kontenery
docker-compose up --build -d

# Zatrzymaj wszystkie serwisy
docker-compose down

# Zatrzymaj i usuń wolumeny (USUWA DANE!)
docker-compose down -v
```

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
python scripts/test_hybrid_search.py
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
│   │   └── persona_events.py        # Model eventów
│   ├── schemas/                      # Pydantic schemas (API validation)
│   │   ├── project.py
│   │   ├── persona.py
│   │   ├── focus_group.py
│   │   ├── survey.py
│   │   ├── graph.py
│   │   └── settings.py              # Schemas dla ustawień
│   ├── services/                     # Logika biznesowa
│   │   ├── persona_generator_langchain.py       # Generator person
│   │   ├── focus_group_service_langchain.py     # Orkiestracja dyskusji
│   │   ├── survey_response_generator.py         # Generator odpowiedzi ankiet
│   │   ├── discussion_summarizer.py             # AI podsumowania
│   │   ├── memory_service_langchain.py          # System pamięci
│   │   ├── persona_validator.py                 # Walidacja statystyczna
│   │   └── graph_service.py                     # Graf wiedzy Neo4j
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
│   └── versions/                    # Pliki migracji
├── static/                           # Pliki statyczne
│   └── avatars/                     # Uploadowane avatary użytkowników
├── tests/                            # Testy (134 testy)
│   ├── test_core_config_security.py # Konfiguracja i bezpieczeństwo
│   ├── test_persona_generator.py
│   ├── test_focus_group_service.py
│   ├── test_graph_service.py
│   ├── test_survey_response_generator.py
│   ├── test_memory_service_langchain.py
│   ├── test_discussion_summarizer_service.py
│   ├── test_persona_validator_service.py
│   ├── test_critical_paths.py       # Critical paths end-to-end
│   ├── test_api_integration.py
│   ├── test_auth_api.py
│   ├── test_main_api.py
│   ├── test_models.py
│   └── conftest.py
├── scripts/                          # Skrypty pomocnicze
│   └── init_db.py                   # Inicjalizacja bazy
├── docker-compose.yml                # Konfiguracja Docker
├── Dockerfile                        # Backend Dockerfile
├── requirements.txt                  # Zależności Python
├── README.md                         # Dokumentacja użytkownika
└── CLAUDE.md                         # Ten plik
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
