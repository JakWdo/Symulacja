# 🛠️ Scripts - Utility Scripts dla Market Research SaaS

Ten folder zawiera skrypty pomocnicze (utility scripts) do zarządzania infrastrukturą i inicjalizacji systemu.

---

## 📜 Dostępne Skrypty

### 1. init_db.py

**Opis:** Inicjalizacja bazy danych PostgreSQL

**Co robi:**
- Włącza rozszerzenie `pgvector` (wektory dla embeddings AI)
- Tworzy wszystkie tabele z modeli SQLAlchemy (Project, Persona, FocusGroup, PersonaEvent, etc.)

**Kiedy używać:**
- Pierwszy setup projektu (alternatywa dla Alembic migrations)
- Development environment reset
- Testowanie czystej bazy danych

**Uruchomienie:**
```bash
# Z poziomu root projektu
python scripts/init_db.py

# Lub jako moduł
python -m scripts.init_db
```

**Wymagania:**
- PostgreSQL uruchomiony (`docker-compose up -d postgres`)
- `DATABASE_URL` skonfigurowany w `.env`

**Uwagi:**
- Bezpiecznie: używa `CREATE IF NOT EXISTS` - nie nadpisuje istniejących danych
- W produkcji zalecane jest używanie Alembic migrations zamiast tego skryptu

---

### 2. init_neo4j_indexes.py

**Opis:** Inicjalizacja indeksów Neo4j dla RAG System

**Co robi:**
1. **Vector Index** (`rag_document_embeddings`)
   - Dla semantic search (Google Gemini embeddings)
   - Node: `RAGChunk`
   - Property: `embedding`
   - Dimensions: 768
   - Similarity: cosine

2. **Fulltext Index** (`rag_fulltext_index`)
   - Dla keyword search (Lucene-based)
   - Node: `RAGChunk`
   - Property: `text`

**Kiedy używać:**
- **PRZED pierwszym użyciem RAG!** (wymagane dla hybrid search)
- Po resecie Neo4j database
- Weryfikacja że indeksy istnieją

**Uruchomienie:**
```bash
# Z poziomu root projektu
python scripts/init_neo4j_indexes.py
```

**Wymagania:**
- Neo4j uruchomiony (`docker-compose up -d neo4j`)
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` w `.env`
- Neo4j 5.x+ (dla vector index support)

**Output:**
- ✅ Potwierdza że indeksy zostały utworzone lub już istnieją
- 📊 Pokazuje liczbę RAGChunk nodes w bazie
- ⚠️ Ostrzega jeśli Neo4j niedostępny lub wersja za stara

**Uwagi:**
- Indeksy są tworzone asynchronicznie - mogą być w stanie POPULATING przez chwilę
- Sprawdź status: `SHOW INDEXES` w Neo4j Browser (http://localhost:7474)

---

## 🚀 Workflow Setup Projektu

### Pierwsze Uruchomienie (New Developer)

```bash
# 1. Start Docker services
docker-compose up -d

# 2. Poczekaj na inicjalizację baz
sleep 10

# 3. Migracje bazy danych (preferowana metoda)
docker-compose exec api alembic upgrade head

# LUB alternatywnie: init_db.py
python scripts/init_db.py

# 4. Inicjalizuj Neo4j indeksy (WYMAGANE dla RAG!)
python scripts/init_neo4j_indexes.py

# 5. Weryfikuj że wszystko działa
docker-compose ps
curl http://localhost:8000/docs  # API docs
curl http://localhost:7474        # Neo4j browser
```

### Reset Environment (Clean State)

```bash
# 1. Zatrzymaj i usuń wszystko (UWAGA: usuwa dane!)
docker-compose down -v

# 2. Start od nowa
docker-compose up -d

# 3. Poczekaj na inicjalizację
sleep 10

# 4. Migracje
docker-compose exec api alembic upgrade head

# 5. Neo4j indeksy
python scripts/init_neo4j_indexes.py

# 6. (Opcjonalnie) Upload RAG documents
# Użyj frontendu lub POST /api/v1/rag/documents/upload
```

---

## 📝 Dodawanie Nowych Skryptów

### Template: Nowy Skrypt Utility

```python
#!/usr/bin/env python3
"""
Opis co robi skrypt

Użycie:
    python scripts/my_script.py [args]

Wymagania:
    - Lista wymagań (DB, API keys, etc.)
"""

