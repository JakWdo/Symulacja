#!/bin/bash
# ==============================================================================
# setup-gcp-secrets.sh
# Bezpieczne tworzenie sekretów w GCP Secret Manager dla Cloud Run deployment
# ==============================================================================

set -e  # Exit on error

PROJECT_ID=$(gcloud config get-value project)
echo "🔐 Setup GCP Secret Manager dla projektu: $PROJECT_ID"
echo ""

# Funkcja do tworzenia/aktualizacji secretu
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
    if [ "$secret_name" = "DATABASE_URL_CLOUD" ]; then
        # DATABASE_URL_CLOUD budujemy z POSTGRES_PASSWORD
        if [ -n "$POSTGRES_PASSWORD_VALUE" ]; then
            secret_value="postgresql+asyncpg://postgres:${POSTGRES_PASSWORD_VALUE}@/sight_db?host=/cloudsql/gen-lang-client-0508446677:europe-central2:sight"
            echo "   🔗 Automatycznie generuję z POSTGRES_PASSWORD"
        else
            echo "   ❌ Najpierw ustaw POSTGRES_PASSWORD!"
            return 1
        fi
    elif [ "$secret_name" = "SECRET_KEY" ]; then
        # SECRET_KEY generujemy automatycznie
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

    # Zapisz do zmiennej globalnej (dla DATABASE_URL_CLOUD)
    if [ "$secret_name" = "POSTGRES_PASSWORD" ]; then
        POSTGRES_PASSWORD_VALUE="$secret_value"
    fi

    # Utwórz lub zaktualizuj secret
    if gcloud secrets describe "$secret_name" &>/dev/null; then
        echo "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=-
        echo "   ✅ Secret zaktualizowany!"
    else
        echo "$secret_value" | gcloud secrets create "$secret_name" \
            --data-file=- \
            --replication-policy="automatic" \
            --labels="app=sight,env=production"
        echo "   ✅ Secret utworzony!"
    fi
}

echo "Ten script utworzy/zaktualizuje sekrety w GCP Secret Manager."
echo "Potrzebne wartości:"
echo "  - Google Gemini API Key (https://aistudio.google.com/app/apikey)"
echo "  - Neo4j AuraDB credentials (https://console.neo4j.io/)"
echo "  - Upstash Redis URL (https://console.upstash.com/)"
echo "  - PostgreSQL password dla Cloud SQL"
echo ""
read -p "Kontynuować? (tak/nie): " continue
if [ "$continue" != "tak" ]; then
    echo "Anulowano."
    exit 0
fi

# KRYTYCZNE SEKRETY
echo ""
echo "═══════════════════════════════════════════════════"
echo "  KRYTYCZNE SEKRETY (wymagane dla Cloud Run)"
echo "═══════════════════════════════════════════════════"

create_or_update_secret "GOOGLE_API_KEY" \
    "Google Gemini API Key (AI generowanie person i grup fokusowych)" \
    false

create_or_update_secret "POSTGRES_PASSWORD" \
    "PostgreSQL database password (Cloud SQL)" \
    false

create_or_update_secret "DATABASE_URL_CLOUD" \
    "Cloud SQL connection string (autogenerowany z POSTGRES_PASSWORD)" \
    false

create_or_update_secret "SECRET_KEY" \
    "FastAPI JWT signing key (autogenerowany)" \
    false

create_or_update_secret "NEO4J_URI" \
    "Neo4j AuraDB connection URI (format: neo4j+s://xxxxx.databases.neo4j.io)" \
    false \
    "neo4j+s://xxxxx.databases.neo4j.io"

create_or_update_secret "NEO4J_PASSWORD" \
    "Neo4j AuraDB password" \
    false

create_or_update_secret "REDIS_URL" \
    "Upstash Redis connection string (format: redis://default:PASSWORD@region.upstash.io:PORT)" \
    false \
    "redis://default:PASSWORD@region.upstash.io:6379"

# OPCJONALNE SEKRETY
echo ""
echo "═══════════════════════════════════════════════════"
echo "  OPCJONALNE SEKRETY (można pominąć)"
echo "═══════════════════════════════════════════════════"

create_or_update_secret "OPENAI_API_KEY" \
    "OpenAI API Key (opcjonalny fallback provider)" \
    true

create_or_update_secret "ANTHROPIC_API_KEY" \
    "Anthropic Claude API Key (opcjonalny fallback provider)" \
    true

# GRANT ACCESS DO CLOUD RUN
echo ""
echo "═══════════════════════════════════════════════════"
echo "  UPRAWNIENIA CLOUD RUN"
echo "═══════════════════════════════════════════════════"

SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
echo "📝 Cloud Run service account: ${SERVICE_ACCOUNT}"
echo ""

for SECRET_NAME in GOOGLE_API_KEY NEO4J_URI NEO4J_PASSWORD REDIS_URL DATABASE_URL_CLOUD POSTGRES_PASSWORD SECRET_KEY; do
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
echo "✅ Setup Secret Manager zakończony!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "📋 Utworzone sekrety:"
gcloud secrets list --filter="labels.app=sight" --format="table(name,created)"
echo ""
echo "🔒 Aby zobaczyć wartość secretu:"
echo "   gcloud secrets versions access latest --secret=\"SECRET_NAME\""
echo ""
echo "🗑️  Aby usunąć secret:"
echo "   gcloud secrets delete SECRET_NAME"
echo ""
echo "🚀 Następne kroki:"
echo "   1. Sprawdź Cloud SQL: gcloud sql instances describe sight --region=europe-central2"
echo "   2. Push do GitHub: git push origin cleanup/dead-code-removal"
echo "   3. Monitoruj build: gcloud builds list --limit=1"
