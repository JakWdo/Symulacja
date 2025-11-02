# 🎓 Learn-by-Doing Plugin

**AI-asystent nauczania** - ucz się przez praktykę z kursami generowanymi przez Claude'a. Zorganizowany w **dziedziny** (Backend, Frontend, AI/ML, itd.)

---

## 🚀 Quick Start (3 kroki)

1. **Wybierz dziedzinę**: `/learn --domains`
2. **Rozpocznij kurs**: `/learn "Redis caching w FastAPI"`
3. **Sprawdź wiedzę**: `/quiz`

---

## 📚 Przykłady

```bash
/learn "Docker multi-stage builds"    # Rozpocznij kurs Docker
/learn "GraphQL z Apollo Server"      # Kurs GraphQL
/learn --domain backend               # Zmień aktywną dziedzinę
/learn --domains                      # Pokaż wszystkie dziedziny
/progress                             # Dashboard postępów
/quiz                                 # Quiz z ostatniej lekcji
```

---

## 🎯 Dziedziny

Twoja nauka jest zorganizowana w 7 dziedzin:

| Icon | Dziedzina | Opis |
|------|-----------|------|
| 🔧 | **Backend** | API, databases, async patterns |
| 🎨 | **Frontend** | React, UI/UX, state management |
| 🤖 | **AI/ML** | LLMs, RAG, embeddings |
| 💾 | **Databases** | SQL, NoSQL, optimization |
| 🚀 | **DevOps** | Docker, CI/CD, cloud |
| ✅ | **Testing** | Unit tests, integration, E2E |
| 🏗️ | **System Design** | Architecture, scalability, patterns |

Każda dziedzina ma:
- **Własne koncepty** (40-50 na dziedzinę)
- **Ścieżki nauki** (prerequisites → next steps)
- **Tracking postępów** (mastered concepts)

---

## 📖 Komendy

### `/learn [goal|--domain|--domains]`
Główna komenda - kursy AI, zarządzanie dziedzinami

```bash
/learn                          # Welcome screen + dziedziny
/learn "cel nauki"              # Rozpocznij kurs AI-generowany
/learn --domain <id>            # Zmień aktywną dziedzinę
/learn --domains                # Pokaż wszystkie dziedziny
/learn continue                 # Kontynuuj ostatni kurs (TODO)
```

### `/progress`
Dashboard postępów

```bash
/progress                       # Postępy w aktywnej dziedzinie
```

Pokazuje:
- Aktywną dziedzinę z progress bar
- Przegląd wszystkich dziedzin
- Aktywne kursy (jeśli są)

### `/quiz [concept]`
Quiz wiedzy

```bash
/quiz                           # Quiz z ostatniej lekcji
/quiz "async patterns"          # Quiz na konkretny temat
```

---

## 💡 Jak to działa?

1. **Podajesz cel nauki** - "Chcę nauczyć się X"
2. **Claude generuje kurs** - 3-7 lekcji dostosowanych do Ciebie
3. **Wykonujesz TODO(human)** - praktyczne zadania
4. **Quiz sprawdza wiedzę** - po każdej lekcji
5. **System śledzi postęp** - w kontekście dziedziny

### Przykładowy flow:

```
You: /learn "Redis caching w FastAPI"

Claude:
📚 Kurs: Redis Caching w FastAPI (5 lekcji, ~3h)
🔧 Dziedzina: Backend Development

Lekcja 1: Redis Basics & Installation
  - Instalacja Redis
  - Podstawowe komendy (GET, SET, EXPIRE)
  - TODO(human) 🟢: Zainstaluj Redis lokalnie, przetestuj komendy

Lekcja 2: FastAPI Integration
  ...

Rozpocząć? [y/n]
```

---

## 🔄 Czym to się różni od starej wersji?

| Feature | Stara wersja (v2.x) | Nowa wersja (v3.0) |
|---------|---------------------|---------------------|
| **Śledzenie** | Pasywne (PostToolUse hooks) | Brak - focus na kursy |
| **Główny flow** | Automatyczne wykrywanie konceptów | Kursy AI na żądanie |
| **Komendy** | 6 komend (`/concepts`, `/review`, itd.) | 3 komendy (`/learn`, `/progress`, `/quiz`) |
| **Dziedziny** | 11 (z kodem) | 7 (predefiniowane) |
| **Output** | Długi (~40 linii) | Krótki (max 15 linii) |
| **Kod** | ~7400 linii | ~2200 linii (-70%) |

**Główna zmiana:** Plugin **nie śledzi** Twoich akcji. Zamiast tego **aktywnie pomaga** poprzez AI-generowane kursy.

---

## ❓ FAQ

### **Q: Jak zacząć?**
A: Uruchom `/learn --domains`, wybierz dziedzinę, potem `/learn "co chcesz się nauczyć"`

### **Q: Czy muszę ręcznie dodawać koncepty?**
A: Nie. Koncepty są automatycznie wykrywane z ukończonych lekcji kursów.

### **Q: Jak zmienić dziedzinę?**
A: `/learn --domain <id>` (np. `/learn --domain ai_ml`)

### **Q: Co jeśli chcę uczyć się wielu dziedzin jednocześnie?**
A: Możesz - każda dziedzina ma własny tracking. Zmień aktywną przez `/learn --domain`.

### **Q: Czy mogę dodać własną dziedzinę?**
A: W v3.0 dziedziny są predefiniowane (7 głównych). Custom dziedziny będą w przyszłych wersjach.

---

## 🛠️ Techniczne Detale

**Struktura plików:**
```
learn-by-doing/
├── commands/
│   ├── learn.md           # Główna komenda
│   ├── progress.md        # Dashboard
│   └── quiz.md            # Quizy
├── data/
│   ├── domains.json       # 7 dziedzin
│   ├── knowledge_base.json # 47 konceptów
│   ├── active_courses.json # Aktywne kursy
│   └── config.json        # Konfiguracja
├── scripts/
│   ├── learn.py           # Entry point
│   ├── progress.py        # Dashboard
│   ├── progress_tracker.py # Tracking kursów
│   ├── quiz.py            # Quizy
│   ├── domain_manager.py  # CRUD dziedzin
│   ├── learning_graph.py  # Graf zależności
│   ├── recommendation_engine.py # Sugestie
│   ├── course_manager.py  # Zarządzanie kursami
│   └── course_planner.py  # AI-generowanie kursów
└── README.md
```

**Zależności:** Python stdlib only (json, pathlib, datetime)

---

## 📝 Changelog

**v3.0.0 (2025-11-02)** - Simplification Release
- ❌ Usunięto pasywne śledzenie (70% kodu mniej)
- ✅ Focus na AI-kursy na żądanie
- ✅ System dziedzin z ikonami
- ✅ Uproszczony knowledge base (120→47 konceptów)

**v2.3.0** - Interactive Course Planning
**v2.0.0** - Universal Learning System
**v1.0.0** - Initial Release

---

## 🤝 Wsparcie

Masz pytania? Otwórz issue na GitHub lub zapytaj Claude'a bezpośrednio!

**Made with ❤️ by Claude & Human**
