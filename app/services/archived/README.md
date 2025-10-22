# Archived Services

Ten folder zawiera legacy features które nie są aktywnie używane w obecnej wersji aplikacji.

## Zawartość

### `messaging.py` (PersonaMessagingService)
**Status:** Archived - nie używane w UI
**Ostatnie użycie:** Backend API endpoint istnieje ale nie ma frontend implementation
**Funkcjonalność:** Generowanie przykładowych wiadomości/odpowiedzi email dla person (tone, style, content)

**Powód archiwizacji:**
Feature nie jest obecnie prezentowany w UI. API endpoint istnieje ale nie jest wywoływany przez frontend.
Archiwizujemy do czasu gdy zostanie zdecydowane czy feature wraca do aktywnego rozwoju.

**Jak przywrócić:**
1. Przenieś `messaging.py` z powrotem do `app/services/personas_details/`
2. Zaktualizuj `app/services/personas_details/__init__.py` (przywróć import)
3. Odkomentuj endpoint w `app/api/personas/actions.py` (po refactoringu)
4. Zaimplementuj frontend UI component (MessagingGeneratorDialog jest gotowy ale nie podpięty)

---

### `graph_service.py` - USUNIĘTY
**Status:** Całkowicie usunięty z codebase (2025-10-22)
**Funkcjonalność:** Analiza focus groups przez graf wiedzy Neo4j (concepts, emotions, personas)

**Powód usunięcia:**
Feature został zastąpiony przez RAG-based insights. Backend API + frontend components zostały usunięte.
Jeśli potrzebujesz przywrócić - sprawdź git history przed 2025-10-22.

## Historia zmian

- **2025-10-22**:
  - Archiwizacja messaging.py (nie używane w UI)
  - Całkowite usunięcie graph_service.py + API + frontend components
- **2025-10-15**: Archiwizacja graph_service.py podczas refaktoringu RAG (podział rag_service.py)
