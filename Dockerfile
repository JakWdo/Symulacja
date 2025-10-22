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

# Default CMD - Production-ready z gunicorn
# Cloud Run używa zmiennej $PORT (dynamiczny port assignment)
# Dla local development można override w docker-compose.yml
CMD ["sh", "-c", "gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers ${GUNICORN_WORKERS:-2} --bind 0.0.0.0:${PORT:-8000} --timeout ${GUNICORN_TIMEOUT:-120} --max-requests ${GUNICORN_MAX_REQUESTS:-1000} --log-level ${LOG_LEVEL:-info}"]

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
