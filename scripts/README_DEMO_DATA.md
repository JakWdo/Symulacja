# Dane Demonstracyjne - Sight Platform

Ten dokument opisuje system zarządzania danymi demonstracyjnymi dla platformy Sight w środowisku Cloud Run. System umożliwia automatyczne tworzenie i usuwanie kompletnych kont demo z projektami badawczymi, personami, ankietami i focus groups.

## Przegląd

Platforma Sight wykorzystuje dwa dedykowane konta demonstracyjne do prezentacji funkcjonalności systemu potencjalnym użytkownikom i podczas testów integracyjnych. Każde konto reprezentuje inny profil użytkownika i zawiera projekty badawcze dostosowane do specyficznego rynku.

### Konta Demo

**Konto Polskie (demo-pl@sight.pl)**

Przeznaczone dla polskiego rynku, zawiera projekty badawcze skoncentrowane na lokalnym kontekście społecznym i kulturowym. Wszystkie projekty używają języka polskiego, a persony są generowane z wykorzystaniem polskich danych demograficznych i Graph RAG opartego na raportach GUS oraz badaniach społecznych prowadzonych w Polsce.

- Email: `demo-pl@sight.pl`
- Hasło: `DemoPL2025!Sight`
- Język interfejsu: Polski
- Projekty: 2 kompletne projekty badawcze
  - Kampania Profilaktyki Zdrowia Psychicznego (12 person, 2 ankiety, 1 focus group)
  - Rewolucja Transportu Miejskiego 2025 (12 person, 1 ankieta, 1 focus group)

**Konto Międzynarodowe (demo-intl@sight.pl)**

Przeznaczone dla międzynarodowych użytkowników, szczególnie z rynku amerykańskiego. Zawiera projekty biznesowe i społeczne typowe dla kontekstu anglojęzycznego, z personami generowanymi w oparciu o amerykańskie dane demograficzne.

- Email: `demo-intl@sight.pl`
- Hasło: `DemoINTL2025!Sight`
- Język interfejsu: Angielski
- Projekty: 2 kompletne projekty badawcze
  - Mental Health Awareness Campaign (US) (12 person, 1 ankieta, 1 focus group)
  - Community Safety & Trust Program (12 person, 1 ankieta, 1 focus group)

## Tworzenie Danych Demo

Skrypt `create_demo_data_cloud.py` automatycznie tworzy kompletne środowisko demonstracyjne w Cloud Run. Proces obejmuje rejestrację konta (jeśli nie istnieje), utworzenie team, environments, projektów, generację person z Graph RAG, oraz uruchomienie ankiet i focus groups.

### Podstawowe Użycie

Utworzenie danych demo dla obu kont (domyślne):

```bash
cd scripts
python3 create_demo_data_cloud.py
```

Skrypt automatycznie:
1. Zarejestruje konta demo-pl@sight.pl i demo-intl@sight.pl (jeśli nie istnieją)
2. Zaloguje się do każdego konta
3. Utworzy team "Demo Team" dla każdego konta
4. Utworzy environments dla projektów
5. Utworzy projekty badawcze z pełną konfiguracją
6. Wygeneruje persony (z Graph RAG i orchestration)
7. Uruchomi zbieranie odpowiedzi na ankiety
8. Uruchomi symulacje focus groups

Szacowany czas wykonania: około 12-15 minut dla obu kont (4 projekty, 48 person total).

### Opcje Zaawansowane

**Tworzenie tylko polskiego konta:**

```bash
python3 create_demo_data_cloud.py --account-type pl
```

Utworzy tylko konto demo-pl@sight.pl z dwoma polskimi projektami (Zdrowie Psychiczne + Transport Miejski). Czas wykonania: około 6-8 minut.

**Tworzenie tylko konta międzynarodowego:**

```bash
python3 create_demo_data_cloud.py --account-type intl
```

Utworzy tylko konto demo-intl@sight.pl z dwoma projektami międzynarodowymi (Mental Health + Community Safety). Czas wykonania: około 6-8 minut.

**Niestandardowy endpoint API:**

```bash
python3 create_demo_data_cloud.py --api-base https://custom-instance.run.app/api/v1
```

