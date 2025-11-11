# 🧹 SIGHT PLATFORM - CLEANUP PROMPTS

**Projekt:** Sight AI-powered Focus Groups Platform
**Ścieżka:** `.` (ścieżki repo‑relatywne)
**Data utworzenia:** 2025-11-11
**Scope:** 75 promptów cleanup dla redukcji długu technicznego
**Cel:** Modularyzacja kodu (max 700 linii/plik), usunięcie TODO/hardcoded values, optymalizacja struktury

---

## 📋 Spis Treści

1. [Instrukcja Użytkowania](#instrukcja-użytkowania)
2. [Global Checklist](#global-checklist)
3. [Prompty Cleanup](#prompty-cleanup)
   - [🔴 P0: Backend Core Services (1-15)](#p0-backend-core-services)
   - [🟡 P1: Backend API + Schemas (16-28)](#p1-backend-api--schemas)
   - [🟡 P1: Backend Services Folders (29-35)](#p1-backend-services-folders)
   - [🟢 P2: Frontend Components (36-50)](#p2-frontend-components)
   - [🟢 P2: Frontend Lib/Hooks/Types (51-58)](#p2-frontend-libhookstypes)
   - [🟢 P2: Tests (59-66)](#p2-tests)
   - [🟢 P2: Config & Scripts (67-70)](#p2-config--scripts)
   - [🔵 P3: Documentation (71-75)](#p3-documentation)
4. [Appendix: Komendy i Narzędzia](#appendix-komendy-i-narzędzia)

---

## 📖 Instrukcja Użytkowania

### Kolejność Wykonywania

**KRYTYCZNE:** Wykonuj prompty SEKWENCYJNIE według numeracji 1→75. Nie pomijaj kroków!

**Priorytety:**
- 🔴 **P0 (1-15):** Krytyczne - backend core services (wykonaj w ciągu 1-2 dni)
- 🟡 **P1 (16-35):** Wysokie - backend API + folders (wykonaj w ciągu 3-5 dni)
- 🟢 **P2 (36-70):** Średnie - frontend + tests + config (wykonaj w ciągu 1-2 tygodni)
- 🔵 **P3 (71-75):** Niskie - dokumentacja (wykonaj w ciągu 1 miesiąca)

### Workflow Per Prompt

Każdy prompt wymaga wykonania 6 kroków:

1. **[ ] Grep:** Znajdź wszystkie zależności przed zmianami
2. **[ ] Podział:** Podziel plik na moduły według specyfikacji
3. **[ ] Importy:** Zaktualizuj wszystkie importy w zależnych plikach
4. **[ ] Fixes:** Napraw TODO/hardcoded/deprecated code + **USUŃ NIEUŻYWANY KOD**
   - Przeszukaj nieużywane importy (`rg` lub IDE)
   - Usuń nieużywane funkcje i zmienne
   - Usuń nieużywane parametry funkcji
   - Usuń zakomentowany martwy kod
   - Dla Python: można użyć `autoflake --remove-all-unused-imports --remove-unused-variables`
5. **[ ] Testy:** Uruchom testy regresyjne (`pytest -v`)
6. **[ ] Działa:** Zweryfikuj działanie (`docker-compose restart` lub `npm run build`)

**⚠️ WAŻNE: Po zakończeniu promptu odznacz go w sekcji [Global Checklist](#global-checklist) zmieniając `- [ ]` na `- [x]`**

### Git Workflow

```bash
# Przed rozpoczęciem pracy nad promptem
git checkout main
git pull origin main
git checkout -b cleanup/prompt-XX-short-description

# Po zakończeniu promptu
git add .
git commit -m "cleanup: [Prompt XX] Opis zmiany"
git push origin cleanup/prompt-XX-short-description

# Stwórz PR z labelką "cleanup"
gh pr create --title "Cleanup: Prompt XX - Opis" --label cleanup
```

### Breakpoints (Commit Points)

**Zalecane punkty commit po zakończeniu:**
- Prompt 15 (P0 complete) → Merge do main
- Prompt 35 (P1 complete) → Merge do main
- Prompt 58 (Frontend complete) → Merge do main
- Prompt 70 (P2 complete) → Merge do main
- Prompt 75 (All complete) → Celebrate! 🎉

### Konwencje i Guardrails

- Używaj wyłącznie ścieżek repo‑relatywnych (np. `app/...`, `frontend/...`).
- Unikaj cyklicznych importów: wydzielaj typy/utilsy do wspólnych modułów i utrzymuj jednokierunkowe zależności.
- Po refaktoryzacji utrzymaj publiczne API przez re‑eksporty w `__init__.py` tam, gdzie to potrzebne.
- Każdy prompt jest krótki (do 4 zdań), zawsze zaczyna się od przeglądu zależności/importów i kończy uruchomieniem odpowiednich testów/builda.

---

## ✅ Global Checklist

Odznaczaj po zakończeniu każdego promptu:

### 🔴 P0: Backend Core Services
- [x] 1. persona_generator_langchain.py split ✅ (1074→543 linii + 5 modułów)
- [x] 2. discussion_summarizer.py split ✅ (1143→341 linii + 7 modułów)
- [x] 3. rag_hybrid_search_service.py split ✅ (1074 + 6 modułów: cache, search, reranking, graph)
- [x] 4. persona_orchestration.py split ✅ (987→185 linii + 7 modułów)
- [x] 5. dashboard_orchestrator.py split ✅ (1028→543 linii + 4 moduły)
- [x] 6. rag_graph_service.py split ✅ (665→114 linii + 3 moduły)
- [x] 7. segment_brief_service.py cleanup ✅ (TTL z config/features.yaml)
- [x] 8. persona_details_service.py cleanup ✅ (642→ details_crud + details_enrichment)
- [x] 9. distribution_builder.py cleanup ✅ (634→ distribution_calculator + validator)
- [x] 10. demographics_formatter.py cleanup ✅ (560→ validator + formatter)
- [x] 11. survey_response_generator.py cleanup ✅ (686→524+245 linii: core + formatter)
- [x] 12. workflow_template_service.py cleanup ✅ (543→635+108 linii: crud + validator)
- [x] 13. persona_needs_analyzer.py cleanup ✅ (persona_needs_service.py: 203 linii, bez zmian)
- [x] 14. focus_groups memory_manager.py cleanup ✅ (memory_service_langchain.py: 256 linii, bez zmian)
- [x] 15. dashboard usage_logging.py cleanup ✅ (usage_logging.py: 182 linii, brak print(), bez zmian)

### 🟡 P1: Backend API + Schemas
- [x] 16. api/personas/generation.py split ✅ (1360→394+224+804 linii: endpoints + orchestration + validation)
- [x] 17. api/workflows.py split ✅ (879→442+286+207 linii: crud + execution + templates)
- [x] 18. api/projects.py split ✅ (693→175+549 linii: crud + demographics)
- [x] 19. schemas/workflow.py split ✅ (994→480+589+120 linii: base + nodes + wrapper)
- [x] 20. schemas/persona.py cleanup ✅ (477 linii - bez zmian potrzebnych)
- [x] 21. schemas/focus_group.py cleanup ✅ (131 linii - bez zmian potrzebnych)
- [x] 22. api/focus_groups.py cleanup ✅ (230→228 linii, usunięto BackgroundTasks)
- [x] 23. api/surveys.py cleanup ✅ (311→308 linii, usunięto BackgroundTasks)
- [x] 24. api/rag.py cleanup ✅ (270 linii - brak martwego kodu)
- [x] 25. api/dashboard.py cleanup ✅ (279→278 linii, usunięto datetime)
- [x] 26. api/study_designer.py cleanup ✅ (330 linii - brak martwego kodu)
- [x] 27. schemas/project.py cleanup ✅ (219 linii - brak martwego kodu)
- [x] 28. schemas/dashboard.py cleanup ✅ (287 linii, usunięto nieużywany import Field)

### 🟡 P1: Backend Services Folders
- [x] 29. services/personas/ folder structure ✅ (Fix importów wewnętrznych)
- [x] 30. services/dashboard/ folder structure ✅ (Struktura metrics/, usage/, insights/, costs/)
- [x] 31. services/workflows/ folder structure ✅ (Struktura execution/, templates/, validation/ + docs przeniesione)
- [x] 32. services/rag/ folder structure ✅ (Struktura search/, graph/, documents/, clients/)
- [x] 33. services/focus_groups/ folder structure ✅ (Struktura discussion/, summaries/, memory/)
- [x] 34. services/surveys/ folder structure ✅ (Importy zaktualizowane, struktura wystarczająca)
- [x] 35. services/shared/ folder structure ✅ (Dodano get_embeddings do __init__.py, brak nieużywanego kodu)

### 🟢 P2: Frontend Components
- [ ] 36. Personas.tsx split (częściowo: constants extracted)
- [ ] 37. FocusGroupView.tsx split
- [ ] 38. ❌ GraphAnalysis.tsx - USUŃ (martwy kod, brak użycia)
- [ ] 39. FocusGroupPanel.tsx split
- [ ] 40. WorkflowEditor.tsx split
- [ ] 41. PersonaPanel.tsx split
- [ ] 42. AISummaryPanel.tsx split
- [ ] 43. Surveys.tsx cleanup
- [ ] 44. Dashboard.tsx cleanup
- [ ] 45. ❌ ProjectSettings.tsx - NIE ISTNIEJE (jest Settings.tsx)
- [x] 46. ❌ ReasoningPanel.tsx - NIE ISTNIEJE (jest PersonaReasoningPanel.tsx) ✅
- [x] 47. ❌ WorkflowTemplates.tsx - NIE ISTNIEJE (jest WorkflowsListPage.tsx) ✅
- [x] 48. ❌ WorkflowRun.tsx - NIE ISTNIEJE (sprawdź WorkflowsListPage/ExecutionHistory) ✅
- [x] 49. Hardcoded labels → constants ✅ (constants/personas.ts utworzony)
- [ ] 50. Unused UI components audit

### 🟢 P2: Frontend Lib/Hooks/Types
- [ ] 51. lib/api.ts split
- [ ] 52. types/index.ts split
- [ ] 53. hooks/useWorkflows.ts split
- [ ] 54. hooks/usePersonas.ts cleanup
- [ ] 55. hooks/useFocusGroups.ts cleanup
- [ ] 56. lib/utils.ts cleanup
- [ ] 57. stores/zustand cleanup
- [ ] 58. constants/ consolidation

### 🟢 P2: Tests
- [ ] 59. test_workflow_validator.py split
- [ ] 60. test_workflow_service.py split
- [ ] 61. test_workflow_executor.py split
- [ ] 62. test_rag_hybrid_search.py cleanup
- [ ] 63. test_persona_orchestration.py cleanup
- [ ] 64. fixtures consolidation
- [ ] 65. Deprecated test utilities cleanup
- [ ] 66. Test coverage gaps (target 85%+)

### 🟢 P2: Config & Scripts
- [ ] 67. config/loader.py split
- [ ] 68. scripts/cleanup_legacy_mentions.py archive
- [ ] 69. scripts/create_demo_data consolidation
- [ ] 70. Cache cleanup (.pyc, __pycache__, .DS_Store)

### 🟠 P2.5: Audyt Poprzednich Refaktoryzacji (NOWE - 2025-11-11)
- [x] 76. Backend: Audyt nieużywanych importów po zadaniach 1-35 ✅ (6 naprawionych)
- [x] 77. Frontend: Usunięcie martwego kodu (GraphAnalysis.tsx, etc.) ✅ (897 linii)
- [x] 78. Backend: Sprawdzenie TODO/FIXME z zadań 1-35 ✅ (5 TODO skatalogowanych)
- [ ] 79. Frontend: Audyt komponentów UI shadcn (50+ plików)
- [ ] 80. Backend: Sprawdzenie BackgroundTasks usage
- [ ] 81. Full repo: Znajdź duplikaty kodu (copy-paste)
- [ ] 82. Frontend: Sprawdź nieużywane hooki i utility functions
- [ ] 83. Backend: Sprawdź czy stare serwisy mają deprecated metody
- [ ] 84. Tests: Usuń martwe fixtures i test utilities
- [ ] 85. Global: Sprawdź nieużywane dependencies (requirements.txt, package.json)

### 🔵 P3: Documentation
- [ ] 71. docs/BACKEND.md split
- [ ] 72. docs/AI_ML.md split
- [ ] 73. docs/QA.md optimization
- [ ] 74. docs/INFRASTRUKTURA.md optimization
- [ ] 75. workflows docs move to docs/workflows/

---

## 🧹 Prompty Cleanup

### 🔴 P0: Backend Core Services

#### 1. 🔴 [Backend Services] - persona_generator_langchain.py (1073 linii)

Prompt (krótki): Przejrzyj `app/services/personas/persona_generator_langchain.py` (monolityczny generator). Najpierw zidentyfikuj zależności i użycia: `rg -n "PersonaGenerator|PersonaGeneratorLangChain" app tests`. Rozbij na `persona_generator_core.py`, `persona_prompts_builder.py`, `persona_validators.py`; zaktualizuj importy i usuń TODO/hardcoded. Zweryfikuj: `pytest tests/unit/test_persona_generator.py -v` i `docker-compose restart api`.

Przed: `rg -n "PersonaGenerator|PersonaGeneratorLangChain" app tests` i zanotuj importy/usage.
Po: utrzymane publiczne API przez re‑eksporty w `app/services/personas/__init__.py` (jeśli potrzeba).

---

#### 2. 🔴 [Backend Services] - discussion_summarizer.py (1143 linii)

Prompt (krótki): Przejrzyj `app/services/focus_groups/discussion_summarizer.py` (zbyt wiele odpowiedzialności). Najpierw znajdź zależności: `rg -n "DiscussionSummarizer|DiscussionSummarizerService" app tests`. Rozbij na `summarizer_core.py`, `insights_extractor.py`, `themes_analyzer.py`, `summary_formatter.py`; popraw importy w `app/api/focus_groups.py`. Zweryfikuj: `pytest tests/unit/test_discussion_summarizer_service.py -v` i `docker-compose restart api`.

Przed: `rg -n "DiscussionSummarizer|DiscussionSummarizerService" app tests` i lista zależności.
Po: upewnij się, że brak cykli i ewentualne re‑eksporty w `app/services/focus_groups/__init__.py`.

---

#### 3. 🔴 [Backend Services] - rag_hybrid_search_service.py (1074 linii)

Prompt (krótki): Przejrzyj `app/services/rag/rag_hybrid_search_service.py` (złożony hybrydowy search). Zidentyfikuj zależności: `rg -n "RagHybridSearchService|PolishSocietyRAG" app tests` i ścieżki użycia w API. Rozbij na `hybrid_search_orchestrator.py`, `vector_search.py`, `keyword_search.py`, `rrf_fusion.py`; popraw importy w `app/api/rag.py` i serwisach zależnych. Zweryfikuj: `pytest tests/unit/test_rag_hybrid_search_service.py -v` (opcjonalnie także `tests/unit/test_rag_hybrid_search.py`) i `docker-compose restart api`.

---

#### 4. 🔴 [Backend Services] - persona_orchestration.py (987 linii)

Prompt (krótki): Przejrzyj `app/services/personas/persona_orchestration.py` (orkiestracja + segmentacja). Najpierw znajdź zależności: `rg -n "PersonaOrchestrationService|PersonaOrchestration" app tests` i użycia w endpointach. Rozbij na `orchestration_core.py`, `segment_creator.py`, `orchestration_cache.py`; popraw importy w `app/api/personas/generation.py`. Zweryfikuj: `pytest tests/unit/test_persona_orchestration.py -v` i `docker-compose restart api`.

---

#### 5. 🔴 [Backend Services] - dashboard_orchestrator.py (1028 linii)

Prompt (krótki): Przejrzyj `app/services/dashboard/dashboard_orchestrator.py` (za dużo metryk w jednym serwisie). Zbadaj zależności: `rg -n "DashboardOrchestrator" app tests` i usage w API. Rozbij na `dashboard_core.py`, `metrics_aggregator.py`, `cost_calculator.py`, `usage_trends.py`; popraw importy w `app/api/dashboard.py`. Zweryfikuj: `pytest tests/integration/test_dashboard_orchestrator_pl_integration.py -v` i `docker-compose restart api`.

---

#### 6. 🔴 [Backend Services] - rag_graph_service.py (665 linii)

Prompt (krótki): Przejrzyj `app/services/rag/rag_graph_service.py` (generowanie Cypher + traversal razem). Najpierw zależności: `rg -n "GraphRAGService|RagGraphService" app tests` i usage w orkiestracji. Rozbij na `graph_query_builder.py`, `graph_traversal.py`, `graph_insights_extractor.py`; popraw importy w `app/api/rag.py` i serwisach personas. Zweryfikuj: `pytest tests/unit/test_rag_graph_service.py -v` i `docker-compose restart api neo4j`.

---

#### 7. 🔴 [Backend Services] - segment_brief_service.py (818 linii)

Prompt (krótki): Przejrzyj `app/services/personas/segment_brief_service.py` (generowanie briefu + cache + formatowanie). Najpierw znajdź zależności: `rg -n "SegmentBriefService" app tests` i usage w orkiestracji. Wyodrębnij `segment_brief_generator.py` i `brief_formatter.py`, pozostaw logikę cache w pliku bazowym; popraw importy, usuń TODO dot. cache invalidation i ustaw TTL z `config/features.yaml`. Zweryfikuj: `pytest tests/unit/test_persona_orchestration.py -v` oraz `docker-compose restart api redis`.

---

#### 8. 🔴 [Backend Services] - persona_details_service.py (642 linii)

Prompt (krótki): Przejrzyj `app/services/personas/persona_details_service.py` (CRUD + enrichment razem). Zidentyfikuj zależności: `rg -n "PersonaDetailsService" app tests` i usage w `app/api/personas/details.py`. Wyodrębnij `details_crud.py` i `details_enrichment.py`; zastąp hardcoded polskie nazwy danymi z `config/demographics/poland.yaml` i zaktualizuj importy. Zweryfikuj: `pytest tests/integration/test_personas_api_integration.py -v` i `docker-compose restart api`.

---

#### 9. 🔴 [Backend Services] - distribution_builder.py (634 linii)

Prompt (krótki): Przejrzyj `app/services/personas/distribution_builder.py` (logika dystrybucji + walidacja stat.). Zbadaj zależności: `rg -n "DistributionBuilder" app tests`. Wyodrębnij `distribution_calculator.py` i `statistical_validator.py`; usuń TODO dot. weighted sampling i popraw importy w miejscach użycia (np. orkiestracja). Zweryfikuj: `pytest tests/unit/test_persona_orchestration.py -v` i `docker-compose restart api`.

---

#### 10. 🔴 [Backend Services] - demographics_formatter.py (560 linii)

Prompt (krótki): Przejrzyj `app/services/personas/demographics_formatter.py` (formatowanie + walidacja). Najpierw zależności: `rg -n "DemographicsFormatter" app tests`. Wyodrębnij `demographics_validator.py`, pozostaw formatowanie w pliku bazowym; zastąp hardcoded stopwords danymi z `config/prompts/shared/stopwords.yaml` (utwórz, jeśli brak) i popraw importy. Zweryfikuj: `pytest tests/unit/test_persona_generator.py -v` i `docker-compose restart api`.

---

#### 11. 🔴 [Backend Services] - survey_response_generator.py (686 linii)

Prompt (krótki): Przejrzyj `app/services/surveys/survey_response_generator.py` (generowanie odpowiedzi + formatowanie). Najpierw znajdź zależności: `rg -n "SurveyResponseGenerator" app tests`. Wyodrębnij `response_generator_core.py` i `response_formatter.py`; zaktualizuj importy w `app/api/surveys.py` i usuń przestarzałe `legacy_survey_format()`. Zweryfikuj: `pytest tests/unit/test_survey_response_generator.py -v` i `docker-compose restart api`.

---

#### 12. 🔴 [Backend Services] - workflow_template_service.py (543 linii)

Prompt (krótki): Przejrzyj `app/services/workflows/workflow_template_service.py` (CRUD szablonów + walidacja). Zidentyfikuj zależności: `rg -n "WorkflowTemplateService" app tests`. Wyodrębnij `template_crud.py` i `template_validator.py`; popraw importy w `app/api/workflows.py`. Zweryfikuj: `pytest tests/unit/services/workflows/test_workflow_template_service.py -v` i `docker-compose restart api`.

---

#### 13. 🔴 [Backend Services] - persona_needs_analyzer.py

Prompt (krótki): Przejrzyj `app/services/personas/persona_needs_analyzer.py` (sprawdź rozmiar i odpowiedzialności). Najpierw: `wc -l app/services/personas/persona_needs_analyzer.py && rg -n "PersonaNeedsAnalyzer" app tests`. Jeśli >500 linii, wydziel `needs_extractor.py` i `needs_validator.py`, usuń TODO i popraw importy. Zweryfikuj: `pytest tests/unit -v` i `docker-compose restart api`.

---

#### 14. 🔴 [Backend Services] - memory_manager.py

Prompt (krótki): Przejrzyj `app/services/focus_groups/memory_manager.py` (sprawdź rozmiar i zakres). Najpierw: `wc -l app/services/focus_groups/memory_manager.py && rg -n "MemoryManager" app tests`. Jeśli >500 linii, wydziel `conversation_history.py` (historia) i `context_compression.py` (tokeny) i popraw importy w `app/api/focus_groups.py`. Zweryfikuj: `pytest tests/unit/test_focus_group_service.py -v tests/unit/test_discussion_summarizer_service.py -v` oraz `docker-compose restart api redis`.

---

#### 15. 🔴 [Backend Services] - usage_logging.py

Prompt (krótki): Przejrzyj `app/services/dashboard/usage_logging.py` (rozmiar i odpowiedzialności). Najpierw: `wc -l app/services/dashboard/usage_logging.py && rg -n "usage_logging|print\(" app tests`. Jeśli >500 linii, wydziel `usage_tracker.py` i `usage_persistence.py`; popraw importy i zamień `print` na `logger.info`. Zweryfikuj: `pytest tests/integration/test_dashboard_api.py -v` i `docker-compose restart api`.

---

### 🟡 P1: Backend API + Schemas

#### 16. 🟡 [Backend API] - api/personas/generation.py (1360 linii)

Prompt (krótki): Przejrzyj `app/api/personas/generation.py` (za dużo endpointów w jednym pliku). Najpierw znajdź zależności: `rg -n "from app.api.personas.generation import|include_router\(" app tests`. Podziel na `generation_endpoints.py`, `orchestration_endpoints.py`, `validation_endpoints.py`; zaktualizuj rejestrację routerów w `app/api/personas/__init__.py` i `app/main.py` oraz usuń TODO (batch generation). Zweryfikuj: `pytest tests/integration/test_personas_api_integration.py -v` i `docker-compose restart api`.

---

#### 17. 🟡 [Backend API] - api/workflows.py (879 linii)

Prompt (krótki): Przejrzyj `app/api/workflows.py` (CRUD + execution + templates razem). Najpierw: `rg -n "from app.api.workflows import|include_router\(" app tests` i zanotuj usage. Podziel na `workflow_crud.py`, `workflow_execution.py`, `workflow_templates.py`; zaktualizuj importy i rejestrację routerów w `app/main.py`. Zweryfikuj: `pytest tests/unit/services/workflows -v` i `docker-compose restart api`.

---

#### 18. 🟡 [Backend API] - api/projects.py (693 linii)

Prompt (krótki): Przejrzyj `app/api/projects.py` (zarządzanie projektami + demografia w jednym). Najpierw: `rg -n "from app.api.projects import|include_router\(" app tests`. Podziel na `project_crud.py` i `project_demographics.py`; zaktualizuj rejestrację routerów w `app/main.py`. Zweryfikuj: `pytest tests/integration/test_projects_api_integration.py -v` i `docker-compose restart api`.

---

#### 19. ✅ [Backend Schemas] - schemas/workflow.py (994 linii → podzielony)

Przejrzyj `app/schemas/workflow.py` (zbyt wiele modeli w jednym miejscu). Przed: `rg -n "from app.schemas.workflow import" app tests` i zinwentaryzuj importy. Podziel na `workflow_base.py` i `workflow_nodes.py`; zaktualizuj importy w `app/api/workflows.py`, `app/services/workflows/`, `tests/`. Po: `pytest tests/unit/services/workflows/test_workflow_validator.py -v && docker-compose restart api`.
Checklist: [✅] Grep [✅] Podział [✅] Importy (wrapper) [✅] Fixes [✅] Testy [✅] Działa.
**Wynik**: Podzielono na workflow_base.py (480 linii), workflow_nodes.py (589 linii), wrapper (120 linii). 14 plików importujących zachowało backward compatibility.

---

#### 20. ✅ [Backend Schemas] - schemas/persona.py

Przejrzyj `app/schemas/persona.py` (sprawdź rozmiar i zakres). Przed: `wc -l app/schemas/persona.py && rg -n "from app.schemas.persona import" app tests`. Jeśli >500 linii, wydziel `persona_generation.py` i `persona_details.py`; zaktualizuj importy w `app/api/personas/`, `tests/`. Po: `pytest tests/unit/test_persona_generator.py -v tests/unit/test_persona_orchestration.py -v && docker-compose restart api`.
Checklist: [✅] Grep [✅] Podział [N/A] Importy [N/A] Fixes [✅] Testy [✅] Działa.
**Wynik**: 477 linii - poniżej progu 500 linii, **bez zmian potrzebnych**.

---

#### 21. ✅ [Backend Schemas] - schemas/focus_group.py

Przejrzyj `app/schemas/focus_group.py` (sprawdź rozmiar i zakres). Przed: `wc -l app/schemas/focus_group.py && rg -n "from app.schemas.focus_group import" app tests`. Jeśli >500 linii, wydziel `focus_group_base.py`, `focus_group_responses.py`, `focus_group_summaries.py` i zaktualizuj importy. Po: `pytest tests/unit/test_focus_group_service.py -v && docker-compose restart api`.
Checklist: [✅] Grep [✅] Podział [N/A] Importy [N/A] Fixes [✅] Testy [✅] Działa.
**Wynik**: 131 linii - poniżej progu 500 linii, **bez zmian potrzebnych**.

---

#### 22. 🟡 [Backend API] - api/focus_groups.py

Przejrzyj `app/api/focus_groups.py` (sprawdź rzeczywistą długość). Przed: `wc -l app/api/focus_groups.py && rg -n "from app.api.focus_groups import" app tests`. Jeśli >500 linii, podziel na `focus_group_crud.py`, `focus_group_discussion.py`, `focus_group_summaries.py`; zaktualizuj importy i usuń TODO (jeśli jest). Po: `pytest tests/integration/test_focus_groups_api_integration.py -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes [ ] Testy [ ] Działa.

---

#### 23. 🟡 [Backend API] - api/surveys.py

Przejrzyj `app/api/surveys.py` (sprawdź rzeczywistą długość). Przed: `wc -l app/api/surveys.py && rg -n "from app.api.surveys import" app tests`. Jeśli >500 linii, wyodrębnij `survey_crud.py` i `survey_responses.py` i zaktualizuj importy w `app/main.py`. Po: `pytest tests/integration/test_surveys_api_integration.py -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes [ ] Testy [ ] Działa.

---

#### 24. 🟡 [Backend API] - api/rag.py

Przejrzyj `app/api/rag.py` (sprawdź rzeczywistą długość). Przed: `wc -l app/api/rag.py && rg -n "from app.api.rag import" app tests`. Jeśli >500 linii, wyodrębnij `rag_search.py` (search) i `rag_documents.py` (documents) i zaktualizuj importy. Po: `pytest tests/unit -k "rag_" -v && docker-compose restart api neo4j`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes [ ] Testy [ ] Działa.

---

#### 25. 🟡 [Backend API] - api/dashboard.py

Przejrzyj `app/api/dashboard.py` (sprawdź rzeczywistą długość). Przed: `wc -l app/api/dashboard.py && rg -n "from app.api.dashboard import" app tests`. Jeśli >500 linii, wyodrębnij `dashboard_metrics.py`, `dashboard_usage.py`, `dashboard_costs.py` i zaktualizuj importy. Po: `pytest tests/integration/test_dashboard_api.py -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes [ ] Testy [ ] Działa.

---

#### 26. 🟡 [Backend API] - api/study_designer.py

Przejrzyj `app/api/study_designer.py` (sprawdź rzeczywistą długość). Przed: `wc -l app/api/study_designer.py && rg -n "from app.api.study_designer import" app tests`. Jeśli >500 linii, wyodrębnij moduły według grup endpointów, zaktualizuj importy i usuń TODO (SSE streaming optimization). Po: `pytest tests/integration/test_study_designer_api.py -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (TODO) [ ] Testy [ ] Działa.

---

#### 27. 🟡 [Backend Schemas] - schemas/project.py

Przejrzyj `app/schemas/project.py` (sprawdź rozmiar i podział). Przed: `wc -l app/schemas/project.py && rg -n "from app.schemas.project import" app tests`. Jeśli >500 linii, wyodrębnij `project_base.py` i `project_demographics.py` i zaktualizuj importy. Po: `pytest tests/integration/test_projects_api_integration.py -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes [ ] Testy [ ] Działa.

---

#### 28. ✅ [Backend Schemas] - schemas/dashboard.py

Przejrzyj `app/schemas/dashboard.py` (sprawdź rozmiar i zakres). Przed: `wc -l app/schemas/dashboard.py && rg -n "from app.schemas.dashboard import" app tests`. Jeśli >500 linii, wyodrębnij `dashboard_metrics.py` i `dashboard_usage.py` i zaktualizuj importy. Po: `pytest tests/integration/test_dashboard_api.py -v && docker-compose restart api`.
Checklist: [✅] Grep [✅] Podział [N/A] Importy [✅] Fixes [✅] Testy [✅] Działa.
**Wynik**: 287 linii - poniżej progu 500 linii. Usunięto nieużywany import `Field` z Pydantic. Używany tylko w `app/api/dashboard.py`.

---

### 🟡 P1: Backend Services Folders

#### 29. 🟡 [Backend Services Folder] - services/personas/ restructure

Przejrzyj `app/services/personas/` (struktura i długość plików). PRZED: `ls -lh app/services/personas && find app/services/personas -name "*.py" -exec wc -l {} +`. Zrestrukturyzuj: utwórz `generation/`, `orchestration/`, `details/`, `validation/`, przenieś moduły, uzupełnij `__init__.py` o re-exports i zaktualizuj importy w `app/api/personas/`, `tests/unit/services/personas/` + **usuń nieużywany kod** (`ruff check --select F401,F841 --fix`).
PO: `pytest tests/unit/test_persona_generator.py -v tests/unit/test_persona_orchestration.py -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Testy [ ] Działa.

---

#### 30. 🟡 [Backend Services Folder] - services/dashboard/ restructure

Przejrzyj `app/services/dashboard/` (struktura). PRZED: `ls -lh app/services/dashboard && find app/services/dashboard -name "*.py" -exec wc -l {} +`. Zrestrukturyzuj: utwórz `metrics/`, `usage/`, `costs/`, przenieś moduły, uzupełnij `__init__.py` i zaktualizuj importy w `app/api/dashboard.py`, `tests/` + **usuń nieużywany kod** (`ruff check --select F401,F841 --fix`).
PO: `pytest tests/integration/test_dashboard_api.py -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Testy [ ] Działa.

---

#### 31. 🟡 [Backend Services Folder] - services/workflows/ restructure

Przejrzyj `app/services/workflows/` (struktura + folder z dokumentacją). PRZED: `ls -lh app/services/workflows && find app/services/workflows -name "*.py" -exec wc -l {} +`. Zrestrukturyzuj: utwórz `execution/`, `templates/`, `validation/`, przenieś `docs/*.md` do `docs/workflows/` i zaktualizuj importy w `app/api/workflows.py`, `tests/` + **usuń nieużywany kod** (`ruff check --select F401,F841 --fix`).
PO: `pytest tests/unit/services/workflows -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Testy [ ] Działa.

---

#### 32. 🟡 [Backend Services Folder] - services/rag/ restructure

Przejrzyj `app/services/rag/` (struktura). PRZED: `ls -lh app/services/rag && find app/services/rag -name "*.py" -exec wc -l {} +`. Zrestrukturyzuj: utwórz `search/` (hybrid + graph), `documents/`, `embeddings/`, przenieś moduły i zaktualizuj importy w `app/api/rag.py`, `app/services/personas/`, `tests/` + **usuń nieużywany kod** (`ruff check --select F401,F841 --fix`).
PO: `pytest tests/unit/test_rag_document_service.py -v tests/unit/test_rag_hybrid_search_service.py -v tests/unit/test_rag_graph_service.py -v && docker-compose restart api neo4j`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Testy [ ] Działa.

---

#### 33. 🟡 [Backend Services Folder] - services/focus_groups/ restructure

Przejrzyj `app/services/focus_groups/` (struktura). PRZED: `ls -lh app/services/focus_groups && find app/services/focus_groups -name "*.py" -exec wc -l {} +`. Zrestrukturyzuj: utwórz `discussion/`, `summaries/`, `memory/`, przenieś moduły i zaktualizuj importy w `app/api/focus_groups.py`, `tests/` + **usuń nieużywany kod** (`ruff check --select F401,F841 --fix`).
PO: `pytest tests/unit/test_focus_group_service.py -v tests/unit/test_discussion_summarizer_service.py -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Testy [ ] Działa.

---

#### 34. 🟡 [Backend Services Folder] - services/surveys/ restructure

Przejrzyj `app/services/surveys/` (struktura). PRZED: `ls -lh app/services/surveys && find app/services/surveys -name "*.py" -exec wc -l {} +`. Zrestrukturyzuj: jeśli potrzeba, utwórz `generation/`, `responses/`, przenieś moduły i zaktualizuj importy w `app/api/surveys.py`, `tests/` + **usuń nieużywany kod** (`ruff check --select F401,F841 --fix`).
PO: `pytest tests/unit/test_survey_response_generator.py -v tests/integration/test_surveys_api_integration.py -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Testy [ ] Działa.

---

#### 35. 🟡 [Backend Services Folder] - services/shared/ cleanup

Przejrzyj `app/services/shared/` (nieużywane moduły). PRZED: `ls -lh app/services/shared && rg -n "from app.services.shared" app tests | cut -d: -f2 | sort | uniq -c`. Cleanup: usuń nieużywane moduły, konsoliduj `clients.py` z `rag_provider.py` jeśli duplikują logikę, zaktualizuj importy i usuń deprecated utilities + **usuń nieużywany kod** (`ruff check --select F401,F841 --fix`).
PO: `pytest tests/unit -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Testy [ ] Działa.

---

### 🟢 P2: Frontend Components

#### 36. ✅ [Frontend Component] - Personas.tsx (1195 linii → 653 linii)

Prompt (krótki): Przejrzyj `frontend/src/components/layout/Personas.tsx` (monolityczny komponent). Najpierw: `rg -n "import.*Personas" frontend/src --glob "**/*.{ts,tsx}"` i zanotuj zależności. Podziel na `PersonasLayout.tsx`, `PersonasList.tsx`, `PersonaFilters.tsx`, `PersonaActions.tsx`; przenieś hardcoded labels (linia 76-99) do `frontend/src/constants/personas.ts` i zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview`.

---

#### 37. 🟢 [Frontend Component] - FocusGroupView.tsx (972 linii)

Prompt (krótki): Przejrzyj `frontend/src/components/layout/FocusGroupView.tsx` (dyskusja + odpowiedzi w jednym). Najpierw: `rg -n "import.*FocusGroupView" frontend/src --glob "**/*.tsx"` i zanotuj usage. Podziel na `FocusGroupLayout.tsx`, `DiscussionThread.tsx`, `ResponseComposer.tsx`; zaktualizuj importy i routing + **usuń nieużywany kod** (`npm run lint -- --fix`) + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview`.

---

#### 38. ❌ [Frontend Component] - GraphAnalysis.tsx - USUŃ (martwy kod)

**UWAGA:** GraphAnalysis.tsx (788 linii) NIE JEST UŻYWANY NIGDZIE w aplikacji - to martwy kod!

Prompt (krótki): Przejrzyj `frontend/src/components/layout/GraphAnalysis.tsx` i zweryfikuj że nie jest używany. Najpierw: `rg -l "GraphAnalysis" frontend/src --glob "**/*.tsx" --glob "**/*.ts"` (powinien zwrócić tylko sam plik). Sprawdź routing w `App.tsx` - nie ma case'a dla graph analysis. **USUŃ PLIK** zamiast go dzielić + sprawdź czy inne pliki w `layout/` też nie są martwe (FigmaDashboard.tsx, StatsOverlay.tsx, FloatingControls.tsx) + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview && rg "GraphAnalysis" frontend/src` (powinno być 0 wyników).

**To zadanie zostało zastąpione przez zadanie 77 w sekcji P2.5 Audyt.**

---

#### 39. 🟢 [Frontend Component] - FocusGroupPanel.tsx (783 linii)

Prompt (krótki): Przejrzyj `frontend/src/components/panels/FocusGroupPanel.tsx` (panel + details razem). Najpierw: `rg -n "import.*FocusGroupPanel" frontend/src --glob "**/*.tsx"` i zanotuj usage. Podziel na `FocusGroupPanel.tsx` (panel) i `FocusGroupDetails.tsx` (szczegóły) i zaktualizuj importy w komponentach nadrzędnych + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview`.

---

#### 40. 🟢 [Frontend Component] - WorkflowEditor.tsx (740 linii)

Przejrzyj `frontend/src/components/workflows/WorkflowEditor.tsx` (740 linii, problem: editor + node palette razem).
PRZED: `grep -r "import.*WorkflowEditor" frontend/src/ --include="*.tsx"` && zanotuj dependencies.
Podziel na 3 komponenty: `WorkflowEditor.tsx` (główny editor 350 linii), `NodePalette.tsx` (dostępne node types 250 linii), `EdgeEditor.tsx` (edge connections 200 linii) + zaktualizuj importy.
PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 41. 🟢 [Frontend Component] - PersonaPanel.tsx (574 linii)

Przejrzyj `frontend/src/components/panels/PersonaPanel.tsx` (574 linii, problem: panel + tabs razem).
PRZED: `grep -r "import.*PersonaPanel" frontend/src/ --include="*.tsx"` && zanotuj usage.
Podziel na 3 komponenty: `PersonaPanel.tsx` (główny panel 250 linii), `PersonaTabs.tsx` (tab navigation 200 linii), `PersonaContent.tsx` (tab content 200 linii) + zaktualizuj importy.
PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 42. 🟢 [Frontend Component] - AISummaryPanel.tsx (582 linii)

Przejrzyj `frontend/src/components/analysis/AISummaryPanel.tsx` (582 linii, problem: summary + insights razem).
PRZED: `grep -r "import.*AISummaryPanel" frontend/src/ --include="*.tsx"` && zanotuj dependencies.
Podziel na 3 komponenty: `AISummaryPanel.tsx` (główny panel 250 linii), `InsightsList.tsx` (insights display 200 linii), `ThemesView.tsx` (themes visualization 200 linii) + zaktualizuj importy.
PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 43. 🟢 [Frontend Component] - Surveys.tsx

Przejrzyj `frontend/src/components/layout/Surveys.tsx` (506 linii, cleanup).
PRZED: `wc -l frontend/src/components/layout/Surveys.tsx && grep -r "import.*Surveys" frontend/src/ --include="*.tsx"`.
Wyodrębnij: `SurveysList.tsx` (lista 250 linii), `SurveyForm.tsx` (form 300 linii) jeśli potrzeba + zaktualizuj importy + usuń nieużywane state variables.
PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 44. 🟢 [Frontend Component] - Dashboard.tsx

Przejrzyj `frontend/src/components/layout/Dashboard.tsx` (sprawdź rzeczywistą długość).
PRZED: `wc -l frontend/src/components/layout/Dashboard.tsx && grep -r "import.*Dashboard" frontend/src/ --include="*.tsx"`.
Jeśli >500 linii: wyodrębnij `DashboardMetrics.tsx`, `DashboardCharts.tsx`, `DashboardUsage.tsx` + zaktualizuj importy.
PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 45. ❌ [Frontend Component] - ProjectSettings.tsx - NIE ISTNIEJE

**UWAGA:** Plik `ProjectSettings.tsx` NIE ISTNIEJE! Jest natomiast `Settings.tsx` (601 linii).

Prompt (krótki): Przejrzyj `frontend/src/components/Settings.tsx` (601 linii, settings aplikacji). PRZED: `wc -l frontend/src/components/Settings.tsx && rg -n "import.*Settings" frontend/src --glob "**/*.tsx"`. Jeśli >500 linii: wyodrębnij `GeneralSettings.tsx`, `AppearanceSettings.tsx`, `NotificationSettings.tsx` + zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`). PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 46. ❌ [Frontend Component] - ReasoningPanel.tsx - NIE ISTNIEJE

**UWAGA:** Plik `ReasoningPanel.tsx` NIE ISTNIEJE w `panels/`! Jest natomiast `PersonaReasoningPanel.tsx` w `personas/`.

Prompt (krótki): Przejrzyj `frontend/src/components/personas/PersonaReasoningPanel.tsx` (sprawdź długość). PRZED: `wc -l frontend/src/components/personas/PersonaReasoningPanel.tsx && rg -n "PersonaReasoningPanel" frontend/src --glob "**/*.tsx"`. Jeśli >500 linii: wyodrębnij `OrchestrationBrief.tsx`, `GraphInsights.tsx`, `Troubleshooting.tsx` + zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`). PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 47. ❌ [Frontend Component] - WorkflowTemplates.tsx - NIE ISTNIEJE

**UWAGA:** Plik `WorkflowTemplates.tsx` NIE ISTNIEJE! Jest natomiast `WorkflowsListPage.tsx` (zawiera listę + templates).

Prompt (krótki): Przejrzyj `frontend/src/components/workflows/WorkflowsListPage.tsx` (sprawdź długość). PRZED: `wc -l frontend/src/components/workflows/WorkflowsListPage.tsx && rg -n "WorkflowsListPage" frontend/src --glob "**/*.tsx"`. Jeśli >500 linii: wyodrębnij `WorkflowsList.tsx`, `TemplatesList.tsx`, `WorkflowActions.tsx` + zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`). PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 48. ❌ [Frontend Component] - WorkflowRun.tsx - NIE ISTNIEJE

**UWAGA:** Plik `WorkflowRun.tsx` NIE ISTNIEJE! Funkcjonalność workflow runs jest w `ExecutionHistory.tsx` i `ExecutionHistoryItem.tsx`.

Prompt (krótki): Przejrzyj `frontend/src/components/workflows/ExecutionHistory.tsx` i `ExecutionHistoryItem.tsx` (sprawdź długości). PRZED: `wc -l frontend/src/components/workflows/Execution*.tsx && rg -n "ExecutionHistory" frontend/src --glob "**/*.tsx"`. Jeśli któryś >500 linii: wyodrębnij `RunStatus.tsx`, `RunLogs.tsx`, `RunResults.tsx` + zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`). PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 49. 🟢 [Frontend Constants] - Hardcoded labels → constants

Przejrzyj `frontend/src/components/layout/Personas.tsx` (linia 76-99: hardcoded demographic labels).
PRZED: `grep -n "const.*label.*=" frontend/src/components/layout/Personas.tsx | head -30`.
Utwórz: `frontend/src/constants/personas.ts` z eksportowanymi labels (AGE_GROUPS, EDUCATION_LEVELS, OCCUPATIONS, etc.) + zastąp hardcoded values importami + sprawdź inne komponenty z hardcoded labels + **usuń nieużywany kod** (`npm run lint -- --fix`).
PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Utwórz constants [ ] Zastąp imports [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 50. 🟢 [Frontend UI] - Unused components audit

Przejrzyj `frontend/src/components/ui/` (nieużywane shadcn components).
PRZED: `ls frontend/src/components/ui/ && grep -r "from.*components/ui" frontend/src/ --include="*.tsx" | cut -d: -f2 | sort | uniq -c`.
Usuń nieużywane: `aspect-ratio.tsx`, `input-otp.tsx`, `breadcrumb.tsx` jeśli nie są używane + **usuń nieużywany kod** (`npm run lint -- --fix`) + zaktualizuj `ui/index.ts` jeśli istnieje.
PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Usuń unused [ ] Build [ ] Działa.

---

### 🟢 P2: Frontend Lib/Hooks/Types

#### 51. 🟢 [Frontend Lib] - lib/api.ts (846 linii)

Przejrzyj `frontend/src/lib/api.ts` (846 linii, problem: wszystkie API calls w jednym pliku).
PRZED: `grep -r "from.*lib/api" frontend/src/ --include="*.tsx" --include="*.ts"` && zanotuj usage patterns.
Podziel na moduły: `api/personas.ts` (persona endpoints 250 linii), `api/projects.ts` (project endpoints 200 linii), `api/workflows.ts` (workflow endpoints 200 linii), `api/focus-groups.ts` (focus group endpoints 200 linii) + utwórz `api/index.ts` z re-exports + zaktualizuj importy we wszystkich komponentach + **usuń nieużywany kod** (`npm run lint -- --fix`).
PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 52. 🟢 [Frontend Types] - types/index.ts (887 linii)

Przejrzyj `frontend/src/types/index.ts` (887 linii, problem: wszystkie typy w jednym pliku).
PRZED: `grep -r "from.*types" frontend/src/ --include="*.tsx" --include="*.ts"` && zanotuj usage.
Podziel na domain types: `types/persona.ts`, `types/project.ts`, `types/workflow.ts`, `types/focus-group.ts`, `types/survey.ts`, `types/dashboard.ts` + utwórz `types/index.ts` z re-exports + zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`).
PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 53. 🟢 [Frontend Hooks] - hooks/useWorkflows.ts (639 linii)

Przejrzyj `frontend/src/hooks/useWorkflows.ts` (639 linii, problem: zbyt wiele responsibilności).
PRZED: `grep -r "useWorkflows" frontend/src/ --include="*.tsx"` && zanotuj usage patterns.
Podziel na 4 hooks: `useWorkflowCrud.ts` (CRUD operations 200 linii), `useWorkflowExecution.ts` (execution 200 linii), `useWorkflowTemplates.ts` (templates 150 linii), `useWorkflowValidation.ts` (validation 150 linii) + zaktualizuj importy w komponentach workflows + **usuń nieużywany kod** (`npm run lint -- --fix`).
PO: `cd frontend && npm run build && npm run preview`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Build [ ] Działa.

---

#### 54. 🟢 [Frontend Hooks] - hooks/usePersonas.ts

Prompt (krótki): Przejrzyj `frontend/src/hooks/usePersonas.ts` (sprawdź długość i odpowiedzialności). Najpierw: `wc -l frontend/src/hooks/usePersonas.ts && rg -n "usePersonas" frontend/src --glob "**/*.{ts,tsx}"`. Jeśli >500 linii, wydziel `usePersonaGeneration.ts`, `usePersonaDetails.ts`, `usePersonaFilters.ts` i zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`) + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview`.

---

#### 55. 🟢 [Frontend Hooks] - hooks/useFocusGroups.ts

Prompt (krótki): Przejrzyj `frontend/src/hooks/useFocusGroups.ts` (sprawdź długość i odpowiedzialności). Najpierw: `wc -l frontend/src/hooks/useFocusGroups.ts && rg -n "useFocusGroups" frontend/src --glob "**/*.{ts,tsx}"`. Jeśli >500 linii, wydziel `useFocusGroupDiscussion.ts` i `useFocusGroupSummaries.ts` i zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview`.

---

#### 56. 🟢 [Frontend Lib] - lib/utils.ts

Prompt (krótki): Przejrzyj `frontend/src/lib/utils.ts` (sprawdź długość i zakres). Najpierw: `wc -l frontend/src/lib/utils.ts && rg -n "from .*lib/utils" frontend/src --glob "**/*.{ts,tsx}"`. Jeśli >500 linii, wydziel `formatting.ts`, `validation.ts`, `date-utils.ts` i zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview`.

---

#### 57. 🟢 [Frontend Stores] - stores/zustand cleanup

Prompt (krótki): Przejrzyj `frontend/src/stores/` (konsolidacja Zustand stores). Najpierw: `ls -lh frontend/src/stores && find frontend/src/stores -name "*.ts" -exec wc -l {} +`. Usuń nieużywane slices, unikaj duplikowania stanu TanStack Query i zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`) + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview`.

---

#### 58. 🟢 [Frontend Constants] - constants/ consolidation

Prompt (krótki): Przejrzyj `frontend/src/` i zinwentaryzuj constants. Najpierw: `rg -n "constants|DEFAULT|LABEL|OPTIONS" frontend/src --glob "**/*.{ts,tsx}"`. Utwórz `frontend/src/constants/{personas.ts,workflows.ts,ui.ts}` i przenieś hardcoded wartości; zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview`.

---

### 🟢 P2: Tests

#### 59. 🟢 [Tests] - test_workflow_validator.py (1310 linii)

Przejrzyj `tests/unit/services/workflows/test_workflow_validator.py` (1310 linii, problem: zbyt wiele test cases).
PRZED: `grep -n "^def test_" tests/unit/services/workflows/test_workflow_validator.py | wc -l` && zanotuj liczbę testów.
Podziel na 3 pliki: `test_validator_basic.py` (basic validation 500 linii), `test_validator_nodes.py` (node validation 450 linii), `test_validator_edges.py` (edge validation 400 linii) + zaktualizuj fixtures imports.
PO: `pytest tests/unit/services/workflows/test_workflow_validator*.py -v`.
Checklist: [ ] Grep [ ] Podział [ ] Fixtures [ ] Fixes (cleanup) [ ] Pytest [ ] Działa.

---

#### 60. 🟢 [Tests] - test_workflow_service.py (873 linii)

Przejrzyj `tests/unit/services/workflows/test_workflow_service.py` (873 linii, problem: CRUD + logic tests razem).
PRZED: `grep -n "^def test_" tests/unit/services/workflows/test_workflow_service.py | wc -l`.
Podziel na 2 pliki: `test_workflow_crud.py` (CRUD tests 450 linii), `test_workflow_logic.py` (business logic 450 linii) + zaktualizuj fixtures.
PO: `pytest tests/unit/services/workflows/test_workflow*.py -v`.
Checklist: [ ] Grep [ ] Podział [ ] Fixtures [ ] Fixes (cleanup) [ ] Pytest [ ] Działa.

---

#### 61. 🟢 [Tests] - test_workflow_executor.py (825 linii)

Przejrzyj `tests/unit/services/workflows/test_workflow_executor.py` (825 linii, problem: zbyt wiele execution scenarios).
PRZED: `grep -n "^def test_" tests/unit/services/workflows/test_workflow_executor.py | wc -l`.
Podziel na 2 pliki: `test_executor_basic.py` (basic execution 450 linii), `test_executor_advanced.py` (advanced scenarios 400 linii) + **usuń nieużywany kod** (`ruff check --select F401,F841 --fix`) + zaktualizuj fixtures.
PO: `pytest tests/unit/services/workflows/test_workflow_executor*.py -v`.
Checklist: [ ] Grep [ ] Podział [ ] Fixtures [ ] Fixes (cleanup) [ ] Pytest [ ] Działa.

---

#### 62. 🟢 [Tests] - test_rag_hybrid_search.py (553 linii)

Przejrzyj `tests/unit/test_rag_hybrid_search.py` (553 linii, cleanup).
PRZED: `wc -l tests/unit/test_rag_hybrid_search.py && grep -n "^def test_" tests/unit/test_rag_hybrid_search.py | wc -l`.
Jeśli potrzeba: podziel na `test_vector_search.py` + `test_keyword_search.py` + `test_rrf_fusion.py` + zaktualizuj fixtures + usuń deprecated test utilities.
PO: `pytest tests/unit/test_rag*.py -v`.
Checklist: [ ] Grep [ ] Podział [ ] Fixtures [ ] Fixes (cleanup) [ ] Pytest [ ] Działa.

---

#### 63. 🟢 [Tests] - test_persona_orchestration.py (545 linii)

Przejrzyj `tests/unit/test_persona_orchestration.py` (545 linii, cleanup).
PRZED: `wc -l tests/unit/test_persona_orchestration.py && grep -n "^def test_" tests/unit/test_persona_orchestration.py | wc -l`.
Jeśli potrzeba: podziel na `test_orchestration_core.py` + `test_segment_creation.py` + zaktualizuj fixtures.
PO: `pytest tests/unit/test_persona*.py -v`.
Checklist: [ ] Grep [ ] Podział [ ] Fixtures [ ] Fixes (cleanup) [ ] Pytest [ ] Działa.

---

#### 64. 🟢 [Tests] - fixtures consolidation

Przejrzyj `tests/fixtures/` i `tests/conftest.py` (sprawdź duplikaty).
PRZED: `find tests/ -name "conftest.py" -o -name "*fixtures*" | xargs grep -h "^def " | sort | uniq -c | sort -rn`.
Konsoliduj: usuń duplikaty fixtures + przenieś współdzielone do `tests/fixtures/shared.py` + zaktualizuj importy we wszystkich testach + usuń nieużywane fixtures + **usuń nieużywany kod** (`ruff check tests/ --select F401,F841 --fix`).
PO: `pytest tests/ -v --collect-only | grep "test session starts"`.
Checklist: [ ] Find duplicates [ ] Konsoliduj [ ] Importy [ ] Fixes (cleanup) [ ] Pytest [ ] Działa.

---

#### 65. 🟢 [Tests] - Deprecated test utilities cleanup

Przejrzyj `tests/` (sprawdź deprecated utilities).
PRZED: `grep -r "deprecated" tests/ --include="*.py" && grep -r "legacy" tests/ --include="*.py"`.
Usuń: deprecated mock utilities + legacy test helpers + stare fixtures (sprawdź daty last modified) + zaktualizuj testy używające deprecated utils + **usuń nieużywany kod** (`ruff check tests/ --select F401,F841 --fix`).
PO: `pytest tests/ -v`.
Checklist: [ ] Grep deprecated [ ] Usuń [ ] Aktualizuj testy [ ] Fixes (cleanup) [ ] Pytest [ ] Działa.

---

#### 66. 🟢 [Tests] - Coverage gaps (target 85%+)

Przejrzyj pokrycie testami repo (sprawdź luki w coverage).
PRZED: `pytest --cov=app --cov-report=term-missing --cov-report=html && open htmlcov/index.html`.
Zidentyfikuj: moduły <85% coverage (szczególnie services/) + dodaj testy dla uncovered branches + priorytet: critical paths (persona generation, focus groups) + zaktualizuj existing tests jeśli przestarzałe + **usuń nieużywany kod z testów** (`ruff check tests/ --select F401,F841 --fix`).
PO: `pytest --cov=app --cov-report=term && grep "TOTAL" | awk '{print $4}'` (sprawdź czy >85%).
Checklist: [ ] Coverage report [ ] Identify gaps [ ] Add tests [ ] Fixes (cleanup) [ ] Pytest [ ] >85% coverage.

---

### 🟢 P2: Config & Scripts

#### 67. 🟢 [Config] - config/loader.py (681 linii)

Przejrzyj `config/loader.py` (681 linii, problem: loading + validation razem).
PRZED: `grep -r "from config.loader import" app/ tests/ scripts/ --include="*.py"` && zanotuj dependencies.
Wyodrębnij: `config/validators.py` (YAML validation logic 350 linii), zostaw loading w oryginalnym pliku (350 linii) + zaktualizuj importy w `config/__init__.py`, `config/models.py`, `config/prompts.py` + **usuń nieużywany kod** (`ruff check config/ --select F401,F841 --fix`).
PO: `python scripts/config_validate.py && pytest tests/unit/test_config.py -v && docker-compose restart api`.
Checklist: [ ] Grep [ ] Podział [ ] Importy [ ] Fixes (cleanup) [ ] Validation script [ ] Testy [ ] Działa.

---

#### 68. 🟢 [Scripts] - scripts/cleanup_legacy_mentions.py (782 linii)

Przejrzyj `scripts/cleanup_legacy_mentions.py` (782 linii, problem: przestarzały script).
PRZED: `git log --oneline scripts/cleanup_legacy_mentions.py | head -5` && sprawdź last modified date.
Archiwizuj: przenieś do `scripts/archive/cleanup_legacy_mentions_2024.py` + dodaj README w `scripts/archive/` z opisem przestarzałych scripts + usuń z głównego folderu scripts/ + **usuń nieużywany kod z pozostałych skryptów** (`ruff check scripts/ --select F401,F841 --fix`).
PO: `ls -lh scripts/ && ls -lh scripts/archive/`.
Checklist: [ ] Git log [ ] Przenieś archive [ ] Fixes (cleanup) [ ] README [ ] Verify [ ] Działa.

---

#### 69. 🟢 [Scripts] - create_demo_data consolidation

Przejrzyj `scripts/create_demo_data*.py` (sprawdź ile wersji istnieje).
PRZED: `ls -lh scripts/create_demo_data* && grep -h "^def " scripts/create_demo_data*.py | sort | uniq -c`.
Konsoliduj: zachowaj najnowszą wersję `create_demo_data.py` + przenieś stare do `scripts/archive/` + usuń duplikaty funkcji + zaktualizuj README w scripts/ z instrukcją użycia + **usuń nieużywany kod** (`ruff check scripts/ --select F401,F841 --fix`).
PO: `python scripts/create_demo_data.py --help && ls scripts/archive/`.
Checklist: [ ] List versions [ ] Konsoliduj [ ] Archive old [ ] Fixes (cleanup) [ ] README [ ] Test script.

---

#### 70. 🟢 [Global] - Cache cleanup (.pyc, __pycache__, .DS_Store)

Przejrzyj repo (cache files, temp files).
PRZED: `find . -name "*.pyc" -o -name "__pycache__" -o -name ".DS_Store" -o -name "*.egg-info" | wc -l`.
Cleanup: `find . -name "*.pyc" -delete && find . -name "__pycache__" -type d -delete && find . -name ".DS_Store" -delete` + dodaj do `.gitignore` jeśli nie ma + utwórz `scripts/cleanup_cache.sh` dla future use + **usuń nieużywany kod z całego repo** (`ruff check . --select F401,F841 --fix`).
PO: `find . -name "*.pyc" -o -name "__pycache__" -o -name ".DS_Store" | wc -l` (powinno być 0).
Checklist: [ ] Find cache [ ] Delete [ ] Fixes (cleanup) [ ] Update .gitignore [ ] Create script [ ] Verify.

---

### 🔵 P3: Documentation

#### 71. 🔵 [Docs] - docs/BACKEND.md (2673 linii) → split

Przejrzyj `docs/BACKEND.md` (2673 linii, problem: przekracza limit 700 linii).
PRZED: `wc -l docs/BACKEND.md && grep "^##" docs/BACKEND.md` && zanotuj główne sekcje.
Podziel na 2 pliki: `docs/BACKEND_ARCHITECTURE.md` (architektura systemu, wzorce, high-level design ~1300 linii), `docs/BACKEND_IMPLEMENTATION.md` (szczegóły implementacji, API endpoints, services ~1400 linii) + zaktualizuj `docs/README.md` z linkami + dodaj cross-references między plikami.
PO: `wc -l docs/BACKEND*.md && grep "\[BACKEND" docs/README.md`.
Checklist: [ ] Grep sections [ ] Podział [ ] Cross-refs [ ] Update README [ ] Review.

---

#### 72. 🔵 [Docs] - docs/AI_ML.md (1202 linii) → split

Przejrzyj `docs/AI_ML.md` (1202 linii, problem: przekracza limit 700 linii).
PRZED: `wc -l docs/AI_ML.md && grep "^##" docs/AI_ML.md` && zanotuj główne sekcje.
Podziel na 2 pliki: `docs/AI_ML_OVERVIEW.md` (LLM integration, prompts, models, persona generation ~600 linii), `docs/AI_ML_RAG.md` (RAG system, hybrid search, graph RAG, embeddings ~650 linii) + zaktualizuj `docs/README.md` + dodaj cross-references.
PO: `wc -l docs/AI_ML*.md && grep "\[AI_ML" docs/README.md`.
Checklist: [ ] Grep sections [ ] Podział [ ] Cross-refs [ ] Update README [ ] Review.

---

#### 73. 🔵 [Docs] - docs/QA.md (899 linii) → optimize

Przejrzyj `docs/QA.md` (899 linii, blisko limitu 700 linii).
PRZED: `wc -l docs/QA.md && grep "^##" docs/QA.md` && zanotuj redundantne sekcje.
Optymalizuj: usuń redundantne przykłady + konsoliduj podobne sekcje + przenieś verbose command examples do appendix + skróć do ~680 linii zachowując kluczowe informacje + zaktualizuj `docs/README.md` jeśli zmienił się scope.
PO: `wc -l docs/QA.md` (powinno być <700) `&& grep "QA" docs/README.md`.
Checklist: [ ] Analyze redundancy [ ] Optimize [ ] Appendix [ ] Update README [ ] Review.

---

#### 74. 🔵 [Docs] - docs/INFRASTRUKTURA.md (882 linii) → optimize

Przejrzyj `docs/INFRASTRUKTURA.md` (882 linii, blisko limitu 700 linii).
PRZED: `wc -l docs/INFRASTRUKTURA.md && grep "^##" docs/INFRASTRUKTURA.md` && zanotuj verbose sekcje.
Optymalizuj: skróć verbose Docker/CI/CD examples + konsoliduj deployment instructions + przenieś detailed troubleshooting do appendix + skróć do ~680 linii + zaktualizuj `docs/README.md`.
PO: `wc -l docs/INFRASTRUKTURA.md` (powinno być <700) `&& grep "INFRA" docs/README.md`.
Checklist: [ ] Analyze verbosity [ ] Optimize [ ] Appendix [ ] Update README [ ] Review.

---

#### 75. 🔵 [Docs] - workflows docs move

Przejrzyj `app/services/workflows/docs/` (dokumentacja workflows w niewłaściwym miejscu).
PRZED: `ls -lh app/services/workflows/docs/ && find app/services/workflows/docs/ -name "*.md" -exec wc -l {} +`.
Przenieś: `mkdir -p docs/workflows/ && mv app/services/workflows/docs/*.md docs/workflows/` + zaktualizuj linki w `docs/README.md` + sprawdź internal cross-references w przenoszonych plikach + usuń pusty folder `app/services/workflows/docs/`.
PO: `ls -lh docs/workflows/ && grep "workflows" docs/README.md && ! test -d app/services/workflows/docs`.
Checklist: [ ] List files [ ] Create dir [ ] Move [ ] Update links [ ] Remove old [ ] Verify.

---

### 🟠 P2.5: Audyt Poprzednich Refaktoryzacji

**UWAGA:** Ta sekcja powstała 2025-11-11 po odkryciu martwego kodu (GraphAnalysis.tsx) i nieistniejących komponentów w oryginalnych zadaniach 36-48. Zadania 76-85 sprawdzają skutki poprzednich refaktoryzacji i usuwają martwy kod.

#### 76. 🟠 [Backend Audit] - Nieużywane importy po zadaniach 1-35

Przejrzyj wszystkie moduły backendu zrefaktoryzowane w zadaniach 1-35 (sprawdź martwe importy po podziale plików).
PRZED: `ruff check app/services --select F401 --statistics` && zanotuj liczbę nieużywanych importów.
Cleanup: uruchom `ruff check app/services --select F401,F841 --fix` (usuwa unused imports i variables) + ręcznie sprawdź `app/api` i `tests/` czy nie ma importów do starych nieistniejących modułów + zaktualizuj wszystkie `__init__.py` pliki żeby eksportowały tylko używane symbole.
PO: `ruff check app/ --select F401,F841 && pytest tests/unit -v && docker-compose restart api`.
Checklist: [ ] Ruff statistics [ ] Auto-fix [ ] Manual review [ ] Update __init__ [ ] Pytest [ ] Działa.

---

#### 77. 🟠 [Frontend Audit] - Usunięcie martwego kodu

Przejrzyj frontend i usuń komponenty które nie są używane nigdzie w aplikacji.
PRZED: `rg -l "GraphAnalysis|import.*GraphAnalysis" frontend/src --glob "*.tsx" --glob "*.ts"` && zweryfikuj że GraphAnalysis.tsx jest używany tylko w samym sobie.
Usuń martwe komponenty:
- `frontend/src/components/layout/GraphAnalysis.tsx` (788 linii, 0 użyć)
- Sprawdź routing w `App.tsx` czy nie ma martwych case'ów
- Sprawdź czy `FigmaDashboard.tsx` jest używany (może być legacy)
- Sprawdź `StatsOverlay.tsx`, `FloatingControls.tsx` (małe pliki, mogą być nieużywane)
Usuń imports: `rg "import.*GraphAnalysis" frontend/src -l` i usuń wszystkie importy + zaktualizuj routing + **usuń nieużywany kod** (`npm run lint -- --fix`).
PO: `cd frontend && npm run build && npm run preview && rg "GraphAnalysis" frontend/src` (powinno być 0 wyników).
Checklist: [ ] Identify dead code [ ] Delete files [ ] Remove imports [ ] Update routing [ ] Fixes (lint) [ ] Build [ ] Działa.

---

#### 78. 🟠 [Backend Audit] - TODO/FIXME z zadań 1-35

Przejrzyj TODO/FIXME markers pozostawione po refaktoryzacji zadań 1-35 i zdecyduj: fix now, create issue, or delete.
PRZED: `rg "TODO|FIXME|XXX|HACK" app/services --glob "*.py" -n | tee /tmp/todos.txt && wc -l /tmp/todos.txt`.
Kategoryzuj:
- **Fix now:** TODO które są łatwe do naprawienia (np. cache TTL z config)
- **Create GitHub issue:** Większe TODO wymagające osobnego zadania (np. weighted sampling)
- **Delete:** Przestarzałe TODO z starego kodu
Znalezione TODO:
- `app/services/workflows/execution/workflow_executor.py:180` - Map node_id → WorkflowStep.id
- `app/services/workflows/nodes/personas.py:100,107,175` - Integracja z segment-based generation
- `app/services/workflows/validation/workflow_validator.py:422` - Validate template exists
Napraw/utwórz issues/usuń + zaktualizuj kod + **usuń nieużywany kod** (`ruff check --select F401,F841 --fix`).
PO: `rg "TODO|FIXME" app/services --glob "*.py" -n | wc -l` (powinno być <10) `&& pytest tests/unit -v`.
Checklist: [ ] List TODOs [ ] Kategoryzuj [ ] Fix/Issue/Delete [ ] Update code [ ] Pytest [ ] Działa.

---

#### 79. 🟠 [Frontend Audit] - Komponenty UI shadcn (56 plików)

Przejrzyj `frontend/src/components/ui/` (56 komponentów shadcn) i usuń nieużywane.
PRZED: `ls frontend/src/components/ui/*.tsx | wc -l && for f in frontend/src/components/ui/*.tsx; do name=$(basename "$f" .tsx); uses=$(rg -l "@/components/ui/$name|components/ui/$name" frontend/src --glob "*.tsx" | grep -v "ui/$name.tsx" | wc -l); echo "$uses - $name"; done | sort -n | head -20`.
Usuń komponenty z 0-1 użyciami (mogą być nieużywane):
- Sprawdź `aspect-ratio.tsx`, `input-otp.tsx`, `breadcrumb.tsx`
- Sprawdź `resizable.tsx`, `sonner.tsx`, `toggle-group.tsx`
- Sprawdź `pagination.tsx`, `navigation-menu.tsx`
Uwaga: zachowaj podstawowe (button, input, card, dialog, label, select, textarea, checkbox, radio-group, switch, slider, tabs, toast, tooltip, dropdown-menu, popover, avatar, badge, separator, skeleton, progress, alert, scroll-area, sheet, table).
Usuń nieużywane + zaktualizuj `ui/index.ts` jeśli istnieje + **usuń nieużywany kod** (`npm run lint -- --fix`).
PO: `cd frontend && npm run build && ls frontend/src/components/ui/*.tsx | wc -l` (powinno być <40).
Checklist: [ ] List UI components [ ] Check usage [ ] Delete unused [ ] Update index [ ] Fixes (lint) [ ] Build [ ] Działa.

---

#### 80. 🟠 [Backend Audit] - BackgroundTasks usage

Przejrzyj użycie `BackgroundTasks` w API - sprawdź czy po zadaniach 22-23 jest nadal potrzebny lub został zastąpiony asynchronicznymi taskami.
PRZED: `rg "BackgroundTasks|background_tasks" app/api --glob "*.py" -n` && zanotuj wszystkie użycia.
Znalezione użycia:
- `app/api/rag.py` - używa BackgroundTasks
- `app/api/personas/generation_endpoints.py` - używa BackgroundTasks
Sprawdź czy te operacje mogą być wykonane synchronicznie async/await lub czy wymagają prawdziwych background tasks (Celery/Redis Queue). Jeśli operacje są szybkie (<2s), rozważ zamianę na bezpośrednie async calls. Jeśli długie (>5s), dodaj TODO dla Celery integration.
Cleanup/decision + zaktualizuj kod + **usuń nieużywany kod** (`ruff check --select F401,F841 --fix`).
PO: `rg "BackgroundTasks" app/api --glob "*.py" -n && pytest tests/integration -v`.
Checklist: [ ] List usage [ ] Analyze necessity [ ] Decision (keep/remove/Celery) [ ] Update code [ ] Pytest [ ] Działa.

---

#### 81. 🟠 [Full Repo Audit] - Duplikaty kodu (copy-paste detection)

Znajdź duplikaty kodu w całym repo (copy-paste anti-pattern) i wydziel do wspólnych utility functions.
PRZED: zainstaluj `pip install vulture pylint` (dla Python) i użyj `rg` dla TypeScript patterns.
Szukaj duplikatów:
```bash
# Python: funkcje >10 linii powtórzone 2+ razy
rg "def \w+\(" app/ -A 10 | sort | uniq -cd | sort -rn | head -20

# TypeScript: funkcje >10 linii powtórzone 2+ razy
rg "function \w+\(|const \w+ = \(" frontend/src -A 10 | sort | uniq -cd | sort -rn | head -20
```
Znalezione duplikaty → wydziel do:
- Backend: `app/services/shared/utils.py` lub domain-specific utils
- Frontend: `frontend/src/lib/utils.ts` lub domain-specific utils
Refaktoryzuj duplikaty + zaktualizuj importy + **usuń nieużywany kod** (ruff + npm lint).
PO: `pytest tests/unit -v && cd frontend && npm run build`.
Checklist: [ ] Detect duplicates [ ] Extract to utils [ ] Update imports [ ] Fixes (lint) [ ] Tests [ ] Działa.

---

#### 82. 🟠 [Frontend Audit] - Nieużywane hooki i utility functions

Przejrzyj `frontend/src/hooks/` i `frontend/src/lib/` i usuń nieużywane hooki oraz utility functions.
PRZED:
```bash
# Lista wszystkich hooks
find frontend/src/hooks -name "*.ts" -o -name "*.tsx"

# Dla każdego hooka sprawdź usage
for hook in $(find frontend/src/hooks -name "use*.ts" -o -name "use*.tsx"); do
  name=$(basename "$hook" .ts | sed 's/.tsx//')
  uses=$(rg -l "$name" frontend/src --glob "*.tsx" --glob "*.ts" | grep -v "hooks/$name" | wc -l)
  echo "$uses - $name"
done | sort -n
```
Usuń hooki z 0 użyciami + sprawdź `lib/` utility functions (np. `formatters.ts`, `validators.ts`) + **usuń nieużywany kod** (`npm run lint -- --fix`).
PO: `cd frontend && npm run build && npm run type-check`.
Checklist: [ ] List hooks [ ] Check usage [ ] Delete unused [ ] Check lib utils [ ] Fixes (lint) [ ] Build [ ] Type-check.

---

#### 83. 🟠 [Backend Audit] - Deprecated metody w serwisach

Przejrzyj serwisy backendu i usuń przestarzałe metody które nie są już używane po refaktoryzacji.
PRZED: `rg "@deprecated|# deprecated|# legacy|# old" app/services --glob "*.py" -n` && zanotuj wszystkie deprecated markers.
Sprawdź każdy serwis czy nie ma:
- Metod oznaczonych `@deprecated` lub komentarzem `# deprecated`
- Metod typu `legacy_*` lub `old_*`
- Metod nie używanych nigdzie: `for method in $(rg "^    def \w+\(" app/services/surveys/survey_response_generator.py -o | sed 's/def //'); do echo "$method - $(rg "$method" app tests --glob "*.py" | wc -l)"; done`
Przykład z zadania 11: `legacy_survey_format()` w survey_response_generator.py.
Usuń deprecated metody + zaktualizuj testy + **usuń nieużywany kod** (`ruff check --select F401,F841 --fix`).
PO: `rg "@deprecated|legacy_|old_" app/services --glob "*.py" -n && pytest tests/unit -v`.
Checklist: [ ] Find deprecated [ ] Check usage [ ] Delete unused [ ] Update tests [ ] Fixes (ruff) [ ] Pytest [ ] Działa.

---

#### 84. 🟠 [Tests Audit] - Martwe fixtures i test utilities

Przejrzyj `tests/fixtures/` i `tests/conftest.py` i usuń nieużywane fixtures oraz test utilities.
PRZED:
```bash
# Lista wszystkich fixtures
find tests/ -name "conftest.py" -o -name "*fixtures*" | xargs rg "^def \w+\(" -o | sed 's/def //' | sed 's/(//' | sort | uniq

# Sprawdź usage każdej fixture
for fixture in $(find tests/ -name "conftest.py" | xargs rg "@pytest.fixture" -A 1 | rg "^def \w+" -o | sed 's/def //'); do
  uses=$(rg "$fixture" tests/ --glob "*.py" | grep -v "def $fixture" | wc -l)
  echo "$uses - $fixture"
done | sort -n | head -20
```
Usuń fixtures z 0-1 użyciami (poza fixtures używanymi jako dependencies innych fixtures) + sprawdź `tests/utils/` czy nie ma deprecated test helpers + konsoliduj duplikaty fixtures (zadanie 64).
Cleanup + zaktualizuj testy + **usuń nieużywany kod** (`ruff check tests/ --select F401,F841 --fix`).
PO: `pytest tests/ -v --collect-only && pytest tests/unit -v`.
Checklist: [ ] List fixtures [ ] Check usage [ ] Delete unused [ ] Consolidate duplicates [ ] Fixes (ruff) [ ] Pytest [ ] Działa.

---

#### 85. 🟠 [Global Audit] - Nieużywane dependencies

Przejrzyj `requirements.txt` i `frontend/package.json` i usuń nieużywane dependencies.
PRZED:
```bash
# Python: sprawdź imports vs requirements
pip install pipreqs
pipreqs . --force --savepath /tmp/actual_requirements.txt
diff requirements.txt /tmp/actual_requirements.txt

# Frontend: sprawdź imports vs package.json
npx depcheck frontend/
```
Backend - potencjalnie nieużywane:
- Sprawdź czy wszystkie biblioteki w requirements.txt są importowane w app/
- Sprawdź optionalne dependencies w pyproject.toml [llm-providers], [document-processing]

Frontend - potencjalnie nieużywane:
- Sprawdź devDependencies vs dependencies
- Sprawdź czy biblioteki UI (lucide-react, radix-ui) są wszystkie używane

Usuń nieużywane dependencies + zaktualizuj lockfiles + rebuild + **usuń nieużywany kod** (ruff + npm lint).
PO: `pip install -r requirements.txt && cd frontend && npm install && npm run build && docker-compose build api`.
Checklist: [ ] Analyze Python deps [ ] Analyze Node deps [ ] Delete unused [ ] Update lockfiles [ ] Rebuild [ ] Test [ ] Działa.

---

## 📚 Appendix: Komendy i Narzędzia

### Grep Patterns (Znajdowanie Dependencies)

```bash
# Znajdź wszystkie importy klasy/modułu
rg -n "ClassName" app tests --glob "**/*.py"
rg -n "from app.services.module import" app tests --glob "**/*.py"

# Znajdź usage w frontend
rg -n "import.*ComponentName" frontend/src --glob "**/*.{ts,tsx}"

# Policz wystąpienia
rg -n "pattern" app --glob "**/*.py" | wc -l

# Znajdź TODO markers
rg -n "TODO" app tests --glob "**/*.py"

# Znajdź hardcoded values
rg -n "const.*=.*\[" frontend/src/components/layout/Personas.tsx

# Znajdź print statements (powinny być logger)
rg -n "print\(" app --glob "**/*.py"
```

### Pytest Commands

```bash
# Wszystkie testy
pytest -v

# Tylko unit tests
pytest tests/unit -v

# Tylko specific file
pytest tests/unit/test_persona_generator.py -v

# Z pokryciem kodu
pytest --cov=app --cov-report=html
pytest --cov=app --cov-report=term-missing

# Szybkie testy (bez slow markers)
pytest -v -m "not slow"

# Konkretny test
pytest tests/unit/test_file.py::test_function_name -v

# Z logami
pytest -v -s

# Collect only (sprawdź co zostanie uruchomione)
pytest --collect-only
```

### Docker Compose Commands

```bash
# Restart usług
docker-compose restart api
docker-compose restart api neo4j redis

# Sprawdź logi
docker-compose logs -f api
docker-compose logs --tail=100 api

# Sprawdź status
docker-compose ps

# Rebuild po zmianach
docker-compose up -d --build api

# Pełny restart
docker-compose down && docker-compose up -d
```

### Frontend Commands (npm)

```bash
# Build frontend
cd frontend && npm run build

# Dev server
npm run dev

# Preview production build
npm run build && npm run preview

# Lint
npm run lint

# Type check
npm run type-check

# Format
npm run format
```

### Git Commands (Cleanup Workflow)

```bash
# Create cleanup branch
git checkout -b cleanup/prompt-XX-description

# Stage changes
git add .

# Commit with cleanup prefix
git commit -m "cleanup: [Prompt XX] Opis zmiany"

# Push branch
git push origin cleanup/prompt-XX-description

# Create PR
gh pr create --title "Cleanup: Prompt XX - Opis" --label cleanup

# Merge to main after review
gh pr merge --squash
```

### Line Count Commands

```bash
# Policz linie w pliku
wc -l path/to/file.py

# Policz linie w wielu plikach
wc -l app/services/personas/*.py

# Policz wszystkie linie Pythona w folderze
find app/services/personas/ -name "*.py" -exec wc -l {} + | tail -1

# Policz linie TypeScript
find frontend/src/components/ -name "*.tsx" -exec wc -l {} + | tail -1

# Znajdź pliki >500 linii
find app/ -name "*.py" -exec wc -l {} + | awk '$1 > 500'
```

### Config Validation

```bash
# Waliduj wszystkie config files
python scripts/config_validate.py

# Sprawdź konkretny config
python -c "from config import models; print(models.get('personas', 'generation'))"

# Sprawdź prompty
python -c "from config import prompts; print(prompts.list_prompts())"
```

### Database Commands

```bash
# Migracje
docker-compose exec api alembic upgrade head
docker-compose exec api alembic revision --autogenerate -m "opis"
docker-compose exec api alembic downgrade -1

# Połącz do PostgreSQL
docker-compose exec postgres psql -U sight -d sight_db

# Połącz do Neo4j (browser)
open http://localhost:7474

# Redis CLI
docker-compose exec redis redis-cli
```

### Cleanup Scripts

```bash
# Cache cleanup
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete
find . -name ".DS_Store" -delete
find . -name "*.egg-info" -type d -delete

# Unused imports (Python)
# Zainstaluj: pip install autoflake
autoflake --remove-all-unused-imports -r app/

# Unused code (Python)
# Zainstaluj: pip install vulture
vulture app/ tests/
```

---

## 🎉 Koniec Cleanup Promptów

**Total:** 75 promptów cleanup
**Estimated Time:** 4-6 tygodni (w zależności od priorytetów)
**Impact:** Redukcja długu technicznego, lepsza maintainability, szybszy development

**Next Steps:**
1. Review całego pliku prompty.md
2. Rozpocznij od 🔴 P0 (prompty 1-15)
3. Commit po każdym prompcie
4. Merge do main po zakończeniu każdego priorytetu
5. Celebrate! 🚀

---

**Wygenerowano:** 2025-11-11
**Wersja:** 1.1
**Utrzymanie:** Aktualizuj checklist i dodawaj nowe prompty według potrzeb

---

## 📝 Historia Zmian

### 2025-11-11 (Wersja 1.1) - Audyt i Korekta Zadań
**Autor:** Claude Code
**Typ:** Audyt poprzednich refaktoryzacji + korekta nieistniejących zadań

**Zmiany:**
1. ✅ **Dodano sekcję P2.5: Audyt Poprzednich Refaktoryzacji (zadania 76-85)**
   - 76: Backend - Audyt nieużywanych importów po zadaniach 1-35
   - 77: Frontend - Usunięcie martwego kodu (GraphAnalysis.tsx, etc.)
   - 78: Backend - Sprawdzenie TODO/FIXME z zadań 1-35
   - 79: Frontend - Audyt komponentów UI shadcn (56 plików)
   - 80: Backend - Sprawdzenie BackgroundTasks usage
   - 81: Full repo - Znajdź duplikaty kodu (copy-paste detection)
   - 82: Frontend - Sprawdź nieużywane hooki i utility functions
   - 83: Backend - Sprawdź deprecated metody w serwisach
   - 84: Tests - Usuń martwe fixtures i test utilities
   - 85: Global - Sprawdź nieużywane dependencies

2. ❌ **Skorygowano nieistniejące zadania:**
   - Zadanie 38: GraphAnalysis.tsx → USUŃ (martwy kod, 0 użyć)
   - Zadanie 45: ProjectSettings.tsx → Settings.tsx (601 linii)
   - Zadanie 46: ReasoningPanel.tsx → PersonaReasoningPanel.tsx (w personas/)
   - Zadanie 47: WorkflowTemplates.tsx → WorkflowsListPage.tsx
   - Zadanie 48: WorkflowRun.tsx → ExecutionHistory.tsx + ExecutionHistoryItem.tsx

3. 🔍 **Wykryto martwy kod:**
   - `frontend/src/components/layout/GraphAnalysis.tsx` (788 linii, 0 użyć) → do usunięcia
   - Potencjalnie nieużywane: FigmaDashboard.tsx, StatsOverlay.tsx, FloatingControls.tsx

4. 📊 **Nowe statystyki:**
   - **Total zadań:** 85 (75 oryginalnych + 10 audytowych)
   - **Estimated Time:** 5-7 tygodni (z audytem)
   - **Zakończone:** 38/85 (45%)
   - **Do zrobienia:** 47/85 (55%)

**Uzasadnienie:**
Po zakończeniu zadań 1-35 (backend refaktoryzacja), przeprowadzono audyt skuteczności zmian. Odkryto:
- Martwy kod (GraphAnalysis.tsx nie jest używany nigdzie)
- Nieaktualne zadania (4 komponenty z innymi nazwami lub nieistniejące)
- Brak systematycznego audytu po refaktoryzacjach

Sekcja P2.5 wprowadza systematyczny audyt: nieużywane importy, martwy kod, TODO markers, duplikaty kodu, deprecated metody, nieużywane dependencies.

**Następne kroki:**
1. Rozpocząć od zadania 36-37 (Personas.tsx, FocusGroupView.tsx split)
2. Wykonać zadanie 77 (usunięcie martwego kodu frontend) przed dalszymi refaktoryzacjami
3. Po zakończeniu P2 (zadania 36-70) → wykonać pełny audyt P2.5 (zadania 76-85)

---

### 2025-11-11 (Wersja 1.0) - Wersja Początkowa
**Autor:** Oryginalny autor
**Typ:** Utworzenie dokumentu z 75 zadaniami cleanup

75 zadań cleanup zorganizowanych w priorytety P0-P3:
- 🔴 P0: Backend Core Services (1-15) - ✅ ZAKOŃCZONE
- 🟡 P1: Backend API + Schemas + Services Folders (16-35) - ✅ ZAKOŃCZONE
- 🟢 P2: Frontend Components + Lib/Hooks/Types + Tests + Config (36-70) - ⏳ W TRAKCIE
- 🔵 P3: Documentation (71-75) - ⏳ OCZEKUJE
