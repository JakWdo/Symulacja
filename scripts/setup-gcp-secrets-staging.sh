#!/bin/bash
# ==============================================================================
# setup-gcp-secrets-staging.sh
# Bezpieczne tworzenie sekretów staging w GCP Secret Manager
# ==============================================================================

set -e  # Exit on error

PROJECT_ID=$(gcloud config get-value project)
echo "🔐 Setup GCP Secret Manager dla STAGING: $PROJECT_ID"
echo ""

# Funkcja do tworzenia/aktualizacji secretu staging
create_or_update_secret() {
    local secret_name=$1
    local secret_description=$2
    local is_optional=${3:-false}
    local default_value=${4:-""}

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 Secret: $secret_name"
    echo "   Opis: $secret_description"

    # Sprawdź czy secret już istnieje
    if gcloud secrets describe "$secret_name" &>/dev/null; then
        echo "   ⚠️  Secret już istnieje."
        read -p "   Zaktualizować nową wersją? (tak/nie) [nie]: " update
        update=${update:-nie}
        if [ "$update" != "tak" ]; then
            echo "   ⏭️  Pominięto"
            return 0
        fi
    fi

    # Jeśli optional, daj możliwość pominięcia
    if [ "$is_optional" = true ]; then
        read -p "   Pomiń? (tak/nie) [tak]: " skip
        skip=${skip:-tak}
        if [ "$skip" = "tak" ]; then
            echo "   ⏭️  Pominięto"
            return 0
        fi
    fi

    # Poproś o wartość (ukryta lub jawna w zależności od typu)
    if [ "$secret_name" = "DATABASE_URL_STAGING" ]; then
        # DATABASE_URL_STAGING budujemy z POSTGRES_PASSWORD_STAGING
        if [ -n "$POSTGRES_PASSWORD_STAGING_VALUE" ]; then
            secret_value="postgresql+asyncpg://postgres:${POSTGRES_PASSWORD_STAGING_VALUE}@/sight_db_staging?host=/cloudsql/gen-lang-client-0508446677:europe-central2:sight-staging"
            echo "   🔗 Automatycznie generuję z POSTGRES_PASSWORD_STAGING"
        else
            echo "   ❌ Najpierw ustaw POSTGRES_PASSWORD_STAGING!"
            return 1
        fi
    elif [ "$secret_name" = "SECRET_KEY_STAGING" ]; then
        # SECRET_KEY_STAGING generujemy automatycznie
        secret_value=$(openssl rand -hex 32)
        echo "   🔐 Automatycznie wygenerowano: ${secret_value:0:16}..."
    else
        # Inne sekrety - pobierz od użytkownika
        if [ -n "$default_value" ]; then
            read -sp "   Wpisz wartość [$default_value]: " secret_value
            echo ""
            secret_value=${secret_value:-$default_value}
        else
            read -sp "   Wpisz wartość: " secret_value
            echo ""
        fi
    fi

    # Walidacja - nie może być puste
    if [ -z "$secret_value" ]; then
        echo "   ❌ Wartość nie może być pusta!"
        return 1
    fi

    # Zapisz do zmiennej globalnej (dla DATABASE_URL_STAGING)
    if [ "$secret_name" = "POSTGRES_PASSWORD_STAGING" ]; then
        POSTGRES_PASSWORD_STAGING_VALUE="$secret_value"
    fi

    # Utwórz lub zaktualizuj secret
    if gcloud secrets describe "$secret_name" &>/dev/null; then
        echo "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=-
        echo "   ✅ Secret zaktualizowany!"
    else
        echo "$secret_value" | gcloud secrets create "$secret_name" \
            --data-file=- \
            --replication-policy="automatic" \
            --labels="app=sight,env=staging"
        echo "   ✅ Secret utworzony!"
    fi
}

