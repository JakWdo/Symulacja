#!/bin/bash

echo "🎓 Instalacja Learn-by-Doing lokalnie w projekcie Sight"
echo "======================================================="
echo ""

PROJECT_DIR="/Users/jakubwdowicz/market-research-saas"
CLAUDE_DIR="$PROJECT_DIR/.claude"
PLUGIN_DIR="$CLAUDE_DIR/plugins/learn-by-doing"

# 1. Sprawdź czy jesteśmy w projekcie
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Projekt Sight nie znaleziony w $PROJECT_DIR"
    exit 1
fi

echo "✅ Projekt Sight znaleziony"

# 2. Stwórz katalog .claude jeśli nie istnieje
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "📁 Tworzę katalog .claude w projekcie..."
    mkdir -p "$CLAUDE_DIR"
fi

# 3. Stwórz strukturę pluginu
echo "📁 Tworzę strukturę pluginu..."
mkdir -p "$PLUGIN_DIR"/{commands,hooks,scripts,data,prompts}

# 4. Stwórz plugin.json
echo "📄 Tworzę plugin.json..."
cat > "$PLUGIN_DIR/plugin.json" << 'EOF'
{
  "name": "learn-by-doing",
  "version": "1.0.0",
  "description": "Inteligentny system uczenia się przez praktykę na projekcie Sight",
  "author": {
    "name": "Sight Team"
  },
  "license": "MIT",
  "keywords": ["learning", "education", "polish", "practice"],
  "commands": "./commands/",
  "hooks": "./hooks/hooks.json"
}
EOF

# 5. Stwórz hooks/hooks.json
echo "📄 Tworzę hooks/hooks.json..."
cat > "$PLUGIN_DIR/hooks/hooks.json" << 'EOF'
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session_start.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|StrReplace",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/track_practice.py"
          }
        ]
      }
    ]
  }
}
EOF

# 6. Stwórz prompts/learning_mindset.md
echo "📄 Tworzę prompts/learning_mindset.md..."
cat > "$PLUGIN_DIR/prompts/learning_mindset.md" << 'EOF'
# 🎓 TRYB NAUCZANIA - ZASADY

Jesteś nauczycielem programowania, który uczy przez praktykę na realnym projekcie Sight.

## TWOJA ROLA:
1. **Obserwuj** - zauważaj co użytkownik robi
2. **Wyjaśniaj** - tłumacz DLACZEGO, nie tylko JAK
3. **Ćwicz** - zostawiaj TODO(human) do samodzielnej implementacji
4. **Łącz** - pokazuj powiązania między konceptami w Sight
5. **Pytaj** - zachęcaj do refleksji

## POZIOMY TRUDNOŚCI TODO(human):
- **Łatwy (🟢)**: Dodaj docstring, popraw formatowanie
- **Średni (🟡)**: Dodaj obsługę błędów, napraw testy
- **Trudny (🔴)**: Zaimplementuj nową funkcję, refaktoryzuj kod

## FORMAT WYJAŚNIEŃ:

### 💡 Learning Insight: [Nazwa Konceptu]

**Co zrobiłeś:**
[Krótki opis akcji użytkownika]

**Dlaczego to działa:**
[Wyjaśnienie mechanizmu - 2-3 zdania]

**Kluczowe koncepty:**
- **[Koncept 1]**: Wyjaśnienie
- **[Koncept 2]**: Wyjaśnienie

**Powiązania w Sight:**
- Podobny pattern w: `[plik]`
- Różni się od: `[plik]` - dlaczego?

**Na przyszłość:**
[Podpowiedź jak rozwijać ten pattern]

---

## PRZYKŁAD TODO(human):
```python
# TODO(human) 🟡: Dodaj obsługę błędu Redis connection
# Podpowiedź: Co powinno się stać jeśli Redis nie odpowiada?
# Oczekiwane: try-except z fallbackiem do bezpośredniego obliczenia
# Dlaczego: Aplikacja powinna działać nawet jeśli Redis padnie
# Linie kodu: ~5-8
# Koncepty: exception handling, graceful degradation
```

## ZASADY:
- Zawsze po polsku
- Wyjaśnienia max 5-7 zdań (nie przytłaczaj)
- TODO(human) zawsze z podpowiedzią
- Pytania refleksyjne na końcu większych zmian
- Pokaż konkretne przykłady z kodu Sight
EOF

