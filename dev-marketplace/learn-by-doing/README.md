# 🎓 Learn-by-Doing Plugin v3.0

**AI-asystent nauczania** dla Claude Code - ucz się przez praktykę z kursami generowanymi przez AI. Plugin wspiera **naturalną komunikację** i automatyczne tworzenie kursów.

## ✨ Nowości w v3.1

- 🔄 **Uproszczone Dziedziny** - 8 dziedzin z ikonami i kolorami
- 📚 **Rozszerzona Course Library** - 9 gotowych kursów wysokiej jakości
- 🗣️ **Komunikacja Naturalna** - mów co chcesz, bez komend slash
- 🤖 **Automatyczne Kursy** - Claude proponuje kursy na podstawie Twojej pracy
- 🎯 **Lepszy System Dziedzin** - dziedziny z ikonami, kolorami i możliwością dodawania własnych

---

## 🚀 Szybki Start

### Komunikacja - Mów Naturalnie!

Możesz komunikować się z pluginem na dwa sposoby:

**1. Naturalny język** (ZALECANE):
```
"Chcę dodać dziedzinę Security"
"Stwórz kurs o Docker networking"
"Jak idą moje postępy?"
"Zrób quiz z backendu"
"done" (po ukończeniu lekcji)
```

**2. Komendy slash** (skróty):
```bash
/learn "Redis caching"
/progress
/quiz backend
```

### Pierwsze Kroki

**1. Zobacz dostępne dziedziny:**
```
"Pokaż dziedziny"
lub: /learn --domains
```

**Dziedziny (8):**
- 💻 **Software Engineering** - Full-stack, API, databases, DevOps, testing, security
- 🤖 **AI & Machine Learning** - LLM, RAG, prompt engineering, embeddings
- ☁️ **Cloud & Infrastructure** - GCP, AWS, serverless, containers
- 📊 **Data Science** - Analiza danych, wizualizacja, ML
- 🏗️ **System Design** - Projektowanie skalowalnych systemów
- 📐 **Mathematics** - Matematyka dla programistów
- ⚡ **Algorithms** - Algorytmy i struktury danych
- 🧪 **Testing** - Pytest, integration testing, quality assurance

**2. Rozpocznij kurs:**
```
"Stwórz kurs o Redis caching"
```

Claude:
1. Przeanalizuje cel (wykryje intent `create_course`)
2. Znajdzie koncepty z knowledge base (80+ konceptów!)
3. Wygeneruje plan 3-5 lekcji
4. Zapisze jako aktywny kurs

**3. Kontynuuj naukę:**
```
"kontynuuj"
lub: /learn continue
```

Otrzymasz:
- 💡 **Teoria** - wyjaśnienie konceptu
- 🛠️ **TODO(human)** - praktyczne zadanie
- 🔍 **Podpowiedź** - jak podejść do problemu

**4. Po ukończeniu lekcji:**
```
"done"
```

Claude zaloguje postęp i pokaże następną lekcję.

**5. Sprawdź postępy:**
```
"Jak idą moje postępy?"
lub: /progress
```

Dashboard pokazuje:
- 🔥 Streak (dni nauki)
- 📊 Progress per dziedzina
- 🎯 Top practiced concepts
- 📅 Heatmapa aktywności (28 dni)

---

## 📚 Course Library - Gotowe Kursy

Nie chcesz tworzyć kursu? Wybierz z biblioteki:

```
"Pokaż dostępne kursy"
lub: /learn --library
```

**9 gotowych kursów:**

### 💻 Software Engineering
1. **backend-onboarding** (3 lekcje, ~3.5h, beginner) 🌟
   - FastAPI Routing, Dependency Injection, SQLAlchemy Async

2. **full-stack-essentials** (3 lekcje, ~4.5h, intermediate)
   - React + FastAPI + Database essentials

3. **testing-quality** (3 lekcje, ~3.6h, intermediate)
   - pytest, async testing, fixtures

### 🤖 AI & Machine Learning
4. **ai-ml-mastery** (5 lekcji, ~7.5h, intermediate)
   - LangChain, Gemini API, Prompt Engineering, RAG

### ☁️ Cloud & Infrastructure
5. **database-deep-dive** (4 lekcje, ~6.4h, advanced)
   - PostgreSQL Advanced, Neo4j, Cypher

