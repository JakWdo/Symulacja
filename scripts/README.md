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

**Ostatnia aktualizacja:** 2025-10-14
**Liczba skryptów:** 2
