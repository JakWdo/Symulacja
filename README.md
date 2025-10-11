# sight

System do przeprowadzania wirtualnych grup fokusowych i ankiet syntetycznych z wykorzystaniem Google Gemini AI. Generuje realistyczne persony i symuluje dyskusje oraz odpowiedzi ankietowe dla potrzeb badań rynkowych.

## 📋 Opis Projektu

Market Research SaaS to platforma umożliwiająca:
- **Generowanie realistycznych person** - AI tworzy szczegółowe profile uczestników badań z demografią, psychologią i charakterystykami kulturowymi
- **Symulację grup fokusowych** - Persony odpowiadają na pytania jak prawdziwi ludzie, z zachowaniem kontekstu i spójności
- **Ankiety syntetyczne** - Tworzenie i uruchamianie ankiet z 4 typami pytań (single/multiple choice, rating scale, open text)
- **Analizę grafową** - System grafów wiedzy Neo4j do identyfikacji kontrowersyjnych tematów i wpływowych uczestników
- **Analizę wyników** - Automatyczne podsumowania AI przez Google Gemini + statystyki ankiet

## 🏗️ Architektura

### Stack Technologiczny

**Backend:**
- **FastAPI** - nowoczesny async framework webowy (Python 3.11+)
- **PostgreSQL + pgvector** - baza danych z wsparciem dla embeddingów AI
- **Redis** - cache i kolejki zadań
- **Neo4j** - graf wiedzy do analizy relacji między konceptami
- **Google Gemini 2.5** - model AI (Flash dla person, Flash/Pro dla analiz)
- **LangChain** - framework do orchestracji LLM
- **Docker** - konteneryzacja aplikacji

**Frontend:**
- **React 18 + TypeScript** - nowoczesny framework UI
- **Vite** - szybki build tool
- **TanStack Query** - zarządzanie stanem i fetching danych
- **Tailwind CSS** - utility-first CSS framework
- **React Three Fiber** - wizualizacja 3D grafów

### Struktura Projektu

```
market-research-saas/
├── app/                              # Backend (FastAPI)
│   ├── api/                          # Endpointy REST API
│   │   ├── auth.py                  # Autoryzacja i uwierzytelnianie
│   │   ├── projects.py              # Zarządzanie projektami
│   │   ├── personas.py              # Generowanie person
│   │   ├── focus_groups.py          # Grupy fokusowe
│   │   ├── surveys.py               # Ankiety syntetyczne
│   │   ├── analysis.py              # Analizy i podsumowania
│   │   ├── graph_analysis.py        # Analiza grafowa Neo4j
│   │   └── dependencies.py          # Zależności FastAPI
│   ├── core/                         # Konfiguracja
│   │   ├── config.py                # Ustawienia aplikacji
│   │   ├── constants.py             # Stałe i wartości domyślne
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
│   │   └── persona_events.py        # Model eventów person
│   ├── schemas/                      # Pydantic schemas (API)
│   │   ├── project.py
│   │   ├── persona.py
│   │   ├── focus_group.py
│   │   ├── survey.py
│   │   └── graph.py
│   ├── services/                     # Logika biznesowa
│   │   ├── persona_generator_langchain.py       # Generator person (Gemini)
│   │   ├── focus_group_service_langchain.py     # Orkiestracja dyskusji
│   │   ├── survey_response_generator.py         # Generator odpowiedzi ankiet
│   │   ├── discussion_summarizer.py             # AI podsumowania
│   │   ├── memory_service_langchain.py          # System pamięci/kontekstu
│   │   ├── persona_validator.py                 # Walidacja statystyczna
│   │   └── graph_service.py                     # Graf wiedzy Neo4j
│   └── main.py                       # Aplikacja FastAPI
├── frontend/                         # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── components/              # Komponenty React
│   │   │   ├── layout/             # Layout i nawigacja
│   │   │   ├── panels/             # Panele (personas, focus groups, surveys, graph)
│   │   │   └── ui/                 # Komponenty UI (shadcn/ui)
│   │   ├── contexts/               # React Context (auth)
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── lib/                    # API client
│   │   ├── store/                  # Zustand store
│   │   ├── types/                  # TypeScript types
│   │   └── App.tsx
│   ├── vite.config.ts
│   └── package.json
├── alembic/                          # Migracje bazy danych
│   └── versions/                    # Pliki migracji
├── tests/                            # Testy
│   ├── test_persona_generator.py
│   ├── test_focus_group_service.py
│   ├── test_graph_service.py
│   ├── test_critical_paths.py
│   └── conftest.py
├── scripts/                          # Skrypty pomocnicze
│   └── init_db.py                   # Inicjalizacja bazy
├── docker-compose.yml                # Konfiguracja Docker
├── Dockerfile                        # Backend Dockerfile
├── requirements.txt                  # Zależności Python
├── README.md                         # Ta dokumentacja
└── CLAUDE.md                         # Instrukcje dla AI
```

