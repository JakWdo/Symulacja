#!/bin/bash
# ==============================================================================
# test-deployment-pipeline.sh
# Skrypt do testowania całego pipeline deployment (staging + production)
# ==============================================================================

set -e  # Exit on error

PROJECT_ID="gen-lang-client-0508446677"
REGION="europe-central2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_header "🧪 Sight Deployment Pipeline Test"

echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# ==============================================================================
# 1. Sprawdź wymagania wstępne
# ==============================================================================
print_header "1/7: Sprawdzanie wymagań wstępnych"

# Check gcloud authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    print_error "Nie jesteś zalogowany do gcloud"
    echo "Uruchom: gcloud auth login"
    exit 1
fi
print_success "gcloud authentication OK"

# Check project
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    print_warning "Obecny projekt: $CURRENT_PROJECT"
    echo "Zmieniam na: $PROJECT_ID"
    gcloud config set project $PROJECT_ID
fi
print_success "GCP project: $PROJECT_ID"

# ==============================================================================
# 2. Sprawdź sekrety
# ==============================================================================
print_header "2/7: Sprawdzanie sekretów GCP Secret Manager"

REQUIRED_SECRETS_PROD=(
    "GOOGLE_API_KEY"
    "DATABASE_URL_CLOUD"
    "SECRET_KEY"
    "NEO4J_URI"
    "NEO4J_PASSWORD"
    "REDIS_URL"
    "POSTGRES_PASSWORD"
)

REQUIRED_SECRETS_STAGING=(
    "GOOGLE_API_KEY_STAGING"
    "DATABASE_URL_STAGING"
    "SECRET_KEY_STAGING"
    "NEO4J_URI_STAGING"
    "NEO4J_PASSWORD_STAGING"
    "REDIS_URL_STAGING"
    "POSTGRES_PASSWORD_STAGING"
)

echo "Sprawdzanie sekretów PRODUCTION:"
PROD_SECRETS_OK=true
for SECRET in "${REQUIRED_SECRETS_PROD[@]}"; do
    if gcloud secrets describe "$SECRET" &>/dev/null; then
        print_success "  $SECRET"
    else
        print_error "  $SECRET - BRAK"
        PROD_SECRETS_OK=false
    fi
done

echo ""
echo "Sprawdzanie sekretów STAGING:"
STAGING_SECRETS_OK=true
for SECRET in "${REQUIRED_SECRETS_STAGING[@]}"; do
    if gcloud secrets describe "$SECRET" &>/dev/null; then
        print_success "  $SECRET"
    else
        print_error "  $SECRET - BRAK"
        STAGING_SECRETS_OK=false
    fi
done

if [ "$PROD_SECRETS_OK" = false ] || [ "$STAGING_SECRETS_OK" = false ]; then
    echo ""
    print_error "Brakujące sekrety!"
    echo ""
    echo "Uruchom:"
    echo "  ./scripts/setup-gcp-secrets.sh          # Production secrets"
    echo "  ./scripts/setup-gcp-secrets-staging.sh  # Staging secrets"
    exit 1
fi

print_success "Wszystkie sekrety skonfigurowane"

# ==============================================================================
# 3. Sprawdź Cloud SQL instances
# ==============================================================================
print_header "3/7: Sprawdzanie Cloud SQL instances"

# Production database
if gcloud sql instances describe sight --region=$REGION &>/dev/null; then
    PROD_DB_STATUS=$(gcloud sql instances describe sight --region=$REGION --format="value(state)")
    if [ "$PROD_DB_STATUS" = "RUNNABLE" ]; then
        print_success "Production DB (sight): RUNNABLE"
    else
        print_warning "Production DB (sight): $PROD_DB_STATUS"
    fi
else
    print_error "Production DB (sight): BRAK"
    echo ""
    echo "Utwórz instancję:"
    echo "  gcloud sql instances create sight --database-version=POSTGRES_15 --tier=db-custom-2-7680 --region=$REGION"
    exit 1
fi

# Staging database
if gcloud sql instances describe sight-staging --region=$REGION &>/dev/null; then
    STAGING_DB_STATUS=$(gcloud sql instances describe sight-staging --region=$REGION --format="value(state)")
    if [ "$STAGING_DB_STATUS" = "RUNNABLE" ]; then
        print_success "Staging DB (sight-staging): RUNNABLE"
    else
        print_warning "Staging DB (sight-staging): $STAGING_DB_STATUS"
    fi
else
    print_warning "Staging DB (sight-staging): BRAK (zostanie utworzona automatycznie)"
    echo ""
    echo "Opcjonalnie utwórz manualnie:"
    echo "  gcloud sql instances create sight-staging --database-version=POSTGRES_15 --tier=db-custom-1-3840 --region=$REGION"
fi

# ==============================================================================
# 4. Sprawdź Cloud Run services
# ==============================================================================
print_header "4/7: Sprawdzanie Cloud Run services"

