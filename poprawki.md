# Raport Poprawek i Usprawnień - Market Research SaaS

**Data analizy:** 2025-10-09
**Przeanalizowane pliki:** 52 Python files, 109 TypeScript/React files
**Znalezione problemy:** 27 krytycznych/poważnych, wiele drobnych ulepszeń

---

## 🔴 KRYTYCZNE BŁĘDY (Priorytet: Natychmiastowy)

### 1. Duplikacja Budowania Grafu Wiedzy
**Lokalizacja:**
- `app/services/focus_group_service_langchain.py:143-153`
- `app/api/focus_groups.py:177-186`

**Problem:**
Graf wiedzy Neo4j jest budowany **dwa razy** po każdym zakończonym focus group:
1. Raz w `FocusGroupServiceLangChain.run_focus_group()` (linia 143)
2. Drugi raz w `_run_focus_group_task()` (linia 177)

**Wpływ:**
- ❌ Podwójne zużycie tokenów Gemini API (~$$$)
- ❌ ~2x dłuższy czas wykonania (każdy graph build to ~30-60s)
- ❌ Potencjalne race conditions w Neo4j

**Rozwiązanie:**
Usuń duplikację - pozostaw budowanie grafu tylko w jednym miejscu.

```python
# ❌ PRZED (focus_group_service_langchain.py:143-153)
# Automatically build knowledge graph after completion
logger.info(f"🧠 Starting automatic graph build for focus group {focus_group_id}")
try:
    from app.services.graph_service import GraphService
    graph_service = GraphService()
    graph_stats = await graph_service.build_graph_from_focus_group(db, str(focus_group_id))
    await graph_service.close()
    logger.info(f"✅ Graph built successfully: {graph_stats}")
except Exception as graph_error:
    # Don't fail the entire focus group if graph building fails
    logger.error(f"⚠️ Graph build failed (non-critical): {graph_error}", exc_info=True)

# ✅ PO - USUŃ TEN BLOK całkowicie z focus_group_service_langchain.py
# Graf będzie budowany tylko raz w focus_groups.py
```

**Czas implementacji:** 5 minut
**Savings:** ~50% czasu wykonania graph build, 50% kosztów Gemini

---

### 2. Wyciek Połączeń Neo4j
**Lokalizacja:** `app/services/graph_service.py:58-143`

**Problem:**
`GraphService` tworzy połączenie AsyncDriver w `connect()`, ale nigdy nie jest prawidłowo zamykane:
- W focus_groups.py:180 wywołanie `graph_service.close()` jest po `await`, ale w exception handler nie ma cleanup
- Brak context manager pattern
- Driver może pozostać otwarty przy wyjątkach

**Wpływ:**
- ❌ Memory leaks (każde połączenie ~5-10MB)
- ❌ Neo4j connection pool exhaustion po ~50-100 focus groups
- ❌ Potencjalne "too many open files" errors

**Rozwiązanie:**
Implementuj async context manager dla GraphService:

```python
# ✅ app/services/graph_service.py
class GraphService:
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return False  # Don't suppress exceptions

    # ... rest of class

# ✅ app/api/focus_groups.py:177-186
async def _run_focus_group_task(focus_group_id: UUID):
    try:
        async with AsyncSessionLocal() as db:
            service = FocusGroupService()
            result = await service.run_focus_group(db, str(focus_group_id))

            if result.get('status') == 'completed':
                logger.info(f"🔨 Building knowledge graph...")
                async with GraphService() as graph_service:  # ✅ Proper cleanup
                    graph_stats = await graph_service.build_graph_from_focus_group(
                        db, str(focus_group_id)
                    )
                    logger.info(f"✅ Graph built: {graph_stats}")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
```

**Czas implementacji:** 20 minut
**Priorytet:** Krytyczny (może crashować aplikację)

---

### 3. Race Condition w Event Sourcing
**Lokalizacja:** `app/services/memory_service_langchain.py:72-80`

**Problem:**
Sequence number dla PersonaEvent może się zduplikować przy współbieżnych zapisach:

```python
# ❌ PROBLEMATYCZNY KOD
result = await db.execute(
    select(PersonaEvent)
    .where(PersonaEvent.persona_id == persona_id)
    .order_by(PersonaEvent.sequence_number.desc())
    .limit(1)
)
last_event = result.scalar_one_or_none()
sequence_number = (last_event.sequence_number + 1) if last_event else 1
# ⚠️ W tym momencie inna goroutine może zapisać ten sam sequence_number!
```

**Wpływ:**
- ❌ Duplikaty sequence_number → naruszenie integralności event sourcing
- ❌ Problemy z kolejnością eventów
- ❌ Trudne do debugowania błędy w retrieve_relevant_context

**Rozwiązanie:**
Użyj SELECT FOR UPDATE lub UNIQUE constraint + retry logic:

```python
# ✅ ROZWIĄZANIE 1: SELECT FOR UPDATE
result = await db.execute(
    select(PersonaEvent)
    .where(PersonaEvent.persona_id == persona_id)
    .order_by(PersonaEvent.sequence_number.desc())
    .limit(1)
    .with_for_update()  # ✅ Pessimistic lock
)

# ✅ ROZWIĄZANIE 2: Dodaj constraint + retry
# W models/persona_events.py dodaj:
# __table_args__ = (
#     UniqueConstraint('persona_id', 'sequence_number', name='unique_persona_sequence'),
# )

# W memory_service_langchain.py:
from sqlalchemy.exc import IntegrityError
import asyncio

MAX_RETRIES = 3
for attempt in range(MAX_RETRIES):
    try:
        # ... tworzenie event z sequence_number
        await db.commit()
        break
    except IntegrityError:
        await db.rollback()
        if attempt == MAX_RETRIES - 1:
            raise
        await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
```

