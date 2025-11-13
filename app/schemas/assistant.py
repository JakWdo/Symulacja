"""
Pydantic schemas dla Product Assistant API

Product Assistant to lightweight AI helper dla użytkowników platformy Sight.
Odpowiada na pytania o funkcje, pomaga w nawigacji, NIE WYKONUJE akcji.

Stateless - historia konwersacji przechowywana tylko w frontend (in-memory).
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class ChatRequest(BaseModel):
    """Request do wysłania wiadomości do Product Assistant."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Pytanie użytkownika",
        examples=["Jak wygenerować persony?"]
    )
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Historia konwersacji (in-memory z frontendu). Format: [{'role': 'user', 'content': '...'}, ...]",
        examples=[[
            {"role": "user", "content": "Jak utworzyć projekt?"},
            {"role": "assistant", "content": "Aby utworzyć projekt..."}
        ]]
    )
    include_user_context: bool = Field(
        default=True,
        description="Czy dołączyć kontekst użytkownika (projekty, persony, etc.)"
    )


class ChatResponse(BaseModel):
    """Response od Product Assistant."""

    message: str = Field(
        ...,
        description="Odpowiedź asystenta",
        examples=["Aby wygenerować persony: 1) Otwórz projekt, 2) Przejdź do zakładki 'Persony'..."]
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Sugestie follow-up pytań (generowane przez LLM)",
        examples=[["Jak edytować wygenerowane persony?", "Ile kosztuje generacja person?"]]
    )
