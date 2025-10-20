#!/bin/bash
# ==============================================================================
# setup-gcp-secrets.sh
# Bezpieczne tworzenie sekretów w GCP Secret Manager
# ==============================================================================

set -e  # Exit on error

PROJECT_ID=$(gcloud config get-value project)
echo "🔐 Setup GCP Secret Manager dla projektu: $PROJECT_ID"
echo ""

# Funkcja do tworzenia secretu
create_secret() {
    local secret_name=$1
    local secret_description=$2
    local is_optional=${3:-false}

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 Secret: $secret_name"
    echo "   Opis: $secret_description"

    # Sprawdź czy secret już istnieje
    if gcloud secrets describe "$secret_name" &>/dev/null; then
        echo "   ⚠️  Secret już istnieje. Pomijam."
        return 0
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

    # Poproś o wartość (ukryta)
    read -sp "   Wpisz wartość: " secret_value
    echo ""

    # Walidacja - nie może być puste
    if [ -z "$secret_value" ]; then
        echo "   ❌ Wartość nie może być pusta!"
        return 1
    fi

    # Utwórz secret
    echo "$secret_value" | gcloud secrets create "$secret_name" \
        --data-file=- \
        --replication-policy="automatic" \
        --labels="app=sight,env=demo"

    echo "   ✅ Secret utworzony!"
}

echo "Ten script utworzy sekrety w GCP Secret Manager."
echo "Wartości będą pobrane z Twojego .env file lub podane ręcznie."
echo ""
read -p "Kontynuować? (tak/nie): " continue
if [ "$continue" != "tak" ]; then
    echo "Anulowano."
    exit 0
fi

# KRYTYCZNE SEKRETY
echo ""
echo "═══════════════════════════════════════════════════"
echo "  KRYTYCZNE SEKRETY (wymagane)"
echo "═══════════════════════════════════════════════════"

create_secret "GOOGLE_API_KEY" \
    "Google Gemini API Key (AI generowanie person i grup fokusowych)" \
    false

create_secret "SECRET_KEY" \
    "FastAPI JWT signing key (dla autentykacji użytkowników)" \
    false

create_secret "POSTGRES_PASSWORD" \
    "PostgreSQL database password (zostanie użyte przy Cloud SQL setup)" \
    false

# OPCJONALNE SEKRETY
echo ""
echo "═══════════════════════════════════════════════════"
echo "  OPCJONALNE SEKRETY (można pominąć)"
echo "═══════════════════════════════════════════════════"

create_secret "OPENAI_API_KEY" \
    "OpenAI API Key (opcjonalny fallback provider)" \
    true

create_secret "ANTHROPIC_API_KEY" \
    "Anthropic Claude API Key (opcjonalny fallback provider)" \
    true

echo ""
echo "═══════════════════════════════════════════════════"
echo "✅ Setup Secret Manager zakończony!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "📋 Utworzone sekrety:"
gcloud secrets list --filter="labels.app=sight" --format="table(name,created)"
echo ""
echo "💡 Neo4j i Redis sekrety utworzymy po setupie tych serwisów (Faza 2)"
echo ""
echo "🔒 Aby zobaczyć wartość secretu:"
echo "   gcloud secrets versions access latest --secret=\"SECRET_NAME\""
echo ""
echo "🗑️  Aby usunąć secret:"
echo "   gcloud secrets delete SECRET_NAME"
