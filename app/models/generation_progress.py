"""
Model dla progress tracking generowania person (Server-Sent Events).

Ten moduł definiuje enumy i Pydantic schemas używane do trackowania
real-time progress generacji person przez SSE endpoint.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class GenerationStage(str, Enum):
    """Etapy generacji person.

    Każdy etap odpowiada fazie w pipeline generacji:
    - INITIALIZING: Inicjalizacja (0-5%)
    - ORCHESTRATION: Tworzenie segment briefs (5-20%)
    - GENERATING_PERSONAS: Równoległe wywołania LLM (20-90%)
    - VALIDATION: Walidacja rozkładu demograficznego (90-95%)
    - SAVING: Zapis do bazy danych (95-100%)
    - COMPLETED: Sukces (100%)
    - FAILED: Błąd podczas generacji
    """

    INITIALIZING = "initializing"
    ORCHESTRATION = "orchestration"
    GENERATING_PERSONAS = "generating_personas"
    VALIDATION = "validation"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationProgress(BaseModel):
    """Progress event dla Server-Sent Events stream.

    Ten model jest serializowany do JSON i wysyłany jako SSE event
    przez endpoint /projects/{project_id}/personas/generate/stream.

    Attributes:
        stage: Aktualny etap generacji
        progress_percent: Postęp w procentach (0-100)
        message: Czytelna wiadomość dla użytkownika (po polsku)
        personas_generated: Ile person wygenerowano (dla etapu GENERATING_PERSONAS)
        total_personas: Całkowita liczba person do wygenerowania
        error: Opcjonalny komunikat błędu (tylko dla stage=FAILED)

    Examples:
        >>> progress = GenerationProgress(
        ...     stage=GenerationStage.GENERATING_PERSONAS,
        ...     progress_percent=50,
        ...     message="Wygenerowano 10/20 person",
        ...     personas_generated=10,
        ...     total_personas=20
        ... )
        >>> progress.model_dump()
        {
            "stage": "generating_personas",
            "progress_percent": 50,
            "message": "Wygenerowano 10/20 person",
            "personas_generated": 10,
            "total_personas": 20,
            "error": None
        }
    """

    stage: GenerationStage = Field(
        description="Aktualny etap generacji person"
    )
    progress_percent: int = Field(
        ge=0, le=100,
        description="Postęp w procentach (0-100)"
    )
    message: str = Field(
        description="Czytelna wiadomość dla użytkownika (po polsku)"
    )
    personas_generated: int = Field(
        default=0, ge=0,
        description="Liczba person wygenerowanych do tej pory"
    )
    total_personas: int = Field(
        ge=1,
        description="Całkowita liczba person do wygenerowania"
    )
    error: Optional[str] = Field(
        default=None,
        description="Opcjonalny komunikat błędu (tylko dla stage=FAILED)"
    )
