# 🎓 Learn-by-Doing - Naucz się przez praktykę!

**Universal Learning System v2.2** - Plugin dla Claude Code, który pomaga Ci uczyć się programowania przez praktyczną pracę. Nie ważne czym się zajmujesz - Data Science, Backend, Frontend, czy Machine Learning - plugin automatycznie śledzi Twój postęp i pomaga Ci się rozwijać.

---

## 🚀 Szybki Start (3 minuty)

### Co to jest?

Learn-by-Doing to inteligentny plugin który **automatycznie śledzi** co robisz w Claude Code:
- 📝 Każdą edycję pliku
- ✨ Każdy stworzony plik
- 🧪 Każde uruchomienie testów
- 📦 Każdą używaną bibliotekę

Plugin rozpoznaje co się uczysz (np. React, FastAPI, pandas) i **przypomina Ci o powtórkach** zgodnie ze spaced repetition (1, 3, 7, 14, 30 dni).

### Instalacja

Plugin jest już zainstalowany! Wystarczy że:

1. Otworzysz Claude Code w dowolnym projekcie
2. Zobaczysz welcome message przy starcie sesji
3. Zaczniesz pracować - plugin automatycznie śledzi

Dane są przechowywane globalnie w `~/.claude/learn-by-doing/` - plugin działa **we wszystkich Twoich projektach**.

### Pierwsze Kroki

```bash
# 1. Sprawdź status
/learn

# 2. Wybierz dziedzinę (np. Data Science)
/learn data-science

# 3. Pracuj normalnie - plugin automatycznie śledzi!
# Edytujesz plik z pandas? Plugin to zauważy.
# Uruchamiasz testy? Również zanotuje.

# 4. Po kilku sesjach sprawdź postęp
/progress

# 5. Sprawdź wiedzę quizem
/quiz
```

To wszystko! Plugin działa w tle i uczy Cię przez praktykę.

---

## 🎯 Główne Funkcje

### 1. Automatic Tracking - Śledzi Wszystko

Plugin automatycznie zauważa:

**Edycje plików:**
- Serwisy (`app/services/*.py`) → koncepty Backend
- API endpoints (`app/api/*.py`) → FastAPI routing
- Komponenty React (`*.tsx`, `*.jsx`) → Frontend
- Testy (`tests/**/*.py`) → Testing

**Używane biblioteki:**
- Python: `import pandas` → "pandas basics"
- JavaScript: `import React from 'react'` → "React components"
- TypeScript: `import { useState } from 'react'` → "React hooks"

**Komendy bash:**
- `pytest` → uruchomienie testów
- `git commit` → operacje git
- `docker-compose up` → Docker

**Co zapisuje:**
- Timestamp (UTC)
- Typ akcji (file_edit, file_create, test_run)
- Pełna ścieżka pliku
- Wykryte biblioteki

Wszystko trafia do `practice_log.jsonl` i jest automatycznie przetwarzane.

---

### 2. Auto-Discovery - Wykrywa 200+ Technologii

System automatycznie rozpoznaje co używasz:

**Frontend Frameworks:**
React, Vue, Angular, Svelte, Solid, Preact, Next.js, Nuxt, SvelteKit

**Backend Frameworks:**
FastAPI, Django, Flask, Express, NestJS, Spring Boot, Laravel, Ruby on Rails, Gin (Go)

**Data Science & ML:**
pandas, numpy, scipy, matplotlib, seaborn, scikit-learn, TensorFlow, PyTorch, Keras, LangChain, Hugging Face

**Databases:**
PostgreSQL, MySQL, MongoDB, Redis, Neo4j, Elasticsearch, Cassandra

**DevOps:**
Docker, Kubernetes, Terraform, Ansible, Jenkins, GitHub Actions, GitLab CI

**Testing:**
pytest, Jest, Cypress, Playwright, Selenium, Mocha, Vitest

**Languages:**
Python, JavaScript, TypeScript, Rust, Go, Java, Kotlin, Swift, Ruby, PHP, C++, C#

**Plus wszystko inne** - jeśli użyjesz nierozpoznanej technologii, plugin doda ją do auto-discovered concepts!

---

### 3. Multi-Domain Support - Ucz Się Wielu Rzeczy Naraz

Plugin wspiera **wiele dziedzin równocześnie**. Masz 5 gotowych szablonów:

