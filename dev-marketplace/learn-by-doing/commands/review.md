---
name: review
description: Przegląd nauki
usage: /review [today|week]
---

# Wykonuje skrypt review.py z argumentem

python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py ${1:-today}
