# 🎓 Learn-by-Doing Plugin

**AI-asystent nauczania** dla Claude Code - ucz się przez praktykę z kursami generowanymi przez AI, dostosowanymi do projektu Sight.

Plugin pomaga ci opanować koncepty techniczne poprzez:
- 🤖 **AI-generowane kursy** - Claude tworzy plan nauki dopasowany do celu
- 📊 **Tracking postępów** - śledzi co opanowałeś w każdej dziedzinie
- 🎯 **Praktyczne zadania** - TODO(human) z podpowiedziami
- 📝 **Quizy** - sprawdzają twoją wiedzę po lekcjach

---

## 🚀 Szybki Start

### 1. Pierwsze uruchomienie

Sprawdź dostępne dziedziny nauki:

```bash
/learn --domains
```

Zobaczysz 7 dziedzin:
- 🔧 **Backend** - FastAPI, SQLAlchemy, Redis, async patterns
- 🎨 **Frontend** - React, TypeScript, TanStack Query, Zustand
- 🤖 **AI/ML** - LangChain, Gemini, RAG, embeddings
- 💾 **Databases** - PostgreSQL, Neo4j, Cypher, pgvector
- 🚀 **DevOps** - Docker, Cloud Run, CI/CD, monitoring
- ✅ **Testing** - pytest, fixtures, async testing
- 🏗️ **System Design** - microservices, scalability, CQRS

### 2. Ustaw aktywną dziedzinę

Wybierz dziedzinę, którą chcesz teraz studiować:

```bash
/learn --domain backend
```

Wszystkie kursy będą teraz domyślnie w tej dziedzinie.

### 3. Rozpocznij kurs

Powiedz Claude'owi czego chcesz się nauczyć:

```bash
/learn "Redis caching w FastAPI"
```

Claude:
1. Przeanalizuje twój cel
2. Znajdzie powiązane koncepty z knowledge base (51 konceptów)
3. Wygeneruje plan kursu z 3-5 lekcjami
4. Pokaże ci preview kursu
5. Zapisze kurs jako aktywny

**Przykładowy output:**

```
✅ Znalazłem 3 konceptów do nauczenia

# ✅ Kurs Gotowy!

## 📚 "Redis caching w FastAPI"

**Parametry:**
- Poziom: intermediate
- Czas: standard (~2.5h)
- Styl: balanced

**Lekcje (3):**

Lekcja 1: Redis Caching & Rate Limiting (backend)
  ⏱️ ~90 min

Lekcja 2: FastAPI Async Patterns (backend)
  ⏱️ ~90 min

Lekcja 3: Caching Strategies (backend)
  ⏱️ ~72 min

✅ Kurs zapisany! ID: redis-caching-w-fastapi
```

### 4. Kontynuuj naukę

Rozpocznij lub kontynuuj ostatni kurs:

```bash
/learn continue
```

Claude pokaże ci:
- **Teorię** - wyjaśnienie konceptu (💡)
- **TODO(human)** - praktyczne zadanie do wykonania (🛠️)
- **Podpowiedź** - hint jak podejść do problemu
- **Oczekiwania** - ile linii kodu, jaki plik, ile czasu

**Przykładowa lekcja:**

```
## Lekcja 1/3: Redis Caching & Rate Limiting
⏱️ Szacowany czas: ~90 min

---

💡 Koncept: Redis Caching & Rate Limiting

Cache'owanie danych, rate limiting, session storage

**Zakładam że znasz podstawy**

📝 Zastosowania:
- Cache segment briefs (reduce LLM calls)
- Rate limiting dla API endpoints
- Session storage dla user state

**Dlaczego to ważne:**
Redukuje koszty LLM (cache segment briefs) i chroni przed abuse

---

🛠️ TODO(human) 🟡: Praktyczne zadanie

**Zadanie:** Zaimplementuj Redis Caching & Rate Limiting w kontekście: "Redis caching w FastAPI"

**Podpowiedź:**
redis-py z async support, używaj TTL dla auto-expiry

**Oczekiwane:**
- ~20-50 linii kodu
- Czas: ~90 minut
- Plik: app/services/your_file.py

**Koncepty:**
Redis Caching & Rate Limiting, backend

**Gotowy?** Powiedz "done" gdy skończysz!
```

### 5. Ukończ lekcję

Gdy skończysz implementację, powiedz Claude'owi:

```
"done"
```

lub

```
"ukończyłem lekcję"
```

