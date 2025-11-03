# 📦 scripts/archive

Zarchiwizowane narzędzia, które były używane jednorazowo (backfill, eksperyment, ręczne testy) albo mają bezpieczniejsze zamienniki. Kod pozostaje dostępny do referencji/historycznych uruchomień, ale nie powinien być częścią standardowych procedur.

| Plik | Status / następca | Notatki |
| --- | --- | --- |
| `init_db.py` | Zastąpione przez `alembic upgrade head` | Tworzy tabele i włącza pgvector; zostawione tylko do wyjątkowych przypadków dev |
| `create-database-url-secret.sh` | Pokryte przez `setup-gcp-secrets.sh` | Oddzielny sekret Cloud SQL – obecnie generowany automatycznie |
| `build_test_image.sh` | Nieużywane | Legacy helper do lokalnego builda obrazu |
| `backfill_insights_v2.py` | Jednorazowy backfill | Wymaga backupu Neo4j i ostrożności |
| `backfill_sanitize_personas.py` | Jednorazowy backfill | Czyści dane person sprzed refaktoru |
| `backfill_segment_metadata.py` | Jednorazowy backfill | Uzupełnia metadane segmentów |
| `test_persona_details_performance.py` | Ręczny benchmark | Przydatne do eksperymentów wydajnościowych |

> 💡 Jeśli któryś z tych skryptów wróci do regularnego obiegu – przenieś go z powrotem do głównego katalogu `scripts/`, zaktualizuj README i dodaj test/CI krok.
