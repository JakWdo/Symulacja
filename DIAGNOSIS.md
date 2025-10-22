# Cloud Run Deployment - Diagnoza Problemu

**Data:** 2025-10-22
**Branch:** refactor/cloud-run-diagnosis
**Status:** 🔴 CRITICAL - Aplikacja nie startuje

---

## 🔴 Problem #1: IndentationError (BLOKER)

**Typ:** Syntax Error
**Lokalizacja:** `app/api/personas.py` (lub podobny plik w strukturze personas/)
**Błąd:**

```python
File "/app/app/api/personas.py", line 977
    target_audience_desc = None
    ^^^^^^^^^^^^^^^^^^^^
IndentationError: expected an indented block after 'try' statement on line 975
```

**Impact:**
- Aplikacja **nie ładuje się w ogóle** (gunicorn workers fail to boot)
- Wszystkie requesty kończą się błędem: "HTTP response was malformed or connection to the instance had an error"
- Cloud Run service status: `True` ale wszystkie rewizje crashują przy starcie

**Root Cause:**
- Syntax error w kodzie Python - pusty blok `try:` bez `pass` lub kodu
- Prawdopodobnie niedokończona edycja/refaktoryzacja

**Rozwiązanie:**
1. Znaleźć plik z błędem (sprawdzić `app/api/personas/*.py`)
2. Dodać `pass` lub uzupełnić implementację w bloku try (linia 975-977)
3. Redeploy

---

## 🟡 Problem #2: Historyczne błędy API (Rozwiązane?)

### 2.1 Expired Google API Key (2025-10-21 21:23)

```
google.api_core.exceptions.InvalidArgument: 400 API key expired. Please renew the API key.
[reason: "API_KEY_INVALID"]
```

**Status:** Prawdopodobnie naprawione (nie występuje w najnowszych logach)
**Lokalizacja:** `app/services/rag/rag_clients.py:75` (Neo4jVector initialization)

### 2.2 LLMGraphTransformer - Unexpected Argument (2025-10-21 19:06)

```python
TypeError: LLMGraphTransformer.__init__() got an unexpected keyword argument 'additional_instructions'
```

**Root Cause:**
- Niekompatybilna wersja `langchain-experimental`
- `additional_instructions` dodany w nowszej wersji LangChain

**Status:** Nieznany (może być nadal aktualny)

### 2.3 Neo4j Connection - Invalid Model Name (2025-10-21 18:15)

```
google.api_core.exceptions.InvalidArgument: 400 * BatchEmbedContentsRequest.model: unexpected model name format
```

**Root Cause:**
- Nieprawidłowy format nazwy modelu embeddings w konfiguracji
- Prawdopodobnie problem z `EMBEDDING_MODEL` env variable

---

## ✅ Infrastruktura - Stan Obecny

### Cloud Run Service: `sight`
- **URL:** https://sight-3mdroghbqa-lm.a.run.app
- **Region:** europe-central2
- **Status:** True (ale workers crashują)
- **Latest Revision:** sight-00021-n6k

### Zasoby
- **Memory:** 4Gi ✅
- **CPU:** 2 ✅
- **Max Instances:** 5 ✅
- **Timeout:** Default (prawdopodobnie 300s)

### Environment Variables (Non-Secret)
```
NEO4J_USER
ENVIRONMENT
DEBUG
DEFAULT_LLM_PROVIDER
DEFAULT_MODEL
GRAPH_MODEL
PERSONA_GENERATION_MODEL
ANALYSIS_MODEL
EMBEDDING_MODEL
TEMPERATURE
MAX_TOKENS
RAG_ENABLED
RAG_USE_HYBRID_SEARCH
RAG_CHUNK_SIZE
RAG_CHUNK_OVERLAP
RAG_TOP_K
RAG_VECTOR_WEIGHT
RAG_RRF_K
```

### Secrets (z Secret Manager)
```
DATABASE_URL → DATABASE_URL_CLOUD
GOOGLE_API_KEY → GOOGLE_API_KEY
NEO4J_PASSWORD → NEO4J_PASSWORD
NEO4J_URI → NEO4J_URI
POSTGRES_PASSWORD → POSTGRES_PASSWORD
REDIS_URL → REDIS_URL
SECRET_KEY → SECRET_KEY
```