Claude automatycznie:
1. Oznaczy lekcję jako ukończoną ✅
2. Zaloguje practiced concept do progress tracker
3. Zaktualizuje domain progress
4. Pokaże następną lekcję (jeśli jest)

**Output:**

```
# ✅ Lekcja 1 Ukończona!

**Postęp:** 1/3 lessons

---

**Następna lekcja (2):** FastAPI Async Patterns

Gotowy kontynuować? Użyj:
`/learn continue`
```

### 6. Sprawdź postęp

Zobacz jak ci idzie:

```bash
/progress
```

**Output:**

```
# 📊 Progress Dashboard

## 🔧 Aktywna Dziedzina: Backend
████████░░░░░░░░ 30% (3/10)

## 🎓 Wszystkie Dziedziny
➡️ 🔧 Backend: ███████░░░░░░░░ 30% (3/10)
   🎨 Frontend: ░░░░░░░░░░░░░░░ 0% (0/8)
   🤖 AI/ML: ██░░░░░░░░░░░░░ 10% (1/10) - 1 mastered!

## 📚 Aktywne Kursy
- Redis caching w FastAPI (1/3 lekcji) [backend]
```

### 7. Sprawdź wiedzę quizem

Po ukończeniu kilku lekcji:

```bash
/quiz
```

Claude wygeneruje quiz z practiced concepts (multiple choice, true/false, fill-in).

---

## 📖 Wszystkie Komendy

### `/learn` - Główna komenda

```bash
# Welcome screen z przeglądem dziedzin
/learn

# Rozpocznij nowy kurs AI-generowany
/learn "cel nauki"

# Przykłady celów:
/learn "Docker multi-stage builds"
/learn "React hooks i custom hooks"
/learn "Neo4j Cypher queries"
/learn "LangChain chains i prompts"

# Kontynuuj ostatni kurs
/learn continue

# Zmień aktywną dziedzinę
/learn --domain backend
/learn --domain frontend
/learn --domain ai_ml

# Pokaż wszystkie dziedziny
/learn --domains

# Dodaj nową dziedzinę (interaktywnie)
/learn --add-domain

# Zapisz kurs do library (reusable)
/learn --save-course <course-id>
```

### `/progress` - Dashboard postępów

```bash
/progress
```

Pokazuje:
- Aktywną dziedzinę z progress bar
- Przegląd wszystkich 7 dziedzin
- Aktywne kursy (jeśli są)
- Liczbę mastered concepts

### `/quiz` - Sprawdź wiedzę

```bash
# Quiz z practiced concepts (active domain)
/quiz

# Quiz dla konkretnej dziedziny
/quiz backend
/quiz frontend
```

---

## 🔧 Tworzenie Własnych Dziedzin i Kursów

### Dodawanie Nowej Dziedziny

Chcesz dodać własną dziedzinę nauki? (np. "Mobile Development", "Cloud Architecture")

```bash
/learn --add-domain
```

Plugin zapyta cię o:
1. **ID dziedziny** (slug format, np. `mobile-dev`)
2. **Nazwa** (wyświetlana, np. "Mobile Development")
3. **Ikona** (emoji, np. 📱)
4. **Opis** (opcjonalny)
5. **Kategorie** (przez przecinek, opcjonalne)

**Przykład:**

```
/learn --add-domain

ID dziedziny: mobile-dev
Nazwa: Mobile Development
Ikona: 📱
Opis: iOS, Android, React Native, Flutter
Kategorie: ios, android, react-native, flutter

✅ Dziedzina dodana! 📱 Mobile Development

Ustaw jako aktywną: /learn --domain mobile-dev
```

Po utworzeniu dziedziny:
- Pojawi się w `/learn --domains`
- Możesz ją ustawić jako aktywną
- Kursy w tej dziedzinie będą śledzone oddzielnie

### Zapisywanie Kursu do Library

Ukończyłeś kurs i chcesz go wykorzystać ponownie lub udostępnić?

```bash
/learn --save-course <course-id>
```

**Jak znaleźć course ID:**
1. Uruchom `/progress`
2. Zobacz sekcję "📚 Aktywne Kursy"
3. Course ID to zazwyczaj slug z tytułu (np. `redis-caching-w-fastapi`)

**Przykład:**

```bash
# Zapisz ukończony kurs
/learn --save-course redis-caching-w-fastapi

✅ Kurs zapisany do library!
Lokalizacja: data/course_library/redis-caching-w-fastapi.json
ID: redis-caching-w-fastapi

Użyj go ponownie: /learn --start redis-caching-w-fastapi
```