## 🚀 Szybki Start

### Wymagania
- Docker & Docker Compose
- Google API Key (Gemini API) - https://makersuite.google.com/app/apikey

### 1. Konfiguracja

Utwórz plik `.env` w głównym katalogu:

```bash
# Baza danych
DATABASE_URL=postgresql+asyncpg://market_research:password@postgres:5432/market_research_db

# Google Gemini API (WYMAGANE!)
GOOGLE_API_KEY=your_gemini_api_key_here

# Redis & Neo4j
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password_change_in_prod

# Modele AI
DEFAULT_MODEL=gemini-2.5-flash
PERSONA_GENERATION_MODEL=gemini-2.5-flash
ANALYSIS_MODEL=gemini-2.5-pro

# Aplikacja
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=change-me-in-production
API_V1_PREFIX=/api/v1

# Parametry AI
TEMPERATURE=0.7
MAX_TOKENS=8000
RANDOM_SEED=42
```

### 2. Uruchomienie z Docker

```bash
# Uruchom wszystkie serwisy (Postgres, Redis, Neo4j, Backend, Frontend)
docker-compose up -d

# Sprawdź status
docker-compose ps

# Sprawdź logi
docker-compose logs -f api

# Wykonaj migracje bazy
docker-compose exec api alembic upgrade head
```

### 3. Dostęp

- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173
- **Neo4j Browser**: http://localhost:7474 (neo4j/dev_password_change_in_prod)

## 📖 Użytkowanie

### Przykładowy Workflow

#### 1. Utwórz Projekt

```bash
PROJECT_ID=$(curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Nowego Produktu",
    "description": "Badanie reakcji na innowacyjny produkt tech",
    "target_demographics": {
      "age_group": {"18-24": 0.2, "25-34": 0.5, "35-44": 0.3},
      "gender": {"Male": 0.5, "Female": 0.5}
    },
    "target_sample_size": 20
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "✅ Projekt ID: $PROJECT_ID"
```

#### 2. Wygeneruj Persony

```bash
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/personas/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "num_personas": 20,
    "adversarial_mode": false
  }'

# Generowanie trwa ~30-60s
sleep 45

# Sprawdź wygenerowane persony
curl "http://localhost:8000/api/v1/projects/$PROJECT_ID/personas"
```

**Persony zawierają:**
- Demografia (wiek, płeć, lokalizacja, edukacja, dochód, zawód)
- Psychologia (Big Five traits: openness, conscientiousness, extraversion, agreeableness, neuroticism)
- Kultura (Hofstede dimensions: power distance, individualism, masculinity, uncertainty avoidance, long-term orientation, indulgence)
- Profil (wartości, zainteresowania, background story)

#### 3. Utwórz i Uruchom Grupę Fokusową

```bash
# Pobierz IDs person
PERSONA_IDS=$(curl -s "http://localhost:8000/api/v1/projects/$PROJECT_ID/personas" \
  | python3 -c "import sys,json; ids=[p['id'] for p in json.load(sys.stdin)[:10]]; print(json.dumps(ids))")

# Utwórz grupę fokusową
FG_ID=$(curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/focus-groups" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Sesja Testowa #1\",
    \"persona_ids\": $PERSONA_IDS,
    \"questions\": [
      \"Co sądzisz o tym produkcie?\",
      \"Jakie funkcje byłyby dla Ciebie najważniejsze?\",
      \"Ile byłbyś skłonny zapłacić?\",
      \"Czy poleciłbyś to znajomym?\"
    ],
    \"mode\": \"normal\"
  }" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Uruchom dyskusję (równoległe przetwarzanie!)
curl -X POST "http://localhost:8000/api/v1/focus-groups/$FG_ID/run"

# Dyskusja trwa ~2-5 min
echo "⏳ Czekam na zakończenie dyskusji (120s)..."
sleep 120
```

