FROM neo4j:5.23

# Neo4j automatycznie pobiera kompatybilne wersje pluginów z NEO4J_PLUGINS
# Nie ma potrzeby ręcznego ściągania - unikamy konfliktów wersji

ENV NEO4J_PLUGINS='["apoc","graph-data-science"]' \
    NEO4J_apoc_export_file_enabled=true \
    NEO4J_apoc_import_file_enabled=true \
    NEO4J_dbms_security_allow__csv__import__from__file__urls=true \
    NEO4J_server_config_strict__validation_enabled=false \
    NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.*
