# Market Research SaaS - Wirtualne Grupy Fokusowe z AI

**Minimalistyczna wersja** - system do przeprowadzania wirtualnych grup fokusowych i ankiet syntetycznych z wykorzystaniem Google Gemini AI. Generuje realistyczne persony i symuluje dyskusje oraz odpowiedzi ankietowe dla potrzeb badań rynkowych.

## 📋 Opis Projektu

Market Research SaaS to platforma umożliwiająca:
- **Generowanie realistycznych person** - AI tworzy szczegółowe profile uczestników badań
- **Symulację grup fokusowych** - Persony odpowiadają na pytania jak prawdziwi ludzie
- **Ankiety syntetyczne** ⭐ - Tworzenie i uruchamianie ankiet z 4 typami pytań (single/multiple choice, rating scale, open text)
- **Analizę wyników** - Automatyczne podsumowania AI przez Google Gemini + statystyki ankiet

## 🛠️ Ostatnie zmiany

- Naprawiono błąd zamykający sesję bazy przed zapisaniem person – profile widać w projektach od razu, a zapisy odbywają się partiami dla lepszej wydajności.
- Panel i strona „Personas” korzystają ze wspólnej logiki generowania, więc wywołanie kreatora zawsze uruchamia żądanie API i pokazuje postęp.

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
│   │   ├── surveys.py           # Ankiety syntetyczne ⭐ NEW
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
│   │   ├── survey.py            # Model ankiet ⭐ NEW
│   │   └── persona_events.py
│   ├── schemas/                  # Pydantic schemas
│   │   ├── project.py
│   │   ├── persona.py
│   │   ├── focus_group.py
│   │   └── survey.py            # Schemas ankiet ⭐ NEW
│   ├── services/                 # Logika biznesowa (minimalistyczna wersja)
│   │   ├── persona_generator_langchain.py       # Generator person (Gemini)
│   │   ├── focus_group_service_langchain.py     # Orkiestracja dyskusji
│   │   ├── survey_response_generator.py         # Generator odpowiedzi ankiet ⭐ NEW
│   │   ├── discussion_summarizer.py             # AI podsumowania
│   │   ├── memory_service_langchain.py          # Kontekst rozmowy
│   │   └── persona_validator.py                 # Walidacja person
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

### Przykład cURL

#### 1. Utwórz Projekt

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

#### 2. Wygeneruj Persony

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/personas/generate \
  -H "Content-Type: application/json" \
  -d '{
    "num_personas": 20,
    "adversarial_mode": false
  }'
```

Generowanie 20 person trwa ~30-60 sekund.

#### 3. Utwórz Grupę Fokusową

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

#### 4. Uruchom Dyskusję

```bash
curl -X POST http://localhost:8000/api/v1/focus-groups/{focus_group_id}/run
```

Dyskusja trwa ~2-5 minut (zależy od liczby person i pytań).

#### 5. Pobierz Wyniki

```bash
# Odpowiedzi
curl http://localhost:8000/api/v1/focus-groups/{focus_group_id}/responses

# Metryki
curl http://localhost:8000/api/v1/focus-groups/{focus_group_id}/insights

# AI Summary
curl -X POST http://localhost:8000/api/v1/focus-groups/{focus_group_id}/ai-summary?use_pro_model=true

# Graph Analysis (po zakończeniu focus group)
curl http://localhost:8000/api/v1/graph/{focus_group_id}/controversial  # Kontrowersyjne tematy
curl http://localhost:8000/api/v1/graph/{focus_group_id}/influential    # Wpływowe persony
```

### Przykład Python

```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

# 1. Utwórz projekt
project = requests.post(f"{BASE_URL}/projects", json={
    "name": "Test Aplikacji Mobilnej",
    "description": "Badanie UX nowej aplikacji",
    "target_demographics": {
        "age_group": {"18-24": 0.4, "25-34": 0.6},
        "gender": {"Male": 0.5, "Female": 0.5}
    },
    "target_sample_size": 15
}).json()
project_id = project["id"]
print(f"✅ Projekt utworzony: {project_id}")

