# DevOps & Infrastruktura Market Research SaaS

Market Research SaaS to zaawansowana platforma do wirtualnych grup fokusowych z wykorzystaniem AI, która kładzie nacisk na wydajność, bezpieczeństwo i skalowalność. Nasza architektura kontenerowa oparta jest na Docker Compose, zapewniając spójne środowisko deweloperskie i produkcyjne. System składa się z pięciu kluczowych usług: PostgreSQL z pgvector, Redis, Neo4j z pluginami APOC i Graph Data Science, FastAPI oraz React.

Projekt został zoptymalizowany pod kątem wydajności – zmniejszyliśmy rozmiar obrazów Docker o 84%, zredukowano czas budowania, wprowadzono zaawansowane zarządzanie zasobami i wielowarstwowe bezpieczeństwo.

## Architektura Docker

### Główne Serwisy i Resource Limits

| Serwis | Obraz | Dev Limity | Prod Limity | Rozmiar Obrazu |
|--------|-------|------------|-------------|----------------|
| Backend API | FastAPI | CPU: 1, RAM: 512MB | CPU: 2, RAM: 1.5GB | 2.3 GB |
| Frontend | React + Nginx | CPU: 0.5, RAM: 256MB | CPU: 1, RAM: 512MB | 570 MB |
| PostgreSQL | pgvector | CPU: 1, RAM: 1GB | CPU: 2, RAM: 4GB | 420 MB |
| Redis | In-memory DB | CPU: 0.5, RAM: 256MB | CPU: 1, RAM: 1GB | 110 MB |
| Neo4j | Graph DB | CPU: 1, RAM: 2GB | CPU: 3, RAM: 8GB | 720 MB |

#### Szczegóły Serwisów

1. **Backend API (FastAPI)**
   - Obsługa logiki biznesowej z async/await
   - Wielowarstwowe bezpieczeństwo
   - Health check: `/health` endpoint
   - Startup probe: 30s timeout

2. **Frontend (React + Vite)**
   - Statyczny serwer nginx
   - Zoptymalizowany build (25MB obraz produkcyjny)
   - Health check: nginx status page
   - Startup probe: 15s timeout

3. **Bazy Danych**
   - PostgreSQL z pgvector dla embeddings
   - Redis jako warstwa cache i session storage
   - Neo4j dla zaawansowanych analiz grafowych

## Konfiguracja Środowiska

### Development

```bash
# Uruchomienie wszystkich serwisów
docker-compose up -d

# Rebuild po zmianie dependencies
docker-compose up --build -d

# Migracje bazy danych
docker-compose exec api alembic upgrade head

# Inicjalizacja Neo4j
python scripts/init_neo4j_indexes.py
```

### Deployment Produkcyjny

```bash
# Deployment z docker-compose
docker-compose -f docker-compose.prod.yml up -d --build

# Migracje i inicjalizacja
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
docker-compose -f docker-compose.prod.yml exec api python scripts/init_neo4j_indexes.py
```

## Kluczowe Optymalizacje

### Docker Multi-Stage Builds

#### Neo4j - Konfiguracja Przed Optymalizacją
```dockerfile
# 58 linii, ręczne pobieranie pluginów
FROM neo4j:5.x
RUN wget https://github.com/neo4j/apoc/releases/download/5.x.x/apoc-5.x.x-core.jar
RUN wget https://github.com/neo4j-contrib/gds/releases/download/2.6.7/gds-2.6.7.jar
# Skomplikowana logika instalacji
```

#### Neo4j - Po Optymalizacji
```dockerfile
# 12 linii, automatyczne zarządzanie
FROM neo4j:5.x
RUN echo 'dbms.unmanaged_extension_classes=org.neo4j.graphalg=/gds' >> /conf/neo4j.conf
```

### Metryki Optymalizacji

- **Redukcja rozmiaru obrazów**: 84% (z 55GB do 11GB)
- **Czas budowania**: Redukcja o 67%
- **Bezpieczeństwo**: 54 CVE naprawione
- **Zależności**: Usunięto Celery (4.41GB oszczędności)

### Zarządzanie Zasobami
- Dynamiczne limity CPU/RAM
- Osobne konfiguracje dev/prod
- Ochrona przed atakami DoS
- Izolacja sieci Docker

## Dobre Praktyki DevOps

### Development Workflow

1. **Zmiana kodu**
   - Python/TypeScript: Hot reload
   - Nowe zależności: Rebuild (`docker-compose up --build`)
   - Migracje bazy: `alembic upgrade head`

2. **Docker Compose Patterns**
   - Health checks dla wszystkich serwisów
   - `restart: unless-stopped`
   - Zarządzanie zależnościami (`depends_on`)

3. **Debugging**
   ```bash
   # Analiza kontenerów
   docker stats
   docker-compose logs -f api
   docker exec -it api_container bash
   ```

### Dockerfile Best Practices

- Multi-stage builds
- Minimalizacja warstw
- Używanie `.dockerignore`
- Uruchamianie jako non-root user
- Cachowanie warstw zależności

## Monitorowanie & Observability

### Stos Monitorujący
- **Prometheus**: Zbieranie metryk systemowych
- **Grafana**: Wizualizacja dashboardów
- **Alertmanager**: Powiadomienia (Slack, Email)

### Kluczowe Metryki
- Wydajność systemu (CPU, RAM)
- Statystyki requestów HTTP
- Użycie tokenów LLM
- Statystyki baz danych
- Metryki biznesowe (generowane persony)

## Backup & Disaster Recovery

- Automatyczne, dzienne kopie zapasowe
- Przechowywanie kopii przez 30 dni
- Miesięczne testy przywracania
- Kopie baz: PostgreSQL, Neo4j, Redis
- Backup plików statycznych
- Szyfrowanie kopii zapasowych
- Replikacja off-site

## Troubleshooting

```bash
# Sprawdzenie logów
docker-compose logs api
docker-compose logs frontend

# Czysty restart
docker-compose down -v
docker-compose up --build -d
```

## Potencjalne Kluczowe Ulepszenia

### Monitoring & Observability
- [ ] Pełna integracja Jaeger (distributed tracing)
- [ ] Log aggregation z ELK
- [ ] Advanced Prometheus alerting

### Performance Optimization
- [ ] Redis clustering
- [ ] PostgreSQL read replicas
- [ ] Neo4j enterprise clustering

### CI/CD Enhancement
- [ ] GitHub Actions workflow
- [ ] Automatyczne testy bezpieczeństwa
- [ ] Blue-green deployments

### Infrastruktura
- [ ] Migracja do Kubernetes
- [ ] Terraform dla IaC
- [ ] Zaawansowane zarządzanie sekretami

> **Uwaga:** Ta lista jest dynamiczna. Wykonane ulepszenia są usuwane z dokumentacji.
> Data ostatniej aktualizacji: 2025-10-16

**Ostatnia aktualizacja:** 2025-10-16
**Wersja:** 1.2
**Status DevOps:** Level 3 (Managed)