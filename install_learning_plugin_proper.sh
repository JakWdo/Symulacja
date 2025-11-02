#!/bin/bash

echo "🎓 Instalacja Learn-by-Doing według oficjalnej dokumentacji Claude Code"
echo "========================================================================="
echo ""

PROJECT="/Users/jakubwdowicz/market-research-saas"
MARKETPLACE="$PROJECT/dev-marketplace"
PLUGIN="$MARKETPLACE/learn-by-doing"

cd "$PROJECT"

# 1. Stwórz strukturę marketplace
echo "📁 Tworzę strukturę marketplace..."
mkdir -p "$MARKETPLACE/.claude-plugin"
mkdir -p "$PLUGIN/.claude-plugin"
mkdir -p "$PLUGIN"/{commands,hooks,scripts,data}

# 2. Marketplace manifest
echo "📄 Tworzę marketplace.json..."
cat > "$MARKETPLACE/.claude-plugin/marketplace.json" << 'EOF'
{
  "name": "sight-dev-marketplace",
  "description": "Local development marketplace for Sight project plugins",
  "owner": {
    "name": "Sight Team"
  },
  "plugins": [
    {
      "name": "learn-by-doing",
      "source": "./learn-by-doing",
      "description": "Inteligentny system uczenia się przez praktykę"
    }
  ]
}
EOF

# 3. Plugin manifest
echo "📄 Tworzę plugin.json..."
cat > "$PLUGIN/.claude-plugin/plugin.json" << 'EOF'
{
  "name": "learn-by-doing",
  "version": "1.0.0",
  "description": "Inteligentny system uczenia się przez praktykę na projekcie Sight",
  "author": {
    "name": "Sight Team"
  },
  "license": "MIT",
  "keywords": ["learning", "education", "polish"],
  "commands": "./commands/",
  "hooks": "./hooks/hooks.json"
}
EOF

# 4. Hooks config
echo "📄 Tworzę hooks.json..."
cat > "$PLUGIN/hooks/hooks.json" << 'EOF'
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/session_start.sh"
          }
        ]
      }
    ]
  }
}
EOF

# 5. Session start script (PROSTY - działa zawsze)
echo "📄 Tworzę session_start.sh..."
cat > "$PLUGIN/scripts/session_start.sh" << 'EOF'
#!/bin/bash

# Prosty welcome message - zawsze działa
cat << 'WELCOME'

🎓 TRYB NAUCZANIA AKTYWNY - Projekt Sight

Będę Ci pomagał przez:
- 💡 Wyjaśnianie DLACZEGO coś działa (nie tylko JAK)
- ✍️ Zostawianie TODO(human) do samodzielnej implementacji  
- 🔗 Pokazywanie powiązań między konceptami w Sight
- 🤔 Zadawanie pytań do refleksji

Dostępne komendy: /learn, /review, /progress

Szczęśliwego kodowania! 🚀

WELCOME
EOF

chmod +x "$PLUGIN/scripts/session_start.sh"

# 6. Komenda /learn
echo "📄 Tworzę commands/learn.md..."
cat > "$PLUGIN/commands/learn.md" << 'EOF'
---
name: learn
description: Status trybu nauczania
usage: /learn
---

# 🎓 Tryb Nauczania

Plugin **learn-by-doing** jest aktywny w projekcie Sight.

## Co robi:
- Wyjaśnia dlaczego coś działa (nie tylko jak)
- Pozostawia TODO(human) do implementacji
- Śledzi postęp w nauce
- Przypomina o powtórkach

## Dostępne komendy:
- `/learn` - Ten ekran
- `/review` - Dzisiejsza nauka
- `/progress` - Dashboard postępów

**Status:** ✅ Aktywny
EOF

# 7. Komenda /review
echo "📄 Tworzę commands/review.md..."
cat > "$PLUGIN/commands/review.md" << 'EOF'
---
name: review
description: Przegląd nauki
usage: /review
---

# 📝 Przegląd Nauki

Podsumowanie tego czego się nauczyłeś.

## Dostępne opcje:
- `/review` - Dzisiejsza nauka
- `/review week` - Ostatni tydzień

(W przyszłości: analiza practice_log.jsonl)
EOF

# 8. Komenda /progress
echo "📄 Tworzę commands/progress.md..."
cat > "$PLUGIN/commands/progress.md" << 'EOF'
---
name: progress
description: Dashboard postępów
usage: /progress
---

# 📊 Dashboard Postępów

Statystyki uczenia się w projekcie Sight.

(W przyszłości: wizualizacja postępu, streaki, koncepty)
EOF

# 9. Test
echo ""
echo "🧪 Testuję session_start.sh..."
"$PLUGIN/scripts/session_start.sh"

echo ""
echo "✅ PLUGIN STWORZONY!"
echo ""
echo "📂 Lokalizacja:"
echo "   $MARKETPLACE"
echo ""
echo "📋 INSTRUKCJE INSTALACJI:"
echo ""
echo "1. Przejdź do projektu:"
echo "   cd $PROJECT"
echo ""
echo "2. Uruchom Claude Code:"
echo "   claude"
echo ""
echo "3. Dodaj marketplace:"
echo "   /plugin marketplace add ./dev-marketplace"
echo ""
echo "4. Zainstaluj plugin:"
echo "   /plugin install learn-by-doing@sight-dev-marketplace"
echo ""
echo "5. Zrestartuj Claude Code (Ctrl+D, potem 'claude')"
echo ""
echo "6. Powinno się pokazać powitanie! 🎓"
echo ""