### 📊 Data Science
6. **data-science-foundations** (4 lekcje, ~5h, beginner) 🆕
   - Pandas, NumPy, Matplotlib, Stats basics

### 🏗️ System Design
7. **system-design-essentials** (4 lekcje, ~6h, intermediate) 🆕
   - Scalability, caching, load balancing, microservices

### 📐 Mathematics
8. **mathematics-for-devs** (4 lekcje, ~5h, beginner) 🆕
   - Linear algebra, calculus, statistics, optimization

### ⚡ Algorithms
9. **algorithms-mastery** (5 lekcji, ~7h, intermediate) 🆕
   - Sorting, searching, graphs, dynamic programming

**Rozpocznij kurs:**
```
"Zacznij kurs backend-onboarding"
```

---

## 🌍 Dziedziny Nauki

Plugin wspiera wiele dziedzin - możesz używać wbudowanych lub dodawać własne.

**Dostępne dziedziny:**
- 💻 **Software Engineering** - Full-stack, API design, databases, DevOps, testing, security
- 🤖 **AI & Machine Learning** - LLM, RAG, prompt engineering, embeddings, neural networks
- ☁️ **Cloud & Infrastructure** - GCP, AWS, serverless, containers, orchestration
- 📊 **Data Science** - Analiza danych, wizualizacja, machine learning
- 🏗️ **System Design** - Projektowanie skalowalnych systemów, architektura
- 📐 **Mathematics** - Linear Algebra, Calculus, Statistics, Optimization
- ⚡ **Algorithms** - Sorting, Searching, Graphs, Dynamic Programming
- 🧪 **Testing** - Pytest, integration testing, quality assurance

**Dodaj własną dziedzinę** naturalnie:
```
"Chcę dodać dziedzinę Security"
```

Claude zapyta o ikonę, opis i kategorię. Możesz też użyć komendy:
```bash
/learn --add-domain
```

---

## 🤖 Automatyczne Kursy

Claude **proaktywnie sugeruje kursy** gdy:
- Pracujesz z konceptem 3+ razy
- Nie masz aktywnego kursu dla tego konceptu
- Minęło 48h od ostatniej sugestii

**Przykład:**
```
💡 Sugestia Kursu (confidence: 85%)

Pracujesz z 'Redis Caching' już 4x - czas na następny krok!

Proponowany kurs: Pogłęb wiedzę: Redis Caching & Rate Limiting

Chcesz rozpocząć ten kurs? (Powiedz "tak")
```

---

## 📊 Tracking Postępów

### Co jest śledzone:

- ✅ **Practiced Concepts** - każde ukończenie lekcji
- 🔥 **Streak** - dni nauki bez przerwy
- 📈 **Domain Progress** - postęp w każdej dziedzinie
- 🎯 **Mastery** - koncept osiąga mastery po 4+ praktykowaniu

### Jak sprawdzić:

```
"Pokaż moje postępy"
lub: /progress
```

### Quiz:

Sprawdź wiedzę quizem:

```
"Zrób quiz z backendu"
lub: /quiz backend
```

---

## 🛠️ Przykłady Użycia

### Przykład 1: Nowa dziedzina + kurs

```
User: "Chcę dodać dziedzinę Security"
Claude: [Prowadzi przez proces interaktywnie]

User: "Stwórz kurs o OWASP Top 10"
Claude: [Tworzy kurs z 4 lekcjami Security]

User: "Zacznij Lekcję 1"
Claude: [Pokazuje teorię + TODO(human)]

User: [pracuje nad zadaniem]

User: "done"
Claude: [Loguje progress, pokazuje Lekcję 2]
```

### Przykład 2: Course Library

```
User: "Pokaż dostępne kursy"
Claude: [Lista 5 kursów z opisami]

User: "Zacznij kurs ai-ml-mastery"
Claude: [Rozpoczyna kurs, Lekcja 1/5]
```

### Przykład 3: Proaktywna sugestia

```
[User pracuje z Docker 3+ razy]

Claude: 💡 "Widzę że pracujesz z Docker - mam kurs o multi-stage builds. Chcesz?"

User: "tak"
Claude: [Tworzy i rozpoczyna kurs]
```