Zapisany kurs:
- Pojawi się w `/learn --library`
- Możesz go rozpocząć ponownie przez `/learn --start <id>`
- Jest reusable - możesz go użyć wiele razy

**Use cases:**
- **Onboarding** - stwórz kurs dla nowych członków zespołu, zapisz go, używaj dla każdego
- **Best practices** - zapisz kursy które sprawdziły się w praktyce
- **Własne ścieżki** - buduj custom learning paths dla swojego zespołu

---

## 💡 Jak to działa pod maską?

### 1. **Knowledge Base (51 konceptów)**

Plugin ma wbudowaną bazę 51 konceptów technicznych dopasowanych do projektu Sight:

**Backend (10):** fastapi-routing, fastapi-async, fastapi-dependencies, sqlalchemy-async, postgresql-basics, redis-caching, service-layer-pattern, api-design, error-handling, background-tasks

**Frontend (8):** react-hooks, typescript-basics, tanstack-query, zustand-state, component-architecture, tailwind-styling, vite-tooling, async-ui-patterns

**AI/ML (10):** langchain-basics, gemini-api, prompt-engineering, rag-hybrid-search, embeddings-vectors, graph-rag, llm-orchestration, token-optimization, context-management, ai-validation

...i więcej w Database, DevOps, Testing, System Design

Każdy koncept ma:
- **Prerequisites** - co musisz znać wcześniej
- **Next steps** - co uczyć się dalej (learning graph)
- **Use cases** - gdzie to wykorzystasz w Sight
- **Hints** - podpowiedzi jak podejść
- **Difficulty** (1-5) - poziom trudności

### 2. **Ekstraktowanie konceptów**

Gdy piszesz `/learn "cel"`, Claude:

1. **Keyword matching** - szuka słów kluczowych w goal ("redis" → redis-caching)
2. **Concept names** - szuka nazw konceptów (np. "React hooks" → react-hooks)
3. **Use cases** - dopasowuje do use cases w konceptach
4. **Domain context** - priorytetyzuje koncepty z aktywnej dziedziny

Przykład:
```
/learn "Async patterns w FastAPI"

→ Matched concepts:
  1. fastapi-async (exact match)
  2. fastapi-routing (prerequisite)
  3. background-tasks (related)
```

### 3. **Generowanie kursu**

Claude tworzy plan kursu:

1. **Sortuje koncepty** po prerequisites (najpierw fundamenty)
2. **Wybiera 3-5 lekcji** (zależnie od liczby konceptów)
3. **Dla każdej lekcji generuje:**
   - **Theory** - wyjaśnienie konceptu z use cases
   - **TODO(human)** - praktyczne zadanie
   - **Estimated time** - szacowany czas (zależy od difficulty)

Używa defaults:
- **Level:** intermediate (możesz być dopytany później)
- **Time:** standard (~8-10h total)
- **Style:** balanced (mix teorii i praktyki)

### 4. **Progress Tracking**

Gdy ukończysz lekcję, plugin:

1. **Zapisuje practiced concept** do `learning_progress.json`:
   ```json
   {
     "fastapi-async": {
       "name": "FastAPI Async Patterns",
       "domain": "backend",
       "practice_count": 1,
       "first_practiced": "2025-11-03T10:00:00Z",
       "last_practiced": "2025-11-03T10:00:00Z",
       "mastered": false,
       "practice_history": [...]
     }
   }
   ```

2. **Aktualizuje domain progress**:
   - `detected` - ile konceptów w domenie zostało practiced
   - `mastered` - ile konceptów osiągnęło mastery (>3 practice_count)
   - `progress` - % mastered / total_concepts

3. **Generuje rekomendacje** (next_steps):
   - Używa learning graph (prerequisites → concept → next_steps)
   - Priorytetyzuje koncepty gdzie prerequisites są spełnione

### 5. **Learning Graph**

Koncepty są połączone w graf zależności:

```
fastapi-routing
  ↓
  → next_steps: [fastapi-async, fastapi-dependencies]

fastapi-async
  ← prerequisites: [fastapi-routing]
  ↓
  → next_steps: [sqlalchemy-async, background-tasks]
```

Plugin używa tego do:
- Rekomendacji "co dalej"
- Sprawdzania readiness (czy jesteś gotowy na koncept)
- Sortowania lekcji w kursie

---