# Production service
if gcloud run services describe sight --region=$REGION &>/dev/null; then
    PROD_URL=$(gcloud run services describe sight --region=$REGION --format="value(status.url)")
    print_success "Production service (sight): $PROD_URL"

    # Test health endpoint
    echo "  Testing /health endpoint..."
    HEALTH_STATUS=$(curl -f -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$PROD_URL/health" || echo "FAIL")
    if [ "$HEALTH_STATUS" = "200" ]; then
        print_success "  Health check: OK (200)"
    else
        print_warning "  Health check: $HEALTH_STATUS"
    fi
else
    print_warning "Production service (sight): BRAK (zostanie utworzona przy pierwszym deployment)"
fi

# Staging service
if gcloud run services describe sight-staging --region=$REGION &>/dev/null; then
    STAGING_URL=$(gcloud run services describe sight-staging --region=$REGION --format="value(status.url)")
    print_success "Staging service (sight-staging): $STAGING_URL"

    # Test health endpoint
    echo "  Testing /health endpoint..."
    HEALTH_STATUS=$(curl -f -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$STAGING_URL/health" || echo "FAIL")
    if [ "$HEALTH_STATUS" = "200" ]; then
        print_success "  Health check: OK (200)"
    else
        print_warning "  Health check: $HEALTH_STATUS"
    fi
else
    print_warning "Staging service (sight-staging): BRAK (zostanie utworzona przy pierwszym deployment)"
fi

# ==============================================================================
# 5. Sprawdź Cloud Build configuration
# ==============================================================================
print_header "5/7: Sprawdzanie Cloud Build configuration"

if [ -f "cloudbuild.yaml" ]; then
    print_success "cloudbuild.yaml exists"

    # Check for key stages
    if grep -q "deploy-staging" cloudbuild.yaml; then
        print_success "  Stage: deploy-staging ✓"
    else
        print_error "  Stage: deploy-staging - BRAK"
    fi

    if grep -q "smoke-tests-staging" cloudbuild.yaml; then
        print_success "  Stage: smoke-tests-staging ✓"
    else
        print_error "  Stage: smoke-tests-staging - BRAK"
    fi

    if grep -q "deploy-production" cloudbuild.yaml; then
        print_success "  Stage: deploy-production ✓"
    else
        print_error "  Stage: deploy-production - BRAK"
    fi

    if grep -q "traffic-promotion" cloudbuild.yaml; then
        print_success "  Stage: traffic-promotion ✓"
    else
        print_error "  Stage: traffic-promotion - BRAK"
    fi

    if grep -q "auto-rollback" cloudbuild.yaml; then
        print_success "  Stage: auto-rollback ✓"
    else
        print_error "  Stage: auto-rollback - BRAK"
    fi
else
    print_error "cloudbuild.yaml - BRAK"
    exit 1
fi

# ==============================================================================
# 6. Sprawdź recent builds
# ==============================================================================
print_header "6/7: Ostatnie Cloud Builds"

echo "5 ostatnich buildów:"
gcloud builds list --limit=5 --format="table(id,status,createTime,source.repoSource.branchName)"

# ==============================================================================
# 7. Sprawdź traffic distribution
# ==============================================================================
print_header "7/7: Traffic Distribution (Production)"

if gcloud run services describe sight --region=$REGION &>/dev/null; then
    echo "Obecna dystrybucja traffic:"
    gcloud run services describe sight --region=$REGION --format="table(status.traffic.revisionName,status.traffic.percent)"

    echo ""
    echo "Lista rewizji (ostatnie 5):"
    gcloud run revisions list --service=sight --region=$REGION --limit=5 --format="table(metadata.name,status.conditions[0].status,metadata.creationTimestamp)"
else
    print_warning "Production service nie istnieje jeszcze"
fi

# ==============================================================================
# Podsumowanie
# ==============================================================================
print_header "📋 Podsumowanie"

echo ""
echo "Status gotowości do deployment:"
echo ""

if [ "$PROD_SECRETS_OK" = true ]; then
    print_success "Production secrets: OK"
else
    print_error "Production secrets: BRAK"
fi

if [ "$STAGING_SECRETS_OK" = true ]; then
    print_success "Staging secrets: OK"
else
    print_error "Staging secrets: BRAK"
fi

if gcloud sql instances describe sight --region=$REGION &>/dev/null; then
    print_success "Production database: OK"
else
    print_error "Production database: BRAK"
fi

if [ -f "cloudbuild.yaml" ]; then
    print_success "Cloud Build config: OK"
else
    print_error "Cloud Build config: BRAK"
fi

echo ""
print_header "🚀 Następne kroki"

echo ""
echo "Aby rozpocząć deployment:"
echo ""
echo "1. Manual trigger (submit build lokalnie):"
echo "   gcloud builds submit --config=cloudbuild.yaml --region=$REGION"
echo ""
echo "2. Automatyczny trigger (push do GitHub):"
echo "   git add ."
echo "   git commit -m \"feat: deploy changes\""
echo "   git push origin main"
echo ""
echo "3. Monitoruj build:"
echo "   gcloud builds list --limit=1 --ongoing"
echo "   gcloud builds log \$(gcloud builds list --limit=1 --format=\"value(id)\") --stream"
echo ""
echo "4. Po deployment, sprawdź:"
echo "   curl https://sight-staging-193742683473.europe-central2.run.app/health"
echo "   curl https://sight-193742683473.europe-central2.run.app/health"
echo ""

print_header "✅ Test zakończony"
