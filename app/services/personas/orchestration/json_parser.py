"""JSON parsing utilities z 4 strategiami fallback.

Ten moduł ekstraktuje JSON z odpowiedzi LLM która może być otoczona:
- Markdown code blocks (```json ... ```)
- Plain code blocks (``` ... ```)
- Preambułą tekstową (znajduje pierwszy {...})
- Direct JSON (fallback)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def extract_json_from_response(response_text: str) -> dict[str, Any]:
    """Ekstraktuje JSON z odpowiedzi LLM (może być otoczony markdown lub preambułą).

    Strategie parsowania (w kolejności):
    1. ```json ... ``` (Markdown code block z json)
    2. ``` ... ``` (Plain code block)
    3. Pierwszy {...} (Regex search)
    4. Cały tekst (Direct parse fallback)

    Args:
        response_text: Surowa odpowiedź od LLM

    Returns:
        Parsed JSON jako dict

    Raises:
        ValueError: Jeśli nie można sparsować JSON (wszystkie strategie zawiodły)
    """
    text = response_text.strip()

    # Strategia 1: Znajdź blok ```json ... ``` (może być w środku tekstu)
    json_block_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_block_match:
        json_text = json_block_match.group(1).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Nie można sparsować JSON z bloku markdown: {e}")
            logger.error(f"JSON block text: {json_text[:500]}...")
            # Kontynuuj do następnej strategii

    # Strategia 2: Znajdź blok ``` ... ``` (bez json)
    code_block_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if code_block_match:
        json_text = code_block_match.group(1).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Nie można sparsować JSON z bloku kodu: {e}")
            # Kontynuuj do następnej strategii

    # Strategia 3: Znajdź pierwszy { ... } (może być po preambule)
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        json_text = brace_match.group(0).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Nie można sparsować JSON z braces: {e}")
            logger.error(f"Braces text: {json_text[:500]}...")

    # Strategia 4: Spróbuj sparsować cały tekst (fallback)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Nie można sparsować JSON (all strategies failed): {e}")
        logger.error(f"❌ Response text length: {len(text)} chars")
        logger.error(f"❌ Response text (first 1000 chars): {text[:1000]}")
        logger.error(f"❌ Response text (last 1000 chars): {text[-1000:]}")
        raise ValueError(f"LLM nie zwrócił poprawnego JSON: {e}")