#### 4. Pobierz Wyniki i Analizy

```bash
# Odpowiedzi uczestników
curl "http://localhost:8000/api/v1/focus-groups/$FG_ID/responses"

# Metryki (idea score, consensus level, sentiment)
curl "http://localhost:8000/api/v1/focus-groups/$FG_ID/insights"

# AI Summary (Gemini Pro)
curl -X POST "http://localhost:8000/api/v1/focus-groups/$FG_ID/ai-summary?use_pro_model=true"

# === ANALIZA GRAFOWA (automatycznie budowana po focus group) ===

# Kluczowe koncepty
curl "http://localhost:8000/api/v1/graph/$FG_ID/concepts"

# Kontrowersyjne tematy (wysokie polaryzacja)
curl "http://localhost:8000/api/v1/graph/$FG_ID/controversial"

# Wpływowe persony (najwięcej połączeń)
curl "http://localhost:8000/api/v1/graph/$FG_ID/influential"

# Korelacje demograficzne (wiek vs opinie)
curl "http://localhost:8000/api/v1/graph/$FG_ID/correlations"

# Rozkład emocji
curl "http://localhost:8000/api/v1/graph/$FG_ID/emotions"
```

#### 5. Ankiety Syntetyczne

```bash
# Utwórz ankietę
SURVEY_ID=$(curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/surveys" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Ankieta Produktowa",
    "description": "Ocena funkcji produktu",
    "questions": [
      {
        "question_text": "Jak oceniasz design produktu?",
        "question_type": "rating_scale",
        "options": null,
        "min_value": 1,
        "max_value": 10
      },
      {
        "question_text": "Które funkcje są najważniejsze?",
        "question_type": "multiple_choice",
        "options": ["Szybkość", "Bezpieczeństwo", "Łatwość użycia", "Cena"],
        "allow_multiple": true
      }
    ]
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Uruchom ankietę
curl -X POST "http://localhost:8000/api/v1/surveys/$SURVEY_ID/run"

# Sprawdź wyniki
curl "http://localhost:8000/api/v1/surveys/$SURVEY_ID/results"
```

## 📊 Funkcjonalności

### 1. Zarządzanie Kontem i Ustawienia (Settings)

**Dostępne funkcje:**
- **Profil użytkownika** - edycja danych (imię, rola, firma)
- **Avatar** - upload i zarządzanie awatarem (JPG, PNG, WEBP, max 2MB)
- **Statystyki konta** - liczba projektów, person, grup fokusowych, ankiet
- **Motyw aplikacji** - tryb jasny/ciemny (Light/Dark mode)
- **Usuwanie konta** - soft delete z potwierdzeniem

**Endpointy API:**
```bash
# Profil
GET /api/v1/settings/profile
PUT /api/v1/settings/profile -d '{"full_name": "Jan Kowalski", "role": "Product Manager", "company": "TechCorp"}'

# Avatar (multipart/form-data)
POST /api/v1/settings/avatar -F "file=@avatar.jpg"
DELETE /api/v1/settings/avatar

# Statystyki
GET /api/v1/settings/stats
# Response: { "plan": "free", "projects_count": 5, "personas_count": 100, "focus_groups_count": 15, "surveys_count": 8 }

# Usuwanie konta (soft delete)
DELETE /api/v1/settings/account
```

**Frontend:** Panel Settings dostępny w sidebarz, pełna integracja z systemem uwierzytelniania

### 2. Generowanie Person (Persona Generator)

**Technologia:** Google Gemini 2.5 Flash + statystyczne sampling

**Proces:**
1. Sampling demografii z rozkładów docelowych (chi-square validation)
2. Sampling Big Five personality traits (rozkład normalny)
3. Sampling Hofstede dimensions (bazowane na lokalizacji)
4. LLM generuje realistyczną narrację (background, wartości, zainteresowania)
5. Walidacja statystyczna całej kohorty

**Features:**
- Rozkłady demograficzne (wiek, płeć, edukacja, dochód, lokalizacja)
- Psychologia (Big Five: openness, conscientiousness, extraversion, agreeableness, neuroticism)
- Kultura (Hofstede: power distance, individualism, masculinity, uncertainty avoidance, long-term orientation, indulgence)
- Walidacja statystyczna (test chi-kwadrat)
- Tryb adversarial (generuje "trudnych" uczestników)

