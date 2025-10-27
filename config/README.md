# Config System - Centralized Configuration

Centralny system konfiguracji dla Market Research SaaS - wszystkie prompty, modele, parametry LLM i RAG w jednym miejscu.

## 🎯 Cel

**Przed:** Prompty i parametry hardcode'owane w kodzie - trudne do edycji, brak wersjonowania.
**Po:** Wszystko w `config/` - łatwa edycja, versioning, walidacja, reprodukowalność.

## 📁 Struktura Katalogów

```
config/
├── README.md                   # Ten plik
├── models.yaml                 # Model registry (fallback chain)
├── pricing.yaml                # Model pricing (USD/1M tokens)
├── features.yaml               # Feature flags
├── logging.yaml                # Logging configuration
├── providers.yaml              # LLM providers (klucze API)
├── app.yaml                    # Global app settings
│
├── env/                        # Environment overrides
│   ├── development.yaml        # Dev env (DEBUG logs, dłuższe timeouts)
│   ├── staging.yaml
│   └── production.yaml         # Prod env (INFO logs, Pro models)
│
├── prompts/                    # Wszystkie prompty (23 pliki)
│   ├── system/                 # System prompts (9)
│   │   ├── market_research_expert.yaml
│   │   ├── polish_society_expert.yaml
│   │   ├── quality_control.yaml
│   │   └── ...
│   ├── personas/               # Persona prompts (6)
│   │   ├── jtbd.yaml
│   │   ├── orchestration.yaml
│   │   ├── segment_brief.yaml
│   │   └── ...
│   ├── focus_groups/           # Focus group prompts (2)
│   │   ├── persona_response.yaml
│   │   └── discussion_summary.yaml
│   ├── rag/                    # RAG prompts (2)
│   │   ├── cypher_generation.yaml
│   │   └── graph_rag_answer.yaml
│   └── surveys/                # Survey prompts (4)
│       ├── single_choice.yaml
│       ├── multiple_choice.yaml
│       ├── rating_scale.yaml
│       └── open_text.yaml
│
├── rag/                        # RAG configuration
│   ├── graph_transformer.yaml  # LLMGraphTransformer config
│   ├── retrieval.yaml          # Chunking, hybrid search, reranking
│   └── queries/                # Pre-defined Cypher queries
│       └── demographic_context.cypher
│
├── demographics/               # Demographics data
│   ├── poland.yaml             # POLISH_* constants
│   └── international.yaml      # DEFAULT_* constants
│
└── schema/                     # JSON Schemas dla walidacji
    ├── prompt.schema.json
    └── model.schema.json
```

## 🚀 Quick Start

### 1. Używanie Promptów

```python
from config import prompts

# Pobierz prompt
prompt_template = prompts.get("surveys.single_choice")

# Renderuj z variables (Jinja2, custom delimiters: ${var})
rendered_messages = prompt_template.render(
    persona_context="Kobieta, 28 lat, Marketing Manager...",
    question="Jak często korzystasz z social media?",
    description="",
    options="- Codziennie\n- Kilka razy w tygodniu\n- Rzadko"
)

# Użyj w LangChain
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    (msg["role"], msg["content"]) for msg in rendered_messages
])
```

### 2. Używanie Modeli

```python
from config import models
from app.services.shared.clients import build_chat_model

# Pobierz model config (fallback chain: domain.subdomain → domain.default → global.default)
model_config = models.get("personas", "orchestration")

# Build LLM
llm = build_chat_model(**model_config.params)
```

### 3. Używanie RAG Config

```python
from config import rag

# Chunking
chunk_size = rag.chunking.chunk_size  # 1000
chunk_overlap = rag.chunking.chunk_overlap  # 300

# Retrieval
top_k = rag.retrieval.top_k  # 8
use_hybrid = rag.retrieval.use_hybrid_search  # True

# Graph Transformer
allowed_nodes = rag.graph_transformer.allowed_nodes  # ["Obserwacja", "Wskaznik", ...]
additional_instructions = rag.graph_transformer.additional_instructions

# Cypher queries
demographic_query = rag.queries["demographic_context"]
```

## 📝 Format Promptów (YAML)

Każdy prompt to plik YAML w `config/prompts/`:

```yaml
id: surveys.single_choice
version: "1.0.0"
description: "Generate single-choice survey response as a specific persona"
messages:
  - role: system
    content: |
      You are answering a survey question as a specific persona...
  - role: user
    content: |
      Persona Profile:
      ${persona_context}

      Question: ${question}
      ${description}

      Options:
      ${options}
```

**Kluczowe cechy:**
- **Placeholders**: `${variable}` (custom Jinja2 delimiters, bezpieczne dla Cypher)
- **Versioning**: Semantic versioning (auto-bump przy zmianie hash)
- **Hashing**: SHA256 hash content'u dla version detection
- **Walidacja**: JSON Schema validation (`scripts/config_validate.py`)

## 🔧 Model Configuration (models.yaml)

