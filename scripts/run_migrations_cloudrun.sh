#!/bin/bash
# Migration script for Cloud Run Jobs with detailed logging

set -e  # Exit on error
set -x  # Print commands (verbose)

echo "=================================================="
echo "🔄 Starting database migrations..."
echo "=================================================="

echo "Environment variables:"
echo "  DATABASE_URL: ${DATABASE_URL:0:30}... (masked)"
echo "  PYTHONPATH: $PYTHONPATH"
echo "  PWD: $(pwd)"

echo ""
echo "Checking alembic installation..."
alembic --version || {
    echo "❌ ERROR: Alembic not found!"
    exit 1
}

echo ""
echo "Checking database connection..."
python3 -c "
import os
from sqlalchemy import create_engine, text

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('❌ ERROR: DATABASE_URL not set!')
    exit(1)

# Convert to sync URL for connection test
sync_url = db_url.replace('postgresql+asyncpg://', 'postgresql+psycopg2://')
print(f'✅ DATABASE_URL set: {sync_url[:30]}...')

try:
    engine = create_engine(sync_url, pool_pre_ping=True)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        version = result.scalar()
        print(f'✅ Database connection successful!')
        print(f'   PostgreSQL version: {version[:50]}...')
except Exception as e:
    print(f'❌ Database connection FAILED: {e}')
    exit(1)
" || exit 1

echo ""
echo "Current migration revision:"
alembic current || echo "No revision applied yet"

echo ""
echo "Running migrations..."
alembic upgrade head

echo ""
echo "Migration completed successfully!"
alembic current

echo "=================================================="
echo "✅ All migrations completed!"
echo "=================================================="
