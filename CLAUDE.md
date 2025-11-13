# CLAUDE.md

Ten plik zawiera wskazówki dla Claude Code (claude.ai/code) podczas pracy z kodem w tym repozytorium.

## ⚠️ WAŻNE: Język Komunikacji

**Claude ZAWSZE komunikuje się PO POLSKU** podczas pracy z tym projektem. Wszystkie odpowiedzi, komentarze, commity i dokumentacja powinny być w języku polskim.

**Nie twórz te zbędnych plików .md!**

Wyjątki:
- Kod (nazwy zmiennych, funkcji, klas) - angielski
- Dokumentacja techniczna specyficzna dla bibliotek - może być po angielsku
- Commity mogą zawierać angielskie słowa techniczne, ale główny opis po polsku

## Szybkie Komendy

```bash
# Deployment (Cloud Run)
# Wszystkie zmiany są automatycznie deployowane na Cloud Run po push do main
git add .
git commit -m "opis zmian"
git push origin main
# Cloud Build automatycznie zbuduje i zdeployuje na Cloud Run

# Sprawdź status deployment
gcloud run services describe sight --region europe-central2
gcloud builds list --limit 5

# Sprawdź logi produkcyjne
gcloud run services logs read sight --region europe-central2 --limit 50

# Testy lokalne (bez docker-compose)
pytest -v                                    # Wszystkie testy
pytest tests/unit -v                        # Tylko testy jednostkowe (~90s)
pytest -v -m "not slow"                     # Tylko szybkie testy
pytest --cov=app --cov-report=html          # Z pokryciem kodu

# Sprawdź jakość kodu
ruff check app/                             # Linting

# Dostęp do usług (produkcja)
# Frontend + API: https://sight-193742683473.europe-central2.run.app
# API Docs: https://sight-193742683473.europe-central2.run.app/docs
```

## Architektura Wysokiego Poziomu

### Przegląd Systemu

**Sight** to platforma wirtualnych grup fokusowych wykorzystująca Google Gemini 2.5 do generowania realistycznych person i symulacji dyskusji badawczych. System łączy:

1. **Generacja person opartą na segmentach** - Persony AI z ograniczeniami demograficznymi
2. **Asynchroniczne grupy fokusowe** - Równoległe wywołania LLM dla realistycznych rozmów
3. **Hybrydowy system RAG** - Wyszukiwanie wektorowe + słownikowe z wiedzą grafową Neo4j
4. **Śledzenie użycia** - Monitoring kosztów i zarządzanie budżetem operacji LLM

### Główne Wzorce Architektoniczne

#### 1. Wzorzec Warstwy Serwisowej

Cała logika biznesowa znajduje się w `app/services/` zorganizowanej według domeny:

```
app/services/
├── personas/           # Generacja person, orkiestracja, analiza potrzeb
├── focus_groups/       # Zarządzanie dyskusjami, podsumowania, pamięć
├── surveys/            # Generacja odpowiedzi na ankiety
├── rag/               # Wyszukiwanie hybrydowe, transformacje grafowe, zarządzanie dokumentami
├── dashboard/         # Śledzenie użycia, logowanie
├── shared/            # Współdzielone klienty LLM, narzędzia
└── maintenance/       # Zadania czyszczące, zaplanowane zadania
```

**Kluczowa zasada:** Endpointy API (`app/api/`) są cienkimi wrapperami, które delegują do serwisów. Logika biznesowa, wywołania LLM i transformacje danych odbywają się w serwisach.

#### 2. Scentralizowany System Konfiguracji

**KRYTYCZNE:** Wszystkie prompty, modele i ustawienia są w `config/` (bazowane na YAML):

```
config/
├── models.yaml         # Rejestr modeli z łańcuchem fallback
├── features.yaml       # Flagi funkcji, cele wydajnościowe
├── app.yaml           # Ustawienia infrastruktury (DB, Redis, Neo4j)
├── prompts/           # 25+ promptów zorganizowanych według domeny
│   ├── personas/      # Prompty generacji person
│   ├── focus_groups/  # Prompty dyskusji
│   ├── surveys/       # Prompty odpowiedzi na ankiety
│   └── rag/          # Prompty zapytań RAG
└── rag/              # Konfiguracja RAG (chunking, retrieval)
```