**📊 Data Science** (`/learn data-science`)
- pandas (analizadanych)
- numpy (obliczenia numeryczne)
- matplotlib, seaborn (wizualizacja)
- scikit-learn (machine learning)
- scipy, statsmodels (statystyka)

**🏗️ System Design** (`/learn system-design`)
- Scalability (skalowanie systemów)
- Databases (bazy danych)
- Caching (Redis, Memcached)
- Load Balancing (rozpraszanie obciążenia)
- Microservices (architektura)

**🧮 Mathematics** (`/learn mathematics`)
- Linear Algebra (algebra liniowa)
- Calculus (rachunek różniczkowy)
- Statistics (statystyka)
- Probability (prawdopodobieństwo)
- Optimization (optymalizacja)

**🤖 Machine Learning** (`/learn machine-learning`)
- Supervised Learning (uczenie nadzorowane)
- Unsupervised Learning (uczenie nienadzorowane)
- Deep Learning (głębokie sieci)
- Neural Networks (sieci neuronowe)
- Transformers, BERT, GPT

**📐 Algorithms** (`/learn algorithms`)
- Sorting & Searching (sortowanie, wyszukiwanie)
- Graphs (grafy, DFS, BFS)
- Trees (drzewa binarne, AVL)
- Dynamic Programming (programowanie dynamiczne)
- Greedy Algorithms

**Custom Domains:**
Możesz też stworzyć własną dziedzinę:
```bash
/learn "Quantum Computing"
```

Plugin będzie śledzić wszystko co robisz w tym temacie i automatycznie wykrywać używane narzędzia.

---

### 4. Spaced Repetition - Przypomina o Powtórkach

System używa techniki **spaced repetition** aby pomóc Ci zapamiętać to czego się uczysz.

**Mastery Levels (1-5):**
- **Level 1 (Beginner)** - dopiero zaczynasz, powtórz po 1 dniu
- **Level 2 (Intermediate)** - trochę umiesz, powtórz po 3 dniach
- **Level 3 (Proficient)** - **MASTERED!** - opanowałeś, powtórz po 7 dniach
- **Level 4 (Advanced)** - ekspert, powtórz po 14 dniach
- **Level 5 (Expert)** - mistrz, powtórz po 30 dniach

**Jak działa:**
1. Używasz pandas pierwszy raz → Level 1
2. Pracujesz z pandas przez kilka dni → Level 2
3. Regularnie praktyku jesz → Level 3 (MASTERED!)
4. Kontynuujesz → Level 4, 5

System przypomni Ci w welcome message:
```
Do Powtórki (Spaced Repetition):
  📅 pandas basics (7 dni temu) - czas powtórzyć!
  📅 React hooks (14 dni temu) - czas powtórzyć!
```

---

### 5. Quiz System - Sprawdź Swoją Wiedzę

Plugin generuje quizy z **konceptów które faktycznie praktykował eś**:

```bash
/quiz              # Quiz z aktywnej dziedziny
/quiz data-science # Quiz z konkretnej dziedziny
```

**Typy pytań:**

**Multiple Choice:**
```
Q: Co powinieneś znać PRZED nauką FastAPI Async?
A) FastAPI Routing ✅
B) React Components
C) Docker Compose
D) Kubernetes
```

**True/False:**
```
Q: FastAPI Routing jest używany w kategorii Backend
A) Prawda ✅
B) Fałsz
```

**Kategoria:**
```
Q: Do jakiej kategorii należy React Hooks?
A) Frontend ✅
B) Backend
C) Database
D) DevOps
```

Pytania są generowane z `knowledge_base.json` i uwzględniają:
- Prerequisites (co musisz znać wcześniej)
- Next steps (co uczyć się potem)
- Kategorie
- Use cases

Po quizie możesz zobaczyć odpowiedzi:
```bash
/quiz --show-answers
```

---

### 6. Progress Dashboard - Zobacz Swój Postęp

```bash
/progress
```

Zobaczysz:

**Global Statistics:**
- ⭐ **Passa:** 5 dni pod rząd
- 📊 **Sesje:** 47 sesji uczenia
- 📈 **Koncepty:** 12/48 opanowanych (25%)

**Progress per Domena:**
```
📊 Data Science: ████████░░░░ 66% (4/6)
   pandas basics ✅, numpy arrays ✅, matplotlib ✅, sklearn 🔄

🏗️ System Design: ███░░░░░░░░░ 25% (2/8)
   caching ✅, load-balancing ✅, microservices 📝

🤖 Software Engineering: ████░░░░░░░░ 33% (16/48)
   FastAPI ✅, React ✅, SQLAlchemy ✅, Docker ✅...
```

