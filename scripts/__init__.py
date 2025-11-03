"""
Utility scripts for Sight.

Active helpers live directly in ``scripts/`` (Neo4j indeksy, walidacja konfiguracji,
backup/cleanup grafu, setup sekretów GCP).
Jednorazowe / legacy narzędzia znajdują się w ``scripts.archive``.

Nie importuj bezpośrednio – skrypty uruchamiaj jako moduły CLI, np.:

    python scripts/init_neo4j_indexes.py
    python scripts/config_validate.py --check-placeholders
"""
