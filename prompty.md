# 🧹 SIGHT PLATFORM - CLEANUP PROMPTS (pozostałe)

**Projekt:** Sight AI-powered Focus Groups Platform
**Ścieżka:** `.` (ścieżki repo‑relatywne)
**Data utworzenia:** 2025-11-11
**Scope:** 11 pozostałych promptów cleanup (wykonane usunięto z pliku)
**Cel:** Domknięcie luk: coverage 85%+, split `config/loader.py`, aktualizacja dokumentacji

---

## 📋 Spis Treści

1. Instrukcja Użytkowania
2. Global Checklist (pozostałe)
3. Prompty Cleanup (pozostałe)
4. Appendix: Komendy i Narzędzia

---

## 📖 Instrukcja Użytkowania

### Kolejność Wykonywania

- Najpierw testy i config (66–67), potem dokumentacja (111–115).

### Workflow Per Prompt

1. Grep: znajdź zależności przed zmianami
2. Podział/zmiana: wprowadź zmiany zgodnie z opisem promptu
3. Importy: zaktualizuj importy w zależnych plikach
4. Fixes: usuń TODO/hardcoded/deprecated oraz nieużywany kod
5. Testy: uruchom `pytest -v`
6. Działa: `docker-compose restart` lub `npm run build`

### Konwencje i Guardrails

- Ścieżki repo‑relatywne (`app/...`, `frontend/...`).
- Brak cyklicznych importów (wspólne typy/utilsy → moduły shared/, jednokierunkowe zależności).
- Utrzymuj publiczne API przez re‑eksporty w `__init__.py`, jeśli to potrzebne.
- Prompty krótkie (≤4 zdania), zawsze: zależności → zmiana → importy → test/build.

### Status i Ocena

- Ocena postępu: 93/100
- Zrealizowano: większość P0/P1 (1–35), refaktoryzacje frontendu (36–49), lib/hooks (52–56), audyty i cleanupy (74–110).
- Pozostało: coverage 85% (66), split `config/loader.py` (67), oraz aktualizacje dokumentacji (111–115).

---

## ✅ Global Checklist (pozostałe)

Odznaczaj po zakończeniu każdego promptu:

### 🟢 P2: Tests
- [ ] 66. Test coverage gaps (target 85%+)

### 🟢 P2: Config & Scripts
- [ ] 67. config/loader.py split

### 🟡 P1: Backend API
- [ ] 116. api/rag.py – BackgroundTasks cleanup

### 🟢 P2: Konsolidacje i porządki
- [ ] 117. workflows docs – przenieś do `docs/workflows/`
- [ ] 118. Stopwords – centralizacja i użycie z config
- [ ] 119. Frontend constants – `constants/workflows.ts`, `constants/ui.ts`

### 🔵 P3: Documentation
- [ ] 111. docs/AI_ML.md – aktualizacja RAG (3,6), persona generation (1,4,8–10)
- [ ] 112. docs/ROADMAP.md – „Completed 2024” (1–70), Q1 2025 (71–115)
- [ ] 113. docs/CLAUDE.md – referencje plików, przykłady importów po splitach
- [ ] 114. docs/README.md – linki, opisy, nowe sekcje
- [ ] 115. Kompleksowa aktualizacja dokumentacji – audyt całego `docs/`

---

## 🧹 Prompty Cleanup (pozostałe)

### 🟢 P2: Tests

#### 66. 🟢 Test coverage gaps (target 85%+)
Prompt (krótki): Zmierz pokrycie i wskaż luki. Najpierw: `pytest --cov=app --cov-report=term-missing` oraz (jeśli dotyczy) `pytest --cov=frontend --maxfail=1 -q`. Skup się na modułach o niskim pokryciu (personas/orchestration, rag/graph, dashboard/metrics) i dopisz testy smoke/regresyjne. Zweryfikuj raport HTML: `pytest --cov=app --cov-report=html`.

---

### 🟢 P2: Config & Scripts

#### 67. 🟢 config/loader.py (681 linii)
Prompt (krótki): Wydziel walidację YAML z `config/loader.py`. Najpierw: `rg -n "validate|schema|yaml" config --glob "**/*.py"`. Utwórz `config/validators.py` (~350 linii), przenieś logikę walidacji, zaktualizuj importy (`config/__init__.py`, moduły korzystające). Zweryfikuj: `python scripts/config_validate.py` + `pytest -k config -v`.

---

### 🟡 P1: Backend API

#### 116. 🟡 api/rag.py – BackgroundTasks cleanup
Prompt (krótki): Oceń i uporządkuj użycie `BackgroundTasks` w `app/api/rag.py`. Najpierw: `rg -n "BackgroundTasks|add_task\(" app/api/rag.py` i zmapuj przepływ `_process_document_background`. Jeśli processing >2s, rozważ kolejkę (Cloud Tasks/Celery) lub pozostaw background z lepszym logowaniem i idempotencją; ujednolić statusy/błędy w DB. Zweryfikuj: `pytest -k "rag_" -v`.

