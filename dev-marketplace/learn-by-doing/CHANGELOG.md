# Changelog - Learn-by-Doing Plugin

Wszystkie istotne zmiany w pluginie Learn-by-Doing będą dokumentowane w tym pliku.

Format bazuje na [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.0.0] - 2025-11-02 - **Simplification Release**

### 🎯 Major Changes

**Filozofia:** Od pasywnego trackera do aktywnego AI-asystenta nauczania

- **❌ Usunięto pasywne śledzenie** - brak SessionStart/PostToolUse hooks
- **✅ Focus na AI-kursy na żądanie** - główny flow: `/learn "cel"` → kurs
- **✅ System dziedzin z ikonami** - 7 predefiniowanych dziedzin
- **✅ Uproszczony knowledge base** - 120→47 core concepts
- **✅ Krótkie outputy** - max 15 linii (było ~40)

### ✅ Added (Dodano)

**Nowe pliki:**
- `data/domains.json` - 7 predefiniowanych dziedzin z ikonami (Backend, Frontend, AI/ML, Databases, DevOps, Testing, System Design)
- `scripts/progress_tracker.py` - Lightweight tracking tylko kursów (bez practice_log)
- `data/active_courses.json` - Tracking aktywnych kursów

**Nowe funkcje:**
- Domain filtering w recommendation_engine
- Uproszczony dashboard (`/progress`) - dziedziny + kursy
- Welcome screen z ikonami dziedzin (`/learn`)

### ❌ Removed (Usunięto) - **65% redukcja kodu**

**Pliki Python (12 skryptów):**
- `track_practice.py` - Pasywne śledzenie akcji
- `concept_detector.py` - Pattern matching
- `auto_discovery.py` - Autodiscovery technologii
- `update_progress.py` - Złożony orchestrator
- `session_start.py` - Gadatliwy welcome screen
- `session_start_wrapper.sh` - Hook wrapper
- `log_rotator.py` - Archiwizacja logów
- `tech_classifier.py` - Klasyfikacja technologii
- `track_concepts.py`, `concepts.py`, `review.py`, `concept_manager.py`

**Pliki danych:**
- `practice_log.jsonl` - Event log akcji
- `dynamic_concepts.json` - Odkryte koncepty

**Komendy (3 usunięte):**
- `/concepts` - Lista konceptów
- `/review` - Przegląd nauki
- `/track-concepts` - Ręczne trackowanie

**Testy (2 pliki):**
- `test_track_practice.py`
- `test_log_rotation.py`

**Hooki:**
- SessionStart hook - usunięty z `hooks.json`
- PostToolUse hook - usunięty z `hooks.json`

### 🔄 Refactored (Zrefaktoryzowano)

**learn.py** (337→215 linii, -36%)
- Usunięto: `add_new_domain()`, `add_domain_from_template()`, `remove_domain_command()`, legacy commands (on/off/status)
- Uproszczono: `show_domains_status()` → `show_welcome()` (krótszy output)
- Dodano: Integrację z course_planner dla głównego flow

**progress.py** (175→140 linii, -20%)
- Usunięto: `load_practice_log()`, `load_dynamic_concepts()`, `count_actions_by_type()`, recent quizzes section
- Zachowano: `render_progress_bar()`, domain progress overview
- Uproszczono: Dashboard do max 15 linii outputu

**recommendation_engine.py** (+50 linii, nowa funkcjonalność)
- Zmieniono: `category` → `domain` w całym pliku
- Dodano: `domain_id` parameter w `suggest_next_concepts()`
- Dodano: Domain filtering w rekomendacjach
- Zaktualizowano: `_get_recent_categories()` → `_get_recent_domains()`

**knowledge_base.json** (843→340 linii, -60%)
- Uproszczono: 120→47 konceptów (najważniejsze)
- Usunięto: Pattern matching (`patterns` field)
- Zmieniono: `category` → `domain`
- Struktura: Tylko `name`, `domain`, `difficulty`, `description`, `prerequisites`, `next_steps`

### 📝 Documentation (Dokumentacja)

**README.md** - Całkowicie przepisany (1 strona)
- Quick Start (3 kroki)
- Tabela 7 dziedzin z ikonami
- Przykładowy flow kursu
- Porównanie v2.x vs v3.0
- FAQ (5 pytań)
- Techniczne detale

**Command descriptions:**
- `learn.md` - Zaktualizowany opis usage
- `progress.md` - Nowy krótki opis
- `quiz.md` - Zaktualizowany format