**Wydajność:** ~30-60s dla 20 person

### 3. Grupy Fokusowe (Focus Groups)

**Technologia:** LangChain + Google Gemini + równoległe przetwarzanie (asyncio)

**Proces:**
1. Każda persona dostaje osobny async task
2. LLM generuje odpowiedź bazując na profilu persony + kontekście
3. Odpowiedzi są zapisywane jako PersonaEvents (event sourcing)
4. Embeddingi Google używane do semantic search w historii
5. Finalne agregowanie i analiza

**Features:**
- Równoległe przetwarzanie odpowiedzi (do 20x szybsze)
- System pamięci (kontekst rozmowy między pytaniami)
- Spójność odpowiedzi (persona konsekwentnie reprezentuje swój profil)
- Semantic search w historii (pgvector)
- Target: <3s per persona response

**Wydajność:** ~2-5 min dla 20 person × 4 pytania

### 4. Ankiety Syntetyczne (Surveys)

**Typy pytań:**
- **Single choice** - jedno z wielu
- **Multiple choice** - wiele z wielu (checkboxy)
- **Rating scale** - skala liczbowa (np. 1-10)
- **Open text** - otwarte pytanie tekstowe

**Features:**
- Drag & drop builder ankiet (frontend)
- AI-powered responses (Gemini generuje odpowiedzi bazując na profilach person)
- Równoległe przetwarzanie (wszystkie persony odpowiadają jednocześnie)
- Automatyczne agregowanie wyników
- Analiza demograficzna (podział według wieku, płci, wykształcenia, dochodu)
- Wizualizacje (bar charts, pie charts)

**Wydajność:** ~1-3s na odpowiedź persony, pełna ankieta <60s

### 5. Analiza Grafowa (Graph Analysis)

**Technologia:** Neo4j + LLM-powered concept extraction

**Graf wiedzy:**
- **Nodes:** Personas, Concepts (tematy), Emotions
- **Relationships:** MENTIONS, FEELS, AGREES_WITH, DISAGREES_WITH

**Proces:**
1. Po zakończeniu focus group automatycznie triggeruje się budowa grafu
2. LLM (Gemini Flash) ekstraktuje z każdej odpowiedzi:
   - Kluczowe koncepty (np. "pricing", "design", "usability")
   - Emocje (np. "excited", "frustrated", "confused")
   - Sentiment (-1.0 do 1.0)
3. Tworzy się graf w Neo4j z relacjami
4. Cypher queries analizują graf

**Dostępne insighty:**
- **Kluczowe koncepty** - najczęściej wspomniane tematy
- **Kontrowersyjne tematy** - wysokie polaryzacja (wysoka wariancja sentymentu)
- **Wpływowe persony** - PageRank-style (najwięcej połączeń)
- **Korelacje demograficzne** - jak wiek/płeć wpływa na opinie
- **Rozkład emocji** - emocje całej grupy

**Wizualizacja:** Interaktywny graf 3D (React Three Fiber + Force Graph 3D)

**Wydajność:** ~30-60s dla 20 person × 4 pytania (~80 responses)

### 6. Analizy AI (Analysis)

**Features:**
- **Executive Summary** - streszczenie dyskusji (Gemini Pro/Flash)
- **Key Insights** - najważniejsze wnioski
- **Recommendations** - rekomendacje biznesowe
- **Sentiment Analysis** - analiza sentymentu
- **Idea Score** - ocena pomysłu (0-100)
- **Consensus Level** - poziom consensusu w grupie (0-1)

## 🛠️ Konfiguracja

### Zmienne Środowiskowe