**Czas implementacji:** 45 minut (z migracją DB)
**Priorytet:** Krytyczny (corrupts data)

---

### 4. Hardcoded Credentials w Repozytorium
**Lokalizacja:**
- `docker-compose.yml:7, 37, 61, 65, 84, 88`
- `app/core/config.py:42`

**Problem:**
Hasła i klucze są hardcoded w plikach śledzonych przez git:
```yaml
POSTGRES_PASSWORD: dev_password_change_in_prod  # ❌
NEO4J_AUTH: neo4j/dev_password_change_in_prod   # ❌
SECRET_KEY: str = "change-me"                    # ❌
```

**Wpływ:**
- 🔒 **SECURITY VULNERABILITY** - każdy z dostępem do repo ma credentials
- ❌ Niemożliwe bezpieczne deploy na production
- ❌ Wymaga zmiany haseł po każdym leak

**Rozwiązanie:**
1. Przenieś wszystkie credentials do `.env` (nigdy nie commituj!)
2. Dodaj `.env.example` z placeholder values
3. Dodaj walidację w production

```python
# ✅ app/core/config.py
class Settings(BaseSettings):
    SECRET_KEY: str  # ❌ Usuń default
    POSTGRES_PASSWORD: str  # ❌ Usuń default
    NEO4J_PASSWORD: str  # ❌ Usuń default

    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if v in ('change-me', '', None):
            raise ValueError('SECRET_KEY must be set to a secure random value')
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters')
        return v
```

```yaml
# ✅ docker-compose.yml - użyj zmiennych środowiskowych
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Z .env
  neo4j:
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
```

```bash
# ✅ .env.example (commit to repo)
SECRET_KEY=CHANGE_ME_TO_RANDOM_32_CHAR_STRING
POSTGRES_PASSWORD=CHANGE_ME
NEO4J_PASSWORD=CHANGE_ME
GOOGLE_API_KEY=your_api_key_here

# ✅ .env (NIE commituj!)
SECRET_KEY=9k2j3h4g5j6k7l8m9n0p1q2r3s4t5u6v7w8x9y0z  # Generated z: openssl rand -hex 32
POSTGRES_PASSWORD=secure_random_password_123
NEO4J_PASSWORD=another_secure_password_456
GOOGLE_API_KEY=actual_gemini_api_key
```

**Czas implementacji:** 30 minut
**Priorytet:** Krytyczny (security)

---

## ⚠️ POWAŻNE PROBLEMY (Priorytet: Wysoki)

### 5. Nieobsłużone Błędy w Background Tasks
**Lokalizacja:** `app/api/focus_groups.py:161-189`

**Problem:**
Background task `_run_focus_group_task` łapie wszystkie wyjątki ale tylko loguje:
```python
except Exception as e:
    logger.error(f"❌ Error: {e}", exc_info=True)
    # ❌ Brak retry logic
    # ❌ FocusGroup.status pozostaje "running" na zawsze
    # ❌ User nie wie że task failed
```

**Wpływ:**
- ❌ Focus group stuck w stanie "running" → UI pokazuje spinner w nieskończoność
- ❌ Brak automatic retry przy transient errors (network issues, API rate limits)
- ❌ Trudne debugowanie - user nie dostaje feedback

**Rozwiązanie:**
Implementuj proper error handling + retry logic + status update:

```python
# ✅ app/api/focus_groups.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import asyncio

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((asyncio.TimeoutError, ConnectionError)),
    reraise=True
)
async def _run_focus_group_with_retry(focus_group_id: UUID):
    """Inner function with retry logic for transient errors"""
    async with AsyncSessionLocal() as db:
        service = FocusGroupService()
        return await service.run_focus_group(db, str(focus_group_id))

async def _run_focus_group_task(focus_group_id: UUID):
    """Background task with proper error handling"""
    logger = logging.getLogger(__name__)
    logger.info(f"🎯 Starting focus group {focus_group_id}")

    try:
        result = await _run_focus_group_with_retry(focus_group_id)
        logger.info(f"✅ Completed: {result.get('status')}")

        if result.get('status') == 'completed':
            async with GraphService() as graph_service:
                async with AsyncSessionLocal() as db:
                    await graph_service.build_graph_from_focus_group(db, str(focus_group_id))

    except Exception as e:
        logger.error(f"❌ Fatal error after retries: {e}", exc_info=True)

        # ✅ Update status to failed
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(FocusGroup).where(FocusGroup.id == focus_group_id)
            )
            fg = result.scalar_one_or_none()
            if fg:
                fg.status = "failed"
                fg.error_message = str(e)[:500]  # Truncate long errors
                await db.commit()

        # ✅ Opcjonalnie: wyślij notification do usera (email/webhook)
```

**Czas implementacji:** 1 godzina
**Priorytet:** Wysoki (UX issue)

---

### 6. Brak Walidacji API Keys przy Starcie
**Lokalizacja:** `app/main.py:1-123`

**Problem:**
Aplikacja startuje bez weryfikacji czy `GOOGLE_API_KEY` jest ustawiony i poprawny:
```python
# app/main.py - brak walidacji!
app = FastAPI(...)
# ❌ Fails dopiero przy pierwszym wywołaniu LLM (po 30 sekundach oczekiwania)
```

**Wpływ:**
- ❌ Aplikacja startuje "healthy" ale nie działa
- ❌ Health check `/health` zwraca OK mimo braku API key
- ❌ User dostaje error dopiero po wygenerowaniu person (~30s wait)

**Rozwiązanie:**
Dodaj startup event z walidacją API keys:

