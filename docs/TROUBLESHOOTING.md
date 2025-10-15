# 🐛 Troubleshooting Guide

Comprehensive troubleshooting guide dla Market Research SaaS - od common issues do advanced debugging.

---

## 📋 Spis Treści

1. [Common Issues](#common-issues)
   - Backend Won't Start
   - Environment Variables
   - Persona Generation Failures
   - Neo4j Connection Errors
   - Frontend Module Errors
   - UI/UX Issues
2. [Performance Issues](#performance-issues)
3. [Data Issues](#data-issues)
4. [LLM/AI Specific Problems](#llmai-specific-problems)
5. [Docker & Infrastructure](#docker--infrastructure)
6. [Getting Help](#getting-help)

---

## 🔧 Common Issues

### 1. Backend Won't Start

**Symptoms:**
- API container exits immediately after `docker-compose up`
- Status shows `Exit 1` or `Exit 137` (OOM)
- Frontend shows "Failed to fetch" errors

**Possible Causes:**
- Database not ready (Postgres/Redis/Neo4j still initializing)
- Missing or incorrect environment variables
- Port 8000 already in use by another process
- Out of memory (Docker desktop limit too low)

**Solutions:**

```bash
# Step 1: Check database health
docker-compose ps
# All services should show "healthy" (not just "up")

# Step 2: Check API logs for specific error
docker-compose logs api | tail -50

# Step 3: Restart databases first, then API
docker-compose restart postgres redis neo4j
sleep 15  # Wait for databases to initialize
docker-compose up -d api

# Step 4: If still failing, check port conflicts
lsof -i :8000  # Check if port 8000 is in use
# If in use: kill the process or change API port in docker-compose.yml

# Step 5: Check Docker memory limit
# Docker Desktop → Settings → Resources → Memory
# Increase to at least 4GB for all services
```

**Advanced Debugging:**

```bash
# Enter API container for interactive debugging
docker-compose exec api /bin/bash

# Check Python dependencies
pip list

# Test database connections manually
python -c "from app.db.session import get_db_session; print('DB OK')"
python -c "import redis; r=redis.from_url('redis://redis:6379'); print('Redis OK')"

# Check environment variables
env | grep -E "GOOGLE_API_KEY|DATABASE_URL|NEO4J"
```

---

### 2. Environment Variables

#### 2.1. "GOOGLE_API_KEY not found" Error

**Symptom:**
```
ValueError: GOOGLE_API_KEY environment variable not set
```

**Solutions:**

```bash
# Verify .env file exists
ls -la .env

# Check if GOOGLE_API_KEY is set (should NOT be empty)
grep GOOGLE_API_KEY .env

# If missing or empty, add it:
echo "GOOGLE_API_KEY=your_actual_gemini_api_key_here" >> .env

# IMPORTANT: No spaces around = sign!
# ✅ CORRECT: GOOGLE_API_KEY=abc123
# ❌ WRONG:   GOOGLE_API_KEY = abc123

# Restart API to apply changes
docker-compose restart api

# Verify key is loaded
docker-compose exec api env | grep GOOGLE_API_KEY
```

#### 2.2. "Invalid API Key" from Gemini

**Symptom:**
```
google.api_core.exceptions.PermissionDenied: 403 API key not valid
```

**Solutions:**

1. **Check key format:**
   - Should start with `AIza...`
   - Length ~39 characters
   - No quotes, no spaces

2. **Verify key in Google AI Studio:**
   - [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
   - Check if key is enabled and not expired

3. **Generate new key:**
   - Sometimes keys are invalidated (rare)
   - Create fresh key in Google AI Studio
   - Update `.env` and restart API

#### 2.3. Other Missing Variables

**Common missing vars:**

```bash
# Check all required variables
docker-compose exec api python -c "
from app.core.config import get_settings
settings = get_settings()
print('GOOGLE_API_KEY:', 'SET' if settings.GOOGLE_API_KEY else 'MISSING')
print('DATABASE_URL:', 'SET' if settings.DATABASE_URL else 'MISSING')
print('NEO4J_URI:', 'SET' if settings.NEO4J_URI else 'MISSING')
"
```

---

### 3. Personas Not Generating

**Symptoms:**
- Generation hangs or times out (>60s)
- Error: "RAG service unavailable"
- Error: "Gemini API quota exceeded"
- Empty personas or incomplete data

#### 3.1. Gemini API Quota Exceeded

**Error:**
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**Cause:** Exceeded 15 requests/minute (free tier limit)

**Solutions:**

```bash
# 1. Check quota in Google Cloud Console
# https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas

# 2. Wait 1 minute before retrying
sleep 60

# 3. Generate fewer personas at once (max 20)
# In UI: Set "Liczba person" to 20 instead of 100

# 4. Upgrade to paid tier (if needed)
# Paid tier: 360 RPM = 6x faster generation
```

**Prevention (Development):**
- Generate 5-10 personas for quick tests
- Use `--run-slow` marker only when needed
- Don't run multiple generation tasks simultaneously

#### 3.2. Neo4j Indexes Missing

**Symptom:**
- RAG queries timeout (>30s)
- Error: "No suitable index found"
- Personas generate but lack RAG context

**Solutions:**

```bash
# 1. Recreate Neo4j indexes (SAFE - won't delete data)
python scripts/init_neo4j_indexes.py

# Expected output:
# ✅ Neo4j connected successfully
# ✅ Created vector index: persona_embeddings
# ✅ Created fulltext index: document_fulltext
# ✅ Initialization complete

# 2. Verify indexes exist
docker-compose exec neo4j cypher-shell -u neo4j -p dev_password_change_in_prod

# In cypher-shell:
SHOW INDEXES;

# Should see at least 2 indexes:
# - persona_embeddings (VECTOR)
# - document_fulltext (FULLTEXT)

# 3. If indexes still missing, restart Neo4j
docker-compose restart neo4j
sleep 30  # Neo4j needs time to initialize
python scripts/init_neo4j_indexes.py
```

#### 3.3. RAG Service Unavailable

**Symptom:**
```
ERROR [rag_hybrid_search_service] RAG hybrid search failed: Connection refused
```

**Cause:** Neo4j not running or not healthy

**Solutions:**

```bash
# 1. Check Neo4j status
docker-compose ps neo4j
# Should show "Up" and "healthy"

# 2. Check Neo4j logs
docker-compose logs neo4j | tail -50

# Look for:
# ✅ "Started." - Neo4j ready
# ❌ "Unable to start" - Neo4j failed

# 3. Restart Neo4j
docker-compose restart neo4j

# 4. Wait for healthcheck (may take 30-60s)
watch -n 5 docker-compose ps neo4j

# 5. Test connection manually
docker-compose exec neo4j cypher-shell -u neo4j -p dev_password_change_in_prod
# If connects → Neo4j OK
# If fails → Neo4j unhealthy
```

#### 3.4. Orchestration Service Failed

**Symptom:**
- Personas generate but PersonaReasoningPanel shows "brak reasoning"
- Logs show: "❌ Błąd podczas tworzenia planu alokacji"

**Causes:**
- Gemini 2.5 Pro timeout (prompt too long)
- Invalid JSON response from LLM
- GraphRAG query timeout (>30s)

**Solutions:**

```bash
# 1. Check API logs for orchestration errors
docker-compose logs api | grep orchestration

# Look for:
# ✅ "Plan alokacji utworzony" - LLM odpowiedział poprawnie
# ❌ "JSON parsing failed" - LLM returned invalid JSON
# ❌ "Graph RAG queries przekroczyły timeout" - Neo4j slow

# 2. If JSON parsing fails - regenerate personas
# LLM occasionally returns malformed JSON (rare, <5% cases)
# Solution: Regenerate (retry logic in code handles this)

# 3. If Graph RAG timeout - check Neo4j performance
docker-compose exec neo4j cypher-shell -u neo4j -p dev_password_change_in_prod
# Run slow query test:
MATCH (n) RETURN count(n);
# Should return in <1s

# 4. Nuclear option - restart orchestration components
docker-compose restart api neo4j
```

---

### 4. Neo4j Connection Error

**Symptoms:**
- Error: "ServiceUnavailable: Connection refused"
- Error: "Failed to establish connection to bolt://neo4j:7687"
- RAG queries fail immediately

#### 4.1. Neo4j Not Started

**Solutions:**

```bash
# Neo4j takes 30-60s to initialize (longer than other services)
docker-compose logs neo4j | grep "Started"

# If no "Started" message after 60s:
docker-compose restart neo4j

# Watch logs until you see:
docker-compose logs -f neo4j
# Wait for: "... Started." (last line)
```

#### 4.2. Wrong Credentials

**Symptom:**
```
AuthError: Invalid username or password
```

**Solutions:**

```bash
# Check credentials in .env
grep NEO4J .env

# Default development credentials:
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=dev_password_change_in_prod

# Test connection manually
docker-compose exec neo4j cypher-shell -u neo4j -p dev_password_change_in_prod

# If fails → password wrong
# Reset Neo4j password:
docker-compose down neo4j
docker volume rm market-research-saas_neo4j_data  # WARNING: Deletes graph data!
docker-compose up -d neo4j
```

#### 4.3. Port Conflicts

**Symptom:**
```
Error starting userland proxy: listen tcp 0.0.0.0:7687: bind: address already in use
```

**Solutions:**

```bash
# Check if port 7687 is in use
lsof -i :7687

# If another Neo4j instance running:
# Option 1: Kill other instance
kill <PID>

# Option 2: Change Neo4j port in docker-compose.yml
# ports:
#   - "7688:7687"  # External port 7688, internal 7687
```

---

### 5. Frontend "Module not found" Error

**Symptoms:**
- Frontend container crashes immediately
- Error: `Cannot find module 'react'` or similar
- UI shows blank page or "Failed to compile"

**Causes:**
- `node_modules` not installed
- Conflicting dependencies (host vs container)
- Cached build artifacts corrupted

**Solutions:**

#### Nuclear Option (Recommended, Safe):

```bash
# Stop all services and remove volumes
docker-compose down -v

# Rebuild from scratch
docker-compose up --build -d

# Watch frontend logs
docker-compose logs -f frontend

# Should see:
# ✅ "vite v5.0.0 dev server running at http://localhost:5173"
```

#### Targeted Fix (Faster):

```bash
# Rebuild only frontend
docker-compose up --build -d frontend

# If still failing, clear Docker cache
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

#### Manual Debugging:

```bash
# Enter frontend container
docker-compose exec frontend /bin/sh

# Check node_modules
ls -la /app/node_modules

# Reinstall dependencies
npm install

# Try running dev server manually
npm run dev
```

---

### 6. UI/UX Issues (October 2025 Features)

#### 6.1. PersonaReasoningPanel Shows "No Reasoning"

**Symptom:**
Alert message: "Ta persona nie ma szczegółowego reasoning"

**Causes:**
1. Persona generated before orchestration service was enabled
2. Orchestration service failed during generation (check logs)
3. Gemini 2.5 Pro returned invalid JSON

**Solutions:**

```bash
# 1. Check if orchestration is enabled
docker-compose exec api env | grep ORCHESTRATION
# Should NOT be disabled

# 2. Check API logs for orchestration failures
docker-compose logs api | grep -A 5 "Orchestration:"

# 3. Generate NEW personas (old ones won't have reasoning)
# UI → Create Project → Generate Personas → [new batch]

# 4. Verify new personas have reasoning
# Click persona → Reasoning tab → Should show collapsible sections
```

#### 6.2. Character Counter Not Showing in Wizard

**Symptom:**
No character count visible below "Dodatkowy Opis" textarea

**Causes:**
- Browser cache outdated (stale JavaScript)
- React hydration mismatch

**Solutions:**

```bash
# 1. Hard refresh browser
# Chrome/Firefox: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

# 2. Clear browser cache
# Chrome: DevTools → Network tab → "Disable cache" checkbox

# 3. Check browser console for errors
# F12 → Console tab → Look for React errors

# 4. If errors persist, rebuild frontend
docker-compose restart frontend
```

#### 6.3. Collapsible Sections Don't Expand

**Symptom:**
Clicking chevron icon doesn't expand sections in PersonaReasoningPanel

**Causes:**
- JavaScript error (check browser console)
- Conflicting CSS (rare)

**Solutions:**

```bash
# 1. Check browser console (F12)
# Look for errors like:
# ❌ "Cannot read properties of undefined"

# 2. Verify React Query data loaded
# In browser DevTools → React DevTools → Components
# Find PersonaReasoningPanel → Check `reasoning` prop

# 3. Hard refresh + clear cache
# Ctrl+Shift+R (or Cmd+Shift+R)

# 4. Test with different browser
# Try Firefox/Chrome/Safari to isolate issue
```

#### 6.4. Confidence Colors Not Showing

**Symptom:**
Graph insights lack green/yellow/gray color coding

**Causes:**
- Tailwind CSS not compiled
- Dark mode conflict

**Solutions:**

```bash
# 1. Rebuild frontend (Tailwind recompile)
docker-compose up --build -d frontend

# 2. Check if dark mode enabled
# Toggle dark mode in UI (top right corner)
# Colors should work in both light/dark modes

# 3. Inspect element in DevTools
# Right-click insight → Inspect
# Check if classes applied: "border-green-500", "bg-green-50/50"
```

---

## ⚡ Performance Issues

### 1. Slow Persona Generation (>60s for 20 personas)

**Target:** ~42-45s for 20 personas

**Possible Causes:**
- Gemini API latency (variable, depends on Google infrastructure)
- RAG queries slow (Neo4j not indexed)
- Token usage too high (prompts not optimized)

**Diagnostics:**

```bash
# 1. Check token usage in logs
docker-compose logs api | grep "token"

# Look for:
# ✅ "Token count: 1500" (good - optimized)
# ❌ "Token count: 4000" (bad - bloated prompt)

# 2. Check RAG query times
docker-compose logs api | grep "RAG query"

# Look for:
# ✅ "RAG query completed in 350ms" (good)
# ❌ "RAG query completed in 5000ms" (bad - missing indexes)

# 3. Check Gemini API response times
docker-compose logs api | grep "Gemini response"

# Typical times:
# Flash: 1-3s per request
# Pro: 3-5s per request
```

**Solutions:**

```bash
# If RAG slow → recreate indexes
python scripts/init_neo4j_indexes.py

# Jeśli tokeny rosną → sprawdź logi "Gemini response length"
docker-compose logs api | grep "Gemini response length"
# Dzięki nowemu promptowi powinniśmy zobaczyć ~900-1200 znaków na brief

# If Gemini slow → wait or use fewer personas
# Gemini latency varies 1-5s (nothing we can control)
```

### 2. High Memory Usage

**Symptom:**
- Docker dashboard shows API/Neo4j using >2GB RAM
- System slows down or crashes

**Solutions:**

```bash
# 1. Check current memory usage
docker stats

# Typical usage:
# api:      ~500MB
# postgres: ~200MB
# redis:    ~50MB
# neo4j:    ~1GB (normal - graph database)
# frontend: ~200MB

# 2. Add resource limits to docker-compose.yml
# Edit docker-compose.yml:

services:
  api:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  neo4j:
    environment:
      - NEO4J_server_memory_heap_initial__size=512m
      - NEO4J_server_memory_heap_max__size=1G

# 3. Restart services
docker-compose down
docker-compose up -d

# 4. If still high → increase Docker Desktop memory limit
# Docker Desktop → Settings → Resources → Memory
# Increase to 6-8GB total
```

### 3. Slow UI/Frontend Lag

**Symptom:**
- UI freezes when clicking elements
- Slow page transitions
- React Query refetching constantly

**Solutions:**

```bash
# 1. Check React Query devtools
# Open browser → React Query Devtools (bottom right icon)
# Look for:
# ❌ Red queries = failed requests
# 🟡 Yellow queries = fetching (should be rare)

# 2. Increase staleTime for caching
# Already optimized in code:
# - persona-reasoning: 10 min cache
# - project-list: 5 min cache

# 3. Clear browser cache
# Ctrl+Shift+R

# 4. Check network tab for slow requests
# F12 → Network → Filter by "Fetch/XHR"
# API calls should be <500ms
```

---

## 💾 Data Issues

### 1. "No RAG documents found"

**Symptom:**
- Personas lack context (generic profiles)
- RAG search returns empty results

**Cause:** No documents uploaded to RAG system

**Solutions:**

```bash
# 1. Upload sample documents via API
curl -X POST http://localhost:8000/api/v1/rag/documents/upload \
  -F "file=@sample_report.pdf" \
  -F "title=Polish Society Report 2023" \
  -F "document_type=report"

# 2. Check uploaded documents
curl http://localhost:8000/api/v1/rag/documents

# 3. Verify documents in Neo4j
docker-compose exec neo4j cypher-shell -u neo4j -p dev_password_change_in_prod
# Run:
MATCH (d:Document) RETURN d.title, d.document_type LIMIT 10;

# 4. If no documents → use sample data (future feature)
# python scripts/load_sample_rag_data.py
```

### 2. Database Migration Errors

**Symptom:**
```
alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
```

**Causes:**
- Migrations out of sync
- Database contains old schema
- Migration history corrupted

**Solutions:**

#### Safe Solution (Try First):

```bash
# Check current migration version
docker-compose exec api alembic current

# Check available migrations
docker-compose exec api alembic heads

# Apply missing migrations
docker-compose exec api alembic upgrade head
```

#### Nuclear Solution (Deletes All Data!):

```bash
# WARNING: This will DELETE ALL DATA!
# Only use in development

# 1. Stop services
docker-compose down

# 2. Remove database volumes
docker volume rm market-research-saas_postgres_data
docker volume rm market-research-saas_neo4j_data

# 3. Start services
docker-compose up -d postgres redis neo4j

# 4. Wait for databases to initialize
sleep 15

# 5. Apply migrations
docker-compose exec api alembic upgrade head

# 6. Initialize Neo4j indexes
python scripts/init_neo4j_indexes.py

# 7. Start API
docker-compose up -d api
```

### 3. Duplicate Personas

**Symptom:**
- Same persona generated multiple times
- Personas have identical names/demographics

**Cause:**
- Concurrent generation requests (race condition)
- LLM deterministic output (temperature=0)

**Solutions:**

```bash
# 1. Check if multiple generation tasks running
docker-compose logs api | grep "generate_personas_batch"

# 2. Wait for current generation to complete
# Don't click "Generate" multiple times

# 3. Delete duplicate personas (via UI or API)
curl -X DELETE http://localhost:8000/api/v1/personas/{persona_id}

# 4. Prevent future duplicates (already implemented in code)
# Service uses unique constraints on (project_id, email)
```

---

## 🤖 LLM/AI Specific Problems

### 1. LLM Returns Empty Response

**Symptom:**
```
ValueError: LLM returned empty response
```

**Causes:**
- `max_tokens` too low (Gemini 2.5 uses reasoning tokens!)
- Prompt triggers safety filters
- API key quota exhausted

**Solutions:**

```bash
# 1. Check max_tokens setting
docker-compose exec api python -c "
from app.services.persona_generator_langchain import PersonaGeneratorLangChain
gen = PersonaGeneratorLangChain()
print('Max tokens:', gen.llm.max_output_tokens)
"
# Should be >= 2048 for Gemini 2.5

# 2. Check API logs for safety filter triggers
docker-compose logs api | grep "SAFETY"

# 3. Check quota
# https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas

# 4. Retry generation (code has automatic retry logic)
```

### 2. LLM Returns Invalid JSON

**Symptom:**
```
json.JSONDecodeError: Expecting ',' delimiter
```

**Cause:** LLM occasionally returns malformed JSON (~5% cases with Gemini)

**Solutions:**

```bash
# Already implemented in code (see persona_orchestration.py):
# - Multiple JSON extraction strategies (markdown blocks, braces, fallback)
# - Retry logic with exponential backoff

# If persistent:
# 1. Check prompt formatting
docker-compose logs api | grep "📤 PROMPT"

# 2. Regenerate personas (retry usually succeeds)
```

### 3. Orchestration Brief Too Long

**Symptom:**
```
WARNING: orchestration_brief exceeds token budget (2500 chars)
```

**Expected Behavior:** Model generuje od razu 900-1200 znaków – bez post-processingu.

**Co sprawdzić:**

```bash
# 1. Zweryfikuj w logach rzeczywistą długość odpowiedzi
docker-compose logs api | grep "Gemini response length"

# 2. Jeśli nadal wychodzi 2500+ znaków → sprawdź czy prompt nie został nadpisany
git diff app/services/persona_orchestration.py

# 3. Tymczasowy hotfix: obniż temperature (np. 0.1) lub limituj max_tokens
```

---

## 🐳 Docker & Infrastructure

### 1. "No space left on device"

**Symptom:**
```
Error: ENOSPC: no space left on device
```

**Solutions:**

```bash
# 1. Check Docker disk usage
docker system df

# 2. Clean up unused images/volumes
docker system prune -a --volumes

# WARNING: This removes:
# - All stopped containers
# - Unused images
# - Unused volumes (data will be lost!)

# 3. Free up host disk space
# macOS: Docker Desktop → Settings → Resources → Disk image size
# Increase from 60GB to 100GB+ if needed

# 4. Remove specific volumes (target cleanup)
docker volume ls
docker volume rm <unused_volume_name>
```

### 2. Services Won't Stop

**Symptom:**
```
docker-compose down
# Hangs for >60s, containers still running
```

**Solutions:**

```bash
# 1. Force stop
docker-compose down --timeout 10

# 2. Kill all containers (nuclear)
docker kill $(docker ps -q)

# 3. Remove stuck volumes
docker volume prune -f

# 4. Restart Docker Desktop
# macOS: Click whale icon → Restart
# Windows: Right-click Docker icon → Restart
```

### 3. Port Already in Use

**Symptom:**
```
Error: bind: address already in use
```

**Solutions:**

```bash
# Find process using port
lsof -i :8000  # API
lsof -i :5173  # Frontend
lsof -i :5432  # Postgres
lsof -i :6379  # Redis
lsof -i :7687  # Neo4j

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
# ports:
#   - "8001:8000"  # External 8001, internal 8000
```

---

## 🆘 Getting Help

### Before Asking for Help

**Checklist:**
1. ✅ Read this troubleshooting guide
2. ✅ Check logs: `docker-compose logs api | tail -100`
3. ✅ Verify all services healthy: `docker-compose ps`
4. ✅ Try restarting: `docker-compose restart`
5. ✅ Search GitHub Issues (if public repo)

### How to Report a Bug

**Include in your report:**

```bash
# 1. System info
echo "OS: $(uname -a)"
echo "Docker: $(docker --version)"
echo "Docker Compose: $(docker-compose --version)"

# 2. Service status
docker-compose ps

# 3. Relevant logs (last 100 lines)
docker-compose logs api | tail -100 > api_logs.txt
docker-compose logs neo4j | tail -100 > neo4j_logs.txt

# 4. Environment (without secrets!)
grep -v "GOOGLE_API_KEY\|SECRET_KEY" .env > env_sanitized.txt

# 5. Steps to reproduce
# Example:
# - Created project "Test"
# - Clicked "Generate Personas"
# - Selected 20 personas, Millennials, Technology
# - Error: "RAG service unavailable"
```

### Where to Get Help

1. **Documentation:**
   - [QUICKSTART.md](QUICKSTART.md) - Setup guide
   - [CLAUDE.md](../CLAUDE.md) - Architecture & patterns
   - [TESTING.md](TESTING.md) - Test suite
   - [RAG.md](RAG.md) - RAG system deep dive

2. **Logs:**
   - API: `docker-compose logs -f api`
   - Frontend: `docker-compose logs -f frontend`
   - Neo4j: `docker-compose logs -f neo4j`

3. **GitHub Issues:** [link if public repo]

4. **Contact Support:** [support email if available]

---

## 🔍 Advanced Debugging

### Enable Debug Mode

```bash
# Edit .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart API
docker-compose restart api

# Watch verbose logs
docker-compose logs -f api
```

### Interactive Debugging (Python)

```bash
# Enter API container
docker-compose exec api /bin/bash

# Start Python REPL
python

# Test components interactively
>>> from app.services.persona_generator_langchain import PersonaGeneratorLangChain
>>> gen = PersonaGeneratorLangChain()
>>> # Test methods manually
```

### Database Inspection

```bash
# PostgreSQL
docker-compose exec postgres psql -U market_research -d market_research_db
# \dt - list tables
# \d personas - describe personas table
# SELECT COUNT(*) FROM personas;

# Neo4j
docker-compose exec neo4j cypher-shell -u neo4j -p dev_password_change_in_prod
# MATCH (n) RETURN count(n);  - count all nodes
# MATCH (d:Document) RETURN d LIMIT 5;  - show documents

# Redis
docker-compose exec redis redis-cli
# KEYS *  - list all keys
# GET key_name  - get value
```

---

**Ostatnia aktualizacja:** 2025-10-15
**Dla wersji:** 3.0 (October 2025)

**Problem not listed here?** Check [docs/CLAUDE.md](../CLAUDE.md) or open a GitHub issue.
