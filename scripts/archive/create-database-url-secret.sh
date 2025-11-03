#!/bin/bash
# ==============================================================================
# create-database-url-secret.sh
# Tworzy DATABASE_URL_CLOUD secret dla Cloud Run
# ==============================================================================

set -e

echo "🔐 Tworzenie DATABASE_URL_CLOUD secret..."
echo ""

# Pobierz hasło z Secret Manager
POSTGRES_PASSWORD=$(gcloud secrets versions access latest --secret="POSTGRES_PASSWORD")

# Utwórz connection string dla Cloud SQL Proxy
# Format: postgresql+asyncpg://user:password@//cloudsql/PROJECT:REGION:INSTANCE/DATABASE
CONNECTION_STRING="postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@//cloudsql/gen-lang-client-0508446677:europe-central2:sight/sight_db"

# Zapisz jako secret
echo "$CONNECTION_STRING" | gcloud secrets create DATABASE_URL_CLOUD \
  --data-file=- \
  --replication-policy="automatic"

echo ""
echo "✅ DATABASE_URL_CLOUD secret utworzony!"
echo ""
echo "📋 Format connection string (Cloud SQL Proxy):"
echo "   postgresql+asyncpg://postgres:PASSWORD@//cloudsql/PROJECT:REGION:INSTANCE/DATABASE"
echo ""
echo "💡 Cloud Run użyje tego secretu do łączenia z Cloud SQL"