**Category Breakdown:**
- Backend: 6/10 (60%)
- Frontend: 4/8 (50%)
- Database: 2/5 (40%)

**Recent Activity:**
- Dzisiaj: 3 koncepty praktykowane
- Ten tydzień: 8 konceptów
- Ten miesiąc: 15 konceptów

---

### 7. Smart Recommendations - Co Uczyć Się Dalej?

System analizuje:
1. **Co już opanowałeś** (mastery level >= 3)
2. **Dependency graph** - jakie koncepty wymagają prerequisites
3. **Twoje ostatnie praktyki** - co Cię interesuje
4. **Category balance** - równomierne rozłożenie nauki

I sugeruje **co uczyć się dalej**:

```
💡 Rekomendacje:

1. FastAPI Async (Backend)
   Dlaczego: Opanowałeś FastAPI Routing, to naturalny następny krok
   Readiness: ████████████ 100%

2. React Hooks (Frontend)
   Dlaczego: Masz React Components, hooks to fundament
   Readiness: ████████████ 100%

3. SQLAlchemy Relationships (Database)
   Dlaczego: Znasz SQLAlchemy Models, relationships to zaawansowane użycie
   Readiness: ████████░░░░ 80%
```

Rekomendacje są **priorytetyzowane**:
- Koncepty z 100% readiness (wszystkie prerequisites opanowane) są na górze
- Kategorie które ostatnio praktykowałeś mają wyższy priorytet
- Możesz ustawić `prefer_category` w config.json

---

## 📚 Komendy

### Zarządzanie Dziedzinami

| Komenda | Opis | Przykład |
|---------|------|----------|
| `/learn` | Pokaż wszystkie dziedziny + status | `/learn` |
| `/learn <szablon>` | Dodaj dziedzinę z szablonu | `/learn data-science` |
| `/learn "<nazwa>"` | Dodaj custom dziedzinę | `/learn "Quantum Computing"` |
| `/learn --list` | Lista wszystkich dziedzin | `/learn --list` |
| `/learn --active <id>` | Zmień aktywną dziedzinę | `/learn --active data-science` |
| `/learn --remove <id>` | Usuń dziedzinę | `/learn --remove mathematics` |

### Monitor owanie Postępu

| Komenda | Opis |
|---------|------|
| `/progress` | Dashboard - postęp per domena + globalne statystyki |
| `/review` | Przegląd nauki (dzisiaj / tydzień / miesiąc) |
| `/concepts` | Lista wszystkich konceptów (static + discovered) |
| `/track-concepts` | Manualne skanowanie practice log i update progress |

### Quizy

| Komenda | Opis |
|---------|------|
| `/quiz` | Quiz z aktywnej dziedziny |
| `/quiz <domena>` | Quiz z konkretnej dziedziny |
| `/quiz --show-answers` | Pokaż odpowiedzi na ostatni quiz (learning mode) |

---

## ⚙️ Konfiguracja

Plik: `~/.claude/learn-by-doing/config.json`

```json
{
  "enabled": true,

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
    "prefer_category": null  // lub "Backend", "Frontend", etc.
  },

  "log_rotation": {
    "max_practice_log_entries": 1000,
    "archive_enabled": true
  },

  "ui": {
    "show_ai_summary": true,
    "progress_bar_style": "blocks",
    "max_recent_activities": 5
  }
}
```

**Ważne ustawienia:**

- `auto_tracking.enabled` - włącz/wyłącz automatyczne śledzenie
- `spaced_repetition.intervals_days` - odstępy między powtórkami
- `recommendations.prefer_category` - priorytetuj kategorię (np. "Backend")
- `log_rotation.max_practice_log_entries` - limit wpisów przed archiwizacją

---

## 🔧 Jak To Działa?

### Workflow

1. **Tracking** - plugin śledzi każdą akcję (PostToolUse hook)
2. **Detection** - wykrywa koncepty z practice log (pattern matching)
3. **Progress Update** - aktualizuje mastery levels
4. **Graph Analysis** - buduje dependency graph
5. **Recommendations** - sugeruje co uczyć się dalej

### Architektura

