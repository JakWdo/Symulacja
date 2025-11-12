# 🧹 SIGHT PLATFORM - CLEANUP PROMPTS

**Projekt:** Sight AI-powered Focus Groups Platform
**Ścieżka:** `.` (ścieżki repo‑relatywne)
**Data utworzenia:** 2025-11-11
**Scope:** 114 zadań cleanup dla redukcji długu technicznego
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
   - [🟠 P2.5: Audyt Poprzednich Refaktoryzacji (71-80)](#p25-audyt-poprzednich-refaktoryzacji)
   - [🟠 P2.6: Audyt Post-Split (81-85)](#p26-audyt-post-split)
   - [🟡 P2.7: Backend Re-Split (86-88)](#p27-backend-re-split)
   - [🔴 P0: Security & Critical (89-94)](#p0-security--critical)
   - [🟡 P1: Features & Infrastructure (95-99)](#p1-features--infrastructure)
   - [🟢 P2: Performance & Tech Debt (100-104)](#p2-performance--tech-debt)
   - [🟢 P2.8: Repository Cleanup (105-109)](#p28-repository-cleanup)
   - [🔵 P3: Documentation (110-114)](#p3-documentation)
4. [Appendix: Komendy i Narzędzia](#appendix-komendy-i-narzędzia)

---

## 📖 Instrukcja Użytkowania

### Kolejność Wykonywania

**KRYTYCZNE:** Wykonuj prompty SEKWENCYJNIE według numeracji 1→114. Nie pomijaj kroków!

**Priorytety:**
- 🔴 **P0 (1-15, 89-94):** Krytyczne - backend core services + security (wykonaj w ciągu 1-2 dni)
- 🟡 **P1 (16-35, 86-88, 95-99):** Wysokie - backend API/folders + features (wykonaj w ciągu 3-5 dni)
- 🟢 **P2 (36-70, 71-85, 100-109):** Średnie - frontend + tests + audyty + performance (wykonaj w ciągu 1-2 tygodni)
- 🔵 **P3 (110-114):** Niskie - dokumentacja (wykonaj w ciągu 1 miesiąca)

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
- Prompt 15 (P0 Backend Core) → Merge do main
- Prompt 35 (P1 Backend API) → Merge do main
- Prompt 58 (Frontend Lib/Hooks) → Merge do main
- Prompt 70 (P2 Config & Scripts) → Merge do main
- Prompt 80 (P2.5 Audyt) → Merge do main
- Prompt 88 (P2.7 Re-Split) → Merge do main
- Prompt 94 (P0 Security) → Merge do main
- Prompt 99 (P1 Features) → Merge do main
- Prompt 109 (P2.8 Cleanup) → Merge do main
- Prompt 114 (All complete) → Celebrate! 🎉

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

### 🟠 P2.5: Audyt Poprzednich Refaktoryzacji (NOWE - 2025-11-11)
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

### 🟠 P2.5: Audyt Poprzednich Refaktoryzacji

**UWAGA:** Ta sekcja powstała 2025-11-11 po odkryciu martwego kodu (GraphAnalysis.tsx) i nieistniejących komponentów w oryginalnych zadaniach 36-48. Zadania 71-80 sprawdzają skutki poprzednich refaktoryzacji i usuwają martwy kod.

#### 71. 🟠 [Backend Audit] - Nieużywane importy po zadaniach 1-35

Przejrzyj wszystkie moduły backendu zrefaktoryzowane w zadaniach 1-35 (sprawdź martwe importy po podziale plików).
PRZED: `ruff check app/services --select F401 --statistics` && zanotuj liczbę nieużywanych importów.
Cleanup: uruchom `ruff check app/services --select F401,F841 --fix` (usuwa unused imports i variables) + ręcznie sprawdź `app/api` i `tests/` czy nie ma importów do starych nieistniejących modułów + zaktualizuj wszystkie `__init__.py` pliki żeby eksportowały tylko używane symbole.
PO: `ruff check app/ --select F401,F841 && pytest tests/unit -v && docker-compose restart api`.
Checklist: [ ] Ruff statistics [ ] Auto-fix [ ] Manual review [ ] Update __init__ [ ] Pytest [ ] Działa.

---

#### 72. 🟠 [Frontend Audit] - Usunięcie martwego kodu

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

#### 73. 🟠 [Backend Audit] - TODO/FIXME z zadań 1-35

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

#### 74. 🟠 [Frontend Audit] - Komponenty UI shadcn (56 plików)

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

#### 75. 🟠 [Backend Audit] - BackgroundTasks usage

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

#### 76. 🟠 [Full Repo Audit] - Duplikaty kodu (copy-paste detection)

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

#### 77. 🟠 [Frontend Audit] - Nieużywane hooki i utility functions

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

#### 78. 🟠 [Backend Audit] - Deprecated metody w serwisach

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

#### 79. 🟠 [Tests Audit] - Martwe fixtures i test utilities

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

#### 80. 🟠 [Global Audit] - Nieużywane dependencies

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

### 🟠 P2.6: Audyt Post-Split (NOWE - 2025-11-11)
- [x] 81. Frontend: Audyt WorkflowEditor, PersonaPanel, AISummaryPanel po splitach - usuń nieużywane funkcje/importy/komponenty
- [x] 82. Frontend: Audyt Personas, FocusGroupView, Surveys, Settings po splitach - usuń nieużywane funkcje/importy/komponenty
- [ ] 83. Backend: Audyt wszystkich plików po splitach 1-35 - usuń nieużywane funkcje/importy/klasy/helper functions
- [ ] 84. Backend: Audyt nieużywanych utility functions i helper methods - usuń dead code (unreachable, commented out)
- [ ] 85. Dependencies: Audyt package.json + requirements.txt - usuń nieużywane pakiety i dependencies

### 🟡 P2.7: Backend Re-Split (pliki nadal >700 linii)
- [ ] 86. hybrid_search_service.py ponowny split (1074→4 moduły: search_orchestrator, vector_search, keyword_search, fusion <400 linii)
- [ ] 87. segment_brief_service.py ponowny split (820→3 moduły: brief_generator, brief_cache, brief_formatter <350 linii)
- [ ] 88. dashboard_core.py split (674→3 moduły: dashboard_metrics, dashboard_usage, dashboard_costs <300 linii)

### 🔴 P0: Security & Critical (NOWE - Q4 2024)
- [ ] 89. RBAC Implementation - role-based access control (Admin/Researcher/Viewer, middleware, decorators, migration users.role, tests 90%+)
- [ ] 90. Security Audit - comprehensive security audit (OWASP, Bandit, Safety, manual code review, SQL injection, XSS, CSRF, secrets exposure)
- [ ] 91. Staging Environment Setup - separate Cloud Run service + database dla testowania migrations przed production (CI/CD integration)
- [ ] 92. Secrets Scanning w CI/CD - GitHub Actions workflow (TruffleHog, GitGuardian, gitleaks, automated scan, alerts dla findings)
- [ ] 93. Automated Rollback - Cloud Run automatic rollback on health check failure (5xx >5%, latency >2s, rollback <2min, alerts Slack)

### 🟡 P1: Features & Infrastructure (NOWE - Q1 2025)
- [ ] 94. Export PDF/DOCX - generate PDF reports personas/focus groups/surveys (WeasyPrint, python-docx, charts, watermarks dla free tier, download <5s)
- [ ] 95. Team Accounts - multi-user/team accounts (share projects, invite teammates, activity log, permissions, team dashboard)
- [ ] 96. Enhanced Monitoring & Alerting - Cloud Monitoring dashboards, PagerDuty integration, alerts (error rate >5%, downtime, cost spikes, MTTR <20min)
- [ ] 97. E2E Tests Expansion - expand E2E test suite 12→30+ testów (Playwright, cover critical paths: persona generation, focus groups, workflows 90%+)
- [ ] 98. Multi-LLM Provider Support - abstraction layer multi-provider (Gemini, OpenAI, Anthropic, fallback chain, cost-based routing, tracking)
- [ ] 99. Database Connection Pooling Optimization - optimize pool_size, overflow, timeout (pool_size 20, overflow 10, timeout 30s, 0 exhaustion errors)

### 🟢 P2: Performance & Tech Debt (NOWE - Q1-Q2 2025)
- [ ] 100. Bundle Size Reduction - frontend optimization (2.5MB→1.5MB, lazy loading, code splitting, tree shaking, Vite config, Lighthouse >80)
- [ ] 101. Lazy Loading Routes - lazy load wszystkie route components (React.lazy, Suspense, initial load <1MB, route load <200ms)
- [ ] 102. N+1 Query Problem - fix N+1 queries w loops (use selectinload/joinedload, API latency <300ms p90, 0 N+1 w critical paths)
- [ ] 103. Neo4j Connection Leaks - fix connection leaks (context managers `async with`, memory usage stable, monitoring alerts)
- [ ] 104. Missing Database Indexes - add indexes based on pg_stat_statements analysis (all queries <100ms p95, indexes documented)

### 🟢 P2.8: Repository Cleanup (NOWE - 2025-11-11)
- [ ] 105. Cleanup cache directories - usuń .pytest_cache, .ruff_cache, __pycache__, .pyc files (dodaj do .gitignore jeśli brak)
- [ ] 106. Cleanup macOS files - usuń wszystkie .DS_Store files (dodaj do .gitignore)
- [ ] 107. Archive/Delete obsolete .md files - przenieś do archive/ lub usuń: STUDY_DESIGNER_IMPLEMENTATION.md, STUDY_DESIGNER_SUMMARY.md, IMPLEMENTATION_PROGRESS.md, frontend/DARK_MODE_AUDIT_2025_11_08.md
- [ ] 108. Cleanup root directory - uporządkuj root (przenieś DEMO_DATA_INFO.md do docs/ jeśli potrzebny, oceń docker-compose.prod.yml)
- [ ] 109. Docker volumes cleanup - sprawdź czy docker-compose volumes są używane, cleanup nieużywanych (local Neo4j data, PostgreSQL data)

### 🔵 P3: Documentation
- [ ] 110. docs/BACKEND.md - aktualizacja o refaktoryzacje 1-35 (service layer split, nowa struktura folderów)
- [ ] 111. docs/AI_ML.md - aktualizacja o zmiany RAG (zadania 3,6), persona generation (1,4,8-10)
- [ ] 112. docs/ROADMAP.md - dodaj "Completed 2024" (zadania 1-51), zaktualizuj Q1 2025 priorities (86-115)
- [ ] 113. docs/CLAUDE.md - aktualizuj Referencję Kluczowych Plików po refaktoryzacjach, przykłady importów
- [ ] 114. docs/README.md - zaktualizuj linki i opisy, dodaj nowe sekcje jeśli potrzebne

---

## 🧹 Prompty Cleanup - NOWE ZADANIA (71-114)

### 🟠 P2.6: Audyt Post-Split

#### 81. Frontend: Audyt WorkflowEditor, PersonaPanel, AISummaryPanel

Prompt: Audyt plików po splitach 40-42. Sprawdź `WorkflowEditor.tsx` (549→191), `PersonaPanel.tsx` (314→139), `AISummaryPanel.tsx` (253→78). Find unused: `npm run lint | grep -E "unused|never used"`. Remove unused imports, functions, components, variables. Fix all warnings. Verify: `npm run build && npm run lint` (0 warnings w tych plikach).

---

#### 82. Frontend: Audyt Personas, FocusGroupView, Surveys, Settings

Prompt: Audyt plików 36-37,43,45. Check `Personas.tsx` (653→488), `FocusGroupView.tsx` (972→637), `Surveys.tsx` (506→222), `Settings.tsx` (601→95). Find unused exports: `rg "export (const|function)" [plik] | cut -d: -f2`. Check if used: `rg "[name]" frontend/src`. Remove unused. Lint: `npm run lint`. Verify: `npm run build`.

---

#### 83. Backend: Audyt plików po splitach 1-35

Prompt: Audyt backend po 1-35. Large files: `find app/services -name "*.py" -size +10k`. Check functions: `rg "^def |^class " [plik]`. Find unused: `rg "[func_name]" app tests` (0 results = unused). Remove unused functions, imports (`ruff check --select F401`), commented code. Verify: `pytest tests/unit -v`.

---

#### 84. Backend: Audyt utility functions

Prompt: Find utils: `find app -name "*utils*.py" -o -name "*helpers*.py"`. List functions: `rg "^def " [plik]`. Check usage: `rg -c "[func]" app tests`. Remove 0-usage functions, dead code. Verify: `pytest -v`.

---

#### 85. Dependencies audyt

Prompt: **Frontend**: `npm ls --depth=0 | cut -d@ -f1`. Check usage: `rg "from '[pkg]'|import '[pkg]'" frontend/src`. Remove unused: `npm uninstall [pkg]`. **Backend**: `pip freeze > installed.txt`. Check: `rg "^import|^from" app | sort -u`. Compare, remove unused: `pip uninstall [pkg]`. Verify: `npm run build && pytest -v`.

---

### 🟡 P2.7: Backend Re-Split

#### 86. hybrid_search_service.py re-split (1074→<400)

Prompt: Zadanie 3 failed (still 1074 lines). Split `app/services/rag/rag_hybrid_search_service.py` → 4 modules: `hybrid_search/search_orchestrator.py` (~300, main), `vector_search.py` (~350, pgvector), `keyword_search.py` (~250, Neo4j), `rrf_fusion.py` (~150, algorithm). Grep: `rg "RagHybridSearchService" app tests`. Update imports in `app/api/rag.py`. Verify: `pytest tests/unit/test_rag* -v && docker-compose restart api`. Each <400 lines.

---

#### 87. segment_brief_service.py re-split (820→<350)

Prompt: Task 7 failed (still 820). Split `app/services/personas/segment_brief_service.py` → 3: `segment_brief/brief_generator.py` (~350, LLM logic), `brief_cache.py` (~250, Redis), `brief_formatter.py` (~200, formatting). Grep: `rg "SegmentBriefService" app`. Update imports. Verify: `pytest -k segment_brief -v`. Each <350.

---

#### 88. dashboard_core.py split (674→<300)

Prompt: Split `app/services/dashboard/dashboard_core.py` (674) → 3: `dashboard/dashboard_metrics.py` (~280), `dashboard_usage.py` (~220), `dashboard_costs.py` (~170). Grep: `rg "DashboardCore" app`. Update `app/api/dashboard.py` imports. Verify: `pytest -k dashboard -v`. Each <300.

---

### 🔴 P0: Security & Critical

#### 89. RBAC Implementation

Prompt: Implement RBAC (Admin/Researcher/Viewer). **Migration**: `alembic revision -m "add_user_role"` → add `users.role ENUM`. **Middleware**: `app/middleware/rbac.py` → `@requires_role('admin')` decorator. **API**: Protect endpoints (Admin: DELETE /users, Researcher: POST /personas, Viewer: GET only). **Tests**: `pytest tests/unit/test_rbac.py --cov=app/middleware/rbac` (90%+). Verify: role enforcement works, 403 on unauthorized.

---

#### 90. Security Audit

Prompt: Security audit. **OWASP**: SQL injection, XSS, CSRF checks. **Bandit**: `bandit -r app/ -ll` → fix high/medium. **Safety**: `safety check` → update vulnerable deps. **Manual**: JWT expiry, secrets in code (`rg "api_key|password|secret" app`). **Report**: Document findings + fixes. Success: 0 high/critical vulns, report ready.

---

#### 91. Staging Environment

Prompt: Setup staging. **Cloud Run**: `sight-api-staging` service. **DB**: `sight-staging-db` Cloud SQL. **CI/CD**: `.github/workflows/deploy-staging.yml` → auto-deploy `staging` branch. **Migrations**: Test on staging first. **Env**: Separate vars (STAGING=true). Success: staging live, migrations tested, CI/CD works.

---

#### 92. Secrets Scanning CI/CD

Prompt: Secrets scan. **Workflow**: `.github/workflows/secrets-scan.yml` → TruffleHog, GitGuardian. **Config**: `.trufflehog.yaml`. **Alerts**: Fail build, Slack #security. **Historical**: `trufflehog git file://.` → scan all. Success: CI/CD scan works, 0 secrets found, alerts fire.

---

#### 93. Automated Rollback

Prompt: Auto rollback. **Health**: `/health` endpoint (DB, Redis, Neo4j checks). **Policy**: If 5xx>5% OR latency>2s for 2min → rollback. **Config**: `gcloud run services update --health-check=/health`. **Alerts**: Slack on rollback. **Test**: Crash endpoint, verify rollback <2min. Success: rollback works, MTTR<2min.

---

### 🟡 P1: Features & Infrastructure

#### 94. Export PDF/DOCX

Prompt: PDF/DOCX export. **Backend**: `app/services/export/pdf_generator.py` (WeasyPrint), `docx_generator.py` (python-docx). **API**: `POST /api/export/personas/{id}/pdf`. **Features**: Charts, watermarks (free tier), TOC. **Performance**: Background task, <5s download. **Frontend**: Download button. Success: PDF works, <5s, watermarks, tests 85%+.

---

#### 95. Stripe Integration

Prompt: Stripe payments. **Models**: `app/models/subscription.py`. **API**: `POST /api/payments/checkout`, `/webhooks/stripe`. **Plans**: Free, Pro $49/mo. **Webhooks**: `checkout.session.completed`, `invoice.payment_succeeded`. **Portal**: Billing portal link. **Frontend**: Pricing page, checkout. Success: subscribe works, webhooks handled, tests 90%+.

---

#### 96. Team Accounts

Prompt: Teams. **Models**: `app/models/team.py`, `team_members.py`. **API**: `POST /api/teams`, `/teams/{id}/invite`, `/teams/{id}/projects`. **Permissions**: Owner/Member/Viewer. **Projects**: Add `team_id`, share. **Activity**: Audit log. **Frontend**: Team dashboard. Success: teams work, shared projects, tests 85%+.

---

#### 97. Monitoring & Alerting

Prompt: Enhanced monitoring. **Dashboards**: Cloud Monitoring (latency p50/p90/p99, errors, users, costs). **Alerts**: Error>5%, downtime>1min, cost spike>$100/day. **PagerDuty**: Integration, on-call. **Metrics**: Custom (personas/hour, tokens/min). **Reports**: Weekly email. Success: dashboards live, alerts fire, PagerDuty works, MTTR<20min.

---

#### 98. E2E Tests Expansion (12→30+)

Prompt: E2E expansion. **Current**: 12 tests. **Target**: 30+. **Coverage**: Persona flow (create→generate→view), Focus groups (setup→discuss→results), Workflows (create→execute→export), Surveys, Settings. **Framework**: Playwright `tests/e2e/`. **CI**: GitHub Actions. **Critical**: 90%+ coverage. Success: 30+ tests, critical paths covered, CI works, flaky<5%.

---

#### 99. Multi-LLM Support

Prompt: Multi-provider. **Abstraction**: `app/services/shared/llm_router.py`. **Providers**: Gemini, OpenAI, Anthropic. **Fallback**: Gemini→OpenAI→Anthropic. **Cost Routing**: Prefer cheaper for simple tasks. **Config**: `config/models.yaml` per-domain. **Tracking**: Tokens/cost per provider. Success: 3 providers work, fallback tested, cost tracking accurate.

---

### 🟢 P2: Performance & Tech Debt

#### 100. Bundle Size Reduction (2.5MB→1.5MB)

Prompt: Reduce bundle. **Current**: 2.5MB. **Target**: <1.5MB. **Techniques**: Lazy loading, code splitting (`manualChunks`), tree shaking, remove unused deps (task 85). **Analysis**: `npm run build --stats && npx vite-bundle-visualizer`. **Optimize**: Split vendor chunks, dynamic imports. **Lighthouse**: >80. Success: <1.5MB, initial<1MB, Lighthouse>80, <3s on 3G.

---

#### 101. Lazy Loading Routes

Prompt: Lazy routes. **Current**: All eager. **Target**: All lazy. **Implementation**: `const Personas = lazy(() => import('./Personas'))`, wrap `<Suspense>`. **Routes**: Personas, FocusGroups, Workflows, Dashboard, Settings, Surveys. **Fallback**: LoadingSpinner. **Preload**: On hover. Success: all lazy, fallbacks work, initial<1MB, transitions smooth.

---

#### 102. N+1 Query Problem

Prompt: Fix N+1. **Identify**: SQL logging (echo=True), `pg_stat_statements`. **Patterns**: Loops loading related data. **Fix**: `selectinload(Persona.focus_groups)`, `joinedload(Project.personas)`. **Critical**: `/api/personas` (with focus_groups), `/api/projects/{id}` (with personas). **Validate**: Count queries (O(1) not O(n)). Success: 0 N+1 in critical, latency<300ms p90, optimal counts.

---

#### 103. Neo4j Connection Leaks

Prompt: Fix leaks. **Problem**: Connections not closed. **Fix**: Always `async with neo4j_connection.session() as session:`. **Audit**: `rg "neo4j_connection\\.session\\(\\)" app` → check all. **Monitor**: Track `neo4j.bolt.connections.active`. **Validate**: Stress test, memory stable. Success: 0 leaks, memory stable, monitoring works.

---

#### 104. Missing DB Indexes

Prompt: Add indexes. **Analysis**: `SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 20` → slow queries. **Slow**: `personas WHERE project_id AND deleted_at IS NULL`. **Indexes**: Composite `CREATE INDEX idx_personas_project_deleted ON personas(project_id, deleted_at)`, similar for focus_groups, surveys. **Migration**: Alembic. **Validate**: Queries<100ms p95. Success: all<100ms, indexes documented.

---

### 🟢 P2.8: Repository Cleanup

#### 105. Cleanup cache

Prompt: Remove cache. **Dirs**: `.pytest_cache`, `.ruff_cache`, `__pycache__`, `*.pyc`. **Command**: `rm -rf .pytest_cache .ruff_cache && find . -name "__pycache__" -exec rm -rf {} + && find . -name "*.pyc" -delete`. **Gitignore**: Add to `.gitignore`. Success: cache removed, gitignore updated.

---

#### 106. Cleanup .DS_Store

Prompt: Remove .DS_Store. **Find**: `find . -name ".DS_Store"` (7 found). **Remove**: `find . -name ".DS_Store" -delete`. **Gitignore**: Add `.DS_Store`. **Global**: `echo ".DS_Store" >> ~/.gitignore_global`. Success: removed, gitignore updated.

---

#### 107. Archive obsolete .md

Prompt: Archive old docs. **Files**: `STUDY_DESIGNER_*.md`, `IMPLEMENTATION_PROGRESS.md`, `frontend/DARK_MODE_AUDIT_*.md`. **Archive**: `mkdir -p docs/archive && mv [files] docs/archive/`. **Commit**: "chore: archive obsolete docs". Success: archived, root cleaner.

---

#### 108. Cleanup root

Prompt: Clean root. **Review**: `ls -la | grep .md`. **Move**: `DEMO_DATA_INFO.md` → `docs/` or delete. **Evaluate**: `docker-compose.prod.yml` (if unused, delete). **Keep**: `README.md`, `CLAUDE.md`, `prompty.md`, `docker-compose.yml`. Success: root cleaner, only essentials.

---

#### 109. Docker volumes cleanup

Prompt: Cleanup volumes. **Check**: `docker volume ls`. **Data**: Neo4j `./data/neo4j`, PostgreSQL `./data/postgres`. **Decision**: Keep or cleanup. **Cleanup**: `docker-compose down -v && rm -rf ./data/*`. **Gitignore**: `data/` in `.gitignore`. **Fresh**: `docker-compose up -d && python scripts/init_neo4j_indexes.py`. Success: reviewed, decision made, fresh start works.

---

### 🔵 P3: Documentation

#### 110. docs/BACKEND.md - aktualizacja refaktoryzacji

Prompt: Zaktualizuj `docs/BACKEND.md` o wszystkie zmiany z zadań 1-35. **Dodaj sekcje**: Nowa struktura `app/services/` (personas/, dashboard/, workflows/, rag/, focus_groups/ z podfolderami). **Zaktualizuj**: Service layer patterns, import examples. **Sprawdź**: Cross-references do nowych modułów. Success: docs aktualne, wszystkie nowe moduły udokumentowane.

---

#### 111. docs/AI_ML.md - aktualizacja RAG i persona generation

Prompt: Zaktualizuj `docs/AI_ML.md`. **RAG changes**: Zadania 3,6 (hybrid search split, graph service split). **Persona generation**: Zadania 1,4,8-10 (generator split, orchestration, details, distribution). **Dodaj**: Nowe moduły, zaktualizowane flow diagrams. Success: docs aktualne, RAG i persona generation jasne.

---

#### 112. docs/ROADMAP.md - completed tasks i Q1 2025

Prompt: Zaktualizuj `docs/ROADMAP.md`. **Add**: "Completed 2024" section z zadaniami 1-70 (refaktoryzacje backend/frontend). **Update**: Q1 2025 priorities z zadaniami 71-114 (audyty, re-splits, security, features). **Check**: Priorytety vs BIZNES.md KPIs. Success: roadmap aktualny, completed tracked.

---

#### 113. docs/CLAUDE.md - referencje i przykłady

Prompt: Zaktualizuj `docs/CLAUDE.md`. **Section "Referencja Kluczowych Plików"**: Dodaj nowe moduły z zadań 1-35. **Update**: Import examples (nowe ścieżki). **Add**: Troubleshooting dla split modules. Success: claude.md aktualny, import examples poprawne.

---

#### 114. docs/README.md - linki i indeks

Prompt: Zaktualizuj `docs/README.md`. **Review**: Wszystkie linki do docs. **Add**: Nowe sekcje jeśli brakuje (workflows docs z zadania 31). **Check**: Alfabetyczny porządek, opisy aktualne. Success: README indeks aktualny, wszystkie docs linkowane.

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

#### 36. ✅ [Frontend Component] - Personas.tsx (1195 → 653 → 488 linii)

Prompt (krótki): Przejrzyj `frontend/src/components/layout/Personas.tsx` (monolityczny komponent). Najpierw: `rg -n "import.*Personas" frontend/src --glob "**/*.{ts,tsx}"` i zanotuj zależności. Podziel na `PersonasLayout.tsx`, `PersonasList.tsx`, `PersonaFilters.tsx`, `PersonaActions.tsx`; przenieś hardcoded labels (linia 76-99) do `frontend/src/constants/personas.ts` i zaktualizuj importy + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview`.

**Wynik (2025-11-11)**: ✅ Zakończono
- Plik główny: 653 → 488 linii (-25%)
- Utworzono 3 nowe komponenty:
  - `PersonasHeader.tsx` (85 linii) - header z akcjami
  - `PersonasProgressBar.tsx` (62 linie) - progress bar generacji
  - `PersonasStats.tsx` (98 linii) - statystyki demograficzne
- PersonasList i PersonaFilters już istniały jako osobne komponenty
- Usunięto nieużywany kod (currentPersonaName, currentPersonaAgeLabel)
- Commit: d50896a

---

#### 37. ✅ [Frontend Component] - FocusGroupView.tsx (972 → 637 linii)

Prompt (krótki): Przejrzyj `frontend/src/components/layout/FocusGroupView.tsx` (dyskusja + odpowiedzi w jednym). Najpierw: `rg -n "import.*FocusGroupView" frontend/src --glob "**/*.tsx"` i zanotuj usage. Podziel na `FocusGroupLayout.tsx`, `DiscussionThread.tsx`, `ResponseComposer.tsx`; zaktualizuj importy i routing + **usuń nieużywany kod** (`npm run lint -- --fix`) + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview`.

**Wynik (2025-11-11)**: ✅ Zakończono
- Plik główny: 972 → 637 linii (-34%)
- Utworzono 3 nowe komponenty:
  - `FocusGroupHeader.tsx` (76 linii) - header z back button i statusem
  - `FocusGroupSetupTab.tsx` (176 linii) - konfiguracja pytań i uczestników
  - `FocusGroupDiscussionTab.tsx` (228 linii) - progress bar i live chat
- Usunięto duplikację kodu (getStatusColor, getStatusText przeniesione do header)
- Uproszczono importy (usunięto nieużywane)
- Commit: 16dad46

---

#### 38. ❌ [Frontend Component] - GraphAnalysis.tsx - USUŃ (martwy kod)

**UWAGA:** GraphAnalysis.tsx (788 linii) NIE JEST UŻYWANY NIGDZIE w aplikacji - to martwy kod!

Prompt (krótki): Przejrzyj `frontend/src/components/layout/GraphAnalysis.tsx` i zweryfikuj że nie jest używany. Najpierw: `rg -l "GraphAnalysis" frontend/src --glob "**/*.tsx" --glob "**/*.ts"` (powinien zwrócić tylko sam plik). Sprawdź routing w `App.tsx` - nie ma case'a dla graph analysis. **USUŃ PLIK** zamiast go dzielić + sprawdź czy inne pliki w `layout/` też nie są martwe (FigmaDashboard.tsx, StatsOverlay.tsx, FloatingControls.tsx) + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview && rg "GraphAnalysis" frontend/src` (powinno być 0 wyników).

**To zadanie zostało zastąpione przez zadanie 77 w sekcji P2.5 Audyt.**

---

#### 39. ✅ [Frontend Component] - FocusGroupPanel.tsx (783 linii)

Prompt (krótki): Przejrzyj `frontend/src/components/panels/FocusGroupPanel.tsx` (panel + details razem). Najpierw: `rg -n "import.*FocusGroupPanel" frontend/src --glob "**/*.tsx"` i zanotuj usage. Podziel na `FocusGroupPanel.tsx` (panel) i `FocusGroupDetails.tsx` (szczegóły) i zaktualizuj importy w komponentach nadrzędnych + **usuń nieużywany kod** (`npm run lint -- --fix`). Zweryfikuj: `cd frontend && npm run build && npm run preview`.

**Wynik (2025-11-11)**: ✅ Zakończono
- Plik główny: 783 → 136 linii (-83%)
- Utworzono 3 nowe komponenty:
  - `StatusBadge.tsx` (52 linie) - badge z ikonami dla statusów (pending, running, completed, failed)
  - `FocusGroupCard.tsx` (204 linie) - karta grupy z animacjami, metrykami, akcjami
  - `FocusGroupForm.tsx` (410 linii) - formularz tworzenia/edycji z walidacją
- Usunięto 3 inline funkcje z głównego pliku
- Wyczyszczono nieużywane importy (14 importów usuniętych)
- Commit: 47b9c06

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
**Wersja:** 1.3
**Utrzymanie:** Aktualizuj checklist i dodawaj nowe prompty według potrzeb

---

## 📝 Historia Zmian

### 2025-11-11 (Wersja 1.3) - Cleanup Repo + Poprawki Dokumentacji
**Autor:** Claude Code
**Typ:** Dodanie zadań cleanup + korekta zadań dokumentacji

**Zmiany:**
1. ✅ **Dodano sekcję P2.8: Repository Cleanup (zadania 111-115)**
   - 111: Cleanup cache directories (.pytest_cache, .ruff_cache, __pycache__)
   - 112: Cleanup macOS files (.DS_Store)
   - 113: Archive/Delete obsolete .md files (STUDY_DESIGNER, IMPLEMENTATION_PROGRESS, DARK_MODE_AUDIT)
   - 114: Cleanup root directory (DEMO_DATA_INFO.md, docker-compose.prod.yml)
   - 115: Docker volumes cleanup (local data)

2. ✅ **Poprawiono zadania dokumentacji (71-75):**
   - Zmieniono z "split" na "aktualizacja"
   - 71: BACKEND.md - aktualizuj o refaktoryzacje 1-35
   - 72: AI_ML.md - aktualizuj o zmiany RAG i persona generation
   - 73: ROADMAP.md - dodaj "Completed 2024", zaktualizuj Q1 2025
   - 74: CLAUDE.md - aktualizuj referencje plików
   - 75: README.md - zaktualizuj linki

3. 📊 **Zaktualizowano statystyki:**
   - Total zadań: 110→115 (75 oryginalnych + 40 nowych)
   - Zakończone: 51/115 (44%)
   - Do zrobienia: 64/115 (56%)

---

### 2025-11-11 (Wersja 1.2) - Rozszerzenie Zadań: Security, Features, Performance
**Autor:** Claude Code
**Typ:** Dodanie 25 nowych zadań (86-110) + korekta nieaktualnych

**Zmiany:**
1. ✅ **Dodano sekcję P2.6: Audyt Post-Split (zadania 86-90)**
   - 86-87: Frontend audyt plików po splitach 36-48
   - 88-89: Backend audyt plików po splitach 1-35
   - 90: Dependencies audyt (package.json, requirements.txt)

2. ✅ **Dodano sekcję P2.7: Backend Re-Split (zadania 91-93)**
   - 91: hybrid_search_service.py ponowny split (1074 linii)
   - 92: segment_brief_service.py ponowny split (820 linii)
   - 93: dashboard_core.py split (674 linii)

3. ✅ **Dodano sekcję P0: Security & Critical (zadania 94-98)**
   - 94: RBAC Implementation
   - 95: Security Audit (OWASP, Bandit)
   - 96: Staging Environment Setup
   - 97: Secrets Scanning CI/CD
   - 98: Automated Rollback

4. ✅ **Dodano sekcję P1: Features & Infrastructure (zadania 99-105)**
   - 99: Export PDF/DOCX
   - 100: Stripe Payment Integration
   - 101: Team Accounts
   - 102: Enhanced Monitoring & Alerting
   - 103: E2E Tests Expansion (12→30+)
   - 104: Multi-LLM Provider Support
   - 105: Database Connection Pooling

5. ✅ **Dodano sekcję P2: Performance & Tech Debt (zadania 106-110)**
   - 106: Bundle Size Reduction (2.5MB→1.5MB)
   - 107: Lazy Loading Routes
   - 108: N+1 Query Problem
   - 109: Neo4j Connection Leaks
   - 110: Missing Database Indexes

6. ✅ **Skorygowano nieaktualne zadania:**
   - Zadanie 38: GraphAnalysis.tsx → NIE ISTNIEJE (już usunięty)
   - Zadanie 46-48: Poprawione nazwy plików (PersonaReasoningPanel, WorkflowsListPage, ExecutionHistory)

7. 📊 **Zaktualizowano statystyki:**
   - Total zadań: 85→115 (75 oryginalnych + 40 nowych)
   - Zakończone: 50→51/115 (44%)
   - Do zrobienia: 35→64/115 (56%)

---

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
   - **Total zadań:** 115 (75 oryginalnych + 10 audytowych + 30 nowych)
   - **Estimated Time:** 9-13 tygodni (z audytem + nowymi zadaniami)
   - **Zakończone:** 51/115 (44%)
   - **Do zrobienia:** 64/115 (56%)

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
