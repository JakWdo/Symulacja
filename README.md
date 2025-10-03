# Market Research SaaS - Wirtualne Grupy Fokusowe z AI

**Minimalistyczna wersja** - system do przeprowadzania wirtualnych grup fokusowych z wykorzystaniem Google Gemini AI. Generuje realistyczne persony i symuluje dyskusje dla potrzeb badań rynkowych.

## 📋 Opis Projektu

Market Research SaaS to platforma umożliwiająca:
- **Generowanie realistycznych person** - AI tworzy szczegółowe profile uczestników badań
- **Symulację grup fokusowych** - Persony odpowiadają na pytania jak prawdziwi ludzie
- **Analizę wyników** - Automatyczne podsumowania AI przez Google Gemini

## 🏗️ Architektura

### Backend
- **FastAPI** - nowoczesny framework webowy (Python 3.11+)
- **PostgreSQL** - baza danych z SQLAlchemy ORM
- **Google Gemini 2.5** - model AI (Flash dla person, Flash/Pro dla analiz)
- **LangChain** - framework do orchestracji LLM
- **Docker** - konteneryzacja aplikacji

### Frontend
- **React 18 + TypeScript**
- **Vite** - build tool
- **TanStack Query** - zarządzanie stanem i fetching danych
- **Tailwind CSS** - stylowanie

### Struktura projektu

```
market-research-saas/
├── app/                          # Backend (FastAPI)
│   ├── api/                      # Endpointy REST API
│   │   ├── projects.py          # Zarządzanie projektami
│   │   ├── personas.py          # Generowanie person
│   │   ├── focus_groups.py      # Grupy fokusowe
│   │   └── analysis.py          # Analizy i podsumowania
│   ├── core/                     # Konfiguracja
│   │   ├── config.py
│   │   └── constants.py
│   ├── db/                       # Baza danych
│   │   ├── session.py
│   │   └── base.py
│   ├── models/                   # Modele SQLAlchemy
│   │   ├── project.py
│   │   ├── persona.py
│   │   ├── focus_group.py
│   │   └── persona_events.py
│   ├── schemas/                  # Pydantic schemas
│   │   ├── project.py
│   │   ├── persona.py
│   │   └── focus_group.py
│   ├── services/                 # Logika biznesowa (minimalistyczna wersja)
│   │   ├── persona_generator_langchain.py    # Generator person (Gemini)
│   │   ├── focus_group_service_langchain.py  # Orkiestracja dyskusji
│   │   ├── discussion_summarizer.py          # AI podsumowania
│   │   ├── memory_service_langchain.py       # Kontekst rozmowy
│   │   └── persona_validator.py              # Walidacja person
│   └── main.py                   # Aplikacja FastAPI
├── frontend/                     # Frontend (React)
│   ├── src/
│   │   ├── components/          # Komponenty React
│   │   ├── lib/                 # API client
│   │   ├── types/               # TypeScript types
│   │   └── App.tsx
│   └── vite.config.ts
├── alembic/                      # Migracje bazy danych
├── tests/                        # Testy
├── docker-compose.yml            # Konfiguracja Docker
├── requirements.txt              # Zależności Python
└── README.md

```

## 🚀 Szybki Start

### Wymagania
- Docker & Docker Compose
- Google API Key (Gemini API)

### 1. Konfiguracja

Utwórz plik `.env` w głównym katalogu:

```bash
# Baza danych
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/market_research

# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# Środowisko
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# Modele (opcjonalne)
DEFAULT_MODEL=gemini-2.5-flash
PERSONA_GENERATION_MODEL=gemini-2.5-flash
```

### 2. Uruchomienie z Docker

```bash
# Uruchom wszystkie serwisy
docker-compose up -d

# Sprawdź logi
docker-compose logs -f backend

# Wykonaj migracje bazy
docker-compose exec backend alembic upgrade head
```

### 3. Dostęp

- **Backend API**: http://localhost:8000
- **Dokumentacja API**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173

## 📖 Użytkowanie

### 1. Utwórz Projekt

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Produktu XYZ",
    "description": "Badanie reakcji na nowy produkt",
    "target_demographics": {
      "age_group": {"18-24": 0.3, "25-34": 0.5, "35-44": 0.2},
      "gender": {"Male": 0.45, "Female": 0.55}
    },
    "target_sample_size": 20
  }'
```

### 2. Wygeneruj Persony

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/personas/generate \
  -H "Content-Type: application/json" \
  -d '{
    "num_personas": 20,
    "adversarial_mode": false
  }'
```

