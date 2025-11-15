#!/bin/bash
# Sprawdzanie nieużywanych komponentów UI

for file in frontend/src/components/ui/*.tsx; do
  component=$(basename "$file" .tsx)
  count=$(grep -r "$component" frontend/src --include="*.tsx" --include="*.ts" --exclude-dir=ui | wc -l)
  if [ "$count" -eq 0 ]; then
    echo "$component: 0 użyć (NIEUŻYWANY)"
  fi
done