**Data Storage** (`~/.claude/learn-by-doing/`):
```
config.json                    # Konfiguracja
user_learning_domains.json     # Twoje dziedziny
learning_progress.json          # Postęp (sessions, streak, concepts)
practice_log.jsonl              # Historia akcji (max 1000 wpisów)
knowledge_base.json             # 48 predefiniowanych konceptów
dynamic_concepts.json           # Auto-discovered koncepty
archives/                       # Archiwum starych logów
  practice_log_archive_2025-11-02.jsonl
```

**Key Services:**
- `track_practice.py` - śledzi akcje (PostToolUse hook)
- `concept_detector.py` - wykrywa koncepty (pattern matching)
- `learning_graph.py` - buduje dependency graph
- `recommendation_engine.py` - generuje sugestie
- `quiz_generator.py` - tworzy quizy

---

## ❓ FAQ

**Q: Skąd system wie czego się uczę?**
A: Z Twojej praktyki! Wykrywa importy (`import pandas`), file paths (`app/api/*.py`), config files (`Dockerfile`), i komendy bash (`pytest`).

**Q: Czy mogę uczyć się kilku dziedzin naraz?**
A: Tak! Możesz mieć Data Science + System Design + Software Engineering równocześnie. Plugin śledzi wszystko.

**Q: Co jeśli zapomniałem o pojęciu?**
A: System przypomni Ci w welcome message (Spaced Repetition). Możesz też zrobić `/quiz` aby sprawdzić wiedzę.

**Q: Czy dane są synchronizowane między projektami?**
A: Tak! Dane są w `~/.claude/learn-by-doing/` - plugin działa we wszystkich projektach.

**Q: Jak wyłączyć plugin?**
A: Ustaw `"enabled": false` w `config.json`.

---

## 🎓 Przykład: Nauka Data Science

```bash
# Dzień 1: Setup
/learn data-science

# Pracujesz z pandas
# Tworzysz: data_analysis.py
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')
df.head()

# Plugin automatycznie wykrywa:
# ✅ pandas → "pandas basics" (Level 1)
# ✅ numpy → "numpy arrays" (Level 1)

# Dzień 2: Kontynuujesz
# Pracujesz dalej z pandas, matplotlib
import matplotlib.pyplot as plt

plt.plot(df['x'], df['y'])
plt.show()

# Plugin aktualizuje:
# ✅ pandas → Level 2
# ✅ matplotlib → "visualization" (Level 1)

# Dzień 3: Progress
/progress
# Output:
# 📊 Data Science: ████░░░░░░ 40% (2/5)
#    pandas basics 🔄, numpy arrays 🔄

# Dzień 7: Quiz
/quiz
# Pytanie: Co to jest pandas DataFrame?
# A) Struktura danych 2D ✅
# B) Neural network
# C) Sorting algorithm

# Miesiąc później:
/progress
# 📊 Data Science: ████████░░ 80% (4/5)
#    pandas ✅ (Level 3 - MASTERED!)
#    numpy ✅ (Level 3)
#    matplotlib ✅ (Level 3)
#    sklearn 🔄 (Level 2)
```

---

## 🚀 Co Dalej?

1. **Pracuj regularnie** - plugin automatycznie śledzi
2. **Sprawdzaj `/progress`** - co tydzień zobacz postęp
3. **Róbquizy** - `/quiz` co 5 sesji
4. **Dodaj więcej dziedzin** - `/learn system-design`, `/learn algorithms`
5. **Wykorzystaj recommendations** - system podpowie co uczyć się dalej

---

## 📦 Changelog

**v2.2.0 (2025-11-02)** - Final Improvements
- ✨ Quiz generator: Inteligentne pytania z knowledge_base
- ✨ Import detection: JavaScript/TypeScript support
- ✨ Testy: 20 nowych testów (recommendation_engine, learning_graph)

**v2.1.0 (2025-11-02)** - Bug Fixes
- 🔧 Fixed: track_practice zachowuje pełne ścieżki plików
- 🔧 Fixed: UTC timestamps (7 plików)
- ✨ New: Log rotation z archiwizacją

**v2.0 (2025-11-02)** - Universal Learning System
- ✨ Auto-discovery (200+ technologii)
- ✨ Multi-domain support
- ✨ Spaced repetition
- ✨ Smart recommendations

Więcej w [CHANGELOG.md](CHANGELOG.md).

---

**Happy Learning! 🎓**

Plugin działa globalnie - we wszystkich projektach. Ucz się dowolnej dziedziny przez praktykę!
