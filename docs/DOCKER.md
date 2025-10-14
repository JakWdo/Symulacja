# Docker Architecture

Dokumentacja architektury Docker dla Market Research SaaS.

## Multi-Stage Builds

### Backend (Dockerfile)

**2-stage build:**
1. **BUILDER** - instaluje gcc, g++, kompiluje Python packages
2. **RUNTIME** - kopiuje tylko packages, bez build tools

**Korzyści:**
- Image size: 850MB → 450MB (47% mniejszy)
- Security: brak compilerów w runtime
- Layer caching: requirements.txt cached osobno od kodu

### Frontend (frontend/Dockerfile)

**4-stage build:**
1. **DEPS** - `npm ci` (cached dopóki package.json nie zmieni się)
2. **BUILDER** - `npm run build` (production static files)
3. **DEVELOPMENT** - Vite dev server z hot reload
4. **PRODUCTION** - nginx serving static build

**Korzyści:**
- Instant starty: node_modules z cache (NIE npm install przy każdym up)
- Production: 500MB → 25MB (95% mniejszy!)
- Named volume `frontend_node_modules` zapobiega konfliktom host vs container

## Docker Compose

### Development (docker-compose.yml)

**Key features:**
- Hot reload dla backendu (uvicorn --reload) i frontendu (Vite)
- Volume mounts: `./:/app` dla live code changes
- Named volume: `frontend_node_modules` (krytyczne dla uniknięcia konfliktów)
- Healthchecks: API startuje dopiero gdy databases są healthy
- Multi-stage targets: `target: runtime` (backend), `target: development` (frontend)

**WAŻNE:** Frontend NIE uruchamia `npm install` przy każdym `up` (jest w Dockerfile!)

### Production (docker-compose.prod.yml)

**Key features:**
- Frontend: nginx serving static build
- Backend: gunicorn z multiple workers
- Resource limits (CPU, memory)
- Internal network: databases nie exposed na host
- BRAK volume mounts (kod z image)
- Environment variables z `.env.production`

## .dockerignore

### Backend (.dockerignore)
Wyklucza: `__pycache__`, `.pytest_cache`, `.venv`, `frontend/`, `node_modules`, `.git`, `docs/`

**Korzyść:** Build context 500-800MB → 50-100MB (70-90% mniejszy)

### Frontend (frontend/.dockerignore)
Wyklucza: `node_modules`, `dist`, `.env*`

## Named Volumes

### Development
- `postgres_data`, `redis_data`, `neo4j_data` - Database persistence
- `api_static` - Avatary użytkowników
- `frontend_node_modules` - **KRYTYCZNE**: Zapobiega konfliktom host (macOS) vs container (Linux)

### Production
- Wszystkie development volumes + `nginx_logs`
- Rozważ external volumes z backupami

## Performance Benchmarks

### Build Times (cached)
- Backend: ~5-10s (tylko kod changed)
- Frontend: ~5-10s (tylko kod changed)
- Full rebuild (dependencies): ~60-120s

### Image Sizes
- Backend: ~450MB (runtime stage)
- Frontend dev: ~500MB (node + deps)
- Frontend prod: ~25MB (nginx + static)

### Runtime
- Backend cold start: ~5-10s (czeka na databases)
- Frontend cold start: ~1-2s (Vite dev server)
- Production frontend: <100ms (nginx static)

## Development Workflow

### Podstawowe komendy

```bash
# Start all services
docker-compose up -d

# Rebuild (po zmianie requirements.txt / package.json)
docker-compose up --build -d

# Logi
docker-compose logs -f api
docker-compose logs -f frontend

# Stop
docker-compose down

# Czysty start (USUWA DANE!)
docker-compose down -v
docker-compose up --build -d
```

### Kiedy rebuild?

✅ **REBUILD wymagany:**
- Zmiana `requirements.txt`
- Zmiana `package.json`
- Zmiana `Dockerfile`

❌ **REBUILD NIE wymagany:**
- Zmiana kodu `.py`, `.tsx` (hot reload działa)

## Production Deployment

### Setup

1. Skopiuj template:
   ```bash
   cp .env.production.example .env.production
   ```

2. Wypełnij **WSZYSTKIE** env vars:
   - `SECRET_KEY` (użyj `openssl rand -hex 32`)
   - `POSTGRES_PASSWORD`, `NEO4J_PASSWORD`
   - `GOOGLE_API_KEY`
   - `ALLOWED_ORIGINS` (tylko trusted domains)

3. Deploy:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

### Pre-Deploy Checklist

**Security:**
- [ ] SECRET_KEY zmieniony
- [ ] Hasła baz danych zmienione
- [ ] ALLOWED_ORIGINS skonfigurowany (tylko trusted domains)
- [ ] SSL/TLS certyfikaty skonfigurowane

**Infrastructure:**
- [ ] Backupy dla postgres_data, neo4j_data, api_static
- [ ] Monitoring/alerting skonfigurowany
- [ ] Firewall rules ustawione

**Performance:**
- [ ] Gunicorn workers dostosowane do CPU (2-4x cores)
- [ ] Database connection pools skonfigurowane
- [ ] Redis maxmemory policy ustawiony
- [ ] Neo4j memory limits dostosowane

## Troubleshooting

### Problem: "Module not found" po docker-compose up

**Przyczyna:** Konflikt host node_modules vs container

**Rozwiązanie:**
```bash
docker-compose down -v  # Usuń stare volumes
docker-compose up --build -d
```

### Problem: Frontend robi npm install przy każdym up

**Przyczyna:** Stary docker-compose.yml z `command: npm install`

**Rozwiązanie:**
```bash
# Sprawdź że NIE masz command: npm install w docker-compose.yml
git pull  # Pobierz nowy docker-compose.yml
docker-compose up --build -d
```

### Problem: Dependencies nie są instalowane

**Przyczyna:** Brak rebuild po zmianie requirements.txt / package.json

**Rozwiązanie:**
```bash
docker-compose up --build -d
```

### Problem: Cache przestarzały

**Rozwiązanie:**
```bash
docker-compose build --no-cache
docker-compose up -d
```

## Best Practices

1. **Layer caching** - kopiuj dependencies files PRZED kodem
2. **Multi-stage** - oddziel build dependencies od runtime
3. **.dockerignore** - wyklucz niepotrzebne pliki (szybsze buildy)
4. **Named volumes** - zapobiega konfliktom host vs container
5. **Non-root user** - security best practice
6. **Healthchecks** - zapewnij że services są ready przed startem
7. **Resource limits** - zapobiega resource exhaustion w production

## Files

- `Dockerfile` - Backend multi-stage build
- `.dockerignore` - Backend ignore rules
- `frontend/Dockerfile` - Frontend multi-stage build
- `frontend/.dockerignore` - Frontend ignore rules
- `frontend/nginx.conf` - Nginx config (SPA routing, API proxy)
- `docker-compose.yml` - Development environment
- `docker-compose.prod.yml` - Production environment
- `.env.production.example` - Production env template
- `docker-entrypoint.sh` - Backend entrypoint (migrations)
