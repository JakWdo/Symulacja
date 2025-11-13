# 📌 SIGHT Platform — Roadmap i Plan Wdrożeń (priorytetyzowany)

Projekt: Sight — AI‑powered Focus Groups & Research Ops
Ścieżka: `.` (repo‑relatywna)
Wersja dokumentu: 2025‑11‑13

Cel dokumentu: Jedna, spójna mapa wdrożeń i porządków dla backendu, frontendu i CI/CD, obejmująca Shared Context (Środowiska+Tagi), RBAC, konta zespołowe, eksport raportów oraz bezpieczne wdrożenia. Zawiera priorytety, etapy, definicje Done i checklisty.

---

## 📑 Spis treści

1. Cel i Założenia
2. Priorytety i Fazy
3. Specyfikacje (RBAC + Teamy, Shared Context, Eksport, Staging)
4. Backlog Szczegółowy (checklisty) — w tym zaktualizowane wcześniejsze zadania
5. Testy i Definition of Done
6. Ryzyka i Mitigacje
7. Appendix: Komendy i narzędzia

---

## 1) Cel i Założenia

- Stack: FastAPI, SQLAlchemy (async), Alembic, Postgres, React/TypeScript.
- Stan bazowy:
  - RBAC: istnieje `SystemRole` (`admin|researcher|viewer`) i dependencies w `app/api/dependencies.py`.
  - Eksport: gotowe raporty PDF/DOCX dla person, focus groups, surveys.
  - CI/CD: Cloud Build z etapem migracji i smoke‑testami (bez realnego rollbacku ruchu).
- Cel biznesowy: skrócić setup projektów do ~5 minut, ograniczyć koszty API poprzez reuse zasobów, zwiększyć bezpieczeństwo i stabilność wdrożeń.

---

## 2) Priorytety i Fazy

Kolejność dowożenia (wartość → ryzyko → zależności):

- Faza 1 (P0): RBAC + Team Accounts (fundamenty bezpieczeństwa i izolacji danych)
- Faza 2 (P0): Shared Context (Środowiska + Tagi + Filtry + Snapshoty)
- Faza 3 (P1): Eksport Raportu Projektu (PDF/DOCX)
- Faza 4 (P1): Staging + migracje + auto‑rollback (twarde praktyki wdrożeniowe)
- Prace horyzontalne (P2): test coverage 85%+, split config loader, konsolidacje i dokumentacja

Szacowanie (orientacyjnie, roboczodni):
- F1: 5–7d, F2: 8–12d, F3: 2–4d, F4: 2–3d, Horyzontalne: 3–5d (równolegle)

---

## 3) Specyfikacje

### 3.1 RBAC + Team Accounts (Faza 1)

Cel: Globalne role (SystemRole) oraz role przynależności zespołowej decydują o możliwościach użytkownika i widoczności danych.

- Baza (Alembic):
  - `teams` (id, name, created_at)
  - `team_memberships` (team_id, user_id, role_in_team ENUM: owner|member|viewer, created_at)
  - `projects`: dodać `team_id` (FK→teams, index). Backfill: każdy istniejący projekt przypiąć do teamu właściciela (auto utworzyć „Personal Team” jeśli brak).

- Modele i relacje (ORM):
  - `User ↔ TeamMembership ↔ Team`, `Team → Project (1:N)`.

- Dependencies i scoping:
  - `require_team_membership(team_id, allowed_roles)`: wymusza rolę w teamie.
  - `get_project_for_user`/`get_persona_for_user`: filtrowanie po `project.team_id ∈ teamów usera`, nie wyłącznie owner.
  - RBAC enforcement: viewer = GET‑only; researcher = POST/PUT w obrębie teamu; admin = operacje globalne.

- API minimalne:
  - `POST /teams` — tworzy team (admin lub pierwszy user)
  - `GET /teams/my` — lista teamów użytkownika
  - `POST /teams/{id}/members` — dodaje istniejącego usera (email/ID)

