# Archived Services

Ten folder zawiera legacy features które nie są aktywnie używane w obecnej wersji aplikacji.

## Zawartość

### `graph_service.py`
**Status:** Archived (nie używane w obecnej wersji)
**Ostatnie użycie:** v0.x (przed refaktoringiem RAG)
**Funkcjonalność:** Analiza focus groups przez graf wiedzy Neo4j (concepts, emotions, personas)

**Powód archiwizacji:**
Zdecydowaliśmy się skupić na RAG-based insights zamiast graph analysis person z focus groups.
Serwis pozostaje w archiwum na wypadek gdybyśmy chcieli wrócić do tej funkcjonalności w przyszłości.

**Backend API:**
- `app/api/graph_analysis.py` - importuje z archived (legacy endpoints zachowane)
- `app/api/focus_groups.py` - importuje z archived dla build_graph

**Frontend:**
- Komponenty Graph Analysis zostały ukryte z UI (AppSidebar, App.tsx routing)
- Pliki pozostają w codebase ale są niedostępne dla użytkowników

## Przywrócenie funkcjonalności

Jeśli w przyszłości chcesz przywrócić Graph Analysis:

1. Przenieś `graph_service.py` z powrotem do `app/services/`
2. Zaktualizuj importy w `app/api/graph_analysis.py` i `app/api/focus_groups.py`
3. Przywróć frontend:
   - Odkomentuj menu item w `frontend/src/components/layout/AppSidebar.tsx`
   - Odkomentuj routing w `frontend/src/App.tsx`
   - Przywróć komponenty z `frontend/src/components/archived/` (jeśli przeniesione)

## Historia zmian

- **2025-10-15**: Archiwizacja graph_service.py podczas refaktoringu RAG (podział rag_service.py)