# 7. Stwórz scripts/session_start.py
echo "📄 Tworzę scripts/session_start.py..."
cat > "$PLUGIN_DIR/scripts/session_start.py" << 'PYEOF'
#!/usr/bin/env python3
"""
SessionStart Hook - Ładuje kontekst uczenia się na początek sesji
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

PLUGIN_ROOT = Path(__file__).parent.parent
DATA_DIR = PLUGIN_ROOT / "data"
PROMPTS_DIR = PLUGIN_ROOT / "prompts"

DATA_DIR.mkdir(exist_ok=True)

def load_progress():
    """Wczytaj postęp uczenia się"""
    progress_file = DATA_DIR / "learning_progress.json"
    
    if not progress_file.exists():
        default_progress = {
            "sessions": 0,
            "total_concepts": 0,
            "mastered_concepts": 0,
            "current_focus": "Backend (FastAPI + PostgreSQL)",
            "last_session": None,
            "streak_days": 0,
            "concepts": {},
            "learning_paths": {
                "backend_mastery": {
                    "name": "Backend Mastery",
                    "progress": 0.0,
                    "concepts": ["fastapi_async", "sqlalchemy_async", "redis_caching"]
                },
                "rag_systems": {
                    "name": "Systemy RAG",
                    "progress": 0.0,
                    "concepts": ["vector_search", "graph_rag", "hybrid_search"]
                }
            }
        }
        progress_file.write_text(json.dumps(default_progress, indent=2, ensure_ascii=False))
        return default_progress
    
    return json.loads(progress_file.read_text())

def get_concepts_to_review(progress):
    """Znajdź koncepty do powtórki (spaced repetition)"""
    to_review = []
    
    intervals = {
        1: timedelta(days=1),
        2: timedelta(days=3),
        3: timedelta(days=7),
        4: timedelta(days=14),
        5: timedelta(days=30),
    }
    
    for concept_id, data in progress.get("concepts", {}).items():
        level = data.get("mastery_level", 1)
        last_practiced = data.get("last_practiced")
        
        if not last_practiced:
            continue
            
        last_date = datetime.fromisoformat(last_practiced)
        interval = intervals.get(level, timedelta(days=1))
        
        if datetime.now() - last_date >= interval:
            to_review.append({
                "name": data.get("name", concept_id),
                "level": level,
                "days_ago": (datetime.now() - last_date).days
            })
    
    return to_review

def format_concepts(concepts):
    """Formatuj listę konceptów do przeglądu"""
    if not concepts:
        return "✅ Wszystko aktualne!"
    
    lines = []
    for c in concepts[:3]:
        emoji = "🟢" if c["level"] < 3 else "🟡" if c["level"] < 5 else "🔴"
        lines.append(f"  {emoji} **{c['name']}** (poziom {c['level']}, {c['days_ago']} dni temu)")
    
    if len(concepts) > 3:
        lines.append(f"  ... i {len(concepts) - 3} więcej (użyj /review)")
    
    return "\n".join(lines)

def update_session_count(progress):
    """Aktualizuj licznik sesji"""
    progress["sessions"] += 1
    
    last = progress.get("last_session")
    if last:
        last_date = datetime.fromisoformat(last).date()
        today = datetime.now().date()
        diff = (today - last_date).days
        
        if diff == 1:
            progress["streak_days"] += 1
        elif diff > 1:
            progress["streak_days"] = 1
    else:
        progress["streak_days"] = 1
    
    progress["last_session"] = datetime.now().isoformat()
    
    progress_file = DATA_DIR / "learning_progress.json"
    progress_file.write_text(json.dumps(progress, indent=2, ensure_ascii=False))

def generate_daily_goals(progress):
    """Generuj cele na dzisiaj"""
    session_num = progress["sessions"]
    
    goals = [
        "�� Pisz kod z TODO(human) - praktyka czyni mistrza",
        "💡 Pytaj 'dlaczego' gdy coś jest niejasne",
        "🔗 Szukaj podobnych patternów w innych częściach Sight"
    ]
    
    if session_num > 0 and session_num % 5 == 0:
        goals.insert(0, "🎯 Dzisiaj: Test wiedzy (/quiz) - sprawdź co pamiętasz!")
    
    return goals

def load_learning_prompt():
    """Wczytaj główny prompt uczący"""
    prompt_file = PROMPTS_DIR / "learning_mindset.md"
    
    if prompt_file.exists():
        return prompt_file.read_text()
    return ""

def main():
    """Główna funkcja SessionStart hook"""
    try:
        progress = load_progress()
        update_session_count(progress)
        to_review = get_concepts_to_review(progress)
        goals = generate_daily_goals(progress)
        learning_prompt = load_learning_prompt()
        
        streak_emoji = "🔥" if progress["streak_days"] >= 3 else "⭐"
        
        context = f"""
{learning_prompt}

