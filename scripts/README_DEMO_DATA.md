# Zarządzanie Danymi Demo

Skrypty do zarządzania danymi demonstracyjnymi dla konta `demo@sight.pl`.

## Skrypty

### 1. `delete_demo_data.py` - Usuwanie danych demo

Usuwa wszystkie projekty wraz z powiązanymi danymi (persony, ankiety, focus groups).

#### Użycie

```bash
# Lokalne środowisko (localhost:8000)
python scripts/delete_demo_data.py

# Cloud Run (produkcja)
python scripts/delete_demo_data.py --cloud

# Tryb testowy (dry run) - nie usuwa, tylko pokazuje co by zostało usunięte
python scripts/delete_demo_data.py --cloud --dry-run

# Pomiń potwierdzenie (OSTROŻNIE!)
python scripts/delete_demo_data.py --cloud --yes

# Custom API endpoint
python scripts/delete_demo_data.py --api-base https://custom-api.example.com/api/v1
```

#### Parametry

- `--api-base` - URL API (domyślnie: `http://localhost:8000/api/v1`)
- `--cloud` - Użyj Cloud Run API (`https://sight-xfabt2svwa-lm.a.run.app/api/v1`)
- `--email` - Email konta demo (domyślnie: `demo@sight.pl`)
- `--password` - Hasło konta demo
- `--dry-run` - Tryb testowy bez faktycznego usuwania
- `--yes` - Pomiń potwierdzenie (użyj ostrożnie!)

#### Przykład

```bash
$ python scripts/delete_demo_data.py --cloud
======================================================================
USUWANIE DANYCH DEMO - SIGHT
======================================================================
API: https://sight-xfabt2svwa-lm.a.run.app/api/v1
Konto: demo@sight.pl
Tryb: PRODUKCJA (faktyczne usuwanie danych)
Data: 2025-01-14 20:30:00
======================================================================

⚠️  UWAGA! Ta operacja usunie WSZYSTKIE projekty i powiązane dane.
    Dane zostaną permanentnie usunięte z bazy danych!

Czy na pewno chcesz kontynuować? Wpisz 'TAK' aby potwierdzić: TAK

🔐 Logowanie jako demo@sight.pl...
✓ Zalogowano pomyślnie

📊 Znaleziono 4 projektów

======================================================================
USUWANIE PROJEKTÓW
======================================================================

[1/4] Kampania Profilaktyki Zdrowia Psychicznego
  📊 12 person, 2 ankiet, 1 focus groups
  ✓ Usunięto projekt: Kampania Profilaktyki Zdrowia Psychicznego
...

======================================================================
✓ USUWANIE DANYCH UKOŃCZONE
======================================================================
Projekty: 4/4 usuniętych
Łącznie usuniętych zasobów:
  - Persony: 48
  - Ankiety: 8
  - Focus Groups: 4
======================================================================
```

### 2. `create_demo_data_cloud.py` - Tworzenie danych demo

Tworzy nowe projekty demo z personami, ankietami i focus groups.

**UWAGA:** Teraz persony są generowane z `use_rag=True`, co oznacza że będą miały:
- Szczegółowe reasoning z orchestration
- Segment społeczny z charakterystykami
- Graph insights z polskich raportów demograficznych
- Allocation reasoning (dlaczego osoba trafiła do tego segmentu)

#### Użycie

```bash
# Cloud Run (produkcja)
python scripts/create_demo_data_cloud.py

# Tylko polskie projekty
python scripts/create_demo_data_cloud.py --account-type pl

# Tylko międzynarodowe projekty
python scripts/create_demo_data_cloud.py --account-type intl

# Oba typy (domyślne)
python scripts/create_demo_data_cloud.py --account-type both

# Custom API endpoint
python scripts/create_demo_data_cloud.py --api-base https://custom-api.example.com/api/v1
```

#### Parametry

