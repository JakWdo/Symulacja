# 🎓 Learn-by-Doing Plugin - Quick Start Guide

**Universal Learning System v2.0** - Naucz się WSZYSTKIEGO przez praktykę!

---

## 🚀 Czym Jest Ten Plugin?

**Learn-by-Doing** to inteligentny plugin dla Claude Code, który pomaga Ci uczyć się **dowolnej dziedziny** przez praktyczną pracę:
- 💻 **Data Science** - pandas, numpy, machine learning
- 🏗️ **System Design** - scalability, databases, caching
- 🧮 **Mathematics** - algebra, calculus, statistics
- 🤖 **Machine Learning** - supervised, unsupervised, deep learning
- 📊 **Algorithms** - sorting, searching, graphs, trees
- ...i **wszystko inne** czego chcesz się nauczyć!

---

## ⚡ Szybki Start (3 minuty)

### 1. Sprawdź Status Pluginu
```bash
/learn
```

Zobaczysz:
- 🎯 **Aktywną dziedzinę** (domyślnie: "Software Engineering")
- 📚 **Wszystkie dziedziny** które śledzisz
- 💡 **Dostępne szablony** (data-science, system-design, mathematics...)

### 2. Dodaj Swoją Pierwszą Dziedzinę
```bash
/learn data-science
```

System automatycznie:
- ✅ Dodaje dziedzinę "Data Science"
- 🎯 Ustawia ją jako aktywną
- 📋 Przygotowuje kategorie (pandas, numpy, matplotlib, sklearn, stats)

### 3. Rozpocznij Pracę!
**Po prostu zacznij pracować** nad zadaniami z tej dziedziny. Plugin automatycznie:
- 🔍 **Wykryje** używane biblioteki (import pandas, import numpy...)
- 📊 **Śledzi** Twój postęp
- 💡 **Wyjaśnia** dlaczego coś działa (nie tylko jak!)
- ✍️ **Zostawia TODO(human)** do samodzielnej implementacji

### 4. Sprawdź Postęp
```bash
/progress
```

Zobaczysz:
- 📈 **Globalne statystyki** (sesje, passa, aktywność)
- 🎓 **Progress per domena** (ile konceptów opanowałeś)
- 🎯 **Ostatnie quizy** (jeśli robiłeś)

### 5. Sprawdź Wiedzę
```bash
/quiz
```

Plugin wygeneruje quiz z **practiced concepts** - tylko te, które faktycznie używałeś!

---

## 🎯 Kluczowe Komendy

### Zarządzanie Dziedzinami

| Komenda | Opis |
|---------|------|
| `/learn` | Pokaż wszystkie dziedziny + status |
| `/learn data-science` | Dodaj Data Science (szablon) |
| `/learn "System Design"` | Dodaj custom dziedzinę |
| `/learn --list` | Lista wszystkich dziedzin |
| `/learn --active <id>` | Zmień aktywną dziedzinę |
| `/learn --remove <id>` | Usuń dziedzinę |

### Monitorowanie Postępu

| Komenda | Opis |
|---------|------|
| `/progress` | Dashboard - progress per domena + global stats |
| `/review` | Przegląd nauki (dzisiaj / tydzień) |
| `/concepts` | Lista wszystkich konceptów (static + discovered) |

### Quizy i Testy

| Komenda | Opis |
|---------|------|
| `/quiz` | Quiz z aktywnej dziedziny |
| `/quiz data-science` | Quiz z konkretnej dziedziny |
| `/quiz --show-answers` | Pokaż odpowiedzi na ostatni quiz (learning mode) |

---

## 📚 Dostępne Szablony Dziedzin

Plugin ma **5 gotowych szablonów**:

### 1. **Data Science** (`data-science`)
Analiza danych, wizualizacja, machine learning
- pandas, numpy, matplotlib, sklearn, stats

### 2. **System Design** (`system-design`)
Projektowanie skalowalnych systemów
- scalability, databases, caching, load-balancing, microservices

### 3. **Mathematics** (`mathematics`)
Matematyka dla programistów i data science
- linear-algebra, calculus, statistics, probability, optimization

### 4. **Machine Learning** (`machine-learning`)
Uczenie maszynowe i deep learning
- supervised, unsupervised, deep-learning, neural-networks, transformers