---

# 🎓 SESJA UCZENIA #{progress['sessions']}

## Twoje Statystyki:
- {streak_emoji} **Passa:** {progress['streak_days']} dni pod rząd
- 📊 **Opanowane koncepty:** {progress.get('mastered_concepts', 0)}/{progress.get('total_concepts', 0)}
- 🎯 **Obecny focus:** {progress['current_focus']}

## Dzisiejsze Cele:
{chr(10).join(f"  {goal}" for goal in goals)}

## Do Powtórki (Spaced Repetition):
{format_concepts(to_review)}

---

**PAMIĘTAJ:** Tryb nauczania jest aktywny! Będę wyjaśniał, pozostawiał TODO(human) i pytał o zrozumienie.
Możesz używać komend: /learn, /review, /progress
"""
        
        output = {
            "hookSpecificOutput": {
                "additionalContext": context
            }
        }
        
        print(json.dumps(output))
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Błąd w SessionStart hook: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
PYEOF

# 8. Stwórz scripts/track_practice.py
echo "📄 Tworzę scripts/track_practice.py..."
cat > "$PLUGIN_DIR/scripts/track_practice.py" << 'PYEOF'
#!/usr/bin/env python3
"""
PostToolUse Hook - Śledzi akcje użytkownika i loguje do practice_log
"""
import json
import sys
from pathlib import Path
from datetime import datetime

PLUGIN_ROOT = Path(__file__).parent.parent
DATA_DIR = PLUGIN_ROOT / "data"
LOG_FILE = DATA_DIR / "practice_log.jsonl"

DATA_DIR.mkdir(exist_ok=True)

def categorize_action(tool_name, tool_input):
    """Kategoryzuj akcję użytkownika"""
    
    if tool_name == "Write":
        return "file_create"
    elif tool_name == "Edit" or tool_name == "StrReplace":
        return "file_edit"
    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        if "pytest" in command:
            return "test_run"
        elif "git" in command:
            return "git_operation"
        else:
            return "bash_command"
    else:
        return "other"

def extract_context(tool_input):
    """Wyciągnij kontekst z tool_input"""
    
    if "path" in tool_input:
        path = tool_input["path"]
        
        if "/services/" in path:
            return {"type": "service", "file": Path(path).name}
        elif "/api/" in path:
            return {"type": "api_endpoint", "file": Path(path).name}
        elif "/tests/" in path:
            return {"type": "test", "file": Path(path).name}
        else:
            return {"type": "other", "file": Path(path).name}
    
    return {"type": "unknown"}

def is_learning_moment(action, context):
    """Sprawdź czy to moment uczący"""
    
    if action in ["file_create", "file_edit"]:
        return True
    
    if action == "test_run":
        return True
    
    return False

def log_action(entry):
    """Zapisz akcję do logu"""
    
    try:
        with LOG_FILE.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"⚠️ Nie udało się zapisać logu: {e}", file=sys.stderr)

def main():
    """Główna funkcja PostToolUse hook"""
    
    try:
        hook_data = json.loads(sys.stdin.read())
        
        tool_name = hook_data.get("tool_name", "")
        tool_input = hook_data.get("tool_input", {})
        
        action = categorize_action(tool_name, tool_input)
        context = extract_context(tool_input)
        
        if is_learning_moment(action, context):
            entry = {
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "action": action,
                "context": context
            }
            
            log_action(entry)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"⚠️ Błąd w track_practice: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
PYEOF

# 9. Stwórz commands/learn.md
echo "📄 Tworzę commands/learn.md..."
cat > "$PLUGIN_DIR/commands/learn.md" << 'EOF'
---
name: learn
description: Wyświetl status trybu nauczania i statystyki
usage: /learn
---

# 🎓 Status Trybu Nauczania

Ten plugin jest **zawsze aktywny** w projekcie Sight.

## Co robi ten plugin?

1. **Obserwuje** Twoją pracę nad projektem
2. **Wyjaśnia** dlaczego coś działa (nie tylko jak)
3. **Pozostawia TODO(human)** do samodzielnej implementacji
4. **Śledzi postęp** i przypomina o powtórkach

## Dostępne komendy:

- `/learn` - Ten ekran (status)
- `/review` - Podsumowanie dzisiejszej nauki
- `/progress` - Dashboard postępów

---

**Powodzenia w nauce! 🚀**
EOF

# 10. Stwórz commands/review.md
echo "📄 Tworzę commands/review.md..."
cat > "$PLUGIN_DIR/commands/review.md" << 'EOF'
---
name: review
description: Przegląd tego czego się nauczyłeś
usage: /review [today|week]
---

# 📝 Przegląd Nauki

Pokaż podsumowanie Twojej nauki z pluginu Learn-by-Doing.

## Użycie:
```bash
/review              # Dzisiejsza nauka
/review week         # Ostatnie 7 dni
```

---

**Miłej nauki! 🎓**
EOF

# 11. Stwórz commands/progress.md
echo "📄 Tworzę commands/progress.md..."
cat > "$PLUGIN_DIR/commands/progress.md" << 'EOF'
---
name: progress
description: Dashboard postępów w nauce
usage: /progress
---

# 📊 Dashboard Postępów

Wizualna reprezentacja Twojego postępu w nauce projektu Sight.

## Statystyki:
- Liczba sesji programowania
- Opanowane koncepty
- Obecna passa dni
- Learning paths progress

---

**Trzymaj tempo! 💪**
EOF

# 12. Ustaw uprawnienia
echo ""
echo "🔧 Ustawiam uprawnienia..."
chmod +x "$PLUGIN_DIR/scripts"/*.py

# 13. Stwórz .claude/settings.local.json
echo "📄 Tworzę .claude/settings.local.json..."
cat > "$CLAUDE_DIR/settings.local.json" << EOF
{
  "plugins": {
    "learn-by-doing": {
      "enabled": true,
      "path": "./.claude/plugins/learn-by-doing"
    }
  }
}
EOF

# 14. Test skryptów
echo ""
echo "🧪 Testuję skrypty..."
cd "$PLUGIN_DIR"
OUTPUT=$(python3 scripts/session_start.py 2>&1)
if echo "$OUTPUT" | grep -q "additionalContext"; then
    echo "✅ session_start.py działa!"
else
    echo "⚠️ session_start.py może mieć problem"
fi

echo '{"tool_name":"Write","tool_input":{"path":"test.py"}}' | python3 scripts/track_practice.py 2>&1
if [ $? -eq 0 ]; then
    echo "✅ track_practice.py działa!"
fi

# 15. Dodaj do .gitignore (opcjonalnie)
echo ""
echo "📝 Dodaję .claude/ do .gitignore..."
if [ -f "$PROJECT_DIR/.gitignore" ]; then
    if ! grep -q ".claude/plugins/learn-by-doing/data" "$PROJECT_DIR/.gitignore"; then
        echo "" >> "$PROJECT_DIR/.gitignore"
        echo "# Learning plugin data (local)" >> "$PROJECT_DIR/.gitignore"
        echo ".claude/plugins/learn-by-doing/data/" >> "$PROJECT_DIR/.gitignore"
    fi
fi

echo ""
echo "✅ PLUGIN ZAINSTALOWANY LOKALNIE!"
echo ""
echo "📂 Lokalizacja:"
echo "   $PLUGIN_DIR"
echo ""
echo "📋 Następne kroki:"
echo "   1. Przejdź do projektu:"
echo "      cd $PROJECT_DIR"
echo ""
echo "   2. Uruchom Claude Code:"
echo "      claude"
echo ""
echo "   3. Powinno się pokazać:"
echo "      🎓 SESJA UCZENIA #1"
echo "      ..."
echo ""
echo "   4. Sprawdź komendy:"
echo "      /learn"
echo "      /progress"
echo "      /review"
echo ""
echo "🎓 Gotowe do nauki przez praktykę!"