```bash
# === BAZA DANYCH ===
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname

# === API KEYS ===
GOOGLE_API_KEY=your_gemini_api_key  # WYMAGANE!

# === REDIS & NEO4J ===
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password_change_in_prod

# === MODELE AI ===
DEFAULT_MODEL=gemini-2.5-flash              # Model domyślny
PERSONA_GENERATION_MODEL=gemini-2.5-flash   # Generowanie person
ANALYSIS_MODEL=gemini-2.5-pro               # Analizy (opcjonalnie Pro dla lepszej jakości)

# === PARAMETRY AI ===
TEMPERATURE=0.7                # Temperatura LLM (0.0-1.0, wyższa = bardziej kreatywne)
MAX_TOKENS=8000                # Max tokenów w odpowiedzi (gemini-2.5 używa reasoning tokens!)
RANDOM_SEED=42                 # Seed dla powtarzalności

# === PERFORMANCE TARGETS ===
MAX_RESPONSE_TIME_PER_PERSONA=3    # Target: <3s per persona response
MAX_FOCUS_GROUP_TIME=30            # Target: <30s total focus group time

# === APLIKACJA ===
ENVIRONMENT=development        # development/production
DEBUG=true                     # Debug mode (true/false)
SECRET_KEY=change-me           # Secret key dla JWT (ZMIEŃ W PRODUKCJI!)
API_V1_PREFIX=/api/v1          # Prefix API
ALLOWED_ORIGINS=*              # CORS origins (w prod: https://app.example.com)
```

## 🧪 Testowanie

```bash
# Wszystkie testy
python -m pytest tests/ -v

# Konkretny test
python -m pytest tests/test_persona_generator.py -v

# Z coverage
python -m pytest tests/ -v --cov=app --cov-report=html

# Tylko critical paths
python -m pytest tests/test_critical_paths.py -v
```

**Dostępne testy (134 testy):**
- `test_core_config_security.py` - konfiguracja i bezpieczeństwo (6 testów)
- `test_persona_generator.py` - generowanie person
- `test_focus_group_service.py` - orkiestracja grup fokusowych
- `test_graph_service.py` - analiza grafowa Neo4j
- `test_survey_response_generator.py` - ankiety syntetyczne
- `test_memory_service_langchain.py` - system pamięci
- `test_discussion_summarizer_service.py` - podsumowania AI
- `test_persona_validator_service.py` - walidacja statystyczna
- `test_critical_paths.py` - end-to-end critical paths (9 testów)
- `test_api_integration.py` - integracja API
- `test_auth_api.py` - autoryzacja i JWT
- `test_main_api.py` - główne endpointy
- `test_models.py` - modele bazy danych

## 🐛 Troubleshooting

### Backend nie startuje

```bash
# Sprawdź logi
docker-compose logs api

# Restart
docker-compose restart api postgres

# Rebuild
docker-compose up --build -d
```

### Błąd "GOOGLE_API_KEY not found"

```bash
# Sprawdź czy key jest w .env
cat .env | grep GOOGLE_API_KEY

# Dodaj key
echo "GOOGLE_API_KEY=your_key_here" >> .env

# Restart
docker-compose restart api
```

### Błąd połączenia z bazą

```bash
# Sprawdź status
docker-compose ps

# Reset bazy (UWAGA: usuwa dane!)
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
```

### Persony nie generują się

```bash
# Sprawdź API key
docker-compose exec api printenv GOOGLE_API_KEY

# Test Gemini API
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hi"}]}]}'

# Sprawdź logi
docker-compose logs -f api
```

### Puste odpowiedzi w focus group

Sprawdź `max_tokens` w [app/services/focus_group_service_langchain.py](app/services/focus_group_service_langchain.py) - dla gemini-2.5 potrzeba 2048+ (reasoning tokens!)

### Neo4j nie startuje

```bash
# Sprawdź logi
docker-compose logs neo4j

# Restart
docker-compose restart neo4j

# Sprawdź połączenie
curl http://localhost:7474
```

## 📚 Dokumentacja API

Pełna dokumentacja API dostępna po uruchomieniu aplikacji:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Rozwój

### Development Workflow

```bash
# 1. Edytuj kod
# 2. Restart backend
docker-compose restart api

# 3. Sprawdź logi
docker-compose logs -f api

# 4. Testy
python -m pytest tests/ -v

# 5. Migracja bazy (jeśli zmieniasz modele)
docker-compose exec api alembic revision --autogenerate -m "opis zmian"
docker-compose exec api alembic upgrade head
```

### Dodawanie nowych migracji

```bash
# Utwórz migrację
docker-compose exec api alembic revision --autogenerate -m "add new column"

# Zastosuj
docker-compose exec api alembic upgrade head

# Rollback
docker-compose exec api alembic downgrade -1

# Historia
docker-compose exec api alembic history
```

## 📝 Licencja

Ten projekt jest własnością prywatną.