---

### 🟢 P2: Konsolidacje i porządki

#### 117. 🟢 workflows docs – przenieś do `docs/workflows/`
Prompt (krótki): Przenieś dokumenty z `app/services/workflows/docs/` do `docs/workflows/`. Najpierw: `ls app/services/workflows/docs && rg -n "services/workflows/docs" -S`. Zaktualizuj odwołania w `README.md`/`docs/*` i usuń stary folder. Zweryfikuj: `rg -n "services/workflows/docs" docs README.md` (brak wyników).

#### 118. 🟢 Stopwords – centralizacja i użycie z config
Prompt (krótki): Użyj `config/prompts/shared/stopwords.yaml` jako źródła stopwords dla modułów tekstowych. Najpierw: `rg -n "STOPWORDS|stopwords" app/services --glob "**/*.py"`. Zastąp duplikaty (np. focus_groups/nlp/constants) loaderem z config i dodaj fallback; usuń zduplikowane listy. Zweryfikuj: `pytest -k "language_detection|concept_extraction" -v`.

#### 119. 🟢 Frontend constants – `constants/workflows.ts`, `constants/ui.ts`
Prompt (krótki): Skonsoliduj rozproszone stałe do `frontend/src/constants/{workflows.ts,ui.ts}`. Najpierw: `rg -n "label:\\s*'|DEFAULT|OPTIONS|true_branch_label|false_branch_label" frontend/src --glob "**/*.{ts,tsx}"`. Przenieś m.in.: `types/workflowNodeConfigs.ts:239,250-251` (domyślne etykiety), `components/focus-group/StatusBadge.tsx:13,20,28,35` (etykiety statusów). Zweryfikuj: `cd frontend && npm run build`.

---

### 🔵 P3: Documentation

#### 111. 🔵 docs/AI_ML.md
Prompt (krótki): Zaktualizuj sekcje RAG (zad. 3,6) i persona generation (1,4,8–10). Uzupełnij o nowe moduły/diagramy, sprawdź spójność nazw plików i importów. Zweryfikuj linki.

#### 112. 🔵 docs/ROADMAP.md
Prompt (krótki): Dodaj „Completed 2024” (1–70) i zaktualizuj Q1 2025 (71–115). Upewnij się, że priorytety są spójne z KPI w BIZNES.md. Zweryfikuj sekcje statusu.

#### 113. 🔵 docs/CLAUDE.md
Prompt (krótki): Zaktualizuj referencję kluczowych plików i przykłady importów po splitach (1–35). Dodaj troubleshooting dla najczęstszych błędów importów. Sprawdź zgodność ścieżek.

#### 114. 🔵 docs/README.md
Prompt (krótki): Przejrzyj i zaktualizuj linki/sekcje. Dodaj informacje o nowej strukturze `app/services/` i docs workflows. Zweryfikuj porządek i aktualność opisów.

#### 115. 🔵 Kompleksowa aktualizacja dokumentacji
Prompt (krótki): Wykonaj audyt całego `docs/` pod kątem zgodności z aktualnym kodem. Usuń martwe fragmenty, uzupełnij brakujące sekcje, napraw linki między dokumentami. Wynik zapisz skrótowo w `docs/CHANGELOG_DOCS.md`.

---

## 📚 Appendix: Komendy i Narzędzia

### Grep Patterns

```bash
# Znajdź importy/routy/komponenty
rg -n "ClassName|def router|import.*ComponentName" app frontend/src --glob "**/*.{py,ts,tsx}"

# TODO / hardcoded / print
rg -n "TODO|FIXME" app tests frontend/src --glob "**/*.{py,ts,tsx}"
rg -n "const.*=.*\[" frontend/src --glob "**/*.tsx"
rg -n "print\(" app --glob "**/*.py"
```

### Pytest Commands

```bash
pytest -v
pytest tests/unit -v
pytest --cov=app --cov-report=term-missing
pytest --cov=app --cov-report=html
pytest -k config -v
```

### Docker Compose

```bash
docker-compose restart api
docker-compose logs -f api
docker-compose up -d --build api
```

### Frontend (npm)

```bash
cd frontend && npm run build
npm run dev
npm run lint
npm run type-check
```

### Git Workflow

```bash
git checkout -b cleanup/prompt-XX-description
git add . && git commit -m "cleanup: [Prompt XX] opis"
git push origin cleanup/prompt-XX-description
gh pr create --title "Cleanup: Prompt XX" --label cleanup
```

### Cleanup Scripts

```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete
find . -name ".DS_Store" -delete
```

---

## 🎉 Koniec Cleanup Promptów (pozostałych)

**Pozostałe zadania:** 11
**Cel:** domknięcie coverage, split config, aktualizacje docs