---

## 💡 Pro Tips

1. **Używaj naturalnego języka** - "chcę się nauczyć X" działa lepiej niż zapamiętywanie komend
2. **Ustaw aktywną dziedzinę** - kursy będą dopasowane do Twojego focusu
3. **Mów "done" po każdej lekcji** - tracking działa tylko gdy powiesz
4. **Sprawdzaj Course Library** - gotowe kursy są lepiej zbalansowane
5. **Zrób quiz po kursie** - sprawdź czy naprawdę opanowałeś material

---

## 🔧 Komendy Slash (Skróty)

Jeśli wolisz komendy:

```bash
/learn                          # Welcome screen
/learn "cel nauki"              # Stwórz kurs
/learn continue                 # Kontynuuj ostatni kurs
/learn --domain backend         # Ustaw aktywną dziedzinę
/learn --domains                # Pokaż wszystkie dziedziny
/learn --library                # Pokaż Course Library
/learn --start <course-id>      # Rozpocznij kurs z library
/learn --save-course <id>       # Zapisz kurs do library
/learn --add-domain             # Dodaj nową dziedzinę (interaktywnie)
/progress                       # Dashboard postępów
/quiz                           # Quiz (aktywna dziedzina)
/quiz <domain>                  # Quiz dla konkretnej dziedziny
```

---

## 🎯 Jak to działa pod maską

### Architektura v3.0

**1. Natural Language Intent Detection** (`intent_detector.py`)
- Wykrywa 10 intencji: add_domain, create_course, show_progress, quiz, done, continue, etc.
- Keyword matching + regex patterns
- Confidence score 0.7-1.0

**2. System Dziedzin** (`domains.json` + `domain_manager.py`)
- **Dziedziny wbudowane** - w `data/domains.json`
- **Dziedziny użytkownika** - zapisywane w `~/.claude/learn-by-doing/user_learning_domains.json`
- **Merge** - obie struktury łączone przy load

**3. Knowledge Base** (`knowledge_base.json`)
- **80 konceptów** (51 old + 29 new)
- Każdy koncept: name, domain, difficulty, prerequisites, next_steps, use_cases, why_important, hint
- **Dependency Graph** - prerequisites zapewniają poprawną progresję

**4. Course Planning** (`course_planner.py`)
- **Ekstraktuje koncepty** z celu (keyword matching)
- **Sortuje po dependencies** (prerequisites first)
- **Generuje lekcje** z teoria + TODO(human)
- **Proaktywne sugestie** - suggest_course_proactively()

**5. Progress Tracking** (`data_manager.py`, `progress_tracker.py`)
- **learning_progress.json** - practiced concepts, streak, domain progress
- **practice_log.jsonl** - append-only log wszystkich praktyk
- **Mastery** - concept osiąga mastery po 4+ practice_count

---

## 📂 Struktura Plików

```
learn-by-doing/
├── data/
│   ├── domains.json                 # Dziedziny wbudowane ⭐ NEW
│   ├── knowledge_base.json          # 80 konceptów (51→80) ⭐ UPDATED
│   ├── active_courses.json          # Aktywne kursy użytkownika
│   └── course_library/              # 9 gotowych kursów
│       ├── backend-onboarding.json
│       ├── ai-ml-mastery.json
│       ├── full-stack-essentials.json
│       ├── database-deep-dive.json
│       └── testing-quality.json
├── scripts/
│   ├── intent_detector.py           # NL intent detection ⭐ NEW
│   ├── learn.py                     # Główny entry point
│   ├── progress.py                  # Dashboard postępów
│   ├── quiz.py                      # Quiz generator
│   ├── course_planner.py            # AI course generation + proaktywne sugestie ⭐ UPDATED
│   ├── course_manager.py            # CRUD kursów
│   ├── lesson_conductor.py          # Prowadzenie lekcji
│   ├── domain_manager.py            # Zarządzanie dziedzinami ⭐ UPDATED
│   ├── data_manager.py              # Data persistence ⭐ UPDATED
│   ├── learning_graph.py            # Graf zależności konceptów
│   └── recommendation_engine.py     # Rekomendacje next steps
├── commands/
│   ├── learn.md                     # /learn
│   ├── progress.md                  # /progress
│   └── quiz.md                      # /quiz
├── prompts/
│   ├── learning_mindset.md          # System prompt
│   └── course_generation.md         # AI course planning prompt ⭐ NEW
└── README.md                        # Ten plik ⭐ UPDATED
```