Przydatne podczas testowania na środowiskach pre-production lub lokalnych instancjach.

### Monitoring Postępu

Skrypt wyświetla szczegółowe logi podczas wykonywania:

```
======================================================================
TWORZENIE DANYCH DEMO W CLOUD RUN - SIGHT
======================================================================
API: https://sight-193742683473.europe-central2.run.app/api/v1
Data: 2025-11-15 14:30:00
Tryb: both
======================================================================

======================================================================
KONTO: demo-pl@sight.pl
Opis: Konto demonstracyjne z polskimi projektami badawczymi
Język: pl
======================================================================

🔐 Logowanie jako demo-pl@sight.pl...
✓ Zalogowano pomyślnie

🏢 Sprawdzanie team dla demo-pl@sight.pl...
  ✓ Znaleziono team: Demo Team (ID: ...)

======================================================================
PROJEKT: Kampania Profilaktyki Zdrowia Psychicznego
======================================================================
  ✓ Utworzono environment: Środowisko: Kampania Profilaktyki Zdrowia Psychicznego
✓ Utworzono projekt: Kampania Profilaktyki Zdrowia Psychicznego (ID: ...)
  → Generowanie 12 person uruchomione (background)
  Czekam na wygenerowanie 12 person (max 300s)...
    ... 6/12 person (czas: 45s)
  ✓ Wygenerowano 12 person
  ✓ Utworzono ankietę: Bariery w dostępie do terapii
  → Zbieranie odpowiedzi uruchomione (background)
  ✓ Utworzono ankietę: Postrzeganie zdrowia psychicznego
  → Zbieranie odpowiedzi uruchomione (background)
  ✓ Utworzono focus group: Jak zachęcić młodych do szukania pomocy?
  → Symulacja focus group uruchomiona (background)

✓ Projekt 'Kampania Profilaktyki Zdrowia Psychicznego' ukończony!
  - 12 person
  - 2/2 ankiet
  - 1/1 focus groups
```

### Retry Logic i Odporność na Błędy

Skrypt zawiera automatyczne mechanizmy retry dla wszystkich operacji sieciowych. W przypadku tymczasowych błędów (timeouty, błędy 500, problemy sieciowe), każda operacja jest powtarzana do 3 razy z 5-sekundowymi przerwami między próbami.

Jeśli jedno konto nie może być utworzone (np. problemy z siecią, błędy API), skrypt kontynuuje pracę z pozostałymi kontami zamiast przerywać całą operację. Podsumowanie finalne pokazuje szczegóły sukcesu i błędów per konto.

## Usuwanie Danych Demo

Skrypt `delete_demo_accounts.py` usuwa wszystkie dane z kont demonstracyjnych, przywracając je do stanu początkowego. Jest to przydatne przed utworzeniem świeżych danych demo lub podczas czyszczenia środowiska testowego.

### Podstawowe Użycie

Usunięcie danych z obu kont (z potwierdzeniem):

```bash
cd scripts
python3 delete_demo_accounts.py
```

Skrypt poprosi o potwierdzenie przed rozpoczęciem usuwania:

```
======================================================================
USUWANIE DANYCH DEMO W CLOUD RUN - SIGHT
======================================================================
API: https://sight-193742683473.europe-central2.run.app/api/v1
Data: 2025-11-15 15:00:00
Tryb: both
======================================================================

⚠️  OSTRZEŻENIE: Ten skrypt usunie WSZYSTKIE dane z następujących kont:
  - demo-pl@sight.pl
  - demo-intl@sight.pl

Czy na pewno chcesz kontynuować? (wpisz 'TAK' aby potwierdzić):
```

Wpisz dokładnie `TAK` (wielkie litery) aby kontynuować. Jakikolwiek inny input anuluje operację.

### Opcje Zaawansowane

**Usuwanie bez potwierdzenia (automatyzacja):**

```bash
python3 delete_demo_accounts.py --confirm
```

Przydatne w skryptach CI/CD lub automatycznych workflow. UWAGA: Używaj ostrożnie, nie będzie promptu potwierdzającego!

**Usuwanie tylko polskiego konta:**