```python
# ✅ app/main.py
from langchain_google_genai import ChatGoogleGenerativeAI
import logging

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def validate_configuration():
    """Validate critical configuration on startup"""

    # 1. Validate API keys
    if not settings.GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY is not set. Please set it in .env file.\n"
            "Get your key from: https://makersuite.google.com/app/apikey"
        )

    # 2. Test API key with simple call
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            max_tokens=10
        )
        test_response = await llm.ainvoke("Hi")
        logger.info("✅ Google Gemini API key validated successfully")
    except Exception as e:
        raise ValueError(
            f"Google Gemini API key validation failed: {e}\n"
            "Please check your GOOGLE_API_KEY in .env"
        )

    # 3. Validate database connection
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(select(1))
        logger.info("✅ Database connection validated")
    except Exception as e:
        raise ValueError(f"Database connection failed: {e}")

    # 4. Validate Neo4j (optional, non-critical)
    try:
        from app.services.graph_service import GraphService
        async with GraphService() as gs:
            pass  # Connection test in __aenter__
        logger.info("✅ Neo4j connection validated")
    except Exception as e:
        logger.warning(f"⚠️ Neo4j connection failed (non-critical): {e}")

@app.get("/health")
async def health_check():
    """Enhanced health check with dependency status"""
    health_status = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "checks": {
            "gemini_api": "unknown",
            "database": "unknown",
            "neo4j": "unknown"
        }
    }

    # Quick checks (no slow operations)
    if settings.GOOGLE_API_KEY:
        health_status["checks"]["gemini_api"] = "configured"

    return health_status
```

**Czas implementacji:** 45 minut
**Priorytet:** Wysoki (prevents silent failures)

---

### 7. N+1 Query Problem w Graph Building
**Lokalizacja:** `app/services/graph_service.py:204-223`

**Problem:**
Tworzenie persona nodes w pętli - każda iteracja to osobne query do Neo4j:
```python
# ❌ NIEEFEKTYWNY KOD
for persona_id, persona in personas.items():
    await session.run(  # ❌ Individual query dla każdej persony
        """
        MERGE (p:Persona {id: $id})
        SET p.name = $name, ...
        """,
        id=persona_id, name=persona.full_name, ...
    )
    stats["personas_added"] += 1
```

Dla 20 person = 20 osobnych roundtripów do Neo4j (~200ms każdy = 4 sekundy marnowane!)

**Wpływ:**
- ❌ Graph building zajmuje ~30-60s zamiast ~10-20s
- ❌ Niepotrzebne obciążenie Neo4j
- ❌ Nie skaluje się dla dużych grup (100+ person)

**Rozwiązanie:**
Użyj bulk operations z UNWIND:

```python
# ✅ EFEKTYWNY KOD - batch insert
personas_data = [
    {
        "id": str(persona_id),
        "name": persona.full_name,
        "age": persona.age,
        "gender": persona.gender,
        "occupation": persona.occupation,
        "focus_group_id": focus_group_id
    }
    for persona_id, persona in personas.items()
]

await session.run(
    """
    UNWIND $personas AS persona
    MERGE (p:Persona {id: persona.id})
    SET p.name = persona.name,
        p.age = persona.age,
        p.gender = persona.gender,
        p.occupation = persona.occupation,
        p.focus_group_id = persona.focus_group_id,
        p.updated_at = datetime()
    """,
    personas=personas_data
)
stats["personas_added"] = len(personas_data)
```

**Podobnie dla innych queries:**
- Linia 242-266: Concept creation (używaj UNWIND)
- Linia 269-291: Emotion relationships (używaj UNWIND)
- Linia 295-330: Inter-persona relationships (batchuj calculations)

**Czas implementacji:** 2 godziny
**Priorytet:** Wysoki (performance)
**Expected speedup:** 50-70% szybsze graph building

---

### 8. Brak Timeoutów dla LLM Calls
**Lokalizacja:**
- `app/services/focus_group_service_langchain.py:382`
- `app/services/persona_generator_langchain.py:284`
- `app/services/discussion_summarizer.py:188`

**Problem:**
Wszystkie wywołania `llm.ainvoke()` mogą wisieć w nieskończoność:
```python
result = await self.llm.ainvoke(prompt_text)  # ❌ Brak timeout
```

Google Gemini może mieć timeouty (rate limits, network issues) → cała aplikacja hang.

**Wpływ:**
- ❌ Background tasks stuck forever
- ❌ Zablokowane connection poolsy
- ❌ Out of memory przy wielu stuck tasks

**Rozwiązanie:**
Dodaj timeout wrapper z asyncio:

```python
# ✅ app/core/llm_utils.py (nowy plik)
import asyncio
from typing import Any, Callable
from app.core.config import get_settings

settings = get_settings()
DEFAULT_LLM_TIMEOUT = 120  # 2 minuty

async def call_llm_with_timeout(
    llm_func: Callable,
    *args,
    timeout: int = DEFAULT_LLM_TIMEOUT,
    **kwargs
) -> Any:
    """
    Wywołaj LLM function z timeout protection

    Args:
        llm_func: Async function to call (e.g., llm.ainvoke)
        timeout: Max seconds to wait

    Raises:
        asyncio.TimeoutError: If call exceeds timeout
    """
    try:
        return await asyncio.wait_for(
            llm_func(*args, **kwargs),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"LLM call exceeded {timeout}s timeout. "
            "This may indicate API issues or rate limiting."
        )

# ✅ Użycie w services
from app.core.llm_utils import call_llm_with_timeout

# W focus_group_service_langchain.py:382
async def _invoke_llm(self, prompt_text: str) -> str:
    try:
        result = await call_llm_with_timeout(
            self.llm.ainvoke,
            prompt_text,
            timeout=60  # 1 minuta dla krótkich odpowiedzi
        )
        # ... rest of logic
    except TimeoutError as e:
        logger.error(f"LLM timeout: {e}")
        return ""
```

