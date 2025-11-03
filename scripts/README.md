# 🛠️ Scripts – aktywne narzędzia operacyjne

Ten katalog zawiera tylko te skrypty, które są regularnie używane w bieżącej infrastrukturze. Wszystkie historyczne/razowe narzędzia zostały przeniesione do `scripts/archive/`.

| Plik | Cel | Kiedy uruchamiać |
| --- | --- | --- |
| `init_neo4j_indexes.py` | Tworzy wymagane indeksy Neo4j (vector + fulltext) | Po pierwszym uruchomieniu Neo4j, po resecie bazy lub w pipeline (docker-compose, Cloud Run job) |
| `init_neo4j_cloudrun.py` | Wrapper do uruchomienia indeksów na Cloud Run (bezpośredni driver Aura/Cloud) | Cloud Build step / Cloud Run Job (`neo4j-init`) |
| `config_validate.py` | Waliduje całą konfigurację YAML (prompty, modele, feature flags) | Przed commitem, w CI, po zmianach w `config/` |
| `backup_neo4j.py` | Eksportuje graf Neo4j do pliku `.cypher` (pełen snapshot) | Przed wykonywaniem cleanupów lub migracji danych |
| `cleanup_legacy_mentions.py` | Bezpieczne czyszczenie starych relacji/person w grafie (wymaga backupu) | Akcje utrzymaniowe po zmianach schematu / danych |
| `setup-gcp-secrets.sh` | Tworzy/aktualizuje sekrety w Google Secret Managerze i nadaje uprawnienia | Nowe środowisko GCP, rotacja sekretów |

### Wzorzec uruchamiania

```bash
# Przykład: inicjalizacja indeksów Neo4j
python scripts/init_neo4j_indexes.py

# Walidacja konfiguracji przed commitem
python scripts/config_validate.py --check-placeholders
```

Skrypty są idempotentne – można je uruchamiać wielokrotnie. Przy błędach wypisują klarowne komunikaty i kończą się statusem ≠ 0.

### Archiwum

- Narzędzia jednorazowe (backfille, stare init-y, benchmarki) → `scripts/archive/`
- Lista i opis: zobacz `scripts/archive/README.md`