```bash
python3 delete_demo_accounts.py --account-type pl
```

**Usuwanie tylko konta międzynarodowego:**

```bash
python3 delete_demo_accounts.py --account-type intl
```

### Co Jest Usuwane

Skrypt usuwa dane w następującej kolejności:

1. **Projekty** - Wszystkie projekty badawcze wraz z:
   - Personami (wraz z reasoning i orchestration data)
   - Ankietami i odpowiedziami
   - Focus groups i dyskusjami
   - Wszystkimi powiązanymi danymi

2. **Environments** - Wszystkie środowiska utworzone dla projektów

3. **Teams** - Dodatkowe teams (domyślny "Demo Team" jest pomijany, ponieważ użytkownik musi mieć przynajmniej jeden team)

UWAGA: Samo konto użytkownika NIE jest usuwane. Skrypt usuwa tylko dane utworzone przez skrypt create_demo_data_cloud.py, pozostawiając puste konto gotowe do ponownego użycia.

### Monitoring Usuwania

```
======================================================================
KONTO: demo-pl@sight.pl
======================================================================

🔐 Logowanie jako demo-pl@sight.pl...
✓ Zalogowano pomyślnie

🗑️  Usuwanie projektów...
  ✓ Usunięto projekt: Kampania Profilaktyki Zdrowia Psychicznego
  ✓ Usunięto projekt: Rewolucja Transportu Miejskiego 2025
  → Usunięto 2/2 projektów

🗑️  Usuwanie environments...
  ✓ Usunięto environment: Środowisko: Kampania Profilaktyki Zdrowia Psychicznego
  ✓ Usunięto environment: Środowisko: Rewolucja Transportu Miejskiego 2025
  → Usunięto 2/2 environments

🗑️  Usuwanie teams...
  → Pominięto domyślny team: Demo Team
  → Usunięto 0/1 teams

======================================================================
✓ UKOŃCZONO USUWANIE: demo-pl@sight.pl
======================================================================
  Projekty: 2
  Environments: 2
  Teams: 0
```

## Workflow: Odświeżanie Danych Demo

Typowy proces odświeżania danych demo (np. przed demo dla klienta lub po wprowadzeniu zmian w generacji person):

```bash
# 1. Usuń stare dane
python3 delete_demo_accounts.py --confirm

# 2. Poczekaj na zakończenie (~2 minuty)

# 3. Utwórz świeże dane
python3 create_demo_data_cloud.py

# 4. Poczekaj na zakończenie (~12-15 minut)

# 5. Weryfikuj przez UI
open https://sight-193742683473.europe-central2.run.app
```

Całkowity czas: około 17-20 minut.

## Zawartość Projektów Demo

### Polskie Projekty

**Kampania Profilaktyki Zdrowia Psychicznego**

Projekt badawczy dotyczący barier w dostępie do terapii i postrzegania zdrowia psychicznego wśród młodych Polaków. Cel biznesowy: opracowanie kampanii edukacyjnej zmniejszającej stygmatyzację.

Grupa docelowa:
- Wiek: 20-40 lat
- Lokalizacja: Duże miasta Polski (Warszawa, Kraków, Wrocław, Gdańsk, Poznań)
- Wykształcenie: Średnie do wyższego magisterskiego
- Wielkość próby: 12 person

Badania:
- Ankieta "Bariery w dostępie do terapii" (4 pytania, 500 odpowiedzi docelowych)
- Ankieta "Postrzeganie zdrowia psychicznego" (4 pytania, 500 odpowiedzi docelowych)
- Focus group "Jak zachęcić młodych do szukania pomocy?" (3 pytania dyskusyjne)

Persony generowane z Graph RAG wykorzystującym polskie raporty o zdrowiu psychicznym, dane GUS oraz badania społeczne CBOS.

**Rewolucja Transportu Miejskiego 2025**

Projekt badawczy dotyczący potrzeb mieszkańców w zakresie komunikacji miejskiej, ekologii i innowacji w transporcie publicznym. Cel: rekomendacje dla władz miejskich.

