#!/bin/sh
set -e

printf '=== Docker Entrypoint: Sight ===\n'

# ──────────────────────────────────────────────────────────────────────────────
# Domyślne konfiguracje – można nadpisać zmiennymi środowiskowymi
# ──────────────────────────────────────────────────────────────────────────────
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-sight}
POSTGRES_DB=${POSTGRES_DB:-sight_db}

REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}

NEO4J_HOST=${NEO4J_HOST:-neo4j}
NEO4J_HTTP_PORT=${NEO4J_HTTP_PORT:-7474}

WAIT_FOR_POSTGRES=${WAIT_FOR_POSTGRES:-true}
WAIT_FOR_REDIS=${WAIT_FOR_REDIS:-false}
WAIT_FOR_NEO4J=${WAIT_FOR_NEO4J:-false}

WAIT_DELAY_SECONDS=${WAIT_DELAY_SECONDS:-2}
WAIT_MAX_ATTEMPTS=${WAIT_MAX_ATTEMPTS:-30}
WAIT_NEO4J_ATTEMPTS=${WAIT_NEO4J_ATTEMPTS:-40}
WAIT_NEO4J_DELAY=${WAIT_NEO4J_DELAY:-3}

BOOTSTRAP_COMMAND=${BOOTSTRAP_COMMAND:-}
BOOTSTRAP_WARNINGS=""

is_true() {
  case "$(echo "$1" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|y|on) return 0 ;;
    *) return 1 ;;
  esac
}

log_wait_progress() {
  service=$1
  attempt=$2
  max=$3
  if [ "$attempt" -le 3 ] || [ $((attempt % 5)) -eq 0 ]; then
    printf '   … wciąż czekam na %s (próba %d/%d)\n' "$service" "$attempt" "$max"
  fi
}

wait_for() {
  service=$1
  check_command=$2
  max_attempts=${3:-$WAIT_MAX_ATTEMPTS}
  delay=${4:-$WAIT_DELAY_SECONDS}
  attempt=1

  printf '⏳ Czekam na %s…\n' "$service"
  until eval "$check_command" >/dev/null 2>&1; do
    if [ "$attempt" -ge "$max_attempts" ]; then
      total_seconds=$((max_attempts * delay))
      printf '⚠️  %s nie odpowiedział po %d próbach (~%ds). Kontynuuję start.\n' \
        "$service" "$max_attempts" "$total_seconds"
      BOOTSTRAP_WARNINGS="${BOOTSTRAP_WARNINGS}\n- ${service}: brak odpowiedzi po ${max_attempts} próbach (~${total_seconds}s)"
      return 0
    fi

    log_wait_progress "$service" "$attempt" "$max_attempts"
    attempt=$((attempt + 1))
    sleep "$delay"
  done

  if [ "$attempt" -gt 1 ]; then
    printf '✓ %s gotowy (po %d próbach).\n' "$service" "$attempt"
  else
    printf '✓ %s gotowy.\n' "$service"
  fi
  return 0
}

# ──────────────────────────────────────────────────────────────────────────────
# Oczekiwanie na zależności (opcjonalne)
# ──────────────────────────────────────────────────────────────────────────────
if is_true "$WAIT_FOR_POSTGRES"; then
  wait_for "PostgreSQL" \
    "pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -q"
else
  printf '⏭  Pomijam oczekiwanie na PostgreSQL (WAIT_FOR_POSTGRES=false).\n'
fi

if is_true "$WAIT_FOR_REDIS"; then
  wait_for "Redis" \
    "redis-cli -h $REDIS_HOST -p $REDIS_PORT ping | grep -q PONG"
else
  printf '⏭  Pomijam oczekiwanie na Redis (WAIT_FOR_REDIS=false).\n'
fi

if is_true "$WAIT_FOR_NEO4J"; then
  wait_for "Neo4j" \
    "wget --spider --quiet --tries=1 --timeout=3 http://$NEO4J_HOST:$NEO4J_HTTP_PORT" \
    "$WAIT_NEO4J_ATTEMPTS" \
    "$WAIT_NEO4J_DELAY"
else
  printf '⏭  Pomijam oczekiwanie na Neo4j (WAIT_FOR_NEO4J=false).\n'
fi

# ──────────────────────────────────────────────────────────────────────────────
# Komenda bootstrap (np. migracje) – uruchamiana opcjonalnie przed CMD
# ──────────────────────────────────────────────────────────────────────────────
if [ -n "$BOOTSTRAP_COMMAND" ]; then
  printf '▶️  Wykonuję polecenie bootstrap: %s\n' "$BOOTSTRAP_COMMAND"
  sh -c "$BOOTSTRAP_COMMAND"
fi

if [ -n "$BOOTSTRAP_WARNINGS" ]; then
  printf '⚠️  Ostrzeżenia przy starcie:%b\n' "$BOOTSTRAP_WARNINGS"
fi

# ──────────────────────────────────────────────────────────────────────────────
# Start docelowego procesu
# ──────────────────────────────────────────────────────────────────────────────
printf '🚀 Uruchamiam proces: %s\n' "$*"
exec "$@"