**Ocena:** ✅ Wszystkie secrets skonfigurowane poprawnie

---

## 📊 Analiza Logów

### Częstotliwość błędów (2025-10-21 do 2025-10-22)

1. **IndentationError** - 12+ wystąpień (ostatnie: 2025-10-22 10:52:43)
   - Blokuje całkowicie uruchomienie aplikacji
   - Pojawia się przy każdej próbie startu worker'a

2. **Malformed response errors** - 15+ wystąpień
   - Wynika z IndentationError (aplikacja się nie ładuje)
   - Cloud Run nie może otrzymać odpowiedzi na health check

3. **API key expired** - 1 wystąpienie (2025-10-21 21:23)
   - Prawdopodobnie naprawione

4. **LLMGraphTransformer error** - 1 wystąpienie (2025-10-21 19:06)
   - Może być nadal aktualny

5. **Neo4j model name error** - 2 wystąpienia (2025-10-21 18:15)
   - Może być nadal aktualny

---

## 🎯 Plan Naprawy - Quick Fix

### Krok 1: Naprawa IndentationError (CRITICAL)

```bash
# 1. Znajdź plik z błędem
grep -rn "try:" app/api/personas/ | grep -A 2 "975"

# 2. Napraw syntax error
# Dodaj 'pass' lub implementację w bloku try na linii 975

# 3. Commit i push
git add app/api/personas/*.py
git commit -m "fix: IndentationError w personas API (linia 975)"
git push
```

### Krok 2: Weryfikacja LangChain Version

```bash
# Sprawdź wersję langchain-experimental
grep "langchain-experimental" requirements.txt

# Jeśli < 0.3.0, zaktualizuj:
# langchain-experimental>=0.3.0
```

### Krok 3: Weryfikacja EMBEDDING_MODEL

```bash
# Sprawdź format modelu w env vars
gcloud run services describe sight --format="json" | grep EMBEDDING_MODEL

# Powinno być np: "models/text-embedding-004"
# Nie: "text-embedding-004" (bez prefixu)
```

### Krok 4: Redeploy

```bash
# Trigger Cloud Build (jeśli skonfigurowany)
gcloud builds submit

# Lub manual deploy
gcloud run deploy sight \
  --source . \
  --region=europe-central2
```

---

## 📋 Plan Refaktoryzacji (Long-term)

Po naprawieniu critical bug'ów, zaplanowana jest pełna refaktoryzacja:

### Cel Główny
- Usunąć zależność od `demographics` jako źródła wejściowego
- Generacja person wyłącznie przez: **RAG/GraphRAG + Model Knowledge**
- Przygotować clean deployment do Cloud Run

### Scope
1. **De-demografizacja** (8-12h)
   - Usunąć `app/core/constants/demographics.py`
   - Usunąć `DemographicDistribution` class
   - Usunąć chi-square validation
   - Drop kolumny z Project: target_demographics, chi_square_statistic, p_values

2. **RAG Hardening** (3-4h)
   - Secret Manager integration
   - Vertex AI Ranking (zamiast sentence-transformers 900MB)
   - Graceful degradation enhancement

3. **Docker & Cloud Run** (3-4h)
   - $PORT support (Cloud Run dynamic port)
   - gunicorn w requirements.txt
   - Health checks (/health, /ready)
   - cloudbuild.yaml

4. **Testing & Docs** (4-6h)
   - Usuń testy demographics
   - Cleanup legacy docs
   - Utworzyć PLAN.md, DEPLOYMENT_CLOUD_RUN.md

**Total:** 18-26h (3-4 dni robocze)

---

## 🔍 Następne Kroki

1. ✅ **Diagnoza complete** - Ten dokument
2. 🔴 **Quick Fix** - Naprawa IndentationError (30 min)
3. 🟡 **Verification** - Weryfikacja LangChain i EMBEDDING_MODEL (30 min)
4. 🟢 **Redeploy** - Test deployment (1h)
5. 📋 **Refaktoryzacja** - Full refactor według planu (18-26h)

---

## 📞 Kontakt & Status

**Branch:** refactor/cloud-run-diagnosis
**Assigned:** Claude Code
**Priority:** P0 (Critical)
**ETA Quick Fix:** 1-2h
**ETA Full Refactor:** 3-4 dni robocze

**Last Updated:** 2025-10-22 14:30 CET