echo "Ten script utworzy/zaktualizuje sekrety STAGING w GCP Secret Manager."
echo ""
echo "⚠️  UWAGA: Użyj INNYCH wartości niż production dla:"
echo "  - POSTGRES_PASSWORD_STAGING (inna baza niż production)"
echo "  - SECRET_KEY_STAGING (inny key niż production)"
echo ""
echo "✅ Możesz użyć TYCH SAMYCH wartości dla:"
echo "  - GOOGLE_API_KEY (ten sam Gemini API key)"
echo "  - NEO4J credentials (możesz użyć tej samej instancji, ale zalecamy osobną)"
echo "  - REDIS_URL (możesz użyć tej samej instancji Upstash)"
echo ""
read -p "Kontynuować? (tak/nie): " continue
if [ "$continue" != "tak" ]; then
    echo "Anulowano."
    exit 0
fi

# KRYTYCZNE SEKRETY - STAGING
echo ""
echo "═══════════════════════════════════════════════════"
echo "  KRYTYCZNE SEKRETY STAGING (wymagane dla Cloud Run)"
echo "═══════════════════════════════════════════════════"

create_or_update_secret "GOOGLE_API_KEY_STAGING" \
    "Google Gemini API Key (staging - może być taki sam jak production)" \
    false

create_or_update_secret "POSTGRES_PASSWORD_STAGING" \
    "PostgreSQL database password (Cloud SQL staging - MUSI BYĆ INNY niż production)" \
    false

create_or_update_secret "DATABASE_URL_STAGING" \
    "Cloud SQL staging connection string (autogenerowany z POSTGRES_PASSWORD_STAGING)" \
    false

create_or_update_secret "SECRET_KEY_STAGING" \
    "FastAPI JWT signing key staging (autogenerowany - MUSI BYĆ INNY niż production)" \
    false

create_or_update_secret "NEO4J_URI_STAGING" \
    "Neo4j staging URI (format: neo4j+s://xxxxx.databases.neo4j.io)" \
    false \
    "neo4j+s://xxxxx.databases.neo4j.io"

create_or_update_secret "NEO4J_PASSWORD_STAGING" \
    "Neo4j staging password" \
    false

create_or_update_secret "REDIS_URL_STAGING" \
    "Redis staging connection string (format: redis://default:PASSWORD@region.upstash.io:PORT)" \
    false \
    "redis://default:PASSWORD@region.upstash.io:6379"

# GRANT ACCESS DO CLOUD RUN
echo ""
echo "═══════════════════════════════════════════════════"
echo "  UPRAWNIENIA CLOUD RUN (STAGING)"
echo "═══════════════════════════════════════════════════"

SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
echo "📝 Cloud Run service account: ${SERVICE_ACCOUNT}"
echo ""

for SECRET_NAME in GOOGLE_API_KEY_STAGING NEO4J_URI_STAGING NEO4J_PASSWORD_STAGING REDIS_URL_STAGING DATABASE_URL_STAGING POSTGRES_PASSWORD_STAGING SECRET_KEY_STAGING; do
    if gcloud secrets describe "$SECRET_NAME" &>/dev/null; then
        echo "  → Granting access to: ${SECRET_NAME}"
        gcloud secrets add-iam-policy-binding "${SECRET_NAME}" \
            --member="serviceAccount:${SERVICE_ACCOUNT}" \
            --role="roles/secretmanager.secretAccessor" \
            &>/dev/null || echo "     (already has access)"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════"
echo "✅ Setup Secret Manager STAGING zakończony!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "📋 Utworzone sekrety staging:"
gcloud secrets list --filter="labels.env=staging" --format="table(name,created)"
echo ""
echo "🔒 Aby zobaczyć wartość secretu:"
echo "   gcloud secrets versions access latest --secret=\"SECRET_NAME\""
echo ""
echo "🚀 Następne kroki:"
echo "   1. Utwórz Cloud SQL staging: gcloud sql instances create sight-staging --region=europe-central2"
echo "   2. Utwórz Cloud Run staging service (automatycznie przez cloudbuild.yaml)"
echo "   3. Przetestuj deployment staging przed production"
