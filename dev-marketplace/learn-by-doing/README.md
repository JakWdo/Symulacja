# 🎓 Learn-by-Doing - Inteligentny System Nauki przez Praktykę

**Universal Learning System v2.3** - Plugin dla Claude Code z **Interactive Course Planning**! Claude tworzy spersonalizowane kursy, prowadzi Cię krok po kroku (teoria + TODO(human)) i stopniowo dochodzisz do celu.

> 💡 **Filozofia:** Wszystko przez komunikację z Claude. Używaj `/learn`, `/course`, `/progress`, `/quiz`

---

## 🚀 Szybki Start

### 1. Rozpocznij Kurs
```
"Chcę dodać Redis caching do projektu"
```
lub
```bash
/course start "Dodaj Redis caching"
```

### 2. Claude Pyta
- Poziom? (beginner/intermediate/advanced)
- Czas? (quick 2-3h / standard 8-10h / deep 20-30h)
- Styl? (theory-first / practice-first / balanced)

### 3. Claude Tworzy Plan
```
Kurs: Redis Caching (5 lekcji, ~8h)
Lekcja 1: Redis Basics
Lekcja 2: Cache Key Design
Lekcja 3: Implementation
Lekcja 4: TTL & Expiration
Lekcja 5: Testing
```

### 4. Claude Prowadzi
Każda lekcja = **Teoria** + **TODO(human)** → wykonujesz → `/course done`

---

## 📚 Główne Funkcje

### 🎓 Interactive Course Planning (v2.3)

**Claude jako aktywny nauczyciel!**

```bash
/course start "cel"       # Rozpocznij kurs (interactive)
/course list              # Lista aktywnych kursów
/course continue <id>     # Następna lekcja
/course done <id>         # Oznacz jako ukończoną
/course progress <id>     # Szczegółowy postęp
```

**Przykład lekcji:**
```
💡 Teoria: Redis to in-memory store dla cache'owania...
🛠️ TODO(human): Połącz się z Redis, test ping/set/get
   Oczekiwane: ~15 linii, 30 min
   Plik: app/core/redis_test.py
```

---

### 📊 Zarządzanie Dziedzinami

**6 szablonów + custom:**

```bash
/learn software-engineering  # 45 konceptów (Backend, Frontend, AI/ML, DevOps)
/learn data-science         # pandas, numpy, matplotlib, sklearn
/learn machine-learning     # supervised, deep-learning, transformers
/learn system-design        # scalability, caching, microservices
/learn algorithms           # sorting, graphs, dynamic-programming
/learn mathematics          # linear-algebra, calculus, statistics
```

**Zarządzanie:**
```bash
/learn                      # Status wszystkich dziedzin
/learn --list               # Lista
/learn --active <id>        # Zmień aktywną
/learn --remove <id>        # Usuń
```

---

### 🔍 Automatyczne Wykrywanie

Plugin automatycznie wykrywa co robisz:

**Python:**
```python
from fastapi import FastAPI          # → FastAPI Routing
import pandas as pd                  # → pandas basics
```

**JavaScript/TypeScript:**
```typescript
import React from 'react'            // → React Components
import { useState } from 'react'     // → React Hooks
```

**Pliki:**
```
app/api/*.py        → FastAPI endpoints
*.tsx               → React components
docker-compose.yml  → Docker Compose
```

**Bash:**
```bash
pytest              # → pytest testing
docker-compose up   # → Docker Compose
```

---

### 📈 Monitoring Postępów

**Dashboard:**
```bash
/progress
```

Pokazuje:
- Progress per dziedzina (10/45 konceptów)
- Breakdown per kategoria (Backend 60%, Frontend 50%)
- Mastery levels (Level 1-5, Level 3+ = MASTERED)
- Passa (streak days)
- Ostatnia aktywność

**Lista konceptów:**
```bash
/concepts
```

34 koncepty w 6 kategoriach (AI/ML, Backend, Database, DevOps, Frontend, Testing)

**Przegląd:**
```bash
/review
```

Co robiłeś dzisiaj/tydzień/miesiąc

---

### 🧠 System Quizów

```bash
/quiz                      # Quiz z aktywnej dziedziny
/quiz software-engineering # Quiz z konkretnej dziedziny
```

Generuje pytania z **practiced concepts** (4 typy: multiple choice, true/false, kategoria, next steps)

---

### 💡 Smart Recommendations

System analizuje:
1. Co już opanowałeś (mastery >= 3)
2. Dependency graph (prerequisites)
3. Ostatnie praktyki
4. Category balance

I sugeruje co uczyć się dalej z **readiness score** (100% = wszystkie prerequisites gotowe)

---

## 📋 Spaced Repetition

System przypomina o powtórkach:
- Level 1 → Powtórz po **1 dniu**
- Level 2 → Powtórz po **3 dniach**
- Level 3 → Powtórz po **7 dniach** (MASTERED!)
- Level 4 → Powtórz po **14 dniach**
- Level 5 → Powtórz po **30 dniach**