Grupa docelowa:
- Wiek: 18-54 lata
- Lokalizacja: Duże miasta Polski
- Regularni użytkownicy transportu publicznego
- Wielkość próby: 12 person

Badania:
- Ankieta "Twoje doświadczenia z komunikacją miejską" (4 pytania, 500 odpowiedzi docelowych)
- Focus group "Jak poprawić transport publiczny?" (3 pytania dyskusyjne)

Persony generowane z wykorzystaniem polskich danych o mobilności miejskiej i preferencjach transportowych.

### Projekty Międzynarodowe

**Mental Health Awareness Campaign (US)**

Research project exploring mental health barriers and stigma in American workplaces. Business goal: develop corporate mental health program recommendations.

Target audience:
- Age: 25-45 years
- Location: US urban areas (New York, Los Angeles, Chicago, San Francisco, Austin)
- Professional backgrounds across various industries
- Sample size: 12 personas

Research:
- Survey "Mental Health in the Workplace Survey" (4 questions, 500 target responses)
- Focus group "Building Supportive Workplace Culture" (3 discussion questions)

Personas generated using US demographic data and workplace culture insights.

**Community Safety & Trust Program**

Research project building trust between local communities and government through safety initiatives. Goal: design community engagement strategies.

Target audience:
- Age: 30-60 years
- Location: US urban communities (New York, Chicago, Houston, Philadelphia, Phoenix)
- Diverse demographics
- Sample size: 12 personas

Research:
- Survey "Trust in Local Governance Survey" (4 questions, 500 target responses)
- Focus group "Building Community Trust Discussion" (3 discussion questions)

Personas generated with focus on community engagement and local governance perspectives.

## Techniczne Szczegóły

### Generacja Person z Graph RAG

Wszystkie persony w projektach demo są generowane z flagą `use_rag: true`, co oznacza pełne wykorzystanie systemu Graph RAG oraz orchestration. Każda persona otrzymuje:

**Orchestration Brief** (900-1200 znaków) - Kontekst społeczny segmentu demograficznego:
- Charakterystyki społeczno-ekonomiczne
- Typowe wzorce behawioralne
- Wartości i przekonania dominujące w segmencie
- Contextualized insights z Graph RAG

**Graph Insights** - Strukturalna wiedza z Neo4j:
- Nodes: Obserwacja, Wskaźnik, Trend, Demografia
- Relationships: RELATED_TO, INFLUENCES, MEASURED_BY
- Metadata: confidence scores, time periods, sources

**Allocation Reasoning** - Uzasadnienie dlaczego persona trafiła do tego segmentu:
- Dopasowanie demograficzne
- Statystyczna reprezentatywność
- Zgodność z celami badawczymi

To powoduje, że persony są znacznie bardziej realistyczne i spójne z rzeczywistymi danymi demograficznymi niż generacja bez RAG.

### Timeout i Limity

**Generacja person:** Max 300 sekund (5 minut) na batch 12 person
- Typowy czas: 60-90 sekund dla batch z Graph RAG
- Background task - nie blokuje innych operacji

**Ankiety:** Background task, instant response
- Faktyczne zbieranie odpowiedzi trwa 1-3 minuty w tle
- 500 odpowiedzi per ankieta (mix wszystkich person)

**Focus groups:** Background task, instant response
- Faktyczna symulacja dyskusji trwa 2-4 minuty w tle
- 3-4 rundy dyskusji per grupa

### Retry Configuration

Wszystkie operacje sieciowe używają:
- Max retries: 3 próby
- Delay: 5 sekund między próbami
- Timeouts: 30-60 sekund per request

## Troubleshooting

### Problem: Konto już istnieje ale nie mogę się zalogować

**Symptom:**
```
✗ Błędne dane logowania dla demo-pl@sight.pl
```

**Przyczyna:** Hasło dla konta zostało zmienione lub konto zostało ręcznie utworzone z innym hasłem.

**Rozwiązanie:**
1. Zresetuj hasło przez panel admin w Cloud Run
2. LUB usuń konto przez panel admin i pozwól skryptowi je ponownie utworzyć
3. LUB zaktualizuj ACCOUNT_CONFIGS w skrypcie z prawidłowym hasłem