### 5. **Algorithms** (`algorithms`)
Algorytmy i struktury danych
- sorting, searching, graphs, trees, dynamic-programming

---

## 🔥 Przykładowy Workflow

```bash
# 1. Rozpocznij naukę Data Science
/learn data-science

# 2. Pracuj nad zadaniami (np. w Jupyter notebook, skryptach Python)
# Plugin automatycznie wykrywa:
# - import pandas → koncept "pandas basics"
# - import numpy → koncept "numpy arrays"
# - import matplotlib → koncept "visualization"

# 3. Po kilku sesjach sprawdź postęp
/progress
# Output:
# 🎯 Aktywna Dziedzina: Data Science
# Progress: 3/5 konceptów (60%)
# ████████████░░░ 60%

# 4. Test wiedzy (po ~5 sesjach)
/quiz
# Output:
# 🎯 QUIZ - Sprawdź Swoją Wiedzę
# Pytanie 1/5: Co to jest Pandas Basics?
# A. Biblioteka do analizy danych
# B. Framework webowy
# ...

# 5. Zmień dziedzinę (np. na System Design)
/learn --active system-design

# 6. Pokaż wszystkie dziedziny
/learn --list
# Output:
#    🟢 Data Science (3/5)
# ➡️ 🟢 System Design (0/8)
#    🟢 Software Engineering (0/45)
```

---

## 🎓 Jak To Działa?

### 1. **Auto-Discovery**
System automatycznie wykrywa:
- 📦 **Biblioteki** - importy w kodzie Python (pandas, numpy, sklearn...)
- 🗂️ **Config files** - Dockerfile, k8s.yaml, terraform.tf
- 🔧 **Technologie** - file extensions (.rs → Rust, .go → Go)

### 2. **Spaced Repetition**
Plugin przypomina o powtórkach:
- 1 dzień → Level 1 (Beginner)
- 3 dni → Level 2 (Intermediate)
- 7 dni → Level 3 (Proficient) ← **MASTERED**
- 14 dni → Level 4 (Advanced)
- 30 dni → Level 5 (Expert)

### 3. **Learning Mindset**
Przy każdej sesji dostajesz:
- 🎯 **Daily goals** (praktyka, pytania "dlaczego", szukanie patternów)
- 📋 **Do powtórki** (koncepty zgodnie ze spaced repetition)
- 🔥 **Passa dni** (motywacja!)

