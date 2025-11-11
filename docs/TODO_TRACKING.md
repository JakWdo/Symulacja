# TODO Tracking - Backend

Dokument śledzący TODO items w kodzie backend (znaleziono w audycie 2025-11-11).

## 🔴 P0: Security & Critical (2 TODO)

### 1. RBAC Checks for Persona Deletion
**Lokalizacja:**
- `app/api/personas/crud.py:139` - Single persona deletion
- `app/api/personas/crud.py:273` - Bulk persona deletion

**Opis:** Obecnie tylko Admin powinien móc usuwać persony, ale brak enforcement.

**Akcja:** Implementować RBAC middleware i dodać `@requires_role('admin')` decorator.

**Priorytet:** 🔴 P0 - Security issue

**Powiązane zadanie:** Zadanie 89 (RBAC Implementation) w prompty.md

---

## 🟡 P1: Features & Infrastructure (7 TODO)

### 2. Workflow: Validate Survey Template Exists
**Lokalizacja:** `app/services/workflows/validation/workflow_validator.py:422`

**Opis:** Walidacja czy survey template istnieje (gdy dodamy survey templates feature).

**Akcja:** Implementować gdy survey templates będą dodane do systemu.

**Priorytet:** 🟡 P1 - Zależne od survey templates feature

---

### 3. Workflow: Map node_id → WorkflowStep.id
**Lokalizacja:** `app/services/workflows/execution/workflow_executor.py:180`

**Opis:** Progress tracking wymaga mapowania node_id do WorkflowStep.id w bazie.

**Akcja:** Rozszerzyć WorkflowStep model i dodać mapping logic.

**Priorytet:** 🟡 P1 - Enhancement dla progress tracking

---

### 4. Workflows: Integrate Segment-Based Persona Generation
**Lokalizacja:**
- `app/services/workflows/nodes/personas.py:100`
- `app/services/workflows/nodes/personas.py:107`

**Opis:** Workflow nodes używają STUB dla generacji person. Należy zintegrować z PersonaOrchestrationService.

**Akcja:**
1. Stworzyć SegmentDefinition objects z allocation_plan.groups
2. Zapisać segmenty do DB
3. Użyć `generator.generate_persona_from_segment()` dla każdej persony
4. Zapisać persony do DB z proper relationships

**Priorytet:** 🟡 P1 - Core feature enhancement

---

### 5. Workflows: Implement Demographic Preset Loading
**Lokalizacja:** `app/services/workflows/nodes/personas.py:175`

**Opis:** Obecnie demographic_preset z workflow config nie jest ładowany z `config/demographics/`.

**Akcja:** Implementować loader dla presets (poland.yaml, etc.) z config/.

**Priorytet:** 🟡 P1 - Feature enhancement

---

### 6. Dashboard: Implement Redis Caching
**Lokalizacja:** `app/api/dashboard.py:87`

**Opis:** Dashboard overview endpoint (8 kart metryk) wymaga Redis cache 30s TTL.

**Akcja:** Dodać Redis caching decorator lub middleware.

**Priorytet:** 🟡 P1 - Performance optimization

---

### 7. Personas API: Real-Time Progress for Orchestration
**Lokalizacja:**
- `app/api/personas/orchestration_endpoints.py:153`
- `app/api/personas/orchestration_endpoints.py:164`

**Opis:** Refaktoryzacja `_generate_personas_task` aby umożliwić real-time progress callbacks.

**Akcja:**
1. Ekstraktować orchestration logic
2. Dodać progress_callback parameter
3. Stream progress do WebSocket lub SSE

**Priorytet:** 🟡 P1 - UX enhancement

---

## 🟢 P2: Enhancements & Tech Debt (5 TODO)

### 8. Personas API: Proper Name Extraction with NLP
**Lokalizacja:** `app/api/personas/generation_endpoints.py:45`

**Opis:** `_infer_full_name()` używa prostego regex. Należy zastąpić NLP (spaCy, Stanza).

**Akcja:** Implementować named entity recognition dla polskich imion i nazwisk.

**Priorytet:** 🟢 P2 - Quality improvement

---

### 9. Personas API: Age-Appropriate Polish Name Generator
**Lokalizacja:** `app/api/personas/generation_endpoints.py:63`

**Opis:** `_fallback_full_name()` używa hardcoded list. Należy użyć generatora uwzględniającego:
- Wiek persony (popularne imiona w danej dekadzie)
- Płeć
- Regionalność

**Akcja:** Integracja z biblioteką polskich imion (faker-polish?) lub LLM.

**Priorytet:** 🟢 P2 - Quality improvement

---

### 10. Personas API: Smart Age Extraction
**Lokalizacja:** `app/api/personas/generation_endpoints.py:83`

**Opis:** `_extract_age_from_story()` używa prostych regex patterns. Należy dodać context awareness.

**Akcja:** Użyć NLP do rozróżniania "ma 35 lat" (age=35) vs "10 lat doświadczenia" (NOT age=10).

**Priorytet:** 🟢 P2 - Accuracy improvement

---

### 11. Personas API: Occupation Matching Logic
**Lokalizacja:** `app/api/personas/generation_endpoints.py:117`

**Opis:** `_get_consistent_occupation()` używa prostej fallback logiki. Należy implementować smart matching:
- Education level → Job market alignment
- Income bracket → Salary ranges
- Age → Career stage
- Polish job market context

**Akcja:** Utworzyć occupation matching service z Polish labor market data.

**Priorytet:** 🟢 P2 - Consistency improvement

---

## 📊 Podsumowanie

- **Łącznie:** 14 TODO items
- **P0 (Security):** 2 TODO
- **P1 (Features):** 7 TODO
- **P2 (Enhancements):** 5 TODO

**Cel zadania 73:** Redukcja do <10 TODO. Jednak wszystkie TODO są aktualne i reprezentują prawdziwe enhancement/feature work. Zamiast usuwania, zostały skategoryzowane i udokumentowane dla przyszłych GitHub issues.

## 🎯 Rekomendacje

1. **Natychmiast:** Utworzyć GitHub issues dla P0 (RBAC)
2. **Q1 2025:** Zaadresować P1 TODO w ramach feature development
3. **Q2 2025:** Rozważyć P2 enhancements jako tech debt

---

**Data audytu:** 2025-11-11
**Audytor:** Claude Code (zadanie 73 z prompty.md)