- Frontend:
  - Dropdown „Team” w topbarze; scoping listy projektów; widok teamu (nazwa, członkowie, role).
  - Ukrycie niedozwolonych akcji (Edit/Delete/Invite) wg roli systemowej i roli w teamie.

Definition of Done (RBAC + Teamy):
- Użytkownik widzi wyłącznie projekty teamów, do których należy; viewer nie modyfikuje; owner/admin mają pełen dostęp.
- 1–2 testy per rola (200 vs 403) na kluczowych operacjach (create project, delete persona, list users/admin).

---

### 3.2 Shared Context: Środowiska + Tagi + Filtry + Snapshoty (Faza 2)

Cel: Wspólny pool person/workflowów na poziomie teamu, filtrowany tagami (facety) i współdzielony między projektami. Snapshoty zapewniają reprodukowalność.

- Baza (Alembic):
  - `environments` (id, team_id FK, name, description, is_active, created_at, updated_at)
  - `tags` (id, facet, key, description, created_at)
  - `resource_tags` (id, environment_id, resource_type, resource_id, tag_id, created_at)
  - `saved_filters` (id, environment_id, name, dsl, created_by, created_at)
  - `project_snapshots` (id, project_id, name, resource_type, resource_ids JSONB, created_at)
  - Zmiany: `projects.environment_id`, `personas.environment_id`, `workflow_templates.environment_id` (+indeksy po `environment_id`).

- Taksonomia tagów:
  - Facety: `dem:*`, `geo:*`, `psy:*`, `biz:*`, `ctx:*`, `custom:*` (whitelist facetów per environment).
  - Reguły: `facet:key` (kebab/snake), aliasy/synonimy; util `app/utils/tags.py` (parse/normalize/validate).

- Filtry (lekki DSL):
  - Składnia: `AND/OR/NOT`, nawiasy, facety (`dem:age-25-34`).
  - Parser: `app/services/filters/dsl_parser.py` → AST (shunting‑yard).
  - SQL builder: `app/services/filters/query_builder.py` (AND→HAVING COUNT DISTINCT, OR→UNION, NOT→anti‑join). Paginacja kursorem.

- Snapshoty:
  - Projekt może wskazać „live filter” (aktualne zasoby) lub „snapshot” (lista ID, immutable) dla reprodukowalności.

- API i UI:
  - `POST/GET /environments` (scoped do teamu), `GET /environments/{id}`
  - `GET /environments/{id}/resources?type=persona&filter=DSL`
  - `POST/GET /saved-filters?environment_id=...`
  - `POST /projects/{id}/snapshots` (z aktualnego filtra)
  - UI: przełącznik środowiska, faceted filters (chips), zapisywanie filtrów, „Create snapshot → attach to project”.

Definition of Done (Shared Context):
- Projekty pobierają subset person/workflowów z poola przez tagi; snapshoty działają; zapytania stabilne na 10k+ zasobów z indeksami.
- Testy: parser DSL i SQL builder (AND/OR/NOT), snapshot restore, filtry na dużych zbiorach.

---

### 3.3 Eksport Raportu Projektu (Faza 3)

Cel: Jednym kliknięciem wygenerować „ładny do wysłania” raport projektu (PDF/DOCX) z listą person, insightami i agregatami ankiet.

- Backend — serwis i szablony:
  - `app/services/export/`: dodać `generate_project_pdf(project_id) -> bytes`, `generate_project_docx(project_id) -> bytes`.
  - Dane: projekt + `personas`, summary focus groups, agregaty ankiet (eager loading przez `selectinload`).
  - Szablony: Jinja2→WeasyPrint (PDF) i python‑docx (DOCX) — strona tytułowa, sekcje per persona, key insights, wyniki ankiet.

- API:
  - `GET /projects/{id}/export/pdf`, `GET /projects/{id}/export/docx` (viewer+ z dostępem do projektu/teamu).

