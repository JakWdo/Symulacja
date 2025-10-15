#!/bin/sh
set -e

echo "=== Docker Entrypoint: Market Research SaaS ==="

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h postgres -p 5432 -U market_research -d market_research_db -q; do
  echo "   PostgreSQL is unavailable - sleeping 2s"
  sleep 2
done
echo "✓ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
until redis-cli -h redis ping 2>/dev/null | grep -q PONG; do
  echo "   Redis is unavailable - sleeping 2s"
  sleep 2
done
echo "✓ Redis is ready!"

# Wait for Neo4j to be ready
# Neo4j healthcheck może przejść zanim APOC/GDS są gotowe - dodatkowy check dla safety
echo "⏳ Waiting for Neo4j..."
max_neo4j_retries=30  # 30 * 2s = 60s max wait
neo4j_retry_count=0
until wget --spider --quiet --tries=1 --timeout=5 http://neo4j:7474 2>/dev/null; do
  neo4j_retry_count=$((neo4j_retry_count + 1))
  if [ $neo4j_retry_count -ge $max_neo4j_retries ]; then
    echo "⚠️  Neo4j nie odpowiada po ${max_neo4j_retries} próbach - kontynuuję (RAG services mają własny retry)"
    break
  fi
  echo "   Neo4j is unavailable - sleeping 2s (attempt $neo4j_retry_count/$max_neo4j_retries)"
  sleep 2
done
echo "✓ Neo4j is ready!"

# Run database migrations using Alembic
echo "🔄 Running database migrations..."
alembic upgrade head
echo "✓ Database migrations completed!"

# Initialize Neo4j indexes (vector + fulltext for RAG)
# WAŻNE: Script jest idempotentny (sprawdza IF NOT EXISTS)
# Jeśli fail → loguje błąd, ale NIE przerywa startu (RAG services mają retry)
echo "🔄 Initializing Neo4j indexes..."
if python scripts/init_neo4j_indexes.py; then
  echo "✓ Neo4j indexes initialized!"
else
  echo "⚠️  Neo4j indexes initialization failed (non-fatal - RAG services will retry)"
  echo "   Check logs: docker-compose logs api"
fi

# Start the application
echo "🚀 Starting application..."
exec "$@"