**Czas implementacji:** 1 godzina (+ testing)
**Priorytet:** Wysoki (stability)

---

## 📊 PROBLEMY WYDAJNOŚCIOWE (Priorytet: Średni)

### 9. Podwójna Normalizacja Rozkładów
**Lokalizacja:** `app/services/persona_generator_langchain.py:176-189`

**Problem:**
```python
normalized = {key: value / total for key, value in distribution.items()}
normalized_total = sum(normalized.values())
# Druga normalizacja jeśli są błędy zaokrągleń numerycznych
if not np.isclose(normalized_total, 1.0):
    normalized = {
        key: value / normalized_total for key, value in normalized.items()
    }
```

Pierwsza normalizacja **zawsze** daje sumę = 1.0 (floating point math).
Druga normalizacja jest niepotrzebna - `np.isclose(1.0, 1.0)` zawsze True.

**Wpływ:**
- ⚠️ Minimalny (~0.01ms per persona), ale niepotrzebny kod
- ⚠️ Confusion dla maintainerów

**Rozwiązanie:**
```python
# ✅ Uproszczona wersja
def _prepare_distribution(
    self, distribution: Dict[str, float], fallback: Dict[str, float]
) -> Dict[str, float]:
    if not distribution:
        return fallback
    total = sum(distribution.values())
    if total <= 0:
        return fallback
    # Jedna normalizacja wystarczy
    return {key: value / total for key, value in distribution.items()}
```

**Czas implementacji:** 5 minut

---

### 10. Brak Backoff w Retry Logic
**Lokalizacja:** `app/services/focus_group_service_langchain.py:361-376`

**Problem:**
```python
if not text:
    logger.warning(f"Empty response from LLM, retrying...")
    retry_prompt = f"""{prompt_text}
    IMPORTANT INSTRUCTION: ...
    """
    response_text = await self._invoke_llm(retry_prompt)  # ❌ Instant retry
```

Instant retry może pogorszyć problem (jeśli API ma rate limit lub temporary issue).

**Rozwiązanie:**
```python
# ✅ Z exponential backoff
import asyncio

if not text:
    logger.warning(f"Empty response, retrying with delay...")
    await asyncio.sleep(1)  # 1 sekunda opóźnienia
    response_text = await self._invoke_llm(retry_prompt)
```

