# Archived Persona Actions Services

**Data archiwizacji:** 2025-10-20
**Powód:** Endpoints nieużywane przez frontend - brak odpowiednich komponentów UI

## Serwisy

### 1. `persona_messaging_service.py`
**Funkcjonalność:** Generowanie marketing messaging dla person (email copy, ad copy, social media)

**Endpoint:** `POST /api/v1/personas/{id}/actions/messaging`

**Dlaczego zarchiwizowane:**
- Brak UI component w frontend (MessagingGeneratorDialog nie jest importowany)
- Hook useGenerateMessaging nie jest używany
- Feature nigdy nie został zintegrowany z UX

**Jak przywrócić:**
1. Przenieś serwis z powrotem do `app/services/`
2. Przywróć endpoint w `app/api/personas.py` (linie ~1840-1876)
3. Dodaj import w `app/services/__init__.py`
4. Zintegruj `MessagingGeneratorDialog` w `PersonaDetailsDrawer`

---

### 2. `persona_comparison_service.py`
**Funkcjonalność:** Porównywanie 2-3 person side-by-side z similarity matrix

**Endpoint:** `POST /api/v1/personas/{id}/actions/compare`

**Dlaczego zarchiwizowane:**
- Brak UI component w frontend (ComparePersonasDialog nie jest importowany)
- Hook useComparePersonas nie jest używany
- Feature nigdy nie został zintegrowany z UX

**Jak przywrócić:**
1. Przenieś serwis z powrotem do `app/services/`
2. Przywróć endpoint w `app/api/personas.py` (linie ~1878-1911)
3. Dodaj import w `app/services/__init__.py`
4. Zintegruj `ComparePersonasDialog` w persona management UI

---

## Uwagi
- Oba serwisy są **w pełni funkcjonalne** i przetestowane
- Kod jest production-ready, tylko brakuje integracji z frontend
- Aby przywrócić, wystarczy przenieść pliki i dodać UI components