### 📊 Metrics (Metryki)

| Metryka | v2.3 (przed) | v3.0 (po) | Zmiana |
|---------|--------------|-----------|---------|
| **Linie kodu (scripts)** | ~7400 | ~2200 | **-70%** |
| **Pliki Python** | 26 | 9 | **-65%** |
| **Komendy** | 6 | 3 | **-50%** |
| **knowledge_base** | 120 | 47 | **-61%** |
| **Dziedziny** | 11 (z kodem) | 7 (config) | Uproszczone |
| **Session start output** | ~40 linii | 0 (brak hooka) | **-100%** |
| **learn.py** | 337 | 215 | **-36%** |
| **progress.py** | 175 | 140 | **-20%** |

### 🐛 Fixes (Naprawione)

- Usunięto dependency na usunięte moduły (track_practice, concept_detector, etc.)
- Naprawiono hooki blokujące wykonanie narzędzi
- Usunięto duplikację logowania danych

### ⚠️ Breaking Changes

1. **Brak pasywnego śledzenia** - plugin nie śledzi automatycznie akcji użytkownika
2. **Nowe komendy** - stare komendy `/concepts`, `/review`, `/track-concepts` nie działają
3. **Nowa struktura danych** - `practice_log.jsonl` i `dynamic_concepts.json` nie są używane
4. **Dziedziny** - custom dziedziny nie są wspierane w v3.0 (7 predefiniowanych)

### 🔮 Migration Guide

**Z v2.x do v3.0:**

1. **Dane postępów są zachowane** - `learning_progress.json` jest kompatybilny
2. **Hooki są wyłączone** - usuń konfigurację SessionStart/PostToolUse jeśli masz własną
3. **Nowy workflow:**
   - Zamiast: Plugin automatycznie wykrywa → `/progress` → `/review`
   - Teraz: `/learn "cel"` → pracuj nad TODO(human) → `/quiz` → `/progress`

4. **Stare komendy:**
   - `/learn status` → `/learn` (welcome screen)
   - `/concepts` → `/learn --domains` (dziedziny)
   - `/review` → `/progress` (dashboard)

---

## [2.1.0] - 2025-11-02

### 🔧 Fixed (Naprawiono)

#### Krytyczny błąd - Utrata ścieżek plików
**Problem:** `track_practice.py` zapisywał tylko nazwy plików zamiast pełnych ścieżek.

**Przykład:**
```python
# PRZED (błąd):
"file": "persona_generator.py"  # ❌ utracona informacja o ścieżce

# PO (poprawka):
"file": "app/services/personas/persona_generator.py"  # ✅ pełna ścieżka
```

**Impact:**
- Concept detection nie działał poprawnie (nie mógł matchować patterns typu `app/api/*.py`)
- Utrata informacji o strukturze projektu
- Potencjalne konflikty przy plikach o tej samej nazwie

**Naprawione pliki:**
- `scripts/track_practice.py:85` - usunięto `path_obj.name`
- `scripts/track_practice.py:100` - zmieniono `file_name` na `file_path`

---

#### Timestamps bez UTC
**Problem:** Wszystkie timestamps używały lokalnego czasu (`datetime.now()`) zamiast UTC.

**Impact:**
- Niespójności przy porównywaniu dat między strefami czasowymi
- Problemy z obliczaniem "dni od ostatniej praktyki"
- Niepoprawne działanie spaced repetition

**Naprawione pliki:**
- `scripts/track_practice.py:14,164` - dodano `timezone` i zmieniono na `.now(timezone.utc)`
- `scripts/quiz_generator.py:16,293`
- `scripts/update_progress.py:20,158`
- `scripts/data_manager.py:14,437,569,604,617,667` - 5 miejsc
- `scripts/domain_manager.py:16,64,269,339` - 3 miejsca
- `scripts/review.py:8,39`

**Łącznie:** 7 plików, 14 linii zmienione

---

### ✨ Added (Dodano)

#### System rotacji logów z archiwizacją
**Problem:** `practice_log.jsonl` rósł bez limitu, potencjalne problemy z wydajnością.

**Rozwiązanie:** Automatyczna archiwizacja starych wpisów.