**Użycie:**
```python
# Modele
from config import models
model_config = models.get("personas", "generation")  # Łańcuch fallback: domain.subdomain → domain.default → global.default
llm = build_chat_model(**model_config.params)

# Prompty (Jinja2 z delimitatorami ${var})
from config import prompts
template = prompts.get("personas.jtbd")
messages = template.render(age=25, occupation="Engineer")

# Funkcje
from config import features
if features.rag.enabled:
    chunk_size = features.rag.chunk_size
```

**Uwaga migracyjna:** Stary wzorzec `get_settings()` został usunięty w PR4. Zawsze używaj `from config import models, features, app`. Zobacz `config/README.md` dla przewodnika migracji.

#### 3. Projekt Async-First

Wszystkie operacje bazodanowe, wywołania LLM i zewnętrzne serwisy używają `async/await`:

```python
# Baza danych
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def my_endpoint(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Persona))

# Wywołania LLM (równoległe dla wydajności)
import asyncio
tasks = [generate_persona(seg) for seg in segments]
personas = await asyncio.gather(*tasks)
```

#### 4. Hybrydowy System RAG

Dwuwarstwowy system pozyskiwania dla polskiego kontekstu demograficznego:

**Warstwa 1: Hybrid Search** (`app/services/rag/rag_hybrid_search_service.py`)
- Wyszukiwanie wektorowe: Embeddingi Google Gemini (768 wymiarów) + podobieństwo cosinusowe
- Wyszukiwanie słownikowe: Indeks pełnotekstowy Neo4j (bazowany na Lucene)
- RRF Fusion: Łączy oba używając reciprocal rank fusion

**Warstwa 2: Graph RAG** (`app/services/rag/rag_graph_service.py`)
- Generacja zapytań Cypher wspierana przez LLM
- Strukturalna ekstrakcja wiedzy (węzły: Obserwacja, Wskaźnik, Trend, Demografia)
- Bogate metadane: summary, key_facts, confidence, time_period

**Kiedy używać:**
- Generacja person odpytuje polskie dane demograficzne dla realistycznego kontekstu
- Orkiestracja używa graph RAG dla głębszych insightów i relacji

#### 5. Event Sourcing dla Person

Persony używają wzorca event sourcingu dla ścieżki audytu i reprodukowalności:

```python
# app/models/persona_events.py
class PersonaEvent(Base):
    __tablename__ = "persona_events"
    event_type: str  # "generated", "validated", "updated"
    event_data: dict  # Kompletna migawka
    triggered_by: str
```

Wszystkie zmiany stanu persony są logowane jako zdarzenia, umożliwiając:
- Ścieżkę audytu dla zgodności
- Cofnięcie do poprzednich stanów
- Debugowanie problemów generacji person
- Odtworzenie tworzenia persony z tymi samymi inputami

#### 6. Generacja Person Oparta na Segmentach

**Architektura:** Persony są generowane per segment demograficzny (nie indywidualnie):