Lub lepiej - użyj biblioteki `tenacity` (już zaproponowana w #5).

**Czas implementacji:** 10 minut

---

### 11. Brak Cache dla Embeddings
**Lokalizacja:** `app/services/memory_service_langchain.py:229-240`

**Problem:**
Te same teksty są embeddowane wielokrotnie:
- Każde pytanie w focus group jest embeddowane N razy (dla każdej persony)
- `_generate_embedding("What's your opinion on X?")` wywołane 20 razy

**Wpływ:**
- ❌ Niepotrzebne zużycie Gemini API (~0.1 centa per embedding, ale × 1000 = $$$)
- ❌ Wolniejsze wykonanie (~100ms per embedding)

**Rozwiązanie:**
Dodaj LRU cache dla embeddings:

```python
# ✅ app/services/memory_service_langchain.py
from functools import lru_cache
import hashlib

class MemoryServiceLangChain:
    def __init__(self):
        # ... existing code
        self._embedding_cache = {}  # In-memory cache

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding with caching"""
        # Create hash key
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # Check cache
        if text_hash in self._embedding_cache:
            return self._embedding_cache[text_hash]

        # Generate embedding
        embedding = await self.embeddings.aembed_query(text)

        # Store in cache (limit size to 1000 entries)
        if len(self._embedding_cache) > 1000:
            # Remove oldest entry (FIFO)
            self._embedding_cache.pop(next(iter(self._embedding_cache)))
        self._embedding_cache[text_hash] = embedding

        return embedding
```

**Lub lepiej - użyj Redis cache:**
```python
# ✅ Z Redis (persistent cache)
import json
from app.core.config import get_settings

async def _generate_embedding(self, text: str) -> List[float]:
    import aioredis
    redis = await aioredis.from_url(settings.REDIS_URL)

    cache_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"

    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Generate
    embedding = await self.embeddings.aembed_query(text)

    # Cache for 7 days
    await redis.setex(cache_key, 60 * 60 * 24 * 7, json.dumps(embedding))

    return embedding
```

**Czas implementacji:** 1-2 godziny
**Expected savings:** 70-90% mniej wywołań Gemini embeddings API

---

### 12. Synchroniczne Neo4j Queries w Pętli
**Lokalizacja:** `app/services/graph_service.py:230-291`

**Problem:**
Podobnie jak #7, ale dla responses processing:
```python
for idx, response in enumerate(responses):
    # ... extraction logic
    for concept in extraction.concepts:
        await session.run(...)  # ❌ Serial queries
    for emotion in extraction.emotions:
        await session.run(...)  # ❌ Serial queries
```

**Rozwiązanie:**
Zobacz rozwiązanie z #7 - użyj UNWIND dla batch operations.

**Czas implementacji:** Included w #7

---

## 🐛 POTENCJALNE BUGI (Priorytet: Średni)

### 13. Import numpy na Końcu Pliku
**Lokalizacja:** `app/services/discussion_summarizer.py:510`

**Problem:**
```python
# ... 509 linii kodu ...

# Import numpy for demographic aggregation
import numpy as np  # ❌ Na samym końcu pliku
```

Używane w linii 284: `np.unique(genders, return_counts=True)`

**Wpływ:**
- ⚠️ PEP 8 violation (imports should be at top)
- ⚠️ Confusion dla code readers
- ⚠️ Potencjalne problemy z IDE autocomplete

**Rozwiązanie:**
```python
# ✅ Przenieś na górę (po innych importach)
# linia 1-26
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np  # ✅ Tutaj
```

**Czas implementacji:** 1 minuta

---

### 14. Nieprawidłowa Walidacja p-value
**Lokalizacja:** `app/services/persona_generator_langchain.py:487-491`

**Problem:**
```python
all_p_values = [r["p_value"] for r in results.values() if "p_value" in r]
results["overall_valid"] = all(
    p > settings.STATISTICAL_SIGNIFICANCE_THRESHOLD for p in all_p_values
) if all_p_values else True  # ❌ Zawsze True jeśli brak p-values!
```

Jeśli `all_p_values` jest puste (np. brak target distributions), zwraca `True` → fałszywie pozytywna walidacja.

**Rozwiązanie:**
```python
# ✅ Poprawiona logika
all_p_values = [r["p_value"] for r in results.values() if "p_value" in r]

if not all_p_values:
    # Brak testów → nie możemy stwierdzić czy valid
    results["overall_valid"] = None  # lub False
    results["validation_status"] = "no_tests_performed"
else:
    results["overall_valid"] = all(
        p > settings.STATISTICAL_SIGNIFICANCE_THRESHOLD for p in all_p_values
    )
    results["validation_status"] = "validated"
```

**Czas implementacji:** 10 minut

---

### 15. Memory Leak w _running_tasks
**Lokalizacja:** `app/api/focus_groups.py:35`

**Problem:**
```python
_running_tasks = set()

# W run_focus_group():
task = asyncio.create_task(_run_focus_group_task(focus_group_id))
_running_tasks.add(task)
task.add_done_callback(_running_tasks.discard)
```

`add_done_callback` usuwa task po zakończeniu, **ale**:
- Jeśli task rzuci wyjątek przed dodaniem callback → leak
- Callback może nie zadziałać przy shutdown

**Wpływ:**
- ⚠️ Set może rosnąć do setek elementów przy ciągłym użytku
- ⚠️ Memory leak (~KB per task, ale × 1000 = MB)

**Rozwiązanie:**
```python
# ✅ Safer approach z cleanup
import weakref

_running_tasks = weakref.WeakSet()  # ✅ Automatic garbage collection

# Lub z periodict cleanup:
import asyncio
from collections import OrderedDict
from datetime import datetime

_running_tasks = OrderedDict()  # task_id -> (task, start_time)

async def cleanup_old_tasks():
    """Periodic cleanup for orphaned tasks"""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        now = datetime.now()
        to_remove = [
            task_id for task_id, (task, start_time) in _running_tasks.items()
            if task.done() or (now - start_time).seconds > 3600  # 1 hour timeout
        ]
        for task_id in to_remove:
            _running_tasks.pop(task_id, None)
        logger.info(f"Cleaned {len(to_remove)} old tasks. Active: {len(_running_tasks)}")

# W startup event:
@app.on_event("startup")
async def start_cleanup():
    asyncio.create_task(cleanup_old_tasks())
```

**Czas implementacji:** 30 minut

---

### 16. Temporal Decay Division by Zero
**Lokalizacja:** `app/services/memory_service_langchain.py:175`

**Problem:**
```python
time_diff = (current_time - event.timestamp).total_seconds()
decay_factor = np.exp(-time_diff / (30 * 24 * 3600))  # ❌ Jeśli time_diff = 0?
```

Jeśli event timestamp == current_time (dokładnie ta sama sekunda), `time_diff = 0` → `exp(0) = 1.0` (OK).

Ale jeśli używamy `time_diff` w innym miejscu (np. dzielenie), może być problem.

**Wpływ:**
- ✅ Aktualnie OK (exp(0) = 1.0)
- ⚠️ Ale w linii 186: `"age_days": time_diff / (24 * 3600)` może dać 0.0 → potencjalnie misleading

**Rozwiązanie:**
```python
# ✅ Dodaj small epsilon dla edge cases
time_diff = max((current_time - event.timestamp).total_seconds(), 0.001)  # Min 1ms
```

**Czas implementacji:** 2 minuty

---

## 🔧 CODE QUALITY (Priorytet: Niski)

### 17. Brak Custom Exception Types
**Lokalizacja:** Wszędzie w projekcie

**Problem:**
Wszystkie błędy używają generic exceptions:
```python
raise ValueError("Focus group not found")  # ❌
raise RuntimeError("LLM call failed")  # ❌
```

Trudno catch specific errors:
```python
try:
    await service.run_focus_group(...)
except ValueError:  # ❌ Czy to "not found" czy "invalid input"?
    pass
```

**Rozwiązanie:**
Utwórz custom exception hierarchy:

```python
# ✅ app/core/exceptions.py (nowy plik)
class MarketResearchError(Exception):
    """Base exception for all domain errors"""
    pass

class ResourceNotFoundError(MarketResearchError):
    """Resource not found (404-like)"""
    pass

class ValidationError(MarketResearchError):
    """Input validation failed (422-like)"""
    pass

class LLMError(MarketResearchError):
    """LLM API call failed"""
    pass

class LLMTimeoutError(LLMError):
    """LLM call exceeded timeout"""
    pass

class DatabaseError(MarketResearchError):
    """Database operation failed"""
    pass

# ✅ Użycie
from app.core.exceptions import ResourceNotFoundError

if not focus_group:
    raise ResourceNotFoundError(f"Focus group {focus_group_id} not found")

# ✅ W API handler (app/main.py)
from app.core.exceptions import ResourceNotFoundError, ValidationError

@app.exception_handler(ResourceNotFoundError)
async def handle_not_found(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(ValidationError)
async def handle_validation(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})
```

**Czas implementacji:** 2 godziny (refactor wszystkich raise statements)
**Benefit:** Lepsze error handling, czytelniejszy kod

---

### 18. Mixing Languages w Docstringach
**Lokalizacja:** Cały projekt

**Problem:**
- Docstringi po polsku: `"""Zarządza symulacjami grup fokusowych"""`
- Kod po angielsku: `def run_focus_group(...)`
- Komentarze mixed: `# Pobierz relevantny kontekst z pamięci`

**Wpływ:**
- ⚠️ Trudność dla international contributors
- ⚠️ IDE suggestions po polsku (confusing)
- ⚠️ Niespójna konwencja

**Rozwiązanie:**
Zdecyduj się na jeden język (rekomendacja: English) i przetłumacz wszystko.

**Opcja 1: Automatyczna translacja**
```bash
# Użyj script do translacji docstringów
python scripts/translate_docstrings.py --from pl --to en
```

**Opcja 2: Stopniowa migracja**
- Nowy kod tylko po angielsku
- Stary kod tłumacz przy każdej edycji

**Czas implementacji:** 4-8 godzin (automated) lub stopniowo
**Priorytet:** Niski (ale ważne long-term)

---

### 19. Magic Numbers bez Wyjaśnienia
**Lokalizacja:**
- `app/services/graph_service.py:306` → `similarity > 0.5`
- `app/services/graph_service.py:318` → `similarity < -0.3`
- `app/services/graph_service.py:836` → `std_dev > 0.4`

**Problem:**
```python
if similarity > 0.5:  # ❌ Skąd 0.5? Dlaczego nie 0.6 czy 0.4?
    # Create AGREES_WITH relationship
elif similarity < -0.3:  # ❌ Co oznacza -0.3?
    # Create DISAGREES_WITH relationship
```

**Rozwiązanie:**
```python
# ✅ app/core/constants.py
# Graph analysis thresholds
AGREEMENT_THRESHOLD = 0.5  # Similarity score above which personas "agree"
DISAGREEMENT_THRESHOLD = -0.3  # Similarity score below which personas "disagree"
POLARIZATION_THRESHOLD = 0.4  # Std dev above which concept is "controversial"

# Explanation:
# - Agreement threshold 0.5 chosen empirically: represents >50% concept overlap
# - Disagreement -0.3: significant negative correlation in sentiment
# - Polarization 0.4: std dev covering ~35% of sentiment range (-1 to 1)

# ✅ W graph_service.py
from app.core.constants import AGREEMENT_THRESHOLD, DISAGREEMENT_THRESHOLD

if similarity > AGREEMENT_THRESHOLD:
    # Create AGREES_WITH relationship
elif similarity < DISAGREEMENT_THRESHOLD:
    # Create DISAGREES_WITH relationship
```

**Czas implementacji:** 30 minut
**Benefit:** Czytelność, łatwiejsze tuning

---

### 20. Brak Input Sanitization
**Lokalizacja:** `app/services/graph_service.py`, `app/api/*`

**Problem:**
Neo4j queries używają parametryzacji (✅ good), ale brak walidacji inputów:
```python
async def get_graph_data(self, focus_group_id: str, filter_type: Optional[str] = None):
    # ❌ Brak walidacji czy focus_group_id jest valid UUID
    # ❌ Brak walidacji czy filter_type jest z allowed values

    await session.run(
        """MATCH (p:Persona {focus_group_id: $focus_group_id})""",
        focus_group_id=focus_group_id  # Parametryzacja chroni przed injection
    )
```

**Wpływ:**
- ⚠️ Możliwe dziwne error messages przy invalid input
- ⚠️ Niepotrzebne queries do DB

**Rozwiązanie:**
```python
# ✅ app/services/graph_service.py
from uuid import UUID
from typing import Literal

FilterType = Literal["positive", "negative", "influence"]

async def get_graph_data(
    self,
    focus_group_id: str,
    filter_type: Optional[FilterType] = None  # ✅ Type-safe
) -> Dict[str, Any]:
    # Validate UUID
    try:
        UUID(focus_group_id)
    except ValueError:
        raise ValidationError(f"Invalid focus_group_id: {focus_group_id}")

    # Validate filter_type (redundant z Literal, ale explicit)
    allowed_filters = {"positive", "negative", "influence", None}
    if filter_type not in allowed_filters:
        raise ValidationError(f"Invalid filter_type: {filter_type}")

    # ... rest of method
```

**Czas implementacji:** 1 godzina (dla wszystkich endpoints)

---

## 📦 ARCHITEKTURA (Priorytet: Niski - Long Term)

### 21. Tight Coupling między Services
**Lokalizacja:** `app/services/focus_group_service_langchain.py:146`

**Problem:**
```python
# W FocusGroupServiceLangChain.run_focus_group():
from app.services.graph_service import GraphService  # ❌ Direct import
graph_service = GraphService()  # ❌ Direct instantiation
```

FocusGroupService ma hard dependency na GraphService → trudne testowanie, trudno podmienić implementację.

**Rozwiązanie:**
Użyj Dependency Injection:

```python
# ✅ app/services/focus_group_service_langchain.py
from typing import Optional

class FocusGroupServiceLangChain:
    def __init__(self, graph_service: Optional[GraphService] = None):
        self.settings = settings
        self.memory_service = MemoryServiceLangChain()
        self.graph_service = graph_service  # ✅ Injected dependency
        # ...

    async def run_focus_group(self, db: AsyncSession, focus_group_id: str):
        # ... main logic ...

        # ✅ Use injected service if available
        if self.graph_service:
            try:
                async with self.graph_service as gs:
                    await gs.build_graph_from_focus_group(db, focus_group_id)
            except Exception as e:
                logger.error(f"Graph build failed: {e}")

# ✅ W API endpoints (app/api/focus_groups.py)
async def _run_focus_group_task(focus_group_id: UUID):
    async with AsyncSessionLocal() as db:
        async with GraphService() as graph_service:
            service = FocusGroupService(graph_service=graph_service)
            await service.run_focus_group(db, str(focus_group_id))

# ✅ W testach
async def test_focus_group():
    mock_graph_service = MagicMock(spec=GraphService)
    service = FocusGroupService(graph_service=mock_graph_service)
    # ... test bez real Neo4j
```

**Czas implementacji:** 3-4 godziny (refactor + tests)
**Benefit:** Testability, flexibility, SOLID principles

---

### 22. Brak Abstraction Layer dla LLM Providers
**Lokalizacja:** Wszędzie - direct use of `ChatGoogleGenerativeAI`

**Problem:**
```python
# W każdym service:
from langchain_google_genai import ChatGoogleGenerativeAI  # ❌ Tight coupling

self.llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GOOGLE_API_KEY,
    ...
)
```

Jeśli chcesz przełączyć na OpenAI/Anthropic/local model → musisz zmienić każdy service.

**Rozwiązanie:**
Utwórz abstraction layer:

```python
# ✅ app/core/llm_factory.py (nowy plik)
from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

class LLMProvider(ABC):
    """Abstract base for LLM providers"""

    @abstractmethod
    def create_llm(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> BaseChatModel:
        pass

class GoogleProvider(LLMProvider):
    def create_llm(self, model: str, **kwargs) -> BaseChatModel:
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=settings.GOOGLE_API_KEY,
            **kwargs
        )

class OpenAIProvider(LLMProvider):
    def create_llm(self, model: str, **kwargs) -> BaseChatModel:
        return ChatOpenAI(
            model=model,
            openai_api_key=settings.OPENAI_API_KEY,
            **kwargs
        )

def get_llm_provider(provider_name: str = None) -> LLMProvider:
    """Factory function to get LLM provider"""
    provider = provider_name or settings.DEFAULT_LLM_PROVIDER

    providers = {
        "google": GoogleProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }

    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}")

    return providers[provider]()

# ✅ Użycie w services
from app.core.llm_factory import get_llm_provider

class FocusGroupServiceLangChain:
    def __init__(self):
        llm_provider = get_llm_provider()
        self.llm = llm_provider.create_llm(
            model=settings.DEFAULT_MODEL,
            temperature=settings.TEMPERATURE,
            max_tokens=2048
        )
```

**Czas implementacji:** 4-6 godzin
**Benefit:** Provider flexibility, easier testing, future-proof

---

### 23. Business Logic w Models
**Lokalizacja:** `app/models/focus_group.py:90-116`

**Problem:**
```python
# W SQLAlchemy model:
class FocusGroup(Base):
    # ... fields ...

    def meets_performance_requirements(self) -> bool:  # ❌ Business logic w modelu
        thresholds = {
            "total_execution_time_ms": 30_000,
            "avg_response_time_ms": 3_000.0,
        }
        # ... validation logic
```

Models powinny być "dumb" data containers. Business logic należy do service layer.

**Rozwiązanie:**
```python
# ✅ app/models/focus_group.py - tylko data
class FocusGroup(Base):
    # ... fields only, no methods

# ✅ app/services/focus_group_validator.py (nowy plik)
from app.models import FocusGroup
from app.core.config import get_settings

settings = get_settings()

class FocusGroupValidator:
    """Business logic for focus group validation"""

    PERFORMANCE_THRESHOLDS = {
        "total_execution_time_ms": 30_000,  # 30 seconds
        "avg_response_time_ms": 3_000.0,    # 3 seconds
    }

    @classmethod
    def meets_performance_requirements(cls, focus_group: FocusGroup) -> bool:
        """Check if focus group meets performance SLAs"""
        if focus_group.total_execution_time_ms is None:
            return False

        if focus_group.total_execution_time_ms > cls.PERFORMANCE_THRESHOLDS["total_execution_time_ms"]:
            return False

        if (focus_group.avg_response_time_ms is not None
            and focus_group.avg_response_time_ms > cls.PERFORMANCE_THRESHOLDS["avg_response_time_ms"]):
            return False

        return True

    @classmethod
    def get_performance_report(cls, focus_group: FocusGroup) -> Dict[str, Any]:
        """Detailed performance analysis"""
        return {
            "meets_requirements": cls.meets_performance_requirements(focus_group),
            "total_time_ms": focus_group.total_execution_time_ms,
            "total_time_vs_threshold": {
                "actual": focus_group.total_execution_time_ms,
                "threshold": cls.PERFORMANCE_THRESHOLDS["total_execution_time_ms"],
                "percentage": (focus_group.total_execution_time_ms /
                             cls.PERFORMANCE_THRESHOLDS["total_execution_time_ms"] * 100)
            },
            # ... more metrics
        }

# ✅ Użycie w API
from app.services.focus_group_validator import FocusGroupValidator

@router.get("/focus-groups/{id}")
async def get_focus_group(id: UUID, db: AsyncSession = Depends(get_db)):
    fg = await db.get(FocusGroup, id)
    return {
        "id": fg.id,
        # ...
        "performance": FocusGroupValidator.get_performance_report(fg)
    }
```

**Czas implementacji:** 2 godziny
**Benefit:** Separation of concerns, testability, maintainability

---

## 🎯 DODATKOWE USPRAWNIENIA

### 24. Health Checks dla External Services
**Implementacja:** Zobacz rozwiązanie w #6 (startup validation)

### 25. Rate Limiting dla Gemini API
```python
# ✅ app/core/rate_limiter.py
import asyncio
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window  # seconds
        self.calls = deque()

    async def acquire(self):
        """Wait until we can make a call"""
        now = datetime.now()

        # Remove old calls outside time window
        while self.calls and (now - self.calls[0]) > timedelta(seconds=self.time_window):
            self.calls.popleft()

        # If at limit, wait
        if len(self.calls) >= self.max_calls:
            sleep_time = (self.calls[0] + timedelta(seconds=self.time_window) - now).total_seconds()
            await asyncio.sleep(sleep_time)
            return await self.acquire()

        # Record this call
        self.calls.append(now)

# Użycie w llm_factory.py:
gemini_rate_limiter = RateLimiter(max_calls=60, time_window=60)  # 60 calls/minute

async def call_llm_with_timeout(...):
    await gemini_rate_limiter.acquire()  # Wait if needed
    return await asyncio.wait_for(llm_func(...), timeout=timeout)
```

### 26. Monitoring/Observability
```python
# ✅ Dodaj OpenTelemetry tracing
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup w main.py:
provider = TracerProvider()
jaeger_exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# Użycie w services:
@tracer.start_as_current_span("generate_persona_response")
async def _get_persona_response(self, persona, question, focus_group_id):
    # ... kod jest automatycznie tracowany
```

### 27. Integration Tests
```python
# ✅ tests/integration/test_focus_group_flow.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
async def test_full_focus_group_flow(async_client: AsyncClient):
    """Test complete focus group workflow end-to-end"""

    # 1. Create project
    project_resp = await async_client.post("/api/v1/projects", json={
        "name": "Test Project",
        "target_demographics": {...},
        "target_sample_size": 5
    })
    project_id = project_resp.json()["id"]

    # 2. Generate personas
    personas_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/personas/generate",
        json={"num_personas": 5}
    )
    assert personas_resp.status_code == 200

    # 3. Create focus group
    fg_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/focus-groups",
        json={
            "name": "Test FG",
            "questions": ["What do you think about pizza?"],
            "persona_ids": [...]
        }
    )
    fg_id = fg_resp.json()["id"]

    # 4. Run focus group
    run_resp = await async_client.post(f"/api/v1/focus-groups/{fg_id}/run")
    assert run_resp.status_code == 202

    # 5. Poll for completion
    for _ in range(60):  # Max 60 seconds
        status_resp = await async_client.get(f"/api/v1/focus-groups/{fg_id}")
        status = status_resp.json()["status"]
        if status == "completed":
            break
        await asyncio.sleep(1)

    assert status == "completed"

    # 6. Verify graph was built
    graph_resp = await async_client.get(f"/api/v1/graph/{fg_id}/concepts")
    assert len(graph_resp.json()["concepts"]) > 0
```

---

## 📊 PODSUMOWANIE PRIORYTETÓW

### 🔴 KRYTYCZNE (Do naprawy natychmiast):
1. ✅ #1: Duplikacja graph building (5 min)
2. ✅ #2: Wyciek połączeń Neo4j (20 min)
3. ✅ #3: Race condition w event sourcing (45 min)
4. ✅ #4: Hardcoded credentials (30 min)

**Total: ~1.5 godziny** → Napraw dziś!

### ⚠️ WYSOKIE (Do naprawy w tym tygodniu):
5. ✅ #5: Error handling w background tasks (1h)
6. ✅ #6: Walidacja API keys (45 min)
7. ✅ #7: N+1 queries w Neo4j (2h)
8. ✅ #8: Timeouty dla LLM (1h)

**Total: ~5 godzin** → Sprint task

### 📊 ŚREDNIE (Nice to have):
9-16: Performance improvements (łącznie ~5-8 godzin)

### 🔧 NISKIE (Long-term refactoring):
17-23: Code quality & architecture (~15-20 godzin)

---

## 🚀 REKOMENDOWANY PLAN DZIAŁANIA

### Faza 1 (Dzisiaj - Krytyczne):
1. Usuń duplikację graph building (#1)
2. Dodaj context manager dla GraphService (#2)
3. Dodaj SELECT FOR UPDATE w memory service (#3)
4. Przenieś credentials do .env (#4)

### Faza 2 (Ten tydzień - Wysokie):
5. Dodaj retry logic z tenacity (#5)
6. Dodaj startup validation (#6)
7. Refactor Neo4j do bulk ops (#7)
8. Dodaj LLM timeouts (#8)

### Faza 3 (Następny sprint - Optymalizacje):
9-16: Performance improvements według potrzeb

### Faza 4 (Długoterminowe - Q1 2025):
17-23: Code quality refactoring stopniowo

---

## 📝 NOTATKI

- Kod jest ogólnie dobrej jakości, dobrze zorganizowany
- Główne problemy to: duplikacje, resource leaks, error handling
- Architektura jest solidna, ale może być bardziej SOLID-compliant
- Dokumentacja (docstringi) jest bardzo dobra, ale w polskim języku
- Testy unit są obecne, brakuje integration tests

**Szacowany czas na wszystkie critical fixes:** 1-2 dni robocze
**Szacowany impact:** 50%+ redukcja kosztów API, 100% reliability improvement

---

**Koniec raportu**