Generowanie 20 person trwa ~30-60 sekund.

### 3. Utwórz Grupę Fokusową

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/focus-groups \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sesja Testowa #1",
    "persona_ids": ["uuid1", "uuid2", ...],
    "questions": [
      "Co sądzisz o tym produkcie?",
      "Jakie funkcje byłyby dla Ciebie najważniejsze?",
      "Ile byłbyś skłonny zapłacić?"
    ],
    "mode": "normal"
  }'
```

### 4. Uruchom Dyskusję

```bash
curl -X POST http://localhost:8000/api/v1/focus-groups/{focus_group_id}/run
```

Dyskusja trwa ~2-5 minut (zależy od liczby person i pytań).

### 5. Pobierz Wyniki

```bash
# Odpowiedzi
curl http://localhost:8000/api/v1/focus-groups/{focus_group_id}/responses

# Metryki
curl http://localhost:8000/api/v1/focus-groups/{focus_group_id}/insights

# AI Summary
curl -X POST http://localhost:8000/api/v1/focus-groups/{focus_group_id}/ai-summary?use_pro_model=true
```

## 🧪 Testowanie

```bash
# Uruchom testy
python -m pytest tests/ -v

# Testy integracyjne
python -m pytest tests/test_insights_v2_api.py tests/test_persona_generator.py -v
```

## 🔧 Stack Technologiczny

### Backend
- Python 3.11+
- FastAPI (async web framework)
- PostgreSQL + asyncpg
- SQLAlchemy (async ORM)
- LangChain (AI orchestration)
- Google Generative AI (Gemini 2.5 Flash/Pro)
- Pandas + NumPy (basic analytics)

### Frontend
- React 18
- TypeScript
- Vite
- TanStack Query (React Query)
- Axios
- Tailwind CSS
- Framer Motion

## 📊 Funkcjonalności

### Generowanie Person
- Rozkłady demograficzne (wiek, płeć, edukacja, dochód, lokalizacja)
- Cechy psychologiczne (Big Five personality traits)
- Wymiary kulturowe (Hofstede dimensions)
- Walidacja statystyczna (test chi-kwadrat)
- ~30s dla 20 person

### Grupy Fokusowe
- Równoległe przetwarzanie odpowiedzi person
- System pamięci (kontekst rozmowy)
- Spójność odpowiedzi
- ~2-5 min dla 20 person × 4 pytania

### Analizy
- **AI Summaries**: executive summary, key insights, recommendations (Gemini 2.5 Pro/Flash)
- **Sentiment analysis**: prosta analiza sentymentu na podstawie słów kluczowych
- **Response tracking**: grupowanie odpowiedzi po pytaniach

## 🛠️ Konfiguracja

### Zmienne środowiskowe

```bash
# Baza danych
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname

# API Keys
GOOGLE_API_KEY=your_gemini_api_key

# Modele AI
DEFAULT_MODEL=gemini-2.5-flash              # Model domyślny
PERSONA_GENERATION_MODEL=gemini-2.5-flash   # Generowanie person
ANALYSIS_MODEL=gemini-2.5-pro               # Analizy (opcjonalnie Pro)

# Parametry
TEMPERATURE=0.7                # Temperatura LLM (0.0-1.0)
MAX_TOKENS=2048                # Maks. tokenów w odpowiedzi
RANDOM_SEED=42                 # Seed dla powtarzalności

# Aplikacja
ENVIRONMENT=development        # development/production
DEBUG=true                     # Debug mode
SECRET_KEY=your-secret-key
API_V1_PREFIX=/api/v1
```

## 🐛 Troubleshooting

### Backend nie startuje

```bash
# Sprawdź logi
docker-compose logs backend

# Restart serwisów
docker-compose restart backend db

# Przebuduj kontenery
docker-compose up --build -d
```

### Błąd "GOOGLE_API_KEY not found"

```bash
# Dodaj API key do .env
echo "GOOGLE_API_KEY=your_key_here" >> .env

# Restart backendu
docker-compose restart backend
```

### Błąd połączenia z bazą

```bash
# Sprawdź czy baza działa
docker-compose ps

# Reset bazy (UWAGA: usuwa dane!)
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Persony nie generują się

```bash
# Sprawdź API key
docker-compose exec backend printenv GOOGLE_API_KEY

# Sprawdź logi
docker-compose logs -f backend

# Testowy request do Gemini
curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY"
```