**Nowy moduł:** `scripts/log_rotator.py`
- Klasa `LogRotator` - zarządzanie rotacją
- Automatyczne tworzenie archiwów: `data/archives/practice_log_archive_YYYY-MM-DD.jsonl`
- Zachowywanie tylko najnowszych N wpisów (domyślnie 1000)
- Możliwość manualnego uruchomienia: `python3 scripts/log_rotator.py`

**Integracja:**
- `scripts/data_manager.py:18-24` - import `log_rotator`
- `scripts/data_manager.py:452-458` - wywołanie rotacji po każdym zapisie
- `data/config.json:28-31` - nowa konfiguracja:
  ```json
  "log_rotation": {
    "max_practice_log_entries": 1000,
    "archive_enabled": true
  }
  ```

**Funkcjonalność:**
- 🔄 Automatyczna rotacja przy zapisie do logu
- 📁 Archiwa z datą w nazwie
- 📊 Statystyki: `LogRotator.get_stats()`
- ⚙️ Konfigurowalne limity

---

#### Testy jednostkowe
**Dodano:** 2 pliki testowe z 30+ testami

**test_track_practice.py** (23 testy):
- ✅ Weryfikacja zachowania pełnych ścieżek
- ✅ Wykrywanie typów plików (service, api_endpoint, test)
- ✅ Wykrywanie języków (Python, JS, TS, Rust, Go)
- ✅ Pattern matching z concept_detector
- ✅ UTC timestamps
- ✅ Import detection

**test_log_rotation.py** (13 testów):
- ✅ Tworzenie katalogów archiwum
- ✅ Rotacja przy przekroczeniu limitu
- ✅ Zachowywanie najnowszych wpisów
- ✅ Tworzenie plików archiwum z datą
- ✅ Statystyki logów
- ✅ Wielokrotne rotacje

**Uruchomienie testów:**
```bash
# Jeśli masz pytest:
pytest tests/ -v

# Manualne testy:
python3 -c "from track_practice import extract_context; ..."
python3 scripts/log_rotator.py
```

---

### 🔄 Changed (Zmieniono)

#### Config.json - nowa sekcja
Dodano konfigurację rotacji logów:

```json
"log_rotation": {
  "max_practice_log_entries": 1000,  // Limit wpisów w głównym logu
  "archive_enabled": true             // Włącz/wyłącz archiwizację
}
```

---

## Migracja dla istniejących użytkowników

### Automatyczna
Większość zmian jest **backward compatible**:
- ✅ Stare wpisy w `practice_log.jsonl` z krótkimi ścieżkami będą nadal działać
- ✅ Nowe wpisy będą miały pełne ścieżki
- ✅ Rotacja logów włączy się automatycznie
- ✅ Config będzie automatycznie uzupełniony o brakujące pola

### Opcjonalna (zalecana)
Jeśli chcesz naprawić stare wpisy:

1. **Backup istniejącego logu:**
   ```bash
   cp data/practice_log.jsonl data/practice_log_backup.jsonl
   ```

2. **Uruchom skrypt naprawczy** (jeśli dostępny):
   ```bash
   python3 scripts/migrate_old_logs.py
   ```

3. **Lub wyczyść log i zacznij od nowa:**
   ```bash
   mv data/practice_log.jsonl data/practice_log_old.jsonl
   touch data/practice_log.jsonl
   ```

---

## Breaking Changes

### ⚠️ Brak
Wszystkie zmiany są backward compatible. Stare dane będą działać, ale nowe dane będą miały poprawiony format.

---

## Testy

### Ręczna weryfikacja
```bash
# Test 1: Sprawdź czy ścieżki są zachowane
cd scripts
python3 -c "
from track_practice import extract_context
context = extract_context({'file_path': 'app/services/test.py'})
print('Full path:', context['file'])
assert context['file'] == 'app/services/test.py', 'FAIL!'
print('✅ PASS')
"

# Test 2: Sprawdź rotację logów
python3 log_rotator.py
```

### Automatyczne (wymagany pytest)
```bash
cd tests
pytest test_track_practice.py -v
pytest test_log_rotation.py -v
```

---

## Co dalej?

### Planned (następne wersje)
- [ ] Import detection dla JS/TS (obecnie tylko Python)
- [ ] Package manager parsing (requirements.txt, package.json)
- [ ] Bash command analysis
- [ ] AI-powered concept summaries
- [ ] Quiz system improvements

---

## Contributors
- Automatyczna naprawa: Claude Code
- Analiza błędów: Code review

---

## Licencja
Część projektu Learn-by-Doing Plugin