## 🎯 Przykłady Użycia

### Scenariusz 1: Nowy członek zespołu

**Cel:** Onboarding do projektu Sight

```bash
# Dzień 1: Backend basics
/learn --domain backend
/learn "FastAPI routing i endpoints"
# ... pracujesz nad TODO(human) ...
"done"
/learn continue
# ... kolejne lekcje ...

# Dzień 2: Database
/learn --domain database
/learn "SQLAlchemy async ORM"

# Dzień 3: AI/ML
/learn --domain ai_ml
/learn "LangChain basics dla persona generation"

# Co tydzień: sprawdź postęp
/progress
```

### Scenariusz 2: Głęboka nauka jednej dziedziny

**Cel:** Zostań ekspertem w AI/ML

```bash
/learn --domain ai_ml

# Kurs 1: Fundamenty
/learn "LangChain chains i prompts"
# ... 5 lekcji ...

# Kurs 2: RAG System
/learn "Hybrid search z embeddings"
# ... 5 lekcji ...

# Kurs 3: Advanced
/learn "Graph RAG z Neo4j"
# ... 5 lekcji ...

# Po każdym kursie: quiz
/quiz

# Sprawdź mastery
/progress
# AI/ML: 80% (8/10) - 6 mastered!
```

### Scenariusz 3: Szybka nauka przed taskiem

**Cel:** Musisz dodać Redis caching do API

```bash
# Quick course
/learn "Redis caching patterns"

# Kontynuuj z przerwami
/learn continue
# ... implementujesz w projekcie ...
"done"

# Następna lekcja
/learn continue
# ... dalej implementujesz ...
"done"

# Quiz na koniec
/quiz

# Gotowe! Masz wiedzę + praktykę
```

---

## 🔥 Pro Tips

### 1. **Używaj konkretnych celów**

❌ Słabo: `/learn "backend"`
✅ Dobrze: `/learn "FastAPI async patterns z background tasks"`

Im konkretniejszy cel, tym lepiej dopasowane koncepty.

### 2. **Pracuj w kontekście projektu**

TODO(human) zadania mówią "Zaimplementuj X w kontekście: [twój cel]"

Nie ćwicz w izolacji - wdrażaj wiedzę od razu w projekcie Sight!

### 3. **Quizy po każdym kursie**

Nie skip'uj quizów - pomagają utrwalić wiedzę i pokazują co trzeba powtórzyć.

### 4. **Jedna dziedzina na raz**

Zamiast skakać między dziedziną, skup się na jednej przez tydzień. Lepszy depth niż breadth.

### 5. **Continue > New Course**

Jeśli masz rozpoczęty kurs, ukończ go przed startowaniem nowego. Plugin priorytetyzuje `/learn continue`.

### 6. **Track mastery, nie tylko completion**

Cel to nie "ukończyć wszystkie kursy", ale **mastered concepts** (practice_count > 3).

Wracaj do konceptów i używaj ich w różnych kontekstach.

---

## ❓ FAQ

### Q: Jak długo trwa typowy kurs?

**A:** Zależy od liczby konceptów:
- Quick (3 lekcje): ~2-3h
- Standard (5 lekcji): ~8-10h
- Deep (8 lekcji): ~20-30h

Ale możesz pracować w swoim tempie - kurs jest zapisany i możesz wracać.

### Q: Co jeśli nie wiem od czego zacząć?

**A:**
```bash
/learn --domains    # Zobacz co jest dostępne
/learn              # Welcome screen z sugestiami
```

Albo po prostu powiedz Claude'owi: "Chcę nauczyć się backend dla projektu Sight"

### Q: Czy muszę kończyć kursy w całości?

**A:** Nie! Możesz:
- Skip'ować lekcje (nie zalecane, ale możliwe)
- Zacząć nowy kurs w dowolnym momencie
- Wrócić do starego kursu później

Ale zalecam dokończyć co zaczęłeś - efekt completion boost!

### Q: Co jeśli koncept jest za trudny?

**A:**
1. Sprawdź **prerequisites** - może musisz nauczyć się czegoś wcześniej
2. Poproś Claude'a o pomoc: "Wyjaśnij X prościej"
3. Zmień level kursu (w przyszłości będzie interaktywny wybór)

### Q: Czy mogę dodać własne koncepty?

**A:** W obecnej wersji (v3.0) nie. Knowledge base jest predefiniowany dla projektu Sight.

Custom concepts będą w przyszłych wersjach (Faza 3).

