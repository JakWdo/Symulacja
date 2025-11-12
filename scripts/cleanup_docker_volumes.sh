#!/bin/bash
# cleanup_docker_volumes.sh - Skrypt czyszczenia lokalnych danych Docker
# Usuwa volumes Docker (Neo4j, PostgreSQL, Redis) i lokalne pliki danych
#
# ⚠️ UWAGA: Ten skrypt usuwa WSZYSTKIE dane lokalne!
# Używaj tylko w środowisku developerskim.

set -e  # Exit on error

# Kolory dla outputu
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🐳 Sight Platform - Docker Volumes Cleanup"
echo "=========================================="
echo ""
echo -e "${YELLOW}⚠️  UWAGA: Ten skrypt usuwa WSZYSTKIE lokalne dane Docker!${NC}"
echo -e "${YELLOW}⚠️  Bazy danych (PostgreSQL, Neo4j, Redis) zostaną wyczyszczone.${NC}"
echo ""

# Confirm before proceeding
read -p "Czy na pewno chcesz kontynuować? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo -e "${RED}❌ Anulowano${NC}"
    exit 1
fi

echo ""

# ============================================================================
# 1. Sprawdź czy Docker jest dostępny
# ============================================================================
echo "🔍 Sprawdzanie dostępności Docker..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker nie jest zainstalowany lub niedostępny${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose nie jest zainstalowany lub niedostępny${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker i docker-compose są dostępne${NC}"
echo ""

# Determine docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# ============================================================================
# 2. Lista aktualnych volumes
# ============================================================================
echo "📋 Aktualne Docker volumes:"
docker volume ls
echo ""

# ============================================================================
# 3. Stop i usuń kontenery z volumes
# ============================================================================
echo "🛑 Stopping i usuwanie kontenerów Docker..."

# Stop wszystkich kontenerów
$DOCKER_COMPOSE down

# Usuń kontenery wraz z volumes
$DOCKER_COMPOSE down -v

echo -e "${GREEN}✅ Kontenery zatrzymane i usunięte (wraz z volumes)${NC}"
echo ""

# ============================================================================
# 4. Usuń lokalne foldery z danymi
# ============================================================================
echo "🗑️  Usuwanie lokalnych folderów z danymi..."

# Lista folderów do usunięcia
DATA_DIRS=(
    "./data"
    "./data/neo4j"
    "./data/postgres"
    "./data/redis"
    "./postgres_data"
    "./neo4j_data"
    "./redis_data"
)

REMOVED_COUNT=0

for DIR in "${DATA_DIRS[@]}"; do
    if [ -d "$DIR" ]; then
        echo -e "${YELLOW}Usuwanie: $DIR${NC}"
        rm -rf "$DIR"
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
    fi
done

if [ $REMOVED_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ Brak lokalnych folderów z danymi do usunięcia${NC}"
else
    echo -e "${GREEN}✅ Usunięto $REMOVED_COUNT folderów z danymi${NC}"
fi

echo ""

# ============================================================================
# 5. Usuń orphan volumes (volumes bez kontenera)
# ============================================================================
echo "🧹 Czyszczenie orphan volumes..."

ORPHAN_VOLUMES=$(docker volume ls -qf dangling=true)

if [ -z "$ORPHAN_VOLUMES" ]; then
    echo -e "${GREEN}✅ Brak orphan volumes do usunięcia${NC}"
else
    echo -e "${YELLOW}Znaleziono orphan volumes:${NC}"
    echo "$ORPHAN_VOLUMES"
    docker volume rm $ORPHAN_VOLUMES
    echo -e "${GREEN}✅ Orphan volumes usunięte${NC}"
fi

echo ""

# ============================================================================
# 6. Weryfikacja .gitignore
# ============================================================================
echo "📝 Weryfikacja .gitignore..."

if grep -q "^data/" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅ data/ jest w .gitignore${NC}"
else
    echo -e "${YELLOW}⚠️  data/ nie jest w .gitignore - dodawanie...${NC}"
    echo "data/" >> .gitignore
    echo -e "${GREEN}✅ data/ dodane do .gitignore${NC}"
fi

if grep -q "postgres_data/" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅ postgres_data/ jest w .gitignore${NC}"
else
    echo -e "${YELLOW}⚠️  postgres_data/ nie jest w .gitignore - dodawanie...${NC}"
    echo "postgres_data/" >> .gitignore
    echo -e "${GREEN}✅ postgres_data/ dodane do .gitignore${NC}"
fi

if grep -q "neo4j_data/" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅ neo4j_data/ jest w .gitignore${NC}"
else
    echo -e "${YELLOW}⚠️  neo4j_data/ nie jest w .gitignore - dodawanie...${NC}"
    echo "neo4j_data/" >> .gitignore
    echo -e "${GREEN}✅ neo4j_data/ dodane do .gitignore${NC}"
fi

if grep -q "redis_data/" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅ redis_data/ jest w .gitignore${NC}"
else
    echo -e "${YELLOW}⚠️  redis_data/ nie jest w .gitignore - dodawanie...${NC}"
    echo "redis_data/" >> .gitignore
    echo -e "${GREEN}✅ redis_data/ dodane do .gitignore${NC}"
fi

echo ""

# ============================================================================
# 7. Fresh start (opcjonalne)
# ============================================================================
echo "=========================================="
echo "🎉 Cleanup zakończony!"
echo "=========================================="
echo ""
echo -e "${BLUE}💡 Następne kroki:${NC}"
echo ""
echo "1. Uruchom fresh stack Docker:"
echo "   ${DOCKER_COMPOSE} up -d"
echo ""
echo "2. Poczekaj na uruchomienie serwisów (30-60s):"
echo "   ${DOCKER_COMPOSE} ps"
echo ""
echo "3. Zastosuj migracje bazy danych:"
echo "   ${DOCKER_COMPOSE} exec api alembic upgrade head"
echo ""
echo "4. Zainicjalizuj indeksy Neo4j:"
echo "   python scripts/init_neo4j_indexes.py"
echo ""
echo "5. (Opcjonalnie) Załaduj demo data:"
echo "   python scripts/create_demo_data.py"
echo ""

echo -e "${GREEN}✅ Wszystkie lokalne dane Docker zostały wyczyszczone!${NC}"
echo ""
