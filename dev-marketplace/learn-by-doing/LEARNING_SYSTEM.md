# 🎓 Learn-by-Doing - Universal Learning System

**Wersja:** 2.0
**Data:** 2025-11-02
**Typ:** Uniwersalny system uczenia się dla Claude Code

---

## 📚 Spis Treści

1. [Przegląd Systemu](#przegląd-systemu)
2. [Architektura](#architektura)
3. [Kluczowe Funkcje](#kluczowe-funkcje)
4. [Jak Działa](#jak-działa)
5. [Struktura Plików](#struktura-plików)
6. [Komendy](#komendy)
7. [Knowledge Base](#knowledge-base)
8. [Auto-Discovery](#auto-discovery)
9. [Dependency Graph](#dependency-graph)
10. [Rekomendacje](#rekomendacje)
11. [Spaced Repetition](#spaced-repetition)
12. [Konfiguracja](#konfiguracja)
13. [Rozszerzanie Systemu](#rozszerzanie-systemu)
14. [FAQ](#faq)
15. [Troubleshooting](#troubleshooting)

---

## 🎯 Przegląd Systemu

**Learn-by-Doing** to inteligentny system uczenia się który automatycznie:
- ✅ Śledzi co robisz (każdy plik, każda komenda, każdy test)
- ✅ Wykrywa używane technologie (45+ predefiniowanych + **nieograniczone auto-discovery**)
- ✅ Oblicza poziom opanowania (Mastery Levels 1-5)
- ✅ Sugeruje co uczyć się dalej (dependency graph + rekomendacje)
- ✅ Przypomina o powtórkach (spaced repetition)
- ✅ Śledzi postęp w kategoriach (Backend, Frontend, AI/ML, DevOps, etc.)

### 🌟 Kluczowa Innowacja: **Uczenie Się Wszystkiego**

W przeciwieństwie do systemów które wymagają manualnej konfiguracji, **Learn-by-Doing v2.0** SAM wykrywa nowe technologie:

**Przykład:**
Zaczniesz uczyć się **Svelte**, **GraphQL**, **Kubernetes** (nie ma w knowledge_base):
1. System wykryje pliki `.svelte`, imports `from 'svelte'`
2. Automatycznie stworzy dynamic concepts
3. Będzie śledzić postęp
4. Pokaże w `/progress` i `/learn`
5. Zasugeruje related concepts

**Wszystko automatycznie, bez konfiguracji!** 🚀

---

## 🏗️ Architektura

### Główne Moduły

```
learn-by-doing/
├── data/                           # Dane
│   ├── knowledge_base.json         # 45 predefiniowanych konceptów
│   ├── dynamic_concepts.json       # Auto-discovered koncepty
│   ├── learning_progress.json     # Twój postęp
│   ├── practice_log.jsonl          # Log wszystkich akcji
│   └── config.json                 # Konfiguracja
│
├── scripts/                        # Core system
│   ├── data_manager.py             # Centralne zarządzanie danymi
│   ├── concept_detector.py         # Wykrywanie konceptów z practice log
│   ├── auto_discovery.py           # Auto-discovery nowych technologii
│   ├── tech_classifier.py          # Klasyfikacja 200+ technologii
│   ├── concept_manager.py          # Unified interface (static + dynamic)
│   ├── learning_graph.py           # Dependency graph & pathfinding
│   ├── recommendation_engine.py    # Aktywne sugestie
│   ├── update_progress.py          # Main orchestrator
│   ├── session_start.py            # Welcome message hook
│   └── track_practice.py           # PostToolUse hook
│
├── commands/                       # Komendy
│   ├── learn.md                    # /learn - status trybu nauczania
│   ├── progress.md                 # /progress - dashboard postępów
│   ├── review.md                   # /review - przegląd nauki
│   └── track-concepts.md           # /track-concepts - manual rescan
│
└── prompts/                        # Prompty
    └── learning_mindset.md         # Główny prompt uczący
```

### Flow Diagram

```
User Code → PostToolUse Hook → practice_log.jsonl
                                      ↓
SessionStart Hook → update_progress.py orchestrator:
                    ├─→ concept_detector.py (static patterns)
                    ├─→ auto_discovery.py (dynamic discovery)
                    ├─→ concept_manager.py (merge static + dynamic)
                    ├─→ learning_graph.py (dependencies)
                    ├─→ recommendation_engine.py (suggestions)
                    └─→ learning_progress.json (save)
                                      ↓
                         Welcome Message (statystyki, sugestie)
```

---

## 🎯 Kluczowe Funkcje

### 1. **Static Knowledge Base** (45 konceptów)

Predefiniowane koncepty specyficzne dla projektu Sight:
- **Backend** (6): FastAPI Routing, SQLAlchemy Async, Redis Caching, Service Layer, Event Sourcing
- **Frontend** (8): React Components, React Hooks, TanStack Query, Tailwind CSS, i18n
- **AI/ML** (7): LangChain Chains, RAG, Graph RAG, Vector Search, Embeddings
- **Database** (5): SQLAlchemy Models, Alembic Migrations, Neo4j
- **DevOps** (5): Docker Compose, Multi-stage Builds, Cloud Run, CI/CD
- **Testing** (3): Pytest Basics, Fixtures, Asyncio

### 2. **Auto-Discovery Engine** (∞ konceptów)

Automatycznie wykrywa WSZYSTKIE technologie które używasz:

**Źródła:**
- **File extensions**: `.rs` → Rust, `.vue` → Vue, `.go` → Go, `.swift` → Swift
- **Config files**: `Dockerfile`, `k8s.yaml`, `nginx.conf`, `terraform.tf`
- **Imports** (future): `import pandas`, `from flask import`, `use tokio::`
- **Package managers** (future): `requirements.txt`, `package.json`, `Cargo.toml`
- **Bash commands** (future): `npm install axios`, `pip install requests`

**Output**: `dynamic_concepts.json` - auto-generated concepts

**Confidence Scoring**: 0.3 - 0.95 (based on frequency, source diversity)

### 3. **Tech Classifier** (200+ technologii)

Baza znanych technologii z klasyfikacją:
- **Frameworks**: React, Vue, Angular, Svelte, FastAPI, Django, Express, NestJS, Spring, Laravel
- **Libraries**: Axios, Pandas, NumPy, LangChain, Redux, Lodash
- **Databases**: PostgreSQL, MongoDB, Redis, Neo4j, Cassandra, Elasticsearch
- **DevOps**: Docker, Kubernetes, Terraform, Ansible, Jenkins, GitLab
- **Testing**: Pytest, Jest, Cypress, Playwright, Selenium
- **Languages**: Python, JavaScript, TypeScript, Rust, Go, Java, Kotlin, Swift, Ruby, PHP
- **AI/ML**: TensorFlow, PyTorch, Scikit-learn, Hugging Face, OpenAI, Anthropic

Jeśli technologia nie jest w bazie → **heurystyczna klasyfikacja** (keywords, patterns)

### 4. **Concept Detector**

Pattern matching na 3 poziomach:
1. **File paths**: `app/api/*.py` → FastAPI, `frontend/src/**/*.tsx` → React
2. **Code regex** (future): `@router.post`, `useState`, `async def`
3. **Bash commands** (future): `docker-compose up`, `kubectl apply`

**Confidence**: 0.7 - 1.0 (exact match = 1.0, fuzzy = 0.7-0.9)

### 5. **Learning Graph** (Dependency Graph)

**Graf zależności**:
```
python_basics → fastapi_routing → fastapi_async
                                 ↘ fastapi_dependencies

http_basics → fastapi_routing

langchain_chains → langchain_agents
                 ↘ langgraph
```

**Algorytmy:**
- `get_available_next_steps()` - co możesz uczyć się dalej (prerequisites spełnione)
- `get_learning_path(from, to)` - BFS pathfinding między konceptami
- `get_prerequisite_tree()` - drzewo prerequisites
- `calculate_readiness()` - ile % prerequisites masz

### 6. **Recommendation Engine**

**Priorytetyzacja sugestii:**
1. Ready vs not ready (gotowe pierwsze)
2. Category preference (jeśli ustawione w config)
3. Recent activity (co robił ostatnio)
4. Difficulty (nie za duży skok)
5. Readiness score

**Generowanie uzasadnień:**
- "Opanowałeś FastAPI Routing, to naturalny następny krok"
- "Wymaga 2 więcej prerequisitów. Kontynuuj naukę podstaw."
- "Rozszerz swoje umiejętności w Backend"

### 7. **Mastery Levels** (1-5)

```
1 (Beginner):     1-3 praktyki
2 (Intermediate): 4-8 praktyk
3 (Proficient):   9-15 praktyk  ← MASTERED
4 (Advanced):     16-30 praktyk
5 (Expert):       30+ praktyk
```

**Decay**: Brak praktyki przez 30 dni → -1 level (forget curve)

### 8. **Spaced Repetition**

Intervals: **1, 3, 7, 14, 30 dni**

```
Mastery 1 → Review after 1 day
Mastery 2 → Review after 3 days
Mastery 3 → Review after 7 days
Mastery 4 → Review after 14 days
Mastery 5 → Review after 30 days
```

Pokazuje w welcome message:
```
🔁 Do Powtórki (Spaced Repetition):
   🟢 FastAPI Routing (poziom 3, 7 dni temu)
   🟡 React Hooks (poziom 2, 14 dni temu)
```

### 9. **Category Progress Tracking**

Śledzi postęp w każdej kategorii:
```json
{
  "Backend": {
    "total_concepts": 12,
    "detected": 8,
    "mastered": 5,
    "in_progress": 3,
    "progress": 0.42
  }
}
```

---

## ⚙️ Jak Działa

### SessionStart (Każda Sesja)

1. User uruchamia Claude Code
2. **SessionStart hook** triggeruje → `session_start_wrapper.sh` → `session_start.py`
3. `session_start.py`:
   - Load progress, config, knowledge_base
   - Update session count & streak
   - Get concepts to review (spaced repetition)
   - Generate daily goals
   - Show welcome message

**Output:**
```
🎓 SESJA UCZENIA #8

Twoje Statystyki:
- 🔥 Passa: 3 dni pod rząd
- 📊 Opanowane koncepty: 12/45
- 🎯 Obecny focus: Backend (FastAPI + PostgreSQL)

Dzisiejsze Cele:
  ✍️ Pisz kod z TODO(human) - praktyka czyni mistrza
  💡 Pytaj 'dlaczego' gdy coś jest niejasne

Do Powtórki (Spaced Repetition):
  🟢 FastAPI Routing (poziom 3, 7 dni temu)
```

### PostToolUse (Każda Akcja)

1. User edytuje plik / uruchamia command
2. **PostToolUse hook** triggeruje → `track_practice.py`
3. `track_practice.py`:
   - Kategoryzuje akcję (file_create, file_edit, test_run, git_operation, bash_command)
   - Ekstrauje kontekst (file path, type)
   - Loguje do `practice_log.jsonl`

**practice_log.jsonl:**
```json
{"timestamp": "2025-11-02T10:30:00", "tool": "Write", "action": "file_create", "context": {"type": "service", "file": "app/services/personas/persona_service.py"}}
{"timestamp": "2025-11-02T10:35:00", "tool": "Edit", "action": "file_edit", "context": {"type": "api_endpoint", "file": "app/api/projects.py"}}
{"timestamp": "2025-11-02T10:40:00", "tool": "Bash", "action": "test_run", "context": {"type": "test", "file": "tests/unit/test_persona.py"}}
```

### Manual Update (`/track-concepts`)

1. User wywołuje `/track-concepts` (lub automatic w SessionStart jeśli enabled)
2. `update_progress.py` orchestrator:
   - Load practice_log, knowledge_base, dynamic_concepts, progress, config
   - **Concept Detector**: Wykryj koncepty z practice log (static patterns)
   - **Auto-Discovery**: Wykryj nowe technologie (dynamic)
   - **Concept Manager**: Merge static + dynamic
   - **Learning Graph**: Build dependency graph
   - **Recommendation Engine**: Generate suggestions
   - Update learning_progress.json
   - Save

**Output:**
```
✅ Koncepty zaktualizowane!
   📊 Wykryte: 15 konceptów
   🔄 Zaktualizowane: 8 konceptów
   💡 Rekomendacje: 5 sugestii
   📂 Kategorie: 6 kategorii
```

---

## 📂 Struktura Plików

### `data/knowledge_base.json`

```json
{
  "concepts": {
    "fastapi_routing": {
      "name": "FastAPI Routing",
      "category": "Backend",
      "subcategory": "Web Framework",
      "difficulty": 2,
      "patterns": [
        {"type": "code", "regex": "@router\\.(get|post|put|delete)"},
        {"type": "file", "path": "app/api/*.py"}
      ],
      "prerequisites": ["python_basics"],
      "next_steps": ["fastapi_dependencies", "fastapi_async"],
      "resources": ["https://fastapi.tiangolo.com/tutorial/routing/"]
    }
  },
  "categories": {
    "Frontend": {
      "description": "Frontend development z React, TypeScript, styling",
      "subcategories": ["React", "TypeScript", "Styling", "State Management"]
    }
  }
}
```

### `data/dynamic_concepts.json`

```json
{
  "svelte_framework": {
    "name": "Svelte Framework",
    "category": "Frontend",
    "subcategory": "Framework",
    "difficulty": 2,
    "patterns": [{"type": "file", "path": "**/*.svelte"}],
    "prerequisites": [],
    "next_steps": [],
    "resources": [],
    "auto_discovered": true,
    "discovery_metadata": {
      "first_seen": "2025-11-02T10:00:00",
      "last_seen": "2025-11-02T15:30:00",
      "discovery_count": 5,
      "sources": ["File extension: .svelte"],
      "confidence": 0.85
    }
  }
}
```

### `data/learning_progress.json`

```json
{
  "sessions": 8,
  "streak_days": 3,
  "last_session": "2025-11-02T10:00:00",
  "concepts": {
    "fastapi_routing": {
      "name": "FastAPI Routing",
      "category": "Backend",
      "mastery_level": 4,
      "confidence": 0.95,
      "practice_count": 20,
      "first_practiced": "2025-10-15T09:00:00",
      "last_practiced": "2025-11-01T14:30:00",
      "next_review": "2025-11-15T00:00:00",
      "evidence": [
        {"file": "app/api/projects.py", "timestamp": "..."},
        {"file": "app/api/personas.py", "timestamp": "..."}
      ],
      "unique_files": ["app/api/projects.py", "app/api/personas.py", "app/api/focus_groups.py"]
    }
  },
  "categories_progress": {
    "Backend": {
      "total_concepts": 12,
      "detected": 8,
      "mastered": 5,
      "in_progress": 3,
      "progress": 0.42
    }
  },
  "current_focus": {
    "category": "Backend",
    "active_concepts": ["fastapi_async", "sqlalchemy_relationships"]
  },
  "recommendations": {
    "generated_at": "2025-11-02T10:00:00",
    "next_steps": [
      {
        "concept_id": "fastapi_dependencies",
        "name": "FastAPI Dependencies",
        "category": "Backend",
        "difficulty": 3,
        "ready": true,
        "reason": "Opanowałeś FastAPI Routing, to naturalny następny krok",
        "priority": 1
      }
    ]
  }
}
```

### `data/practice_log.jsonl`

```jsonl
{"timestamp": "2025-11-02T10:30:00", "tool": "Write", "action": "file_create", "context": {"type": "service", "file": "app/services/personas/persona_service.py"}}
{"timestamp": "2025-11-02T10:35:00", "tool": "Edit", "action": "file_edit", "context": {"type": "api_endpoint", "file": "app/api/projects.py"}}
```

### `data/config.json`

```json
{
  "auto_tracking": {
    "enabled": true,
    "run_on_session_start": true,
    "min_confidence": 0.7
  },
  "spaced_repetition": {
    "enabled": true,
    "intervals_days": [1, 3, 7, 14, 30]
  },
  "recommendations": {
    "enabled": true,
    "max_suggestions": 5,
    "prefer_category": null
  },
  "ui": {
    "show_ai_summary": true,
    "progress_bar_style": "blocks",
    "max_recent_activities": 5
  }
}
```

---

## 🛠️ Komendy

### `/learn` - Status Trybu Nauczania

```
🎓 Status Trybu Nauczania

🔥 Na fali!
- Sesja: #8
- Passa: 3 dni pod rząd
- Focus: Backend (FastAPI + PostgreSQL)

Co robi ten plugin?
1. Obserwuje Twoją pracę
2. Wyjaśnia dlaczego coś działa
3. Pozostawia TODO(human)
4. Śledzi postęp i przypomina o powtórkach

Dostępne komendy: /progress, /review, /track-concepts

Status: ✅ Aktywny
```

### `/progress` - Dashboard Postępów

```
📊 DASHBOARD POSTĘPÓW

🎯 Twoje Statystyki
- Sesje programowania: 8
- Passa dni: 🔥 3 dni pod rząd
- Opanowane koncepty: 12/45

📈 Twoja Aktywność
Całkowita liczba akcji: 127

- ✏️ Edycja pliku: 85
- 📝 Utworzenie pliku: 30
- 🧪 Uruchomienie testów: 10
- 🔀 Operacja Git: 2

🎓 Ścieżki Nauki
Backend: ████████░░ 80% (8/10)
Frontend: ██░░░░░░░░ 20% (1/5)
AI/ML: █████░░░░░ 50% (3/6)

⏱️ Ostatnia Aktywność
- 2025-11-02 10:40 - 🧪 Uruchomienie testów → tests/unit/test_persona.py
- 2025-11-02 10:35 - ✏️ Edycja pliku → app/api/projects.py
```

### `/review [today|week]` - Przegląd Nauki

```
📝 PRZEGLĄD NAUKI (Dzisiaj)

📊 Statystyki:
- 18 akcji (12 edits, 5 creates, 1 test)
- 8 plików edytowanych
- 3 koncepty ćwiczone: FastAPI Routing, SQLAlchemy Async, Redis Caching

🎯 Obszary:
Backend: ████████░░ (14 akcji)
AI/ML: ███░░░░░░░ (4 akcje)

📂 Top Pliki:
1. app/services/personas/persona_service.py (5 edits)
2. app/api/projects.py (4 edits)
3. app/models/persona.py (3 edits)

💪 Trzymaj tempo! Każda sesja to krok w stronę mistrzostwa.
```

### `/track-concepts [--force]` - Manual Rescan

```
🔍 Skanowanie practice log i aktualizacja konceptów...

✅ Koncepty zaktualizowane!
   📊 Wykryte: 15 konceptów
   🔄 Zaktualizowane: 8 konceptów
   💡 Rekomendacje: 5 sugestii
   📂 Kategorie: 6 kategorii

Użyj /learn aby zobaczyć szczegóły
```

---

## 🎓 Knowledge Base

### Struktura Konceptu

```json
{
  "name": "Concept Name",
  "category": "Backend|Frontend|AI/ML|Database|DevOps|Testing|Programming Languages|Mobile|Data Science|Security|Other",
  "subcategory": "Specific subcategory",
  "difficulty": 1-5,
  "patterns": [
    {"type": "code", "regex": "pattern"},
    {"type": "file", "path": "glob pattern"},
    {"type": "bash", "regex": "command pattern"}
  ],
  "prerequisites": ["concept_id1", "concept_id2"],
  "next_steps": ["concept_id3", "concept_id4"],
  "resources": ["URL1", "URL2"]
}
```

### Dodawanie Nowych Konceptów

**Ręcznie** (do `knowledge_base.json`):
```json
{
  "custom_concept": {
    "name": "My Custom Technology",
    "category": "Backend",
    "subcategory": "Custom",
    "difficulty": 3,
    "patterns": [
      {"type": "file", "path": "my_custom/**/*.ext"}
    ],
    "prerequisites": [],
    "next_steps": [],
    "resources": []
  }
}
```

**Automatycznie** (auto-discovery):
- Użyj technologii w kodzie
- System sam wykryje i doda do `dynamic_concepts.json`
- Jeśli często używasz (>15 razy, confidence >0.85) → może być promowany do static

---

## 🔍 Auto-Discovery

### Jak Działa

1. **File Extension Detection**:
   - `.rs` → Rust Language
   - `.vue` → Vue Framework
   - `.go` → Go Language
   - `.swift` → Swift Language
   - `.kt` → Kotlin Language

2. **Config File Detection**:
   - `Dockerfile` → Docker
   - `docker-compose.yml` → Docker Compose
   - `k8s.yaml` → Kubernetes
   - `nginx.conf` → Nginx
   - `terraform.tf` → Terraform

3. **Import Detection** (future):
   - `import pandas` → Pandas (Data Science)
   - `from flask import` → Flask (Backend)
   - `use tokio::` → Tokio (Rust async)

4. **Package Manager Detection** (future):
   - `package.json`: npm dependencies
   - `requirements.txt`: pip packages
   - `Cargo.toml`: Rust crates
   - `go.mod`: Go modules

5. **Bash Command Detection** (future):
   - `npm install axios` → Axios
   - `pip install requests` → Requests
   - `cargo add tokio` → Tokio

### Confidence Scoring

```
Formula: min(count * 0.1 + sources_diversity * 0.15, 0.95)

Examples:
- 1 użycie, 1 źródło → confidence = 0.25
- 5 użyć, 2 źródła → confidence = 0.80
- 10 użyć, 3 źródeł → confidence = 0.95 (max)
```

### Promotion to Static

Dynamic concept → Static knowledge_base gdy:
- Confidence >= 0.85
- Practice count >= 15
- Manual: `concept_manager.promote_to_static(concept_id)`

---

## 📊 Dependency Graph

### Przykładowy Graf

```
Backend:
  python_basics → fastapi_routing → fastapi_async
                → fastapi_routing → fastapi_dependencies

  sql_basics → sqlalchemy_models → sqlalchemy_relationships
                                  → sqlalchemy_async

Frontend:
  javascript_basics → react_components → react_hooks → react_custom_hooks
                                                     → react_context

AI/ML:
  llm_basics → langchain_chains → langchain_agents
                                → langgraph

  embeddings_vectors → vector_search → rag_basic → graph_rag
                                                   → hybrid_search
```

### Algorytmy

**get_available_next_steps(mastered_concepts)**:
```
Dla każdego mastered concept:
  Sprawdź next_steps
  Dla każdego next_step:
    Sprawdź czy wszystkie prerequisites są mastered
    Jeśli TAK → dodaj do available
    Jeśli NIE → oblicz readiness % (ile prerequisites masz)

Sortuj: ready pierwsze, potem po readiness %, potem po difficulty
```

**get_learning_path(from, to)**:
```
BFS (Breadth-First Search):
  Queue = [from_concept]
  Visited = {from_concept}

  While queue not empty:
    Current = queue.pop()
    Dla każdego next_step z current:
      Jeśli next_step == to:
        Return path
      Jeśli next_step not visited:
        Add to queue
        Mark visited

Return None (no path found)
```

---

## 💡 Rekomendacje

### Priorytetyzacja

**Kryteria (w kolejności):**
1. **Ready vs not ready** (+10 pts jeśli ready)
2. **Category preference** (+5 pts jeśli pasuje do focus)
3. **Recent activity** (+3 pts jeśli w tej kategorii pracował ostatnio)
4. **Difficulty** (-1 pt per difficulty above 3)
5. **Readiness score** (+2 pts per 100% readiness)

**Example:**
```
Mastered: [python_basics, fastapi_routing, sqlalchemy_models]
Current focus: Backend
Recent activity: Backend (14 akcji), AI/ML (4 akcje)

Recommendations:
  1. ✅ P1 - FastAPI Dependencies (Backend)
     → Ready: True, Focus match: Yes, Recent: Yes, Difficulty: 3
     → Score: 10 + 5 + 3 + 0 + 2 = 20
     → "Opanowałeś FastAPI Routing, to naturalny następny krok"

  2. ✅ P2 - SQLAlchemy Relationships (Database)
     → Ready: True, Focus match: No, Recent: No, Difficulty: 4
     → Score: 10 + 0 + 0 - 1 + 2 = 11
     → "Opanowałeś SQLAlchemy Models, to naturalny następny krok"

  3. ⏳ P3 - LangChain Chains (AI/ML)
     → Ready: False (missing llm_basics), Recent: Yes
     → Score: 0 + 0 + 3 - 0 + 1.5 = 4.5
     → "Wymaga 1 więcej prerequisitów. Kontynuuj naukę podstaw."
```

---

## 🔁 Spaced Repetition

### Intervals

| Mastery Level | Interval |
|---------------|----------|
| 1 (Beginner) | 1 dzień |
| 2 (Intermediate) | 3 dni |
| 3 (Proficient) | 7 dni |
| 4 (Advanced) | 14 dni |
| 5 (Expert) | 30 dni |

### Algorytm

```python
def get_concepts_to_review(progress, config):
    intervals = config["spaced_repetition"]["intervals_days"]
    to_review = []

    for concept_id, data in progress["concepts"].items():
        level = data["mastery_level"]
        last_practiced = data["last_practiced"]

        days_interval = intervals[level - 1]
        days_ago = (datetime.now() - last_practiced).days

        if days_ago >= days_interval:
            to_review.append(concept)

    return to_review[:3]  # Max 3 at once
```

### Forget Curve

Jeśli nie praktykujesz konceptu przez długi czas:
- **30 dni bez praktyki → Mastery level -1**
- Minimum: Mastery level 1 (nigdy nie schodzi poniżej)

---

## ⚙️ Konfiguracja

### `config.json` Options

```json
{
  "auto_tracking": {
    "enabled": true,              // Auto-update progress on SessionStart
    "run_on_session_start": true, // Run update_progress.py automatically
    "min_confidence": 0.7         // Min confidence for concept detection
  },
  "spaced_repetition": {
    "enabled": true,                       // Enable spaced repetition
    "intervals_days": [1, 3, 7, 14, 30]    // Intervals for each mastery level
  },
  "recommendations": {
    "enabled": true,         // Generate recommendations
    "max_suggestions": 5,    // Max suggestions to show
    "prefer_category": null  // Prefer specific category (null = no preference)
  },
  "ui": {
    "show_ai_summary": true,         // Show AI summary in /review (requires GOOGLE_API_KEY)
    "progress_bar_style": "blocks",  // "blocks" | "percentage" | "both"
    "max_recent_activities": 5       // Max activities in /progress
  }
}
```

### Customization

**Zmień intervals:**
```json
{
  "spaced_repetition": {
    "intervals_days": [2, 5, 10, 20, 40]  // Longer intervals
  }
}
```

**Ustaw category preference:**
```json
{
  "recommendations": {
    "prefer_category": "AI/ML"  // Priorytetyzuj AI/ML sugestie
  }
}
```

**Wyłącz auto-tracking:**
```json
{
  "auto_tracking": {
    "enabled": false  // Manual /track-concepts only
  }
}
```

---

## 🔧 Rozszerzanie Systemu

### Dodaj Nowy Koncept (Static)

1. Edytuj `data/knowledge_base.json`
2. Dodaj nowy koncept:
   ```json
   {
     "my_new_concept": {
       "name": "My New Concept",
       "category": "Backend",
       "subcategory": "Custom",
       "difficulty": 3,
       "patterns": [
         {"type": "file", "path": "path/to/files/*.ext"}
       ],
       "prerequisites": ["prerequisite_concept"],
       "next_steps": ["next_concept"],
       "resources": ["https://docs.example.com"]
     }
   }
   ```
3. Save
4. Run `/track-concepts --force` (force rescan)

### Dodaj Nową Kategorię

1. Edytuj `data/knowledge_base.json`
2. Dodaj do `categories`:
   ```json
   {
     "categories": {
       "My Category": {
         "description": "Description",
         "subcategories": ["Sub1", "Sub2"]
       }
     }
   }
   ```

### Rozszerz Tech Classifier

1. Edytuj `scripts/tech_classifier.py`
2. Dodaj do `KNOWN_TECHNOLOGIES`:
   ```python
   "my_tech": ("Category", "Subcategory", "Description"),
   ```

### Custom Auto-Discovery Patterns

1. Edytuj `scripts/auto_discovery.py`
2. Dodaj do `file_ext_map`:
   ```python
   '.myext': 'my_technology',
   ```
3. Lub dodaj do `special_files`:
   ```python
   'myconfig.conf': ('my_tech', 'DevOps', 'Configuration'),
   ```

---

## ❓ FAQ

**Q: Czy muszę ręcznie dodawać każdą technologię?**
A: NIE! System automatycznie wykrywa nowe technologie (auto-discovery). Wystarczy że zaczniesz ich używać.

**Q: Co jeśli technologia nie jest wykryta?**
A: Możesz ją dodać ręcznie do `knowledge_base.json` lub poczekać aż system zbierze więcej danych (confidence threshold).

**Q: Jak często system aktualizuje postęp?**
A: Domyślnie na SessionStart (jeśli `auto_tracking.enabled = true`). Możesz też ręcznie `/track-concepts`.

**Q: Czy mogę wyłączyć spaced repetition?**
A: Tak, ustaw `spaced_repetition.enabled = false` w `config.json`.

**Q: Jak promować dynamic concept do static?**
A: Automatycznie promuje jeśli confidence >= 0.85 i count >= 15. Ręcznie: `concept_manager.promote_to_static(concept_id)`.

**Q: Czy mogę uczyć się czegokolwiek?**
A: TAK! System jest uniwersalny - wykryje Vue, Rust, Kubernetes, GraphQL, cokolwiek.

**Q: Czy practice log jest prywatny?**
A: Tak, wszystkie dane są lokalne w projekcie (`.claude/plugins/learn-by-doing/data/`).

---

## 🐛 Troubleshooting

### Problem: Koncepty nie są wykrywane

**Przyczyna:** Pattern matching może nie pasować do file paths
**Rozwiązanie:**
1. Sprawdź `practice_log.jsonl` - czy file paths są pełne
2. Dodaj custom patterns do `knowledge_base.json`
3. Run `/track-concepts --force` (force rescan)

### Problem: Auto-discovery nie działa

**Przyczyna:** Confidence threshold za wysoki
**Rozwiązanie:**
1. Obniż `min_confidence` w `config.json` (np. 0.5)
2. Użyj technologii więcej razy (>5)
3. Sprawdź `dynamic_concepts.json` - może już jest wykryty

### Problem: Brak rekomendacji

**Przyczyna:** Brak opanowanych konceptów lub wszystkie next_steps nie gotowe
**Rozwiązanie:**
1. Kontynuuj praktykę istniejących konceptów (do mastery 3+)
2. Sprawdź `learning_progress.json` - ile konceptów masz mastered
3. Sprawdź `config.json` - `recommendations.enabled = true`

### Problem: Mastery level nie rośnie

**Przyczyna:** Concept nie jest wykrywany lub practice_count za niski
**Rozwiązanie:**
1. Sprawdź czy file paths pasują do patterns
2. Run `/track-concepts --force`
3. Sprawdź `learning_progress.json` - `practice_count` dla konceptu

### Problem: Session count nie aktualizuje się

**Przyczyna:** `session_start.py` ma error
**Rozwiązanie:**
1. Sprawdź logi: `~/.claude/logs/` (jeśli dostępne)
2. Test ręcznie: `python3 scripts/session_start.py`
3. Sprawdź `learning_progress.json` - czy istnieje

---

## 📈 Roadmap (Future)

- [ ] Import detection (Python, JavaScript, Rust, Go)
- [ ] Package manager parsing (requirements.txt, package.json, etc.)
- [ ] Bash command logging
- [ ] Code snippet analysis (detect patterns in code)
- [ ] AI-powered summaries w `/review`
- [ ] `/concepts` command - lista/filtrowanie
- [ ] `/learn <concept>` - szczegóły konceptu
- [ ] Quiz system - test wiedzy
- [ ] Gamification - badges, achievements
- [ ] Export progress do PDF/markdown
- [ ] Multi-project support
- [ ] Web dashboard (opcjonalnie)

---

## 📝 Changelog

**v2.0 (2025-11-02)**
- ✨ Universal auto-discovery engine
- ✨ Tech classifier (200+ technologies)
- ✨ Dynamic concepts storage
- ✨ Concept manager (static + dynamic merge)
- ✨ Expanded knowledge base (45 concepts → 6 categories)
- ✨ Learning graph & pathfinding
- ✨ Recommendation engine
- ✨ Spaced repetition system
- ✨ Category progress tracking
- ✨ Mastery levels (1-5)
- 🔧 Refactored architecture
- 🔧 Centralized data_manager
- 🔧 Config system
- 📚 Complete documentation

**v1.0 (2025-10-30)**
- Initial release
- Basic tracking
- Simple commands

---

## 🎉 Podsumowanie

**Learn-by-Doing v2.0** to najbardziej zaawansowany system uczenia się dla Claude Code:

✅ **Uniwersalny** - uczy się WSZYSTKIEGO co robisz
✅ **Automatyczny** - zero konfiguracji, po prostu koduj
✅ **Inteligentny** - dependency graph, recommendations, spaced repetition
✅ **Rozszerzalny** - dodaj custom concepts, categories, patterns
✅ **Gamified** - mastery levels, streaks, progress bars

**Zacznij kodować - system zrobi resztę!** 🚀

---

**Pytania? Problemy? Sugestie?**
Otwórz issue lub edytuj `LEARNING_SYSTEM.md`

**Happy Learning! 🎓**
