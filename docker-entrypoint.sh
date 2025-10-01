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

# Run database migrations using Alembic
echo "🔄 Running database migrations..."
alembic upgrade head
echo "✓ Database migrations completed!"

# Start the application
echo "🚀 Starting application..."
exec "$@"