- Frontend:
  - Przycisk „Eksportuj” na widoku projektu; `exportProject(id, 'pdf'|'docx')` w `frontend/src/lib/api/export.ts`.

Definition of Done (Eksport):
- Dla istniejącego projektu: pobiera się plik, otwiera w czytniku, zawiera nazwę projektu i sekcje. Błędne ID/uprawnienia → 404/403 (nie 500).
- Testy: plik niepusty, zawiera nazwę projektu (sprawdzenie PDF HTML fallback / DOCX XML).

---

### 3.4 Staging + Migracje + Auto‑rollback (Faza 4)

Cel: Stabilne i odwracalne wdrożenia.

- Staging:
  - Osobny serwis i baza (Cloud Run + Cloud SQL), `.env.staging` z innymi sekretami/URL.
  - Pipeline: build → migrate (staging) → deploy (staging) → smoke tests (`/health`, frontend 200).

- Migracje DB:
  - Alembic, każda zmiana schematu w osobnej migracji; checklista indeksów i zgodności danych.

- Auto‑rollback:
  - Cloud Run traffic‑splitting: nowa rewizja 0–10% → smoke test → promote 100% albo rollback.
  - `cloudbuild.yaml`: realny rollback (`gcloud run services update-traffic ...`) przy fail, nie tylko log.

- Dokumentacja:
  - DEPLOY.md: „Jak wypuścić wersję”, „Jak sprawdzić staging”, „Jak zrobić rollback”.

Definition of Done (Staging):
- Nowa wersja przechodzi staging + smoke; w razie błędu produkcja wraca automatycznie do poprzedniej rewizji ≤2 min.

---

## 4) Backlog Szczegółowy (checklisty)

Uwaga: Zadania dostosowane z wcześniejszych promptów, przenumerowane i posortowane wg faz i priorytetów.

### Faza 1 — RBAC + Team Accounts (P0)
- [x] Alembic: `teams`, `team_memberships`, `projects.team_id` (+index) i backfill istniejących projektów
- [x] ORM: modele, relacje, rejestracja w Base
- [x] Dependencies: `require_team_membership`, scoping w `get_project_for_user`/`get_persona_for_user`
- [x] RBAC audit: viewer GET‑only na personas/projects/focus_groups/surveys/workflows/export
- [x] API: `POST /teams`, `GET /teams/my`, `POST /teams/{id}/members`
- [x] Frontend: Team selector, widok teamu, ukrywanie akcji wg ról
- [x] Testy API: 200/403 na głównych operacjach wg ról

### Faza 2 — Shared Context (P0)
- [ ] Alembic: `environments`, `tags`, `resource_tags`, `saved_filters`, `project_snapshots`, FK `environment_id` w projects/personas/templates
- [ ] Utils: `app/utils/tags.py` (parse/validate/normalize, aliasy)
- [ ] Filtry: `app/services/filters/{dsl_parser.py,query_builder.py}` + testy AST/SQL
- [ ] API: `/environments`, `/saved-filters`, `/environments/{id}/resources`, `/projects/{id}/snapshots`
- [ ] Backfill: „Default Environment” per team; przypięcie istniejących danych
- [ ] UI: faceted filters + zapisywanie + snapshot attach

### Faza 3 — Eksport projektu (P1)
- [ ] Serwis: `generate_project_pdf/docx` (WeasyPrint/python‑docx)
- [ ] Endpointy: `GET /projects/{id}/export/{pdf|docx}` (viewer+)
- [ ] Frontend: `exportProject` + przycisk na widoku projektu
- [ ] Testy: plik niepusty, zawiera nazwę projektu; 404/403 poprawne

### Faza 4 — Staging + rollback (P1)
- [ ] `.env.staging` i sekrety staging
- [ ] Cloud Build: traffic‑splitting + realny rollback przy smoke‑fail
- [ ] DEPLOY.md: proces staging/produkcyjny, szybki rollback