- `--api-base` - URL API (domyślnie: Cloud Run)
- `--email` - Email konta demo (domyślnie: `demo@sight.pl`)
- `--password` - Hasło konta demo
- `--account-type` - Typ konta: `pl`, `intl`, `both` (domyślnie: `both`)

#### Projekty Demo

**Polskie (PL):**
1. Kampania Profilaktyki Zdrowia Psychicznego (12 person, 2 ankiety, 1 focus group)
2. Rewolucja Transportu Miejskiego 2025 (12 person, 1 ankieta, 1 focus group)

**Międzynarodowe (INTL):**
1. Mental Health Awareness Campaign (US) (12 person, 1 ankieta, 1 focus group)
2. Community Safety & Trust Program (12 person, 1 ankieta, 1 focus group)

#### Przykład

```bash
$ python scripts/create_demo_data_cloud.py --account-type pl
======================================================================
TWORZENIE DANYCH DEMO W CLOUD RUN - SIGHT
======================================================================
API: https://sight-xfabt2svwa-lm.a.run.app/api/v1
Konto: demo@sight.pl
Data: 2025-01-14 20:45:00
======================================================================

📊 Projektów do utworzenia: 2
⏱ Szacowany czas: ~6 minut

🔐 Logowanie jako demo@sight.pl...
✓ Zalogowano pomyślnie

[1/2]
======================================================================
PROJEKT: Kampania Profilaktyki Zdrowia Psychicznego
======================================================================
✓ Utworzono projekt: Kampania Profilaktyki Zdrowia Psychicznego (ID: abc123...)
  → Generowanie 12 person uruchomione (background)
  Czekam na wygenerowanie 12 person (max 120s)...
  ✓ Wygenerowano 12 person
  ✓ Utworzono ankietę: Bariery w dostępie do terapii
  → Zbieranie odpowiedzi uruchomione (background)
  ✓ Utworzono focus group: Jak zachęcić młodych do szukania pomocy?
  → Symulacja focus group uruchomiona (background)

✓ Projekt 'Kampania Profilaktyki Zdrowia Psychicznego' ukończony!
  - 12 person
  - 2/2 ankiet
  - 1/1 focus groups
...

======================================================================
✓ UKOŃCZONO TWORZENIE DANYCH DEMO!
======================================================================
Utworzono 2/2 projektów pomyślnie

Dostęp do platformy:
  Frontend: https://sight-xfabt2svwa-lm.a.run.app
  Email: demo@sight.pl
  Hasło: Demo2025!Sight
======================================================================
```

## Przepływ pracy: Odświeżenie danych demo

Aby całkowicie odświeżyć dane demo:

```bash
# 1. Usuń stare dane
python scripts/delete_demo_data.py --cloud --yes

# 2. Utwórz nowe dane z RAG reasoning
python scripts/create_demo_data_cloud.py --account-type both

# 3. Zweryfikuj dane (opcjonalnie)
python scripts/verify_demo_data.py
```

## Bezpieczeństwo

- Skrypty wymagają potwierdzenia przed usunięciem danych (chyba że `--yes`)
- Używają retry logic dla stabilności w Cloud Run
- Obsługują timeouty i błędy sieciowe
- Logują wszystkie operacje do stdout

## Troubleshooting

### Błąd logowania
```
✗ Błędne dane logowania dla demo@sight.pl
```
**Rozwiązanie:** Sprawdź czy konto demo istnieje w bazie. Użyj `scripts/register_cloud_account.py` aby je utworzyć.

### Timeout przy generacji person
```
⚠ Wygenerowano 8/12 person (timeout)
```
**Rozwiązanie:** To normalne w Cloud Run - generacja RAG person trwa dłużej (~60s dla 12 person). Skrypt czeka max 120s i kontynuuje z tym co się wygenerowało.

### Błąd 503 Service Unavailable
```
⚠ Create project attempt 1: 503
```
**Rozwiązanie:** Cloud Run cold start lub przeciążenie. Skrypt automatycznie retry 3x z 5s opóźnieniem.