### Q: Gdzie są przechowywane dane?

**A:** W `data/` (local) lub `~/.claude/learn-by-doing/` (global):
- `learning_progress.json` - twoje practiced concepts
- `active_courses.json` - rozpoczęte kursy
- `knowledge_base.json` - 51 konceptów

### Q: Co oznacza "mastered"?

**A:** Koncept jest mastered gdy:
- `practice_count >= 4` (użyłeś go 4+ razy)
- LUB ręcznie oznaczyłeś jako mastered

Mastery ≠ completion. Mastery = deep understanding + multiple uses.

---

## 🛠️ Techniczne Detale

### Struktura Plików

```
learn-by-doing/
├── .claude-plugin/
│   └── plugin.json              # Metadata pluginu
├── commands/
│   ├── learn.md                 # /learn command
│   ├── progress.md              # /progress command
│   └── quiz.md                  # /quiz command
├── data/
│   ├── knowledge_base.json      # 51 konceptów (predefiniowane)
│   ├── learning_progress.json   # Progress tracking (user data)
│   ├── active_courses.json      # Aktywne kursy (user data)
│   └── domains.json             # 7 dziedzin (user preferences)
├── scripts/
│   ├── learn.py                 # Entry point dla /learn
│   ├── progress.py              # Entry point dla /progress
│   ├── quiz.py                  # Entry point dla /quiz
│   ├── course_planner.py        # AI course generation
│   ├── course_manager.py        # CRUD kursów
│   ├── lesson_conductor.py      # Prowadzenie lekcji
│   ├── data_manager.py          # Data persistence
│   ├── domain_manager.py        # Zarządzanie dziedzinami
│   ├── learning_graph.py        # Graf zależności konceptów
│   ├── recommendation_engine.py # Next steps suggestions
│   └── quiz_generator.py        # Quiz generation
└── README.md
```

### Zależności

**Zero external dependencies!** Plugin używa tylko Python stdlib:
- `json` - data persistence
- `pathlib` - file operations
- `datetime` - timestamps
- `logging` - error handling

### Kompatybilność

- Python 3.8+
- Claude Code (marketplace plugin)
- Projekt Sight (koncepty dopasowane)

---

## 📝 Changelog

### v3.0.0 (2025-11-03) - MVP Release ✅

**Nowe funkcje:**
- ✅ Knowledge base z 51 konceptami projektu Sight
- ✅ AI-generowane kursy (ekstraktowanie konceptów → course plan)
- ✅ Full course flow (start → lessons → completion)
- ✅ Lesson completion tracking z auto-logging
- ✅ Progress tracking per domain
- ✅ Learning graph (prerequisites → next_steps)
- ✅ Recommendation engine
- ✅ Quiz generation z practiced concepts
- ✅ Seed demo data (5 practiced concepts)

**Zmiany:**
- ❌ Usunięto pasywne śledzenie (PostToolUse hooks)
- ❌ Usunięto auto-detect concepts (focus na kursy)
- ✅ Uproszczony knowledge base (120 → 51 konceptów)
- ✅ Redukcja kodu o 70% (~7400 → ~2200 linii)

### v2.3.0 - Interactive Course Planning
- Interactive preferences (level, time, style)
- Course preview przed zapisem

### v2.0.0 - Universal Learning System
- Multi-domain tracking
- Pattern matching concepts
- Practice log (JSONL)

### v1.0.0 - Initial Release
- Basic concept tracking
- Manual logging

---

## 🤝 Wsparcie

Masz problemy lub pytania?

1. Sprawdź ten README (większość odpowiedzi jest tutaj!)
2. Zapytaj Claude'a bezpośrednio w konwersacji
3. Otwórz issue na GitHub (jeśli projekt jest na GitH repo)

**Made with ❤️ by Claude & Human for the Sight Project**

---

## 🎯 Co dalej?

Zaplanowane ulepszenia (Faza 2):

- **Progress tracking improvements** - auto-detect ukończonych TODO(human)
- **AI-generated quiz questions** - pytania generowane przez LLM
- **Dashboard enhancements** - wykresy, heatmapy aktywności
- **Course library** - predefiniowane kursy ready-to-use
- **Interactive preferences** - wybór level/time/style przez Claude
- **Multi-language support** - angielski + polski
- **Web dashboard** - HTML/JS interface
- **GitHub integration** - sync z commits
- **AI coach** - personalized feedback na kod

Stay tuned! 🚀
