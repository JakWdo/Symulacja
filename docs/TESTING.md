# Strategia Testowania - Sight

## Wprowadzenie

System testów dla platformy Sight został zaprojektowany jako kompleksowy, wielowarstwowy mechanizm zapewnienia jakości oprogramowania. Nasz cel to nie tylko weryfikacja poprawności funkcjonalnej, ale również budowanie zaufania do systemu poprzez dokładne pokrycie różnych scenariuszy użycia.

Całkowita liczba testów wynosi około 380, podzielonych na kategorie: jednostkowe, integracyjne, end-to-end, wydajnościowe i obsługi błędów. Każda z tych kategorii pełni kluczową rolę w utrzymaniu wysokiej jakości oprogramowania.

## Test Pyramid

```
       ┌─────────────┐
       │   E2E (5%)  │  Selenium, Playwright
       ├─────────────┤
       │ Integration │  FastAPI TestClient
       │   (25%)     │  pytest-asyncio
       ├─────────────┤
       │   Unit      │  pytest, pytest-mock
       │   (70%)     │  Coverage >80%
       └─────────────┘
```

## Kategorie Testów

### Testy Jednostkowe (70%)

Testy jednostkowe stanowią fundament naszej strategii testowej. Obejmują one około 240 testów, które sprawdzają deterministyczne zachowanie poszczególnych komponentów systemu. Weryfikują logikę generatora person, serwisy RAG, walidatory oraz modele ORM.

### Testy Integracyjne (25%)

Około 70 testów integracyjnych sprawdza współpracę różnych komponentów systemu. Korzystają z prawdziwej bazy danych PostgreSQL oraz klienta FastAPI, weryfikując poprawność API, autentykację, zarządzanie projektami oraz generowanie person.

### Testy End-to-End (5%)

Cztery główne scenariusze end-to-end pokrywają pełne ścieżki użycia systemu, w tym rejestrację, generowanie person, przeprowadzenie badania fokusowego oraz analizę wyników.

## Infrastruktura Testowa

### Kluczowe Fixtures

Nasz system testowy wykorzystuje zaawansowane fixtures, które eliminują powtarzalny kod i przyspieszają pisanie testów. Przykładowe fixtures obejmują:

- `authenticated_client`: Zwraca klienta testowego z autoryzacją
- `project_with_personas`: Tworzy projekt z gotowymi personami
- `completed_focus_group`: Generuje kompletną grupę fokusową z odpowiedziami

### Markery Testów

Testy są oznaczone markerami, które pozwalają na selektywne uruchamianie:
- `@pytest.mark.integration`: Testy wymagające bazy danych
- `@pytest.mark.e2e`: Testy end-to-end
- `@pytest.mark.slow`: Testy trwające ponad 10 sekund

## Uruchamianie Testów

### Podstawowe Komendy

```bash
# Domyślny zestaw testów
python -m pytest -v

# Testy z raportem pokrycia
python -m pytest -v --cov=app --cov-report=html

# Testy end-to-end
python -m pytest tests/e2e/ -v --run-slow --run-external -s
```

## Cele Wydajnościowe

| Metryka | Cel | Idealnie |
|---------|-----|----------|
| Generowanie 20 person | <60s | 30-45s |
| Grupa fokusowa 20×4 | <3 min | <2 min |
| Średni czas odpowiedzi | <3s | 1-2s |

## Pokrycie Kodu

Aktualnie utrzymujemy pokrycie kodu powyżej 90%, z następującymi celami:

| Moduł | Cel | Aktualny Stan |
|-------|-----|---------------|
| Serwisy | 85%+ | ~92% |
| API | 85%+ | ~88% |
| Modele | 95%+ | ~96% |

## Rozwiązywanie Problemów

### Typowe Scenariusze

- **Brak połączenia z bazą:** Sprawdź status usług Docker
- **Problemy z Gemini API:** Zweryfikuj klucz API i quota
- **Testy End-to-End:** Użyj flag `--run-slow --run-external`

## Ciągła Integracja

Testy są zintegrowane z GitHub Actions, zapewniając automatyczną weryfikację każdego pull requesta. Wykonywane są zarówno szybkie testy (domyślnie), jak i pełny zestaw testów z usługami zewnętrznymi.

## Dodawanie Nowych Testów

Przy dodawaniu nowych testów stosuj się do zasad:
1. Najpierw test jednostkowy
2. Następnie test integracyjny, jeśli dotyczy interakcji
3. Opcjonalnie test end-to-end dla pełnego scenariusza

---

**Liczba testów:** ~380
**Ostatnia aktualizacja:** 2025-10-16
**Wersja:** 2.3
