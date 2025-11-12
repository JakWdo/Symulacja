# 🧹 SIGHT PLATFORM - CLEANUP PROMPTS

**Projekt:** Sight AI-powered Focus Groups Platform
**Ścieżka:** `.` (ścieżki repo‑relatywne)
**Data utworzenia:** 2025-11-11
**Scope:** 115 zadań cleanup dla redukcji długu technicznego
**Cel:** Modularyzacja kodu (max 700 linii/plik), usunięcie TODO/hardcoded values, optymalizacja struktury

---

## 📋 Spis Treści

1. [Instrukcja Użytkowania](#instrukcja-użytkowania)
2. [Global Checklist](#global-checklist)
3. [Prompty Cleanup](#prompty-cleanup)
4. [Appendix: Komendy i Narzędzia](#appendix-komendy-i-narzędzia)

---

## 📖 Instrukcja Użytkowania

### Kolejność Wykonywania

**KRYTYCZNE:** Wykonuj prompty SEKWENCYJNIE według numeracji 1→115. Nie pomijaj kroków!

**Priorytety:**
- 🔴 **P0 (1-15, 89-93):** Krytyczne - backend core services + security (1-2 dni)
- 🟡 **P1 (16-35, 86-88, 94-99):** Wysokie - backend API/folders + features (3-5 dni)
- 🟢 **P2 (36-70, 71-85, 100-109):** Średnie - frontend + tests + audyty + performance (1-2 tygodnie)
- 🔵 **P3 (110-115):** Niskie - dokumentacja (1 miesiąc)

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
- [x] 36. Personas.tsx split ✅ (653→488 linii + PersonasHeader, PersonasProgressBar, PersonasStats)
- [x] 37. FocusGroupView.tsx split ✅ (972→637 linii + FocusGroupHeader, FocusGroupSetupTab, FocusGroupDiscussionTab)
- [x] 38. ❌ GraphAnalysis.tsx - NIE ISTNIEJE (już usunięty lub nigdy nie był) ✅
- [x] 39. FocusGroupPanel.tsx split ✅ (783→136 linii + StatusBadge, FocusGroupCard, FocusGroupForm)
- [x] 40. WorkflowEditor.tsx split ✅ (WorkflowToolbar.tsx, WorkflowCanvas.tsx)
- [x] 41. PersonaPanel.tsx split ✅ (PersonaList.tsx, PersonaDetailsView.tsx)
- [x] 42. AISummaryPanel.tsx split ✅ (AISummaryInsights.tsx, AISummarySections.tsx)
- [x] 43. Surveys.tsx cleanup ✅ (506→222 linii + 4 komponenty: SurveysSkeleton, SurveysStats, SurveyCard, SurveysList)
- [x] 44. Dashboard.tsx cleanup ✅ (nie wymaga refaktoryzacji: MainDashboard 130 linii, OverviewDashboard 444 linii - oba <500)
- [x] 45. Settings.tsx cleanup ✅ (601→95 linii + 4 komponenty: ProfileSettings, BudgetSettings, AppearanceSettings, AccountSidebar)
- [x] 46. ❌ ReasoningPanel.tsx → PersonaReasoningPanel.tsx (430 linii) - cleanup ✅
- [x] 47. ❌ WorkflowTemplates.tsx → WorkflowsListPage.tsx (364 linii) - cleanup ✅
- [x] 48. ❌ WorkflowRun.tsx → ExecutionHistory.tsx (98) + ExecutionHistoryItem.tsx (367) - cleanup ✅
- [x] 49. Hardcoded labels → constants ✅ (constants/personas.ts utworzony)
- [x] 50. Unused UI components audit ✅ (18 komponentów usunięto: 1825 linii)

### 🟢 P2: Frontend Lib/Hooks/Types
- [x] 51. lib/api.ts split ✅ (846→1003 linii w 10 modułach: client, index, auth, dashboard, focus-groups, personas, projects, rag, surveys, workflows)
- [x] 52. types/index.ts split ✅ (887→1069 linii w 7 modułach: persona 233, project 70, focus-group 390, survey 70, rag 116, graph 137, index 53)
- [x] 53. hooks/useWorkflows.ts split ✅ (639→736 linii w 4 hooki: useWorkflowCrud 307, useWorkflowExecution 188, useWorkflowTemplates 111, useWorkflowValidation 130)
- [x] 54. hooks/usePersonas.ts cleanup ✅ (już podzielony wcześniej: hooks/personas/, usePersonaDetails, useDeletePersona, useUndoDeletePersona)
- [x] 55. hooks/useFocusGroups.ts cleanup ✅ (już podzielony wcześniej: hooks/focus-group/ z 5 modułami)
- [x] 56. lib/utils.ts cleanup ✅ (20 linii - nie wymaga podziału)
- [x] 57. stores/zustand cleanup ✅ (folder stores/ pusty - brak plików Zustand)
- [x] 58. constants/ consolidation ✅ (constants/personas.ts 100 linii - główne stałe przeniesione w zadaniu 49)

### 🟢 P2: Tests
- [x] 59. test_workflow_validator.py split ✅ (1310→475+538+340 linii: basic, nodes, edges)
- [x] 60. test_workflow_service.py split ✅ (873→526+367 linii: crud, logic)
- [x] 61. test_workflow_executor.py split ✅ (825→464+379 linii: basic, advanced)
- [x] 62. test_rag_hybrid_search.py cleanup ✅ (553→552 linii, usunięto 2 nieużywane importy)
- [x] 63. test_persona_orchestration.py cleanup ✅ (545→544 linie, usunięto 2 nieużywane importy)
- [x] 64. fixtures consolidation ✅ (usunięto 5 nieużywanych fixtures: mock_datetime, sample_persona_dict, sample_project_dict, temp_file, reset_singletons + 3 nieużywane importy)
- [x] 65. Deprecated test utilities cleanup ✅ (naprawiono 61 błędów: 49 nieużywanych importów + 12 zmiennych, usunięto deprecated test_get_settings_singleton)
- [ ] 66. Test coverage gaps (target 85%+) ⚠️ POMINIĘTO (wymaga Docker)

### 🟢 P2: Config & Scripts
- [ ] 67. config/loader.py split ⚠️ POMINIĘTO (specyfikacja nieaktualna - brak 350 linii validation logic w pliku)
- [x] 68. scripts/cleanup_legacy_mentions.py archive ✅ (przeniesiono do archive/, zaktualizowano README, naprawiono 22 błędy ruff)
- [x] 69. scripts/create_demo_data consolidation ✅ (archiwizowano 2 scripts: create_demo_data_local_2024.py, reorganize_demo_data_2024.py)
- [x] 70. Cache cleanup ✅ (usunięto 8 plików cache, utworzono scripts/cleanup_cache.sh)

### 🟠 P2.5: Audyt Poprzednich Refaktoryzacji
- [x] 71. Backend: Audyt nieużywanych importów po zadaniach 1-35 ✅ (0 błędów - kod czysty)
- [x] 72. Frontend: Usunięcie martwego kodu (GraphAnalysis.tsx, etc.) ✅ (już usunięte w zadaniu 50)
- [x] 73. Backend: Sprawdzenie TODO/FIXME z zadań 1-35 ✅ (14 TODO udokumentowanych w docs/TODO_TRACKING.md)
- [x] 74. Frontend: Audyt komponentów UI shadcn (38→34 pliki) ✅ (usunięto 4 komponenty)
- [x] 75. Backend: Sprawdzenie BackgroundTasks usage ✅ (usunięto 1 nieużywany parameter)
- [x] 76. Full repo: Znajdź duplikaty kodu (copy-paste) ✅ (analiza w docs/CODE_DUPLICATION_ANALYSIS.md)
- [x] 77. Frontend: Sprawdź nieużywane hooki i utility functions ✅ (usunięto 4 hooks)
- [x] 78. Backend: Sprawdź czy stare serwisy mają deprecated metody ✅ (0 deprecated - czysty kod)
- [x] 79. Tests: Usuń martwe fixtures i test utilities ✅ (0 błędów - czyste fixtures)
- [x] 80. Global: Sprawdź nieużywane dependencies ✅ (analiza w docs/DEPENDENCIES_AUDIT.md)

### 🟠 P2.6: Audyt Post-Split
- [x] 81. Frontend: Audyt WorkflowEditor, PersonaPanel, AISummaryPanel po splitach
- [x] 82. Frontend: Audyt Personas, FocusGroupView, Surveys, Settings po splitach
- [x] 83. Backend: Audyt wszystkich plików po splitach 1-35
- [x] 84. Backend: Audyt nieużywanych utility functions i helper methods
- [x] 85. Dependencies: Audyt package.json + requirements.txt

### 🟡 P2.7: Backend Re-Split
- [x] 86. hybrid_search_service.py ponowny split ✅ (podzielono na search/, graph/, caching/)
- [x] 87. segment_brief_service.py ponowny split ✅ (orchestration/: brief_cache, brief_formatter, segment_brief_service)
- [x] 88. dashboard_core.py split ✅ (187 linii - poniżej limitu 300)

### 🔴 P0: Security & Critical
- [x] 89. RBAC Implementation ✅ (role ENUM w user.py, middleware zaimplementowane)
- [x] 90. Security Audit ✅ (OWASP Top 10 + manual review wykonany)
- [x] 91. Staging Environment Setup ✅ (deploy-staging.yml, .env.staging.example, docs/INFRASTRUKTURA.md aktualizacja)
- [x] 92. Secrets Scanning w CI/CD ✅ (secrets-scan.yml, .trufflehog.yaml, TruffleHog + GitGuardian, daily schedule)
- [x] 93. Automated Rollback ✅ (/health endpoint, InfrastructureHealthService, configure_cloud_run_health_check.sh, docs)

### 🟡 P1: Features & Infrastructure
- [x] 94. Export PDF/DOCX - PDF reports personas/focus groups/surveys (WeasyPrint, python-docx, charts, watermarks free tier, <5s) ✅
- [x] 97. Enhanced Monitoring - Cloud Monitoring dashboards, PagerDuty, alerts (error >5%, downtime, costs, MTTR <20min) ✅
- [x] 98. E2E Tests Expansion - 12→30+ testów (Playwright, critical paths 90%+: personas, focus groups, workflows) ✅
- [x] 99. Multi-LLM Support - abstraction multi-provider (Gemini, OpenAI, Anthropic, fallback, cost routing) ✅

### 🟢 P2: Performance & Tech Debt
- [x] 100. Bundle Size Reduction - 2.5MB→1.5MB (lazy loading, code splitting, tree shaking, Lighthouse >80) ✅
- [x] 101. Lazy Loading Routes - React.lazy wszystkie route components (initial <1MB, route <200ms) ✅
- [x] 102. N+1 Query Problem - selectinload/joinedload (API latency <300ms p90, 0 N+1 critical) ✅
- [x] 103. Neo4j Connection Leaks - context managers `async with` (memory stable, monitoring) ✅
- [ ] 104. Missing Database Indexes - pg_stat_statements analysis (queries <100ms p95, indexed)

### 🟢 P2.8: Repository Cleanup
- [ ] 105. Cleanup cache - .pytest_cache, .ruff_cache, __pycache__, .pyc (dodaj .gitignore)
- [ ] 106. Cleanup .DS_Store - usuń wszystkie .DS_Store (dodaj .gitignore)
- [ ] 107. Archive obsolete .md - przenieś do archive/: STUDY_DESIGNER_*.md, IMPLEMENTATION_PROGRESS.md, DARK_MODE_AUDIT_*.md
- [ ] 108. Cleanup root - przenieś DEMO_DATA_INFO.md do docs/, oceń docker-compose.prod.yml
- [ ] 109. Docker volumes cleanup - sprawdź volumes, cleanup local Neo4j/PostgreSQL data

### 🔵 P3: Documentation
- [ ] 110. docs/BACKEND.md - aktualizacja refaktoryzacji 1-35 (service layer split, nowa struktura)
- [ ] 111. docs/AI_ML.md - aktualizacja RAG (3,6), persona generation (1,4,8-10)
- [ ] 112. docs/ROADMAP.md - dodaj "Completed 2024" (1-70), zaktualizuj Q1 2025 (71-115)
- [ ] 113. docs/CLAUDE.md - aktualizuj Referencję Kluczowych Plików, przykłady importów
- [ ] 114. docs/README.md - zaktualizuj linki, opisy, dodaj nowe sekcje
- [ ] 115. Kompleksowa aktualizacja dokumentacji - audyt wszystkich docs/ (architektura, wzorce, linki, przykłady)

---

## 🧹 Prompty Cleanup

### 🔴 P0: Backend Core Services

#### 1. 🔴 persona_generator_langchain.py (1074 linii)

Rozbij `app/services/personas/persona_generator_langchain.py` na: `persona_generator_core.py` (~350 linii główna logika), `persona_prompts_builder.py` (~400 linii budowanie promptów), `persona_validators.py` (~300 linii walidacja). Zaktualizuj importy w `app/api/personas/generation.py`, usuń TODO dot. batch generation.

#### 2. 🔴 discussion_summarizer.py (1143 linii)

Rozbij `app/services/focus_groups/discussion_summarizer.py` na: `summarizer_core.py`, `insights_extractor.py`, `themes_analyzer.py`, `summary_formatter.py`. Popraw importy w `app/api/focus_groups.py`.

#### 3. 🔴 rag_hybrid_search_service.py (1074 linii)

Rozbij `app/services/rag/rag_hybrid_search_service.py` na: `hybrid_search_orchestrator.py`, `vector_search.py`, `keyword_search.py`, `rrf_fusion.py`. Popraw importy w `app/api/rag.py`.

#### 4. 🔴 persona_orchestration.py (987 linii)

Rozbij `app/services/personas/persona_orchestration.py` na: `orchestration_core.py`, `segment_creator.py`, `orchestration_cache.py`. Popraw importy w `app/api/personas/generation.py`.

#### 5. 🔴 dashboard_orchestrator.py (1028 linii)

Rozbij `app/services/dashboard/dashboard_orchestrator.py` na: `dashboard_core.py`, `metrics_aggregator.py`, `cost_calculator.py`, `usage_trends.py`. Popraw importy w `app/api/dashboard.py`.

#### 6. 🔴 rag_graph_service.py (665 linii)

Rozbij `app/services/rag/rag_graph_service.py` na: `graph_query_builder.py`, `graph_traversal.py`, `graph_insights_extractor.py`. Popraw importy w `app/api/rag.py` i serwisach personas.

#### 7-15. 🔴 Pozostałe Backend Core Services

**7.** segment_brief_service.py: wyodrębnij `segment_brief_generator.py`, `brief_formatter.py`, ustaw TTL z config.
**8.** persona_details_service.py: wyodrębnij `details_crud.py`, `details_enrichment.py`, zastąp hardcoded polskie nazwy z config.
**9.** distribution_builder.py: wyodrębnij `distribution_calculator.py`, `statistical_validator.py`, usuń TODO weighted sampling.
**10.** demographics_formatter.py: wyodrębnij `demographics_validator.py`, zastąp hardcoded stopwords z config.
**11.** survey_response_generator.py: wyodrębnij `response_generator_core.py`, `response_formatter.py`, usuń `legacy_survey_format()`.
**12.** workflow_template_service.py: wyodrębnij `template_crud.py`, `template_validator.py`.
**13-15.** Przejrzyj `persona_needs_analyzer.py`, `memory_manager.py`, `usage_logging.py`. Jeśli >500 linii, wydziel moduły. Zamień `print` na `logger.info`.

---

### 🟡 P1: Backend API + Schemas

#### 16. 🟡 api/personas/generation.py (1360 linii)

Podziel na: `generation_endpoints.py`, `orchestration_endpoints.py`, `validation_endpoints.py`. Zaktualizuj rejestrację routerów w `app/api/personas/__init__.py` i `app/main.py`, usuń TODO batch generation.

#### 17. 🟡 api/workflows.py (879 linii)

Podziel na: `workflow_crud.py`, `workflow_execution.py`, `workflow_templates.py`. Zaktualizuj rejestrację routerów w `app/main.py`.

#### 18. 🟡 api/projects.py (693 linii)

Podziel na: `project_crud.py`, `project_demographics.py`. Zaktualizuj rejestrację routerów.

#### 19. 🟡 schemas/workflow.py (994 linii)

Podziel na: `workflow_base.py` (480), `workflow_nodes.py` (589), wrapper (120). Zaktualizuj importy w API, services, tests.

#### 20-28. 🟡 Pozostałe API i Schemas

Przejrzyj: `schemas/persona.py`, `schemas/focus_group.py`, `api/focus_groups.py`, `api/surveys.py`, `api/rag.py`, `api/dashboard.py`, `api/study_designer.py`, `schemas/project.py`, `schemas/dashboard.py`. Jeśli >500 linii, wydziel moduły. Usuń TODO i nieużywane importy.

---

### 🟡 P1: Backend Services Folders

#### 29-35. 🟡 Services Folder Restructure

**29.** `app/services/personas/`: utwórz `generation/`, `orchestration/`, `details/`, `validation/`. Uzupełnij `__init__.py`, zaktualizuj importy.
**30.** `app/services/dashboard/`: utwórz `metrics/`, `usage/`, `costs/`. Uzupełnij `__init__.py`.
**31.** `app/services/workflows/`: utwórz `execution/`, `templates/`, `validation/`. Przenieś docs do `docs/workflows/`.
**32.** `app/services/rag/`: utwórz `search/`, `documents/`, `embeddings/`. Zaktualizuj importy.
**33.** `app/services/focus_groups/`: utwórz `discussion/`, `summaries/`, `memory/`.
**34.** `app/services/surveys/`: sprawdź czy potrzeba `generation/`, `responses/`.
**35.** `app/services/shared/`: usuń nieużywane moduły, konsoliduj `clients.py` z `rag_provider.py`.

---

### 🟢 P2: Frontend Components

#### 36. 🟢 Personas.tsx (653→488 linii)

Podziel na: `PersonasLayout.tsx`, `PersonasList.tsx`, `PersonaFilters.tsx`, `PersonaActions.tsx`. Przenieś hardcoded labels do `constants/personas.ts`.

#### 37. 🟢 FocusGroupView.tsx (972→637 linii)

Podziel na: `FocusGroupLayout.tsx`, `DiscussionThread.tsx`, `ResponseComposer.tsx`. Zaktualizuj routing.

#### 38. ❌ GraphAnalysis.tsx - NIE ISTNIEJE

GraphAnalysis.tsx (788 linii) NIE JEST UŻYWANY - martwy kod! Sprawdź inne pliki w `layout/`: FigmaDashboard.tsx, StatsOverlay.tsx, FloatingControls.tsx. **USUŃ** zamiast dzielić.

#### 39-48. 🟢 Pozostałe Komponenty Frontend

Podziel komponenty >500 linii: `FocusGroupPanel.tsx`, `WorkflowEditor.tsx`, `PersonaPanel.tsx`, `AISummaryPanel.tsx`, `Surveys.tsx`, `Dashboard.tsx`, `Settings.tsx`, `PersonaReasoningPanel.tsx`, `WorkflowsListPage.tsx`, `ExecutionHistory.tsx`. Usuń hardcoded labels, przenieś do constants.

#### 49-50. 🟢 Constants i UI Cleanup

Utwórz `constants/personas.ts` z labels. Usuń nieużywane shadcn: `aspect-ratio.tsx`, `input-otp.tsx`, `breadcrumb.tsx`, `resizable.tsx`, `sonner.tsx`, `toggle-group.tsx`, `pagination.tsx`, `navigation-menu.tsx`. Zachowaj podstawowe (button, input, card, dialog, etc.).

---

### 🟢 P2: Frontend Lib/Hooks/Types

#### 51. 🟢 lib/api.ts (846 linii)

Podziel na: `api/personas.ts` (~250), `api/projects.ts` (~200), `api/workflows.ts` (~200), `api/focus-groups.ts` (~200). Utwórz `api/index.ts` z re-exports.

#### 52. 🟢 types/index.ts (887 linii)

Podziel na domain types: `types/persona.ts`, `types/project.ts`, `types/workflow.ts`, `types/focus-group.ts`, `types/survey.ts`, `types/dashboard.ts`. Utwórz `types/index.ts` z re-exports.

#### 53. 🟢 hooks/useWorkflows.ts (639 linii)

Podziel na 4 hooks: `useWorkflowCrud.ts` (~200), `useWorkflowExecution.ts` (~200), `useWorkflowTemplates.ts` (~150), `useWorkflowValidation.ts` (~150).

#### 54-58. 🟢 Pozostałe Hooks i Stores

Przejrzyj `hooks/usePersonas.ts`, `hooks/useFocusGroups.ts`, `lib/utils.ts`, `stores/zustand`. Jeśli >500 linii, wydziel moduły. Konsoliduj constants w `constants/{personas,workflows,ui}.ts`.

---

### 🟢 P2: Tests

#### 59. 🟢 test_workflow_validator.py (1310 linii)

Podziel na: `test_validator_basic.py` (~500), `test_validator_nodes.py` (~450), `test_validator_edges.py` (~400).

#### 60-61. 🟢 Workflow Tests

Podziel `test_workflow_service.py` (873) na `test_workflow_crud.py` (~450), `test_workflow_logic.py` (~450). Podziel `test_workflow_executor.py` (825) na `test_executor_basic.py` (~450), `test_executor_advanced.py` (~400).

#### 62-66. 🟢 Pozostałe Testy

Przejrzyj `test_rag_hybrid_search.py`, `test_persona_orchestration.py`. Konsoliduj fixtures w `tests/fixtures/shared.py`, usuń duplikaty. Usuń deprecated test utilities. Sprawdź coverage gaps - target 85%+.

---

### 🟢 P2: Config & Scripts

#### 67. 🟢 config/loader.py (681 linii)

Wyodrębnij `config/validators.py` (YAML validation ~350) z `config/loader.py`. Zaktualizuj importy w `config/__init__.py`, `config/models.py`, `config/prompts.py`.

#### 68-70. 🟢 Scripts i Cache

Archiwizuj `scripts/cleanup_legacy_mentions.py` → `scripts/archive/`. Konsoliduj `scripts/create_demo_data*.py` - zachowaj najnowszą, przenieś stare do archive. Cleanup cache: usuń `*.pyc`, `__pycache__`, `.DS_Store`. Utwórz `scripts/cleanup_cache.sh`.

---

### 🟠 P2.5: Audyt Poprzednich Refaktoryzacji

#### 71. 🟠 Backend: Nieużywane importy

Audyt modułów backend po 1-35. `ruff check app/services --select F401,F841 --fix`. Sprawdź `app/api`, `tests/` czy nie ma importów do starych modułów. Zaktualizuj `__init__.py`.

#### 72. 🟠 Frontend: Martwy kod

Usuń nieużywane komponenty: `GraphAnalysis.tsx` (788, 0 użyć). Sprawdź routing, `FigmaDashboard.tsx`, `StatsOverlay.tsx`, `FloatingControls.tsx`.

#### 73. 🟠 Backend: TODO/FIXME

Przejrzyj TODO/FIXME po 1-35. Kategoryzuj: Fix now, Create issue, Delete. Znalezione: `workflow_executor.py:180`, `personas.py:100,107,175`, `workflow_validator.py:422`.

#### 74. 🟠 Frontend: Komponenty UI shadcn

Przejrzyj `components/ui/` (56 komponentów). Usuń nieużywane: `aspect-ratio.tsx`, `input-otp.tsx`, `breadcrumb.tsx`, `resizable.tsx`, `sonner.tsx`, `toggle-group.tsx`, `pagination.tsx`, `navigation-menu.tsx`. Zachowaj podstawowe.

#### 75. 🟠 Backend: BackgroundTasks

Przejrzyj użycie `BackgroundTasks`. Znalezione: `api/rag.py`, `api/personas/generation_endpoints.py`. Sprawdź czy mogą być sync async/await (<2s) lub wymagają Celery (>5s).

#### 76. 🟠 Full Repo: Duplikaty kodu

Znajdź duplikaty (funkcje >10 linii 2+ razy). Wydziel do: Backend `app/services/shared/utils.py`, Frontend `frontend/src/lib/utils.ts`.

#### 77. 🟠 Frontend: Nieużywane hooki

Przejrzyj `hooks/`, `lib/`. Usuń hooki z 0 użyciami. Sprawdź utility functions (`formatters.ts`, `validators.ts`).

#### 78. 🟠 Backend: Deprecated metody

Przejrzyj serwisy. Usuń `@deprecated`, `legacy_*`, `old_*`. Sprawdź metody nie używane nigdzie.

#### 79. 🟠 Tests: Martwe fixtures

Przejrzyj `tests/fixtures/`, `tests/conftest.py`. Usuń fixtures z 0-1 użyciami (poza dependencies). Sprawdź `tests/utils/` deprecated helpers.

#### 80. 🟠 Global: Nieużywane dependencies

Backend: `pipreqs . --force --savepath /tmp/actual_requirements.txt && diff requirements.txt /tmp/actual_requirements.txt`. Frontend: `npx depcheck frontend/`.

---

### 🟠 P2.6: Audyt Post-Split

#### 81-85. 🟠 Audyt po splitach

**81-82.** Frontend audyt: WorkflowEditor, PersonaPanel, AISummaryPanel, Personas, FocusGroupView, Surveys, Settings - usuń nieużywane funkcje/importy/komponenty.
**83-84.** Backend audyt: pliki po 1-35 - usuń nieużywane funkcje/importy/klasy/helper functions.
**85.** Dependencies audyt: package.json + requirements.txt - usuń nieużywane pakiety.

---

### 🟡 P2.7: Backend Re-Split

#### 86. 🟡 hybrid_search_service.py (1074 linii)

Zadanie 3 failed. Split → 4: `hybrid_search/search_orchestrator.py` (~300), `vector_search.py` (~350), `keyword_search.py` (~250), `rrf_fusion.py` (~150). Każdy <400.

#### 87. 🟡 segment_brief_service.py (820 linii)

Task 7 failed. Split → 3: `segment_brief/brief_generator.py` (~350), `brief_cache.py` (~250), `brief_formatter.py` (~200). Każdy <350.

#### 88. 🟡 dashboard_core.py (674 linii)

Split → 3: `dashboard/dashboard_metrics.py` (~280), `dashboard_usage.py` (~220), `dashboard_costs.py` (~170). Każdy <300.

---

### 🔴 P0: Security & Critical

#### 89. 🔴 RBAC Implementation

RBAC (Admin/Researcher/Viewer). **Migration**: `alembic revision -m "add_user_role"` → `users.role ENUM`. **Middleware**: `app/middleware/rbac.py` → `@requires_role('admin')`. **API**: Protect endpoints. **Tests**: `pytest tests/unit/test_rbac.py --cov=app/middleware/rbac` (90%+).

#### 90. 🔴 Security Audit

**OWASP**: SQL injection, XSS, CSRF. **Bandit**: `bandit -r app/ -ll` → fix high/medium. **Safety**: `safety check`. **Manual**: JWT, secrets (`rg "api_key|password|secret" app`). **Report**: 0 high/critical vulns.

#### 91. 🔴 Staging Environment

**Cloud Run**: `sight-api-staging`. **DB**: `sight-staging-db` Cloud SQL. **CI/CD**: `.github/workflows/deploy-staging.yml` → auto-deploy `staging` branch. **Migrations**: test staging first.

#### 92. 🔴 Secrets Scanning CI/CD

**Workflow**: `.github/workflows/secrets-scan.yml` → TruffleHog, GitGuardian. **Config**: `.trufflehog.yaml`. **Alerts**: Fail build, Slack. **Historical**: `trufflehog git file://.`.

#### 93. 🔴 Automated Rollback

**Health**: `/health` endpoint (DB, Redis, Neo4j). **Policy**: 5xx>5% OR latency>2s for 2min → rollback. **Config**: `gcloud run services update --health-check=/health`. **Test**: MTTR<2min.

---

### 🟡 P1: Features & Infrastructure

#### 94. 🟡 Export PDF/DOCX

PDF/DOCX export. **Backend**: `app/services/export/pdf_generator.py` (WeasyPrint), `docx_generator.py` (python-docx). **API**: `POST /api/export/personas/{id}/pdf`. **Features**: Charts, watermarks (free tier), TOC. **Performance**: <5s download. **Frontend**: Download button.

#### 97. 🟡 Monitoring & Alerting

**Dashboards**: Cloud Monitoring (latency p50/p90/p99, errors, users, costs). **Alerts**: Error>5%, downtime>1min, cost spike>$100/day. **PagerDuty**: Integration. **Metrics**: Custom (personas/hour, tokens/min). **Reports**: Weekly email. MTTR<20min.

#### 98. 🟡 E2E Tests Expansion

**Current**: 12. **Target**: 30+. **Coverage**: Persona flow, Focus groups, Workflows, Surveys, Settings. **Framework**: Playwright `tests/e2e/`. **CI**: GitHub Actions. **Critical**: 90%+ coverage.

#### 99. 🟡 Multi-LLM Support

**Abstraction**: `app/services/shared/llm_router.py`. **Providers**: Gemini, OpenAI, Anthropic. **Fallback**: Gemini→OpenAI→Anthropic. **Cost Routing**: Prefer cheaper for simple. **Config**: `config/models.yaml` per-domain. **Tracking**: Tokens/cost per provider.

---

### 🟢 P2: Performance & Tech Debt

#### 100. 🟢 Bundle Size Reduction

**Current**: 2.5MB. **Target**: <1.5MB. **Techniques**: Lazy loading, code splitting, tree shaking, remove unused deps. **Analysis**: `npm run build --stats && npx vite-bundle-visualizer`. **Lighthouse**: >80.

#### 101. 🟢 Lazy Loading Routes

**Current**: Eager. **Target**: All lazy. **Implementation**: `const Personas = lazy(() => import('./Personas'))`, `<Suspense>`. **Routes**: Personas, FocusGroups, Workflows, Dashboard, Settings, Surveys. **Fallback**: LoadingSpinner.

#### 102. 🟢 N+1 Query Problem

**Identify**: SQL logging, `pg_stat_statements`. **Patterns**: Loops loading related. **Fix**: `selectinload(Persona.focus_groups)`, `joinedload(Project.personas)`. **Critical**: `/api/personas`, `/api/projects/{id}`. 0 N+1 in critical.

#### 103. 🟢 Neo4j Connection Leaks

**Problem**: Connections not closed. **Fix**: Always `async with neo4j_connection.session() as session:`. **Audit**: `rg "neo4j_connection\\.session\\(\\)" app`. **Monitor**: `neo4j.bolt.connections.active`. Memory stable.

#### 104. 🟢 Missing DB Indexes

**Analysis**: `SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 20`. **Slow**: `personas WHERE project_id AND deleted_at IS NULL`. **Indexes**: Composite `CREATE INDEX idx_personas_project_deleted ON personas(project_id, deleted_at)`. **Migration**: Alembic. Queries<100ms p95.

---

### 🟢 P2.8: Repository Cleanup

#### 105. 🟢 Cleanup cache

Remove: `.pytest_cache`, `.ruff_cache`, `__pycache__`, `*.pyc`. Command: `rm -rf .pytest_cache .ruff_cache && find . -name "__pycache__" -exec rm -rf {} + && find . -name "*.pyc" -delete`. Add `.gitignore`.

#### 106. 🟢 Cleanup .DS_Store

Find: `find . -name ".DS_Store"`. Remove: `find . -name ".DS_Store" -delete`. Gitignore: `.DS_Store`. Global: `echo ".DS_Store" >> ~/.gitignore_global`.

#### 107. 🟢 Archive obsolete .md

Archive: `STUDY_DESIGNER_*.md`, `IMPLEMENTATION_PROGRESS.md`, `frontend/DARK_MODE_AUDIT_*.md`. Command: `mkdir -p docs/archive && mv [files] docs/archive/`.

#### 108. 🟢 Cleanup root

Review: `ls -la | grep .md`. Move: `DEMO_DATA_INFO.md` → `docs/` or delete. Evaluate: `docker-compose.prod.yml`. Keep: `README.md`, `CLAUDE.md`, `prompty.md`, `docker-compose.yml`.

#### 109. 🟢 Docker volumes cleanup

Check: `docker volume ls`. Data: Neo4j `./data/neo4j`, PostgreSQL `./data/postgres`. Cleanup: `docker-compose down -v && rm -rf ./data/*`. Gitignore: `data/`. Fresh: `docker-compose up -d && python scripts/init_neo4j_indexes.py`.

---

### 🔵 P3: Documentation

#### 110. 🔵 docs/BACKEND.md

Zaktualizuj o zmiany 1-35. **Dodaj**: Nowa struktura `app/services/` (personas/, dashboard/, workflows/, rag/, focus_groups/). **Zaktualizuj**: Service layer patterns, import examples. **Sprawdź**: Cross-references.

#### 111. 🔵 docs/AI_ML.md

Zaktualizuj. **RAG**: Zadania 3,6 (hybrid search split, graph service split). **Persona generation**: 1,4,8-10 (generator split, orchestration, details, distribution). **Dodaj**: Nowe moduły, flow diagrams.

#### 112. 🔵 docs/ROADMAP.md

Zaktualizuj. **Add**: "Completed 2024" z 1-70 (refaktoryzacje). **Update**: Q1 2025 priorities z 71-115 (audyty, re-splits, security, features). **Check**: Priorytety vs BIZNES.md KPIs.

#### 113. 🔵 docs/CLAUDE.md

Zaktualizuj. **Section "Referencja"**: Dodaj nowe moduły z 1-35. **Update**: Import examples (nowe ścieżki). **Add**: Troubleshooting dla split modules.

#### 114. 🔵 docs/README.md

Zaktualizuj. **Review**: Wszystkie linki. **Add**: Nowe sekcje (workflows docs z 31). **Check**: Alfabetyczny porządek, opisy aktualne.

#### 115. 🔵 Kompleksowa aktualizacja dokumentacji

Audyt wszystkich docs/: BACKEND.md, AI_ML.md, FRONTEND.md, INFRASTRUKTURA.md, QA.md, BIZNES.md, ROADMAP.md, SECURITY.md, CLAUDE.md, README.md. **Zweryfikuj**: Architektura aktualna po 1-115, wzorce kodowania udokumentowane, przykłady działają, linki poprawne, brak missing docs. **Dodaj**: Brakujące sekcje. **Usuń**: Zdezaktualizowane info, martwe linki. **Zaktualizuj**: Strukturę folderów, ścieżki importów, nazwy plików.

---

## 📚 Appendix: Komendy i Narzędzia

### Grep Patterns

```bash
# Znajdź importy
rg -n "ClassName" app tests --glob "**/*.py"
rg -n "import.*ComponentName" frontend/src --glob "**/*.{ts,tsx}"

# Policz wystąpienia
rg -n "pattern" app --glob "**/*.py" | wc -l

# Znajdź TODO
rg -n "TODO" app tests --glob "**/*.py"

# Znajdź hardcoded
rg -n "const.*=.*\[" frontend/src/components/layout/Personas.tsx

# Znajdź print
rg -n "print\(" app --glob "**/*.py"
```

### Pytest Commands

```bash
pytest -v                                    # Wszystkie
pytest tests/unit -v                        # Unit
pytest tests/unit/test_persona_generator.py -v  # Specific
pytest --cov=app --cov-report=html          # Coverage
pytest -v -m "not slow"                     # Szybkie
pytest tests/unit/test_file.py::test_function_name -v  # Konkretny
pytest -v -s                                # Z logami
pytest --collect-only                       # Collect only
```

### Docker Compose

```bash
docker-compose restart api                  # Restart
docker-compose logs -f api                  # Logi
docker-compose ps                           # Status
docker-compose up -d --build api            # Rebuild
docker-compose down && docker-compose up -d # Pełny restart
```

### Frontend (npm)

```bash
cd frontend && npm run build                # Build
npm run dev                                 # Dev
npm run build && npm run preview            # Preview
npm run lint                                # Lint
npm run type-check                          # Type check
npm run format                              # Format
```

### Git Workflow

```bash
git checkout -b cleanup/prompt-XX-description
git add .
git commit -m "cleanup: [Prompt XX] Opis zmiany"
git push origin cleanup/prompt-XX-description
gh pr create --title "Cleanup: Prompt XX - Opis" --label cleanup
gh pr merge --squash
```

### Line Count

```bash
wc -l path/to/file.py                      # Policz linie
wc -l app/services/personas/*.py           # Wiele plików
find app/services/personas/ -name "*.py" -exec wc -l {} + | tail -1  # Suma
find frontend/src/components/ -name "*.tsx" -exec wc -l {} + | tail -1  # TypeScript
find app/ -name "*.py" -exec wc -l {} + | awk '$1 > 500'  # >500 linii
```

### Config Validation

```bash
python scripts/config_validate.py
python -c "from config import models; print(models.get('personas', 'generation'))"
python -c "from config import prompts; print(prompts.list_prompts())"
```

### Database

```bash
docker-compose exec api alembic upgrade head
docker-compose exec api alembic revision --autogenerate -m "opis"
docker-compose exec api alembic downgrade -1
docker-compose exec postgres psql -U sight -d sight_db
open http://localhost:7474                  # Neo4j
docker-compose exec redis redis-cli         # Redis
```

### Cleanup Scripts

```bash
# Cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete
find . -name ".DS_Store" -delete
find . -name "*.egg-info" -type d -delete

# Unused imports (Python)
autoflake --remove-all-unused-imports -r app/

# Unused code (Python)
vulture app/ tests/
```

---

## 🎉 Koniec Cleanup Promptów

**Total:** 115 zadań cleanup
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
**Wersja:** 1.4
**Utrzymanie:** Aktualizuj checklist i dodawaj nowe prompty według potrzeb

---

## 📝 Historia Zmian

### 2025-11-12 (Wersja 1.4) - Skrócenie Dokumentu
**Autor:** Claude Code
**Typ:** Redukcja długości z 1613→~1100 linii (~32% redukcja)

**Zmiany:**
1. ✅ **Usunięto powtórzenia:**
   - Sekcje "Przed:" z komendami `rg -n`, `wc -l`, `grep` (przeniesione do "Workflow Per Prompt")
   - Sekcje "Po:" z `pytest`, `npm run build`, `docker-compose restart` (przeniesione do "Workflow Per Prompt")
   - Sekcję "Breakpoints (Commit Points)" (niepotrzebna)
   - Szczegóły spisu treści (podpunkty usunięte)

2. ✅ **Skrócono prompty:**
   - "Prompt (krótki):" skrócone do 1-2 zdań
   - ZACHOWANE kluczowe szczegóły (nazwy plików, moduły, zadania)
   - Usunięto verbose instrukcje, zachowano essence

3. ✅ **Zachowano wszystkie unikalne informacje:**
   - Global Checklist kompletny
   - Specyfikacje podziału plików
   - Konkretne nazwy i ścieżki
   - Specyficzne TODO
   - Wszystkie zadania 1-115
   - Appendix z komendami
   - Historia zmian (skrócona)

4. ✅ **Zadania 93-99 - poprawki:**
   - ZACHOWANO: 93 (Rollback), 94 (PDF/DOCX), 97 (Monitoring), 98 (E2E), 99 (Multi-LLM)
   - USUNIĘTO: 95 (Stripe), 96 (Team Accounts)
   - Nagłówek "P1: Features & Infrastructure" przed 94

5. 📊 **Wynik:**
   - Długość: 1613 → ~1100 linii (~32% redukcja)
   - Wszystkie unikalne informacje zachowane
   - Dokument bardziej czytelny

---

### 2025-11-11 (Wersja 1.3) - Cleanup Repo + Poprawki Dokumentacji

Dodano P2.8: Repository Cleanup (105-109). Poprawiono dokumentację (110-115) z "split" na "aktualizacja". Total: 110→115 zadań.

---

### 2025-11-11 (Wersja 1.2) - Security, Features, Performance

Dodano P2.6 Audyt Post-Split (81-85), P2.7 Re-Split (86-88), P0 Security (89-93), P1 Features (94-99), P2 Performance (100-104). Skorygowano nieaktualne (38, 46-48). Total: 85→115.

---

### 2025-11-11 (Wersja 1.1) - Audyt i Korekta

Dodano P2.5 Audyt (71-80). Skorygowano nieistniejące (38, 45-48). Wykryto martwy kod (GraphAnalysis.tsx). Total: 115 zadań.

---

### 2025-11-11 (Wersja 1.0) - Wersja Początkowa

75 zadań cleanup: P0 Backend Core (1-15) ✅, P1 Backend API/Folders (16-35) ✅, P2 Frontend/Tests/Config (36-70) ⏳, P3 Documentation (71-75) ⏳.
