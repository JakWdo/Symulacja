#!/bin/bash

# Market Research SaaS - Startup Script
# Uruchamia całą aplikację (backend + frontend + bazy danych)

set -e

echo "🚀 Market Research SaaS - Startup"
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Brak pliku .env!"
    echo "Uruchom: cp .env.example .env"
    echo "Następnie edytuj .env i dodaj GOOGLE_API_KEY"
    exit 1
fi

# Check if GOOGLE_API_KEY is set
if ! grep -q "GOOGLE_API_KEY=AIza" .env 2>/dev/null; then
    echo "⚠️  UWAGA: GOOGLE_API_KEY może nie być skonfigurowany w .env"
    echo "Zdobądź klucz z: https://ai.google.dev/gemini-api/docs/api-key"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker nie jest uruchomiony!"
    echo "Uruchom Docker Desktop i spróbuj ponownie."
    exit 1
fi

echo ""
echo "📦 Budowanie i uruchamianie kontenerów..."
echo ""

# Build and start all services
docker compose up -d --build

echo ""
echo "⏳ Czekanie na inicjalizację baz danych..."
sleep 10

# Check if database is ready
echo "🔍 Sprawdzanie statusu serwisów..."
docker compose ps

echo ""
echo "✅ Aplikacja uruchomiona!"
echo ""
echo "🌐 Frontend UI:  http://localhost:5173"
echo "🔧 Backend API:  http://localhost:8000"
echo "📚 API Docs:     http://localhost:8000/docs"
echo "📊 Neo4j:        http://localhost:7474 (neo4j/dev_password_change_in_prod)"
echo ""
echo "📋 Użyteczne komendy:"
echo "  docker compose logs -f          # Logi wszystkich serwisów"
echo "  docker compose logs -f frontend # Logi tylko frontend"
echo "  docker compose logs -f api      # Logi tylko backend"
echo "  docker compose down             # Zatrzymaj wszystko"
echo "  docker compose restart          # Restart wszystkich serwisów"
echo ""
echo "🛑 Aby zatrzymać: docker compose down"
echo ""