Claude wyświetla przy starcie sesji:
```
Do Powtórki:
📅 pandas basics (7 dni temu) - czas powtórzyć!
```

---

## 🎯 Przykład: Pełny Flow

```bash
# 1. Start kursu
"Chcę dodać ML recommendations do Sight"

# 2. Claude pyta → tworzy plan 5 lekcji

# 3. Lekcja 1: Teoria + TODO
# Wykonujesz zadanie...

# 4. Done
/course done ml-recommendations

# 5. Następna lekcja
/course continue ml-recommendations

# Repeat dla lekcji 2, 3, 4, 5...

# 6. Ukończenie
🎉 GRATULACJE! Kurs ukończony!
```

---

## 📁 Architektura (dla zaawansowanych)

**Storage:** `~/.claude/learn-by-doing/`

```
config.json                   # Konfiguracja
user_learning_domains.json    # Dziedziny
learning_progress.json         # Postęp (sessions, streak, mastery)
practice_log.jsonl             # Historia akcji (max 1000)
courses.json                   # Aktywne kursy (NEW v2.3)
knowledge_base.json            # 45 predefiniowanych konceptów
dynamic_concepts.json          # Auto-discovered
archives/                      # Archiwum
```

**Moduły:**
- `course_planner.py` - Tworzenie kursów
- `course_manager.py` - CRUD kursów
- `lesson_conductor.py` - Prowadzenie lekcji
- `concept_detector.py` - Wykrywanie konceptów
- `learning_graph.py` - Dependency graph
- `recommendation_engine.py` - Sugestie
- `quiz_generator.py` - Quizy

---

## ⚙️ Konfiguracja

**Plik:** `~/.claude/learn-by-doing/config.json`

```json
{
  "enabled": true,
  "auto_tracking": {
    "enabled": true,
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
  }
}
```

**Zmiana przez Claude:**
```
Chcę priorytetować Backend w rekomendacjach
```

---

## ❓ FAQ

**Q: Jak plugin wie czego się uczę?**
A: Wykrywa z practice: `import pandas` → pandas basics, `app/api/*.py` → FastAPI

**Q: Mogę uczyć się kilku dziedzin naraz?**
A: Tak! Software Engineering + Data Science + System Design równocześnie

**Q: Co to mastery level?**
A: Poziom 1-5. Level 3+ = MASTERED (opanowane)

**Q: Jak działa spaced repetition?**
A: System przypomina w odstępach 1, 3, 7, 14, 30 dni

**Q: Dane synchronizowane między projektami?**
A: Tak! `~/.claude/learn-by-doing/` - działa globalnie

**Q: Jak wyłączyć plugin?**
A: Powiedz Claude: "Wyłącz plugin" → ustawia `enabled: false`

**Q: Jak dodać koncepty do dziedziny?**
A: Opcja 1 (zalecana): Po prostu pracuj, system wykryje
   Opcja 2: Powiedz Claude: "Dodaj kategorie do Statistics: descriptive-stats, regression..."

**Q: Wiele kursów równocześnie?**
A: Tak! Możesz mieć 3-5 aktywnych kursów, `/course list` aby zobaczyć wszystkie

---

## 🎓 Dlaczego Learn-by-Doing?

❌ **Stary sposób:**
- Claude tylko notuje co robisz
- Brak struktury
- Nie wiesz co dalej

✅ **Nowy sposób (v2.3):**
- Claude planuje ścieżkę nauki (kursy!)
- Prowadzi krok po kroku (teoria + TODO)
- Stopniowo dochodzisz do celu
- Jasna struktura (Lekcja 1 → 2 → 3...)

---

## 📦 Changelog

**v2.3.0 (2025-11-02)** - Interactive Course Planning 🎓
- ✨ **NEW:** Course Planner - spersonalizowane kursy
- ✨ **NEW:** `/course` command (7 subkomend)
- ✨ **NEW:** Guided lessons (teoria + TODO)
- ✨ **NEW:** Multiple active courses
- 🎯 Focus shift: passive tracking → active teaching

**v2.2.0 (2025-11-02)** - Final Improvements
- ✨ Quiz generator z knowledge_base
- ✨ JS/TS import detection
- 📝 Kompletny README

**v2.0 (2025-11-02)** - Universal Learning System
- ✨ Auto-discovery (200+ technologii)
- ✨ Multi-domain support (6 szablonów)
- ✨ Spaced repetition
- ✨ Smart recommendations
- 📊 Dashboard per domena

---

## 🚀 Rozpocznij Naukę!

```bash
# 1. Sprawdź status
/learn

# 2. Rozpocznij kurs
/course start "Dodaj ML do projektu"

# 3. Claude prowadzi przez lekcje
# Teoria → TODO → done → next → ... → 🎉

# 4. Sprawdzaj postęp
/progress

# 5. Testuj wiedzę
/quiz
```

**Happy Learning! 🎓**

Plugin działa globalnie we wszystkich projektach. Ucz się przez praktykę!

**Pytania? Zapytaj Claude!** 💬