import sys
from pathlib import Path

# Dodaj root directory do path (jeśli potrzebne importy z app/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings

settings = get_settings()


def main():
    """
    Główna funkcja skryptu
    """
    print("=" * 80)
    print("SCRIPT NAME")
    print("=" * 80)

    # Implementacja...

    print("✅ Script completed successfully")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

### Konwencje dla Skryptów

1. **Shebang:** `#!/usr/bin/env python3` (dla Unix-like systems)
2. **Docstring:** Jasny opis, usage, requirements
3. **Exit codes:** 0 = success, 1 = error
4. **Logging:** Print progress i results (user-friendly)
5. **Error handling:** Try/except z informacyjnymi error messages
6. **Idempotentność:** Bezpieczne re-run (CREATE IF NOT EXISTS)

---

## 🧪 Testowanie Skryptów

### Manual Testing

```bash
# Test init_db.py
docker-compose up -d postgres
python scripts/init_db.py
# Verify: psql do bazy, sprawdź \dt (list tables)

# Test init_neo4j_indexes.py
docker-compose up -d neo4j
python scripts/init_neo4j_indexes.py
# Verify: Neo4j Browser → SHOW INDEXES
```

### Automated Testing

Testy skryptów powinny być w `tests/integration/` lub `tests/manual/`:

```python
# tests/integration/test_scripts.py

@pytest.mark.integration
async def test_init_db_script():
    """Test że init_db.py działa poprawnie"""
    result = subprocess.run(
        ["python", "scripts/init_db.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Database initialization complete" in result.stdout
```

---

## 🔍 Debugging Skryptów

### Common Issues

#### ❌ "Module not found" error
```bash
# Rozwiązanie: Uruchom jako moduł lub dodaj do PYTHONPATH
python -m scripts.init_db
# LUB
PYTHONPATH=/Users/jakubwdowicz/market-research-saas python scripts/init_db.py
```

#### ❌ "Connection refused" (PostgreSQL)
```bash
# Rozwiązanie: Sprawdź czy Docker działa
docker-compose ps
docker-compose logs postgres
docker-compose up -d postgres
```

#### ❌ "Connection refused" (Neo4j)
```bash
# Rozwiązanie: Neo4j może potrzebować ~30s na start
docker-compose logs neo4j
# Poczekaj aż zobaczysz: "Started."
sleep 30
python scripts/init_neo4j_indexes.py
```

#### ❌ Neo4j "unsupported feature" error
```bash
# Rozwiązanie: Używasz Neo4j <5.0
# Vector indexes wymagają Neo4j 5.x+
docker-compose down
# Zaktualizuj docker-compose.yml do neo4j:5-enterprise lub neo4j:5
docker-compose up -d neo4j
```

---

## 📚 Powiązana Dokumentacja

- **Główna dokumentacja:** [../CLAUDE.md](../CLAUDE.md)
- **Setup i instalacja:** [../README.md](../README.md)
- **Testy:** [../docs/TESTING.md](../docs/TESTING.md)
- **RAG System:** [../docs/RAG_HYBRID_SEARCH.md](../docs/RAG_HYBRID_SEARCH.md)
- **GraphRAG:** [../docs/GRAPH_RAG.md](../docs/GRAPH_RAG.md)

---

## 🤝 Contributing

Dodając nowy skrypt:
1. Dodaj jasny docstring z usage i requirements
2. Dodaj do tego README.md
3. Dodaj testy (jeśli ma sens)
4. Update [../CLAUDE.md](../CLAUDE.md) jeśli skrypt zmienia workflow

---

### 3. backup_neo4j.py ⭐ NOWY

**Opis:** Backup grafu Neo4j do pliku .cypher (Cypher statements)

**Co robi:**
- Eksportuje wszystkie nodes i relationships do Cypher CREATE statements
- Weryfikuje połączenie z Neo4j przed backup
- Tworzy timestamped backups w `data/backups/`
- Wspiera `--dry-run` mode (podgląd bez tworzenia backup)
- Weryfikuje że backup się powiódł

**Kiedy używać:**
- **PRZED cleanup operations** (np. cleanup_legacy_mentions.py)
- **PRZED production deployment**
- Regularnie jako część backup strategy
- Po ważnych zmianach w grafie