Fallback chain: **domain.subdomain → domain.default → global.default**

```yaml
defaults:
  chat:
    model: "gemini-2.5-flash"
    temperature: 0.7
    max_tokens: 6000
    timeout: 60
    retries: 3

domains:
  personas:
    generation:
      model: "gemini-2.5-flash"
      temperature: 0.8

    orchestration:
      model: "gemini-2.5-pro"    # Complex reasoning
      temperature: 0.3            # Niższa dla analytical tasks
      max_tokens: 8000
      timeout: 120

  surveys:
    response:
      model: "gemini-2.5-flash"

  rag:
    graph:
      model: "gemini-2.5-flash"
      temperature: 0.1            # Bardzo niska dla Cypher generation
```

**Przykład użycia:**
```python
models.get("personas", "orchestration")  # → gemini-2.5-pro, temp=0.3
models.get("personas", "jtbd")           # → fallback do generation → gemini-2.5-flash, temp=0.8
models.get("surveys", "response")        # → gemini-2.5-flash (domain default)
models.get("unknown", "unknown")         # → fallback do defaults.chat
```

## 🌍 Environment Overrides

Kolejność precedencji (highest → lowest):
1. **Environment variables** (e.g., `GOOGLE_API_KEY`)
2. **env/{environment}.yaml** (e.g., `env/production.yaml`)
3. **Base config** (e.g., `models.yaml`)
4. **Code defaults**

**Development** (`env/development.yaml`):
```yaml
models:
  defaults:
    chat:
      timeout: 120  # Dłuższy dla debugging

logging:
  level: "DEBUG"
  structured: false  # Human-readable
```

**Production** (`env/production.yaml`):
```yaml
models:
  defaults:
    chat:
      model: "gemini-2.5-pro"  # Lepszy model w prod

logging:
  level: "INFO"
  structured: true  # JSON dla Cloud Logging
```

## ✅ Walidacja

```bash
# Validate wszystkie configs
python scripts/config_validate.py

# Check placeholders w promptach
python scripts/config_validate.py --check-placeholders

# Auto-bump versions gdy hash się zmienił
python scripts/config_validate.py --auto-bump
```

**Validation rules:**
- Prompty: required fields (id, version, description, messages), ID format, version semver
- Models: defaults.chat.model exists, valid temperature/timeout ranges
- Placeholders: strict mode - błąd jeśli brakuje variable

## 💰 Pricing Configuration (pricing.yaml)

Model pricing dla tracking kosztów LLM operations:

```yaml
models:
  gemini-2.5-flash:
    input_price_per_million: 0.075   # $0.075 per 1M input tokens
    output_price_per_million: 0.30   # $0.30 per 1M output tokens

  gemini-2.5-pro:
    input_price_per_million: 1.25    # $1.25 per 1M input tokens
    output_price_per_million: 5.00   # $5.00 per 1M output tokens

budget_alerts:
  warning_threshold: 0.8   # Alert at 80% budget usage
  critical_threshold: 0.9  # Critical at 90%
```

**Usage:**
```python
from config.loader import ConfigLoader

pricing = ConfigLoader().load_yaml("pricing.yaml")
input_cost = pricing["models"]["gemini-2.5-flash"]["input_price_per_million"]

# Auto-loaded w UsageTrackingService
from app.services.dashboard.usage_tracking_service import MODEL_PRICING
```

## ⚙️ Feature Flags (features.yaml)

Feature flags, performance targets, RAG settings:

```yaml
# Performance targets
performance:
  max_response_time_per_persona: 3
  consistency_error_threshold: 0.05
  random_seed: 42

# RAG system
rag:
  enabled: true
  chunk_size: 1000
  chunk_overlap: 300
  top_k: 8
  use_hybrid_search: true
  vector_weight: 0.7
  use_reranking: true

# Cache
cache:
  segment_brief_enabled: true
  segment_brief_ttl: 604800  # 7 days
  redis_max_connections: 50
```

**Usage:**
```python
from config.loader import ConfigLoader

features = ConfigLoader().load_yaml("features.yaml")
rag_enabled = features["rag"]["enabled"]
```

## 🧪 A/B Testing Promptów

Twórz warianty promptów dla testów:

**1. Utwórz plik variant:**
```
config/prompts/system/market_research_expert_variant_b.yaml
```

**2. Format pliku variant:**
```yaml
id: system.market_research_expert
version: "1.1.0"
variant: "b"        # Nazwa variantu
weight: 1.0         # Waga dla weighted selection
description: "More concise expert prompt"
messages:
  - role: system
    content: |
      You are a market research expert. Be concise.
```

**3. Usage:**
```python
from config import prompts

# Random weighted selection (50/50 dla weight=1.0 każdy)
prompt = prompts.get("system.market_research_expert")

# Lub konkretny variant
prompt = prompts.get("system.market_research_expert", variant="b")
```

**Naming convention:**
- Base prompt: `{name}.yaml`
- Variant: `{name}_variant_{x}.yaml`