### Prace horyzontalne (P2)
- [ ] Pokrycie testami 85%+ (adaptacja zad. „66”): `pytest --cov=app --cov-report=term-missing` i testy brakujących modułów (personas/orchestration, rag/graph, dashboard/metrics)
- [ ] Split `config/loader.py` (adaptacja zad. „67”): wydzielenie walidacji do `config/validators.py` + aktualizacja importów
- [ ] RAG BackgroundTasks cleanup (adaptacja „116”): ocena przepływu, idempotencja/logowanie, ewentualna kolejka
- [ ] Workflows docs move (adaptacja „117”): przenieść do `docs/workflows/` i poprawić linki
- [ ] Stopwords centralizacja (adaptacja „118”): użyć `config/prompts/shared/stopwords.yaml`, usunąć duplikaty
- [ ] Frontend constants (adaptacja „119”): konsolidacja do `frontend/src/constants/{workflows.ts,ui.ts}`
- [ ] Dokumentacja (adaptacja „111–115”):
  - docs/AI_ML.md — zaktualizować RAG/persona generation
  - docs/ROADMAP.md — przenieść completed 2024, dodać Q1 2025
  - docs/CLAUDE.md — referencje po splitach, troubleshooting importów
  - README.md — nowe sekcje i linki
  - CHANGELOG_DOCS.md — wynik audytu dokumentacji

---

## 5) Testy i Definition of Done (globalnie)

- RBAC/Teamy: testy ról (admin/researcher/viewer) na create/update/delete i listing (200/403/404 zgodnie z przypadkiem). Widoczność wyłącznie w teamach użytkownika.
- Shared Context: testy DSL (AST) i SQL buildera; snapshot create/restore; wydajność filtrów z indeksami (próbki >10k zasobów).
- Eksport: testy API PDF/DOCX na projekcie (plik niepusty, zawiera nazwę projektu), 404/403 na brak uprawnień.
- Staging: smoke tests `/health` i frontend 200; pipeline zatrzymuje rollout i robi rollback przy fail.
- Coverage: 85%+ dla `app` (przynajmniej smoke na ścieżki krytyczne i edge‑case’y błędów).

---

## 6) Ryzyka i Mitigacje

- Eskalacja liczby tagów i drift taksonomii → facety i whitelist, aliasy/merge, panel przeglądu zmian.
- Złożone zapytania OR/NOT → limit złożoności DSL, UNION/anti‑join, paginacja kursorem, materialized views dla facet counts.
- Złożoność uprawnień (global vs team) → zasada „min(global, team)”, testy 403/404 i audyty endpointów.
- Wdrożenia: brak automatycznego rollbacku → traffic‑splitting i skrypt rollback w pipeline.

---

## 7) Appendix: Komendy i narzędzia

Grep / wyszukiwanie
```bash
rg -n "ClassName|def router|import.*ComponentName" app frontend/src --glob "**/*.{py,ts,tsx}"
rg -n "TODO|FIXME" app tests frontend/src --glob "**/*.{py,ts,tsx}"
rg -n "print\(" app --glob "**/*.py"
```

Pytest
```bash
pytest -v
pytest tests/unit -v
pytest --cov=app --cov-report=term-missing
pytest --cov=app --cov-report=html
pytest -k config -v
```

Docker / Deploy
```bash
docker-compose restart api
docker-compose logs -f api
docker-compose up -d --build api
```

Frontend (npm)
```bash
cd frontend && npm run build
npm run dev
npm run lint
npm run type-check
```

Git Workflow (opcjonalnie)
```bash
git checkout -b feature/<krótki-opis>
git add . && git commit -m "feat: <krótki opis>"
git push origin feature/<krótki-opis>
```

Cleanup
```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete
find . -name ".DS_Store" -delete
```

---

Koniec dokumentu — roadmap priorytetowa, zintegrowana z dotychczasowymi zadaniami i dostosowana do aktualnego kodu.