**Uruchomienie:**
```bash
# Dry-run (podgląd bez tworzenia backup)
python scripts/backup_neo4j.py --dry-run

# Właściwy backup (domyślna lokalizacja)
python scripts/backup_neo4j.py

# Backup do custom lokalizacji
python scripts/backup_neo4j.py --output /path/to/backup.cypher
```

**Output:**
- Default: `data/backups/neo4j-backup-YYYY-MM-DD-HH-MM.cypher`
- Custom: Ścieżka podana w `--output`

**Co NIE jest w backup:**
- ⚠️ **Embedding vectors** (zbyt duże dla text backup)
- Po restore musisz ponownie uruchomić RAG ingest aby odtworzyć embeddings

**Przywracanie backup:**
```bash
# 1. Zatrzymaj aplikację
docker-compose down

# 2. Usuń Neo4j volume (UWAGA: usuwa wszystkie dane!)
docker volume rm market-research-saas_neo4j_data

# 3. Uruchom Neo4j
docker-compose up -d neo4j

# 4. Załaduj backup
cat data/backups/neo4j-backup-2025-10-15-12-00.cypher | \
  docker exec -i market-research-saas-neo4j-1 cypher-shell \
  -u neo4j -p dev_password_change_in_prod

# 5. Re-create indexes
python scripts/init_neo4j_indexes.py

# 6. Re-create embeddings (upload dokumenty ponownie)
# POST /api/v1/rag/documents/upload
```

**Uwagi:**
- Backup NIE zawiera embedding vectors (zbyt duże)
- Wielkość backup: ~50KB per 1000 nodes (bez embeddings)
- Restore może zająć kilka minut dla dużych grafów

---

### 4. cleanup_legacy_mentions.py ⭐ NOWY

**Opis:** Usuwanie legacy data z archived feature (graph_service.py)

**Co usuwa:**
- **MENTIONS relationships** (2757 relacji = 51% wszystkich relacji)
- **Concept nodes** (20)
- **Emotion nodes** (1)
- **Persona nodes** bez `doc_id` (nie używane przez personas table)

**Co NIE usuwa (RAG nodes - INTACT):**
- ✅ Wskaznik, Obserwacja, Trend, Demografia, Lokalizacja, RAGChunk nodes
- ✅ OPISUJE, DOTYCZY, POKAZUJE_TREND, ZLOKALIZOWANY_W, POWIAZANY_Z relationships

**Kiedy używać:**
- Po potwierdzeniu że archived feature (graph_service.py) nie jest używane
- Aby oczyścić graf z legacy data
- **TYLKO jeśli masz backup!**

**Uruchomienie:**

⚠️ **WAŻNE: Zawsze najpierw zrób backup!**

```bash
# KROK 1: Backup (WYMAGANE!)
python scripts/backup_neo4j.py

# KROK 2: Dry-run (sprawdź co zostanie usunięte)
python scripts/cleanup_legacy_mentions.py --dry-run

# KROK 3: Właściwy cleanup (po potwierdzeniu że dry-run OK)
python scripts/cleanup_legacy_mentions.py
```

**Interactive Confirmation:**
Script wymaga wpisania `YES` aby kontynuować (safety check).

**Expected Results:**
```
BEFORE → AFTER
Total Nodes: 2753 → ~2728 (-25)
Total Relationships: 5453 → ~2696 (-2757)

LEGACY DATA DELETED:
MENTIONS relationships: 2757 → 0
Concept nodes: 20 → 0
Emotion nodes: 1 → 0
Unused Persona nodes: 4 → 0

RAG DATA INTACT:
Wskaznik: 150 → 150 (no change)
Obserwacja: 200 → 200 (no change)
```

**Rollback (jeśli coś poszło nie tak):**
Zobacz instrukcje w output cleanup script lub backup_neo4j.py

**Uwagi:**
- Batch delete (1000 items na raz) dla performance
- Pre + Post verification (fail fast jeśli coś nie tak)
- Detailed logging (INFO level)
- Idempotent (może być uruchomiony multiple times)

---

## 📊 Code Review Report - MENTIONS Usage

### Podsumowanie

**Status:** ✅ Bezpieczne do usunięcia