## 🎨 Jak Dodać Nowy Prompt

1. **Stwórz plik YAML** w `config/prompts/{domain}/{name}.yaml`:

```yaml
id: focus_groups.moderator
version: "1.0.0"
description: "Moderator prompt for focus group discussions"
messages:
  - role: system
    content: |
      You are an experienced focus group moderator...
  - role: user
    content: |
      Discussion topic: ${topic}
      Participants: ${participant_count}
```

2. **Używaj w kodzie:**

```python
from config import prompts

prompt_template = prompts.get("focus_groups.moderator")
rendered = prompt_template.render(
    topic="AI in healthcare",
    participant_count="8"
)
```

3. **Waliduj:**

```bash
python scripts/config_validate.py
```

## 🔄 Jak Dodać Nowy Model

1. **Edit `config/models.yaml`:**

```yaml
domains:
  new_domain:
    subdomain:
      model: "gemini-2.5-flash"
      temperature: 0.7
      max_tokens: 4000
```

2. **Użyj w kodzie:**

```python
from config import models

model_config = models.get("new_domain", "subdomain")
llm = build_chat_model(**model_config.params)
```

## 📊 Pricing Configuration

`config/pricing.yaml` - używane w usage tracking:

```yaml
models:
  gemini-2.5-flash:
    input_price_per_million: 0.075   # $0.075 per 1M tokens
    output_price_per_million: 0.30   # $0.30 per 1M tokens

  gemini-2.5-pro:
    input_price_per_million: 1.25    # $1.25 per 1M tokens
    output_price_per_million: 5.00   # $5.00 per 1M tokens
```

## 🚩 Feature Flags

`config/features.yaml`:

```yaml
rag:
  enabled: true
  node_properties_enabled: true

segment_cache:
  enabled: true
  ttl_days: 7

performance:
  max_focus_group_time: 30
  random_seed: 42
```

## 📚 Przykład Migracji

**Przed** (hardcode):
```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are answering a survey..."),
    ("user", f"Question: {question}\nOptions: {options}")
])
```

**Po** (config):
```python
from config import prompts

prompt_template = prompts.get("surveys.single_choice")
rendered_messages = prompt_template.render(
    persona_context=context,
    question=question,
    options="\n".join(f"- {opt}" for opt in options)
)

prompt = ChatPromptTemplate.from_messages([
    (msg["role"], msg["content"]) for msg in rendered_messages
])
```

## 🧪 Testing

**Test promptów:**
```python
from config import prompts

# Load prompt
prompt = prompts.get("surveys.single_choice")

# Check hash
assert prompt.hash == "abc123..."

# Test rendering
rendered = prompt.render(
    persona_context="Test persona",
    question="Test question",
    options="- Option 1\n- Option 2"
)

assert len(rendered) == 2  # system + user messages
```

**Test modeli:**
```python
from config import models

model_config = models.get("surveys", "response")

assert model_config.model == "gemini-2.5-flash"
assert model_config.temperature == 0.7
```

## 🔑 Best Practices

1. **Nie hardcode'uj promptów** - zawsze używaj PromptRegistry
2. **Nie hardcode'uj modeli** - używaj ModelRegistry
3. **Waliduj przed commit** - `python scripts/config_validate.py`
4. **Bump version manualnie** lub używaj `--auto-bump`
5. **Testuj po zmianach** - upewnij się że placeholders są poprawne
6. **Environment overrides** - różne modele dla dev/staging/prod
7. **Secrets w env** - NIGDY nie commituj API keys do repo

## 📖 Architecture

```
Code
  ↓
config.prompts.get("domain.name")
  ↓
PromptRegistry (cache + version + hash)
  ↓
Load YAML from config/prompts/{domain}/{name}.yaml
  ↓
Render with Jinja2 (${var} delimiters)
  ↓
Return rendered messages
  ↓
Use in LangChain
```

**Fallback chain dla modeli:**
```
models.get("personas", "orchestration")
  ↓
1. Try: domains.personas.orchestration  ✅ Found!
2. If not: domains.personas.generation
3. If not: defaults.chat
```

## 🛠️ Troubleshooting

**Problem: `Prompt not found`**
```
Solution: Check ID format - must be "domain.name"
Example: "surveys.single_choice" (NOT "single_choice")
```

**Problem: `Missing required variable`**
```
Solution: Check placeholders - all ${var} must be provided
Use --check-placeholders to see required variables
```

**Problem: `Model not found`**
```
Solution: Models.get() will fallback to defaults.chat + WARNING
Check models.yaml for correct domain/subdomain structure
```

## 📞 Support

- **Validation errors:** Run `python scripts/config_validate.py --check-placeholders`
- **Prompt issues:** Check YAML syntax in config/prompts/
- **Model issues:** Verify fallback chain in config/models.yaml
- **Environment:** Check `ENVIRONMENT` env var and env/*.yaml overrides
