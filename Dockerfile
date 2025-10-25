# ==============================================================================
# STAGE 1: BUILDER - Instalacja dependencies z build tools
# ==============================================================================
FROM python:3.11-slim AS builder

# Ustaw build argument dla target environment (development/production)
ARG TARGET=development

WORKDIR /app

# Zainstaluj build dependencies (gcc, g++ potrzebne dla kompilacji niektórych Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Kopiuj tylko requirements.txt NAJPIERW (dla lepszego layer caching)
# Jeśli requirements.txt się nie zmieni, ta warstwa zostanie użyta z cache
COPY requirements.txt .

# Zainstaluj Python dependencies
# --no-cache-dir: Nie cache pip downloads (zmniejsza rozmiar image)
# -r requirements.txt: Install z pliku
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download reranker model (~100MB) to eliminate Cloud Run cold start delay.
# Jeżeli pobranie się nie powiedzie (np. chwilowy brak sieci), kontynuuj build
# i zaloguj ostrzeżenie – aplikacja poradzi sobie bez rerankera.
RUN python - <<'PY'
import sys

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

try:
    from sentence_transformers import CrossEncoder

    print(f"📥 Pre-downloading reranker model: {MODEL_NAME}")
    CrossEncoder(MODEL_NAME)
    print("✅ Reranker model downloaded successfully.")
except Exception as exc:
    print(
        f"⚠️  Warning: Failed to pre-download reranker model '{MODEL_NAME}'. "
        "The application will continue without a pre-bundled model.",
        file=sys.stderr,
    )
    print(f"   Details: {exc}", file=sys.stderr)
PY

# ==============================================================================
# STAGE 2: RUNTIME - Finalny lekki image
# ==============================================================================
FROM python:3.11-slim AS runtime

# Ustaw build argument dla target environment
ARG TARGET=development
ENV TARGET=${TARGET}

WORKDIR /app

# Ustaw PYTHONPATH aby Python widział moduł 'app'
ENV PYTHONPATH=/app

# Zainstaluj TYLKO runtime dependencies (bez gcc, g++)
# postgresql-client: Dla healthchecks i pg_isready w entrypoint
# redis-tools: Dla healthchecks w entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    redis-tools \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Kopiuj zainstalowane Python packages z builder stage
# To pozwala uniknąć instalacji gcc, g++ w runtime image
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Kopiuj kod aplikacji
# Dzięki .dockerignore, nie skopiujemy __pycache__, venv, node_modules, etc.
COPY . .

# Kopiuj i ustaw entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Stwórz non-root user dla bezpieczeństwa
# UID 1000 to standardowy pierwszy user na większości systemów Linux
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Stwórz katalog dla static files (avatary użytkowników)
RUN mkdir -p /app/static/avatars && chown -R appuser:appuser /app/static

# Expose port FastAPI
EXPOSE 8000

# Użyj entrypoint script (czeka na Postgres/Redis, uruchamia migracje)
ENTRYPOINT ["docker-entrypoint.sh"]

# Default CMD zależy od TARGET environment
# Development: uvicorn z --reload (hot reload przy zmianach kodu)
# Production: gunicorn z multiple workers (będzie nadpisane w docker-compose.prod.yml)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Switch na non-root user OSTATNI krok
USER appuser

# ==============================================================================
# DLACZEGO MULTI-STAGE BUILD?
# ==============================================================================
# 1. ROZMIAR: Finalny image ~40-50% mniejszy (brak gcc, g++, build artifacts)
# 2. BEZPIECZEŃSTWO: Mniej attack surface (brak compilerów w production)
# 3. WYDAJNOŚĆ: Lepszy layer caching (dependencies vs kod osobno)
# 4. CZYSTOŚĆ: Runtime environment ma tylko to co potrzebne do uruchomienia
#
# PRZYKŁAD ROZMIARÓW:
# - Single-stage: ~800-900 MB
# - Multi-stage: ~400-500 MB
# ==============================================================================