# 2. Wygeneruj persony
requests.post(f"{BASE_URL}/projects/{project_id}/personas/generate", json={
    "num_personas": 15,
    "adversarial_mode": False
})
print("⏳ Czekam 45s na generowanie person...")
time.sleep(45)

# 3. Pobierz persony
personas = requests.get(f"{BASE_URL}/projects/{project_id}/personas").json()
persona_ids = [p["id"] for p in personas[:10]]
print(f"✅ Wygenerowano {len(personas)} person")

# 4. Utwórz focus group
focus_group = requests.post(f"{BASE_URL}/projects/{project_id}/focus-groups", json={
    "name": "Sesja Testowa",
    "persona_ids": persona_ids,
    "questions": [
        "Jakie są Twoje pierwsze wrażenia?",
        "Co Ci się najbardziej podoba?",
        "Co należy poprawić?"
    ],
    "mode": "normal"
}).json()
fg_id = focus_group["id"]
print(f"✅ Focus group: {fg_id}")

# 5. Uruchom dyskusję
requests.post(f"{BASE_URL}/focus-groups/{fg_id}/run")
print("⏳ Czekam 2 min na dyskusję...")
time.sleep(120)

# 6. Pobierz wyniki
insights = requests.get(f"{BASE_URL}/focus-groups/{fg_id}/insights").json()
print(f"\n📈 WYNIKI:")
print(f"  Idea Score: {insights['idea_score']:.1f}/100")
print(f"  Consensus: {insights['consensus_level']:.1%}")

# 7. Pobierz kontrowersyjne tematy z grafu
controversial = requests.get(f"{BASE_URL}/graph/{fg_id}/controversial").json()
print(f"\n🔥 Kontrowersyjne tematy:")
for concept in controversial["controversial_concepts"][:3]:
    print(f"  • {concept['concept']} (polaryzacja: {concept['polarization']:.2f})")
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

### Ankiety Syntetyczne (Surveys) ⭐ NEW
- **4 typy pytań**: Single choice, Multiple choice, Rating scale, Open text
- **Drag & drop builder**: Intuicyjny interfejs do tworzenia ankiet
- **AI-powered responses**: Odpowiedzi generowane przez Gemini bazując na profilach person
- **Równoległe przetwarzanie**: Wszystkie persony odpowiadają jednocześnie
- **Analiza statystyczna**: Automatyczne agregowanie wyników, wykresy, statystyki
- **Analiza demograficzna**: Podział odpowiedzi według wieku, płci, wykształcenia, dochodu
- **Wizualizacje**: Bar charts, pie charts dla wyników ankiet
- **Wydajność**: ~1-3s na odpowiedź persony, pełna ankieta w <60s

### Analiza Grafowa (Graph Analysis) 🔥 NEW
- **Graf wiedzy Neo4j**: Automatyczne budowanie grafu z dyskusji focus group
- **Ekstrakcja konceptów**: LLM wyodrębnia kluczowe tematy i emocje z odpowiedzi
- **Relacje między uczestnikami**: AGREES_WITH, DISAGREES_WITH, MENTIONS, FEELS
- **Kontrowersyjne tematy**: Identyfikacja polaryzujących konceptów (wysoka wariancja sentymentu)
- **Wpływowe persony**: PageRank-style analiza najbardziej połączonych uczestników
- **Korelacje demograficzne**: Jak wiek/płeć wpływa na opinie
- **Wizualizacja 3D**: Interaktywny graf z React Three Fiber (Force Graph 3D)
- **Automatyczne**: Graf buduje się po zakończeniu focus group (~30-60s)

### Analizy
- **AI Summaries**: executive summary, key insights, recommendations (Gemini 2.5 Pro/Flash)
- **Sentiment analysis**: prosta analiza sentymentu na podstawie słów kluczowych
- **Response tracking**: grupowanie odpowiedzi po pytaniach
- **Survey analytics**: statystyki dla każdego typu pytania (mean, median, distribution)
- **Graph insights**: kontrowersyjne koncepty, wpływowe persony, korelacje trait-opinion

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
