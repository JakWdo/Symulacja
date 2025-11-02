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
        "✍️ Pisz kod z TODO(human) - praktyka czyni mistrza",
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
                "hookEventName": "SessionStart",
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