### Problem: Timeout podczas generacji person

**Symptom:**
```
⚠ Wygenerowano 6/12 person (timeout)
```

**Przyczyna:** Graph RAG może być wolny przy pierwszym uruchomieniu (cold start Neo4j) lub Gemini API rate limiting.

**Rozwiązanie:**
1. Uruchom skrypt ponownie - Neo4j będzie już "warm"
2. Zwiększ timeout w linii 296: `max_wait=300` → `max_wait=420` (7 min)
3. Sprawdź czy Neo4j jest dostępny w Cloud Run

### Problem: Błędy 500 przy tworzeniu environments

**Symptom:**
```
⚠ Create environment attempt 1: 500
```

**Przyczyna:** Backend może mieć problemy z modelem ENUM lub Neo4j connection.

**Rozwiązanie:**
1. Sprawdź logi Cloud Run: `gcloud run services logs read sight --region europe-central2 --limit 50`
2. Jeśli błąd dotyczy ENUM - sprawdź czy migracje zostały zastosowane
3. Jeśli błąd dotyczy Neo4j - sprawdź health check w logach
4. Skrypt automatycznie kontynuuje bez environments jeśli fail (projekty mogą być tworzone bez environment)

### Problem: Persony bez reasoning

**Symptom:** W UI zakładka "Uzasadnienie" jest pusta lub pokazuje żółty banner.

**Przyczyna:** Orchestration jest wyłączone w config lub Graph RAG jest niedostępny.

**Rozwiązanie:**
1. Sprawdź `config/features.yaml`: `orchestration.enabled: true`
2. Sprawdź logi Cloud Run czy Neo4j jest dostępny
3. Zobacz szczegółowy troubleshooting w `CLAUDE.md` sekcja "Troubleshooting: Brak Reasoning w Personach"

## Dostęp do Utworzonych Danych

Po pomyślnym uruchomieniu `create_demo_data_cloud.py`, dane są dostępne przez:

**Frontend UI:**
```
https://sight-193742683473.europe-central2.run.app
```

Zaloguj się używając:
- Konto PL: demo-pl@sight.pl / DemoPL2025!Sight
- Konto INTL: demo-intl@sight.pl / DemoINTL2025!Sight

**API (dla testów integracyjnych):**
```bash
# 1. Zaloguj się
curl -X POST https://sight-193742683473.europe-central2.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo-pl@sight.pl", "password": "DemoPL2025!Sight"}'

# 2. Użyj tokenu w kolejnych requestach
curl https://sight-193742683473.europe-central2.run.app/api/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Bezpieczeństwo

**UWAGA:** Hasła do kont demo są hardcoded w skryptach i MUSZĄ być traktowane jako publiczne. NIE używaj tych kont do przechowywania wrażliwych danych produkcyjnych.

Konta demo są przeznaczone wyłącznie do celów demonstracyjnych i testowych. W środowisku produkcyjnym:
- Dane demo są regularnie czyszczone (co tydzień)
- Konta nie mają dostępu do danych produkcyjnych innych użytkowników
- Rate limiting jest włączony dla wszystkich operacji

## Automatyzacja (CI/CD)

Przykładowy workflow GitHub Actions do odświeżania danych demo co tydzień:

```yaml
name: Refresh Demo Data

on:
  schedule:
    - cron: '0 2 * * 0'  # Co niedzielę o 2:00 AM
  workflow_dispatch:  # Manual trigger

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install httpx asyncio

      - name: Delete old data
        run: |
          cd scripts
          python3 delete_demo_accounts.py --confirm

      - name: Create fresh data
        run: |
          cd scripts
          python3 create_demo_data_cloud.py

      - name: Verify data
        run: |
          # Add verification logic here
          echo "Demo data refreshed successfully"
```

## Kontakt i Wsparcie

W przypadku problemów lub pytań dotyczących danych demo:
1. Sprawdź ten dokument (README_DEMO_DATA.md)
2. Sprawdź główną dokumentację (CLAUDE.md)
3. Sprawdź logi Cloud Run dla szczegółów błędów
4. Otwórz issue w repo z tagiem `demo-data`