---

## ❓ FAQ

**Q: Czy muszę używać komend slash?**
A: Nie! Możesz mówić naturalnie: "chcę się nauczyć Redis" działa tak samo jak `/learn "Redis"`.

**Q: Ile dziedzin mogę mieć?**
A: 8 wbudowanych + nieograniczone własne. Dodaj dziedzinę mówiąc "dodaj dziedzinę X".

**Q: Czy kursy są automatycznie tworzone?**
A: Częściowo. Claude proponuje kursy gdy widzi że pracujesz z konceptem 3+ razy. Możesz też poprosić: "stwórz kurs o X".

**Q: Jak działa tracking?**
A: Musisz powiedzieć "done" po każdej lekcji. Bez tego plugin nie wie że ukończyłeś zadanie.

**Q: Czy mogę edytować kursy?**
A: Tak! Kursy są w `data/active_courses.json` (JSON format). Możesz też zapisać kurs do library: `/learn --save-course <id>`.

**Q: Co to jest knowledge_base?**
A: 80 konceptów (Backend, Frontend, AI/ML, Database, DevOps, Testing, System Design, Security, Cloud, Mobile, Product, Design) z prerequisites i next_steps. To "mapa wiedzy" pluginu.

**Q: Czy mogę usunąć dziedzinę?**
A: Wbudowane - nie. Własne dziedziny - tak, używając `domain_manager.py`.

---

## 🔄 Changelog

### v3.1.0 (2025-11-03)

**BREAKING CHANGES:**
- Uproszczenie dziedzin: 12 → 8 (konsolidacja i reorganizacja)
- Wszystkie kursy w course_library/ mają bogatą treść

**Nowe funkcje:**
- 📚 **4 nowe kursy** wysokiej jakości:
  - Data Science Foundations (Pandas, NumPy, Matplotlib)
  - System Design Essentials (Caching, Load Balancing, Microservices)
  - Mathematics for Developers (Linear Algebra, Calculus, Stats)
  - Algorithms Mastery (Sorting, Graphs, DP)
- 🔄 **Skonsolidowane dziedziny**:
  - Software Engineering (konsolidacja Backend, Frontend, Database, DevOps, Testing, Security)
  - AI & Machine Learning (dedykowana dziedzina)
  - Cloud & Infrastructure (dedykowana dziedzina)
- ⚡ **Szybsze ładowanie** - kursy z biblioteki zamiast generowania
- 📖 **README.md przepisany** - odzwierciedla nową strukturę

**Ulepszenia:**
- Każdy kurs ma konkretne TODO odnoszące się do projektu Sight
- Teoria wyjaśnia "dlaczego ważne" i praktyczne zastosowania
- Szacowany czas bardziej realistyczny
- Icons i difficulty dla wszystkich kursów

### v3.0.0 (2025-11-03)

**BREAKING CHANGES:**
- System dziedzin przepisany (domains.json zamiast hardcoded)
- Natural language intent detection
- 80 konceptów (było 51)

**Nowe funkcje:**
- 🗣️ Komunikacja naturalna (intent_detector.py)
- 🌍 12 dziedzin (Backend, Frontend, AI/ML, Database, DevOps, Testing, System Design, Security, Cloud, Mobile, Product, Design)
- 🤖 Proaktywne sugestie kursów (suggest_course_proactively)
- 📚 Course Library (5 początkowych kursów)
- 🎨 Ikony i kolory dla dziedzin

### v2.x
- Universal Learning System
- Practice log + progress tracking
- Heatmapa + streak

### v1.0
- Podstawowy system kursów
- Knowledge base (45 konceptów)

---

## 📖 Więcej Informacji

- **Plugin Metadata:** `.claude-plugin/plugin.json`
- **Technical Docs:** `scripts/` (docstringi w każdym pliku)
- **Architecture:** Zobacz `scripts/README.md` (jeśli istnieje)

---

**Miłej nauki! 🚀**

Masz pytania? Zapytaj Claude'a: "Jak działa plugin learn-by-doing?"