1. **Orkiestracja** (`persona_orchestration.py`) → Tworzy segmenty z docelowych demograficznych
2. **Segment Brief** (`segment_brief_service.py`) → Generuje kontekst społeczny per segment (cache'owany)
3. **Generacja** (`persona_generator_langchain.py`) → Równoległa generacja z ograniczeniami demograficznymi
4. **Walidacja** → Test chi-kwadrat dla statystycznej reprezentatywności

**Korzyści:**
- Wymusza rozkład demograficzny
- Redukuje wywołania LLM (przetwarzanie wsadowe)
- Spójne persony w segmentach
- Wbudowana walidacja statystyczna

### Stack Technologiczny

**Backend:**
- FastAPI (async Python web framework)
- SQLAlchemy 2.0 (async ORM)
- PostgreSQL z rozszerzeniem pgvector
- Redis (cache'owanie, rate limiting)
- Neo4j (grafowa baza danych dla RAG)
- LangChain (orkiestracja LLM)
- Google Gemini 2.5 (Flash dla generacji, Pro dla złożonego rozumowania)

**Frontend:**
- React 18 + TypeScript
- Vite (narzędzie do budowania)
- TanStack Query (stan serwera)
- Zustand (stan UI)
- Tailwind CSS

**Infrastruktura:**
- Docker Compose (lokalne developowanie)
- Google Cloud Run (produkcyjny deployment)
- Cloud Build (CI/CD)
- Alembic (migracje bazy danych)

## Wzorce Developmentu

### Dodawanie Nowego Endpointu API

1. Utwórz endpoint w `app/api/{domain}.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_db
from app.services.{domain}.{service} import MyService

router = APIRouter()

@router.post("/{domain}/action")
async def perform_action(
    request: ActionRequest,
    db: AsyncSession = Depends(get_db)
):
    service = MyService(db)
    result = await service.perform_action(request)
    return result
```

2. Utwórz serwis w `app/services/{domain}/{service}.py` z logiką biznesową

3. Dodaj schematy Pydantic w `app/schemas/{domain}.py` dla walidacji request/response

4. Napisz testy w `tests/unit/services/test_{service}.py`

### Dodawanie Nowego Promptu LLM

1. Utwórz plik YAML w `config/prompts/{domain}/{name}.yaml`:
```yaml
id: domain.name
version: "1.0.0"
description: "Jasny opis co robi ten prompt"
messages:
  - role: system
    content: |
      Instrukcje systemowe tutaj...
  - role: user
    content: |
      Prompt użytkownika ze zmiennymi ${placeholder}
```

2. Użyj w kodzie:
```python
from config import prompts
from langchain_core.prompts import ChatPromptTemplate

template = prompts.get("domain.name")
rendered = template.render(placeholder="wartość")
prompt = ChatPromptTemplate.from_messages([
    (msg["role"], msg["content"]) for msg in rendered
])
```

3. Waliduj: `python scripts/config_validate.py`

### Dodawanie Nowej Konfiguracji Modelu

Edytuj `config/models.yaml`:
```yaml
domains:
  twoja_domena:
    twoje_zadanie:
      model: "gemini-2.5-flash"      # lub gemini-2.5-pro
      temperature: 0.7                # 0.0-1.0
      max_tokens: 6000
      timeout: 60
      retries: 3
```

Użyj w kodzie:
```python
from config import models
from app.services.shared.clients import build_chat_model

model_config = models.get("twoja_domena", "twoje_zadanie")
llm = build_chat_model(**model_config.params)
```

### Migracje Bazy Danych

**UWAGA:** Migracje są automatycznie stosowane podczas deploymentu na Cloud Run (przez `docker-entrypoint.sh`).

Jeśli chcesz testować migracje lokalnie:

```bash
# Auto-generuj migrację ze zmian w modelach (lokalne środowisko)
DATABASE_URL="postgresql+asyncpg://sight:dev_password_change_in_prod@localhost:5433/sight_db" \
  alembic revision --autogenerate -m "Dodaj nowe pole do personas"

# Przejrzyj wygenerowaną migrację w alembic/versions/

# Zastosuj migrację (lokalne środowisko)
DATABASE_URL="postgresql+asyncpg://sight:dev_password_change_in_prod@localhost:5433/sight_db" \
  alembic upgrade head

# Po zacommitowaniu i push, migracje są automatycznie stosowane na Cloud Run
```

**Ważne:** Zawsze przeglądaj auto-generowane migracje. Alembic może pominąć:
- Zmiany indeksów
- Niestandardowe operacje SQL
- Migracje danych

### Śledzenie Użycia dla Wywołań LLM

Opakowuj wywołania LLM kontekstem logowania użycia:

```python
from app.services.dashboard.usage_logging import context_with_model, schedule_usage_logging

# Ustaw kontekst modelu
with context_with_model("gemini-2.5-flash", "personas.generation"):
    # Wywołanie LLM
    result = await llm.ainvoke(messages)

    # Zaplanuj asynchroniczne logowanie użycia
    await schedule_usage_logging(
        user_id=user_id,
        project_id=project_id,
        operation="persona_generation",
        metadata={"num_personas": 20}
    )
```

To śledzi:
- Użycie tokenów (input/output)
- Koszty modelu (z `config/pricing.yaml`)
- Typ operacji i metadane
- Atrybucję użytkownika/projektu

## Zarządzanie Dokumentacją

**WAŻNE**: Priorytetyzuj aktualizację istniejących plików nad tworzeniem nowych!

### Zasady dla Wszystkich (Claude + Agentów):

**1. ZAWSZE sprawdzaj istniejące pliki PRZED utworzeniem nowego**
- Dokumentacja żyje w `docs/` z płaską strukturą plików tematycznych
- Sprawdź czy nie możesz dodać sekcji do istniejącego pliku
- Twórz nowy plik tylko gdy naprawdę nie ma gdzie dodać treści

**2. Limit długości: 700 linii per plik**
- Jeśli plik przekracza 700 linii → podziel na mniejsze pliki
- Używaj naturalnego ciągłego języka z podziałem na sekcje
- Unikaj nadmiernych bullet points - pisz jak eseje techniczne

**3. Grafy ASCII - używaj rozsądnie**
- Dodawaj TYLKO gdy znacząco pomagają zrozumieć koncepcję
- Dobre przypadki: system architecture, data flows, business model canvas
- Złe przypadki: proste listy, relacje które można opisać słowami

### Kiedy Aktualizować Istniejące Pliki:

**Zmiany w architekturze/kodzie:**
- Backend (API, serwisy, DB) → `docs/BACKEND.md`
- AI/ML (LLM, RAG, prompty) → `docs/AI_ML.md`
- Frontend (komponenty, state) → `docs/FRONTEND.md` (jeśli istnieje)
- Infrastructure (Docker, CI/CD) → `docs/INFRASTRUKTURA.md`

**Zmiany w strategii/biznesie:**
- Roadmap, priorytety → `docs/ROADMAP.md`
- Model biznesowy, GTM, pricing → `docs/BIZNES.md`
- Metryki, KPIs → Zaktualizuj sekcje w BIZNES.md

**Zmiany w operacjach:**
- Testy, coverage, benchmarki → `docs/QA.md`
- DevOps, deployment, monitoring → `docs/INFRASTRUKTURA.md`
- Security, compliance → `docs/SECURITY.md` (jeśli istnieje)

### Kiedy Tworzyć Nowe Pliki:

**Rzadkie przypadki kiedy nowy plik jest OK:**
1. **Całkowicie nowy obszar** bez istniejącej dokumentacji
2. **User wyraźnie poprosi** o nowy dokument
3. **Istniejący plik przekroczyłby 700 linii** po dodaniu
4. **Raporty czasowe** → `docs/REPORTS_YYYY_MM.md`

### Struktura Folderów docs/:

```
docs/
├── README.md                          # Indeks dokumentacji (aktualizuj!)
├── BACKEND.md                         # API, Services, Database
├── AI_ML.md                           # LLM, RAG, Prompts
├── INFRASTRUKTURA.md                  # Docker, CI/CD, Cloud Run, DevOps
├── FRONTEND.md                        # React, komponenty, state (jeśli istnieje)
├── BIZNES.md                          # Model biznesowy, GTM, pricing
├── ROADMAP.md                         # Priorytety, milestones, strateg
├── QA.md                              # Testowanie, coverage, benchmarki
├── SECURITY.md                        # Bezpieczeństwo, compliance (jeśli istnieje)
└── archive/                           # Archiwalne dokumenty
    └── [old_docs].md
```

### Agenci z Prawem Regularnego Pisania:

**Ci agenci często tworzą dokumentację** (ale nadal: najpierw aktualizuj!):
- `technical-writer` - Dokumentacja techniczna, user guides, API docs
- `business-analyst` - Analizy biznesowe, modele finansowe
- `product-manager` - PRDy, specs, roadmapy
- `growth-marketer` - Campaign briefs, GTM strategy
- `team-orchestrator` - Coordination plans, ADRs

**Pozostali agenci**: Mogą tworzyć .md, ale TYLKO gdy konieczne (update first!)

### Przykłady Decyzji:

```
❌ NIE: Zmiana auth system → Tworzę docs/AUTH_SYSTEM.md
✅ TAK: Zmiana auth system → Aktualizuję docs/BACKEND.md (dodaję sekcję "Authentication")

❌ NIE: Nowa feature Journey Mapping → Tworzę docs/JOURNEY_MAPPING.md
✅ TAK: Nowa feature Journey Mapping → Aktualizuję docs/ROADMAP.md (dodaję do roadmapu)
      + Jeśli szczegóły feature są obszerne → Aktualizuję docs/BACKEND.md lub docs/AI_ML.md

❌ NIE: Zmiana deployment → Tworzę docs/NEW_DEPLOYMENT.md
✅ TAK: Zmiana deployment → Aktualizuję docs/INFRASTRUKTURA.md (sekcja "Deployment" lub "CI/CD")

✅ TAK: Raport miesięczny → docs/REPORTS_2024_11.md (nowy plik OK, to raport)
```

### Aktualizacja docs/README.md:

**Kiedy dodajesz nowy plik**, zaktualizuj `docs/README.md`:
- Dodaj link w odpowiedniej sekcji dokumentacji
- Dodaj krótki opis (1 zdanie)
- Zachowaj alfabetyczny porządek

**Nie zapomnij**: Dokumentacja bez linku w README jest jak nieodkryta wyspa!

## Strategia Testowania

### Kategorie Testów

```bash
# Testy jednostkowe (~240 testów, <90s) - Izolowana logika serwisów
pytest tests/unit -v

# Testy integracyjne (~70 testów, 10-30s) - API + DB + Zewnętrzne serwisy
pytest tests/integration -v

# Testy E2E (~5 testów, 2-5 min) - Pełne przepływy użytkownika
pytest tests/e2e -v

# Testy wydajnościowe (~3 testy, 5-10 min) - Benchmarki i testy obciążeniowe
pytest tests/performance -v

# Testy obsługi błędów (~9 testów, 5-10s) - Przypadki brzegowe
pytest tests/error_handling -v

# Tylko szybkie testy (wyklucza markery slow)
pytest -v -m "not slow"
```

### Cele Pokrycia

- Ogólnie: 80%+
- Serwisy: 85%+
- Ścieżki krytyczne (generacja person, grupy fokusowe): 90%+

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Fixtury Testowe

Współdzielone fixtury w `tests/conftest.py` i `tests/fixtures/`:
- `db_session`: Asynchroniczna sesja bazodanowa z rollbackiem transakcji
- `test_project`: Projekt z demograficznymi celami
- `test_personas`: 20 wygenerowanych person
- `mock_llm`: Mock LLM do testowania bez wywołań API

### Pisanie Testów

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_generate_personas(db_session, test_project):
    """Test generacji person z ograniczeniami demograficznymi."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/personas/generate",
            json={"num_personas": 20}
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["personas"]) == 20

    # Weryfikuj rozkład demograficzny
    ages = [p["age"] for p in data["personas"]]
    assert min(ages) >= 18
    assert max(ages) <= 65
```

## Częste Pułapki i Rozwiązania

### 1. Problemy z Kontekstem Async

**Problem:** Mieszanie kodu sync i async powoduje błędy runtime.

**Rozwiązanie:** Używaj async wszędzie w endpointach FastAPI:
```python
# ✅ Dobrze
async def my_endpoint(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Persona))

# ❌ Źle
def my_endpoint(db: AsyncSession = Depends(get_db)):
    result = db.execute(select(Persona))  # Brakuje await
```

### 2. Problem N+1 Zapytań

**Problem:** Pobieranie powiązanych danych w pętlach powoduje nadmierne zapytania do DB.

**Rozwiązanie:** Używaj `selectinload` lub `joinedload`:
```python
# ✅ Dobrze (1 zapytanie)
stmt = select(Persona).options(selectinload(Persona.focus_groups))
personas = await db.execute(stmt)

# ❌ Źle (N+1 zapytań)
personas = await db.execute(select(Persona))
for persona in personas:
    focus_groups = await db.execute(
        select(FocusGroup).where(FocusGroup.persona_id == persona.id)
    )
```

### 3. Błędy Importu Konfiguracji

**Problem:** Używanie starego wzorca `get_settings()` (usunięty w PR4).

**Rozwiązanie:** Migruj do scentralizowanej konfiguracji:
```python
# ❌ Stare (nie zadziała)
from app.core.config import get_settings
settings = get_settings()

# ✅ Nowe
from config import models, features, app
model = models.get("personas", "generation")
```

### 4. Inicjalizacja Serwisów RAG

**Problem:** Serwisy RAG crashują przy starcie w Cloud Run z błędami "503 Illegal metadata".

**Rozwiązanie:** Serwisy RAG używają leniwej inicjalizacji (inicjalizowane przy pierwszym użyciu, nie przy starcie aplikacji). Nie inicjalizuj eager w kontekście `lifespan`.

### 5. Rate Limiting LLM

**Problem:** Uderzanie w limity rate Gemini API z równoległymi requestami.

**Rozwiązanie:** Używaj `asyncio.Semaphore` aby limitować równoległe wywołania:
```python
import asyncio

semaphore = asyncio.Semaphore(5)  # Maks 5 równoległych wywołań

async def generate_with_limit(data):
    async with semaphore:
        return await llm.ainvoke(data)
```

### 6. Problemy z Pamięcią przy Dużych Grupach Fokusowych

**Problem:** Generowanie odpowiedzi dla 20+ person powoduje OOM.

**Rozwiązanie:** Przetwarzaj w partiach:
```python
batch_size = 5
for i in range(0, len(personas), batch_size):
    batch = personas[i:i+batch_size]
    tasks = [generate_response(p) for p in batch]
    responses = await asyncio.gather(*tasks)
```

## Checklist Gotowości Produkcyjnej

Przed deploymentem:

- [ ] Wszystkie testy przechodzą: `pytest -v`
- [ ] Pokrycie spełnia cele: `pytest --cov=app --cov-report=term`
- [ ] Linting przechodzi: `ruff check app/`
- [ ] Migracje zastosowane: `alembic upgrade head`
- [ ] Indeksy Neo4j utworzone: `python scripts/init_neo4j_indexes.py`
- [ ] Zmienne środowiskowe ustawione:
  - [ ] `SECRET_KEY` (min 32 znaki, użyj `openssl rand -hex 32`)
  - [ ] `GOOGLE_API_KEY`
  - [ ] `DATABASE_URL` z produkcyjnymi credentials
  - [ ] `ENVIRONMENT=production`
- [ ] Walidacja bezpieczeństwa przechodzi (sprawdzane w `app/main.py` przy starcie)
- [ ] Pliki konfiguracyjne zwalidowane: `python scripts/config_validate.py`
- [ ] Brak sekretów w kodzie lub historii git
- [ ] Origin CORS ograniczone (lub wyłączone dla same-origin deployment)
- [ ] Rate limiting skonfigurowany
- [ ] Śledzenie użycia włączone dla monitoringu kosztów

## Referencja Kluczowych Plików

- `app/main.py` - Punkt wejścia aplikacji FastAPI, middleware, zarządzanie lifespan
- `app/db/session.py` - Zarządzanie sesją bazodanową (async)
- `config/README.md` - Kompletny przewodnik po scentralizowanym systemie konfiguracji
- `config/PROMPTS_INDEX.md` - Katalog wszystkich 25 promptów z parametrami
- `docs/README.md` - Indeks dokumentacji
- `docs/BACKEND.md` - API, serwisy, architektura bazodanowej
- `docs/AI_ML.md` - LLM, RAG, prompty, system generacji person
- `docs/INFRASTRUKTURA.md` - Docker, CI/CD, deployment Cloud Run, DevOps
- `docs/QA.md` - Testowanie, pokrycie kodu, benchmarki
- `docs/BIZNES.md` - Model biznesowy, GTM, pricing, KPIs
- `docs/ROADMAP.md` - Priorytety, milestones, strategia produktu
- `requirements.txt` - Zależności Python (core)
- `pyproject.toml` - Opcjonalne zależności (llm-providers, document-processing, itp.)

## Cele Wydajnościowe

- Generacja person: 20 person < 60s (obecnie ~45s)
- Dyskusja grupy fokusowej: 20 person × 4 pytania < 3 min (obecnie ~2 min)
- Zapytanie Hybrid RAG: < 350ms per zapytanie
- Czas odpowiedzi API: < 500ms (90. percentyl)
- Czas zapytania do bazy: < 100ms (95. percentyl)

## Troubleshooting: Brak Reasoning w Personach

**Symptom:** Persony są wygenerowane, ale zakładka "Uzasadnienie" jest pusta lub pokazuje żółty banner "Ta persona nie ma szczegółowego reasoning".

### Diagnoza

1. **Sprawdź logi serwera (Cloud Run):**
```bash
gcloud run services logs read sight --region europe-central2 --limit 100 | grep "Orchestration"
```

Szukaj:
- ✅ `"✅ Orchestration plan created"` - sukces
- ❌ `"❌ Orchestration failed"` - błąd
- ❌ `"🚫 ORCHESTRATION DISABLED"` - wyłączone

2. **Sprawdź feature flag:**
```bash
# Feature flag jest w config/features.yaml (nie w .env)
grep -A 2 "orchestration:" config/features.yaml
# Powinno być: enabled: true
```

3. **Sprawdź Neo4j (Graph RAG):**
```bash
# Neo4j jest w Cloud Run jako managed service
# Sprawdź health check w logach
gcloud run services logs read sight --region europe-central2 --limit 20 | grep neo4j
```

### Przyczyny Problemu

**1. Feature Flag Wyłączony**
- `orchestration.enabled: false` w `config/features.yaml`
- **Fix:** Zmień na `true`, commit i push do main (automatyczny redeploy)

**2. Neo4j Connection Error**
- Neo4j nie jest dostępny lub błąd konfiguracji
- **Fix:** Sprawdź logi Cloud Run, zweryfikuj NEO4J_URI w Cloud Run env vars

**3. Orchestration Timeout**
- Tworzenie briefów segmentów trwa >90s (domyślny timeout)
- **Fix:** Zwiększ timeout w `config/features.yaml`: `orchestration.timeout: 120`

**4. Gemini API Error**
- Invalid API key lub rate limit
- **Fix:** Sprawdź GOOGLE_API_KEY w Cloud Run env vars, sprawdź quota w GCP Console

**5. Persony Wygenerowane z use_rag=false**
- Frontend lub skrypty użyły `use_rag: false`
- **Fix:** Upewnij się że wszystkie requesty mają `use_rag: true`

### Rozwiązanie

```bash
# 1. Sprawdź konfigurację (lokalne)
grep -A 2 "orchestration:" config/features.yaml

# 2. Sprawdź logi Cloud Run
gcloud run services logs read sight --region europe-central2 --limit 100

# 3. Jeśli potrzebna zmiana config - commit i push
git add config/features.yaml
git commit -m "fix: enable orchestration"
git push origin main
# Cloud Build automatycznie zdeployuje nową wersję

# 4. Sprawdź status deploymentu
gcloud builds list --limit 5
gcloud run services describe sight --region europe-central2

# 5. Wygeneruj persony ponownie
# (Stare persony nie dostaną reasoning retroaktywnie)
```

### Prevention

- ✅ **Backend:** API zwraca `warning` w response jeśli orchestration wyłączone
- ✅ **Frontend UI:** Żółty banner pokazuje się jeśli brak orchestration
- ✅ **ReasoningPanel:** Szczegółowe instrukcje troubleshooting jeśli brak reasoning
- ✅ **Logi:** Structured alert gdy orchestration failuje (`alert: True`)

### Weryfikacja Success

Po naprawie, sprawdź przez frontend (produkcja):
```bash
# 1. Otwórz aplikację
open https://sight-193742683473.europe-central2.run.app

# 2. Wygeneruj testową personę (przez UI lub API)
# Poczekaj ~30s

# 3. Sprawdź reasoning przez API
curl https://sight-193742683473.europe-central2.run.app/api/v1/personas/{persona_id}/reasoning \
  -H "Authorization: Bearer $TOKEN"
```

Jeśli reasoning zawiera `orchestration_brief` (900-1200 znaków), `graph_insights`, `segment_name` - **problem rozwiązany!** ✅

## Uzyskiwanie Pomocy

1. Sprawdź `docs/README.md` dla indeksu dokumentacji
2. Sprawdź `config/README.md` dla problemów z konfiguracją
3. Uruchom `pytest -v` aby zweryfikować setup (testy lokalne)
4. Sprawdź logi produkcyjne: `gcloud run services logs read sight --region europe-central2 --limit 100`
5. Sprawdź health check: `curl https://sight-193742683473.europe-central2.run.app/health`
6. Sprawdź status deploymentu: `gcloud builds list --limit 5`

## Dodatkowe Uwagi

- To jest polska platforma badań rynkowych - UI i dane są po polsku
- Domyślne dane demograficzne dla Polski są w `config/demographics/poland.yaml`
- Prompty używają delimitatorów `${variable}` (nie `{{variable}}`) dla kompatybilności Jinja2 z zapytaniami Cypher
- Wszystkie docstringi są po polsku (konwencja projektu)
- Platforma używa wzorca soft-delete - encje są oznaczane `deleted_at` zamiast twardego usunięcia
- Zadanie czyszczące w tle uruchamia się codziennie aby twardo usunąć soft-deleted encje po 7 dniach retencji
- **Claude ZAWSZE odpowiada i komunikuje się PO POLSKU** przy pracy z tym projektem
