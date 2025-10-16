#!/bin/bash
# Test funkcjonalny po migracji persona details

set -e

echo "🧪 Test 1: Health check API"
curl -s http://localhost:8000/health | grep -q "ok" && echo "✅ API działa" || echo "❌ API nie odpowiada"

echo ""
echo "🧪 Test 2: Lista person (powinno działać bez błędów)"
curl -s http://localhost:8000/api/personas \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  | grep -q "id" && echo "✅ Lista person działa" || echo "❌ Błąd w liście person"

echo ""
echo "🧪 Test 3: Szczegóły persony (GET /details)"
# Zamień PERSONA_ID na rzeczywisty UUID persony z twojej bazy
PERSONA_ID="REPLACE_WITH_REAL_UUID"

if [ "$PERSONA_ID" != "REPLACE_WITH_REAL_UUID" ]; then
  RESPONSE=$(curl -s http://localhost:8000/api/personas/$PERSONA_ID/details \
    -H "Authorization: Bearer YOUR_TOKEN_HERE")

  # Sprawdź czy response zawiera podstawowe pola
  echo "$RESPONSE" | grep -q "full_name" && echo "✅ Details endpoint działa" || echo "❌ Błąd w details"

  # Sprawdź czy NIE MA kpi_snapshot (powinno być null lub brak pola)
  echo "$RESPONSE" | grep -q "kpi_snapshot" && echo "⚠️  WARNING: kpi_snapshot nadal w response!" || echo "✅ kpi_snapshot usunięty"

  # Sprawdź czy NIE MA customer_journey
  echo "$RESPONSE" | grep -q "customer_journey" && echo "⚠️  WARNING: customer_journey nadal w response!" || echo "✅ customer_journey usunięty"

  # Sprawdź czy MA needs_and_pains
  echo "$RESPONSE" | grep -q "needs_and_pains" && echo "✅ needs_and_pains obecny" || echo "⚠️  needs_and_pains missing (może być null)"
else
  echo "⚠️  Pomiń test 3 - ustaw PERSONA_ID w skrypcie"
fi

echo ""
echo "✅ Testy zakończone"