MENTIONS relationships są używane TYLKO przez archived feature `app/services/archived/graph_service.py`.

### Pliki Używające MENTIONS

1. **app/services/archived/graph_service.py** (ARCHIVED)
   - Status: Feature archived, nie używane w obecnej wersji
   - Usage: Tworzenie MENTIONS relationships w `_extract_concepts_and_emotions()`

2. **app/api/graph_analysis.py** (API Endpoints)
   - Status: Endpoints ukryte z frontend UI (AppSidebar, App.tsx)
   - Impact cleanup: Endpoints przestaną działać (ale już są ukryte)
   - Recommendation: Można pozostawić (backend-only) lub usunąć

3. **app/api/focus_groups.py** (Background Task)
   - Status: Automatyczne budowanie grafu po zakończeniu focus group (linia 166)
   - Impact cleanup: Task będzie failować (ale gracefully catchowany)
   - Recommendation: Wyłączyć automatyczne budowanie grafu (zakomentować linie 164-173)

4. **app/schemas/graph.py** (API Schemas)
   - Status: Schemas wspominają "mentions" jako przykład
   - Impact cleanup: Schemas mogą pozostać (backward compatibility)
   - Recommendation: Dodać deprecation notice

5. **tests/** (Unit Tests)
   - Status: Testy dla GraphService i MENTIONS relationships
   - Impact cleanup: Testy mogą pozostać (dokumentują legacy behavior)
   - Recommendation: Dodać skip marker lub przenieść do `tests/archived/`

### Dependency Check Results

✅ **Brak blocking dependencies**

All MENTIONS relationships follow expected pattern:
- `Persona → MENTIONS → Concept` (100% of relationships)

**Konkluzja:** Bezpieczne do usunięcia.

---

## 🚀 Workflow Setup Projektu

### Pierwsze Uruchomienie (New Developer)

```bash
# 1. Start Docker services
docker-compose up -d

# 2. Poczekaj na inicjalizację baz
sleep 10

# 3. Migracje bazy danych (preferowana metoda)
docker-compose exec api alembic upgrade head

# 4. Inicjalizuj Neo4j indeksy (WYMAGANE dla RAG!)
python scripts/init_neo4j_indexes.py

# 5. (OPCJONALNIE) Backup przed jakimikolwiek zmianami
python scripts/backup_neo4j.py

# 6. (OPCJONALNIE) Cleanup legacy data (jeśli nie jest używane)
# python scripts/cleanup_legacy_mentions.py --dry-run

# 7. Weryfikuj że wszystko działa
docker-compose ps
curl http://localhost:8000/docs  # API docs
```

### Reset Environment (Clean State)

```bash
# 1. (OPCJONALNIE) Backup jeśli chcesz zachować dane
python scripts/backup_neo4j.py

# 2. Zatrzymaj i usuń wszystko (UWAGA: usuwa dane!)
docker-compose down -v

# 3. Start od nowa
docker-compose up -d

# 4. Poczekaj na inicjalizację
sleep 10

# 5. Migracje
docker-compose exec api alembic upgrade head

# 6. Neo4j indeksy
python scripts/init_neo4j_indexes.py

# 7. (Opcjonalnie) Restore backup jeśli chcesz
# cat data/backups/neo4j-backup-YYYY-MM-DD-HH-MM.cypher | \
#   docker exec -i market-research-saas-neo4j-1 cypher-shell \
#   -u neo4j -p dev_password_change_in_prod
```

### Maintenance Workflow (Cleanup Legacy Data)

```bash
# 1. BACKUP FIRST!
python scripts/backup_neo4j.py

# 2. Dry-run (sprawdź co zostanie usunięte)
python scripts/cleanup_legacy_mentions.py --dry-run

# 3. Przejrzyj output dry-run
# - Sprawdź legacy data counts
# - Sprawdź że RAG nodes są intact

# 4. Właściwy cleanup (ONLY if dry-run OK)
python scripts/cleanup_legacy_mentions.py

# 5. Weryfikuj że cleanup się powiódł
# - Sprawdź post-cleanup summary
# - Przetestuj RAG queries: POST /api/v1/rag/ask
```

**Ostatnia aktualizacja:** 2025-10-15
**Liczba skryptów:** 4
