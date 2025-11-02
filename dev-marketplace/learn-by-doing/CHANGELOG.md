# Changelog - Learn-by-Doing Plugin

Wszystkie istotne zmiany w pluginie Learn-by-Doing będą dokumentowane w tym pliku.

Format bazuje na [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