### 4. **Global Storage**
Dane są w **~/.claude/learn-by-doing/** - plugin działa **we wszystkich projektach**!

---

## 🔧 Konfiguracja (Opcjonalna)

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
    "prefer_category": null  // Możesz ustawić "Backend", "AI/ML", etc.
  },
  "log_rotation": {
    "max_practice_log_entries": 1000,  // Automatyczna archiwizacja po 1000 wpisów
    "archive_enabled": true             // Włącz/wyłącz archiwizację
  }
}
```

### 🗄️ Log Rotation (Nowe w v2.1.0!)

Plugin automatycznie archiwizuje stare wpisy w `practice_log.jsonl`:
- ✅ **Automatyczna rotacja** po przekroczeniu 1000 wpisów
- 📁 **Archiwa z datą** w `archives/practice_log_archive_YYYY-MM-DD.jsonl`
- 🚀 **Brak problemów z wydajnością** nawet przy długiej historii
- ⚙️ **Konfigurowalne** - ustaw własny limit w config.json

**Sprawdź statystyki:**
```bash
python3 ~/.claude/learn-by-doing/scripts/log_rotator.py
# Output:
# 📊 Log Statistics:
#   Current entries: 121
#   Max entries: 1000
#   Needs rotation: False
#   Total archived: 0
#   Total entries: 121
```

---

## 📁 Struktura Danych

```
~/.claude/learn-by-doing/
├── config.json                      # Konfiguracja pluginu
├── user_learning_domains.json       # Twoje dziedziny (NEW v2.0!)
├── learning_progress.json            # Progress (sessions, streak, concepts)
├── practice_log.jsonl                # Historia akcji (Write, Edit, Bash, Quiz) - max 1000 wpisów
├── knowledge_base.json               # Predefiniowane koncepty (software-engineering)
├── dynamic_concepts.json             # Auto-discovered koncepty
├── archives/                         # 📦 Archiwa logów (NEW v2.1.0!)
│   └── practice_log_archive_YYYY-MM-DD.jsonl   # Stare wpisy
└── prompts/
    └── learning_mindset.md           # Główny prompt uczący
```

**Nowe w v2.1.0:**
- ✨ UTC timestamps we wszystkich logach (spójność między strefami)
- 🗄️ Automatyczna archiwizacja `practice_log.jsonl` (katalog `archives/`)
- 🔧 Naprawiona detect concepts pattern matching (pełne ścieżki plików)

---

## ❓ FAQ

### **Q: Czy mogę uczyć się kilku dziedzin naraz?**
**A:** Tak! Plugin śledzi wszystkie dziedziny, ale masz **jedną aktywną** naraz. Przełączaj się komendą:
```bash
/learn --active data-science
```

### **Q: Skąd system wie czego się uczę?**
**A:** Z praktyki! System wykrywa:
1. **Importy w kodzie** (Python) - `import pandas` → "pandas basics"
2. **File extensions** - `.rs` → "Rust programming"
3. **Config files** - `Dockerfile` → "Docker containerization"

### **Q: Czy mogę dodać własną dziedzinę (bez szablonu)?**
**A:** Oczywiście!
```bash
/learn "Quantum Computing"
```
System utworzy custom dziedzinę. Możesz ręcznie dodać kategorie w `user_learning_domains.json`.

### **Q: Jak działają quizy?**
**A:** Quizy są generowane z **practiced concepts** - tylko te, które faktycznie używałeś! 3 typy pytań:
- **Multiple choice** - wybierz poprawną odpowiedź
- **True/False** - prawda czy fałsz
- **Fill-in-the-blank** - uzupełnij lukę

### **Q: Co jeśli zapomniałem o pojęciu?**
**A:** Użyj:
```bash
/quiz --show-answers
```
Zobaczysz poprawne odpowiedzi + wyjaśnienia (learning mode).

### **Q: Gdzie są przechowywane dane?**
**A:** W **global storage**: `~/.claude/learn-by-doing/`

Plugin działa **we wszystkich projektach** - nie musisz go instalować osobno w każdym!

---

## 🎯 Przykłady Użycia

### Data Science Workflow
```bash
# 1. Start
/learn data-science

# 2. Pracuj (Jupyter notebook, skrypty)
# Tworzysz: data_analysis.py z pandas, numpy, matplotlib

# 3. Plugin wykrywa automatycznie:
# ✅ pandas → koncept "pandas basics"
# ✅ numpy → koncept "numpy arrays"
# ✅ matplotlib → koncept "visualization"

# 4. Po 5 sesjach
/quiz
# Pytanie 1: Co to jest DataFrame w pandas?
# Pytanie 2: Jak stworzyć array w numpy?

# 5. Sprawdź progress
/progress
# Data Science: ███████████░░░ 75% (3/4)
```

### System Design Workflow
```bash
# 1. Start
/learn system-design

# 2. Pracuj (docker-compose, Kubernetes, caching)
# Tworzysz: docker-compose.yml, redis-config.yaml

# 3. Plugin wykrywa:
# ✅ Dockerfile → "Docker containerization"
# ✅ redis config → "Caching strategies"
# ✅ k8s.yaml → "Kubernetes orchestration"

# 4. Quiz
/quiz system-design
# Pytanie: Kiedy używamy Redis cache?

# 5. Progress
/progress
# System Design: █████░░░░░ 50% (4/8)
```

---

## 🚀 Co Dalej?

1. **Dodaj pierwszą dziedzinę** - `/learn data-science`
2. **Zacznij pracować** - plugin automatycznie śledzi
3. **Sprawdź postęp** - `/progress` co tydzień
4. **Testuj wiedzę** - `/quiz` co 5 sesji
5. **Dodaj kolejne dziedziny** - uczysz się wielowymiarowo!

---

## 📞 Pomoc

Problemy? Pytania?
- `/learn` - sprawdź status
- `/progress` - zobacz co już zrobiłeś
- Sprawdź logi: `~/.claude/learn-by-doing/practice_log.jsonl`

---

**Happy Learning!** 🎓🚀

Plugin działa **globalnie** - we wszystkich projektach.
Ucz się **dowolnej dziedziny** - data science, math, system design, i wiele więcej!
