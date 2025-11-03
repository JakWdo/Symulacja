# sight

> Wirtualne grupy fokusowe z AI - symuluj badania rynkowe używając Google Gemini 2.5

## 🚀 Quick Start

```bash
# 1. Skopiuj template .env i uzupełnij wartości
cp .env.example .env
# Edytuj .env i ustaw:
# - GOOGLE_API_KEY (wymagany)
# - SECRET_KEY (generuj: openssl rand -hex 32)
# Pozostałe wartości domyślne działają z docker-compose

# 2. Uruchom cały stack
docker-compose up -d

# 3. Otwórz interfejsy
open http://localhost:5173      # Frontend
open http://localhost:8000/docs # API Docs
```

**Opcjonalne zależności:**
```bash
# Dla multi-provider LLM (OpenAI, Anthropic)
pip install -e ".[llm-providers]"

# Dla upload PDF/DOCX do RAG
pip install -e ".[document-processing]"

# Wszystkie opcjonalne
pip install -e ".[all]"
```

## 📋 Kluczowe Funkcje

| Feature | Opis | Czas |
|---------|------|------|
| **Persony** | AI generuje realistyczne profile | 30-60s / 20 osób |
| **Grupy fokusowe** | Asynchroniczne dyskusje AI | 2-5 min / 20 osób |
| **Ankiety** | 4 typy pytań z AI | <60s / 10 osób |
| **Analiza grafowa** | Ekstrakcja konceptów w Neo4j | 30-60s |
| **RAG** | Hybrydowe wyszukiwanie | 350ms / zapytanie |

## 🏗️ Stack Technologiczny

- **Frontend:** React 18, TypeScript, Vite, TanStack Query
- **Backend:** FastAPI, PostgreSQL, Redis, Neo4j
- **AI:** Google Gemini 2.5 (LangChain)
- **Infrastruktura:** Docker, Docker Compose

## 📖 Przykładowy Workflow

### 1. Utwórz projekt
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test produktu",
    "target_demographics": {
      "age_group": {"18-24": 0.3, "25-34": 0.5, "35-44": 0.2},
      "gender": {"Male": 0.5, "Female": 0.5}
    },
    "target_sample_size": 20
  }'
```

### 2. Generuj persony
```bash
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/personas/generate" \
  -H "Content-Type: application/json" \
  -d '{"num_personas": 20}'
```

### 3. Uruchom focus group
```bash
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/focus-groups" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sesja #1",
    "persona_ids": ["id1", "id2", ...],
    "questions": [
      "Co sądzisz o tym produkcie?",
      "Jakie funkcje są najważniejsze?",
      "Ile byłbyś skłonny zapłacić?"
    ]
  }'
```

## 🧪 Testowanie

```bash
# Szybkie testy
pytest -v

# Z coverage
pytest -v --cov=app --cov-report=html
```

## 📚 Dokumentacja

Szczegółowe dokumenty techniczne:
- [CLAUDE.md](CLAUDE.md): Instrukcje dla deweloperów
- [docs/README.md](docs/README.md): Indeks dokumentacji
- [docs/RAG.md](docs/RAG.md): Hybrid Search & GraphRAG
- [docs/AI_ML.md](docs/AI_ML.md): AI/ML system

## 🆕 Najnowsza Aktualizacja

### Code Organization Refactoring (2025-11-03)

**Zmiany (PR1-PR4):**
- Split `personas.py` (1694 linie) → 5 modułów
- Refaktoryzacja `main.py` (629 → 410 linii, -35%)
- Migracja do centralized config system (`config/*`)
- Opcjonalne zależności w `pyproject.toml` (extras)
- `.env.example` template dla łatwiejszego setupu

### Segment-Based Persona Architecture (2025-10-15)

**Architektura:**
- Każda persona należy do demograficznego segmentu
- Wymuszone constrainty demograficzne
- Indywidualny kontekst społeczny
- Walidacja spójności danych

## 🤝 Contributing

1. Przeczytaj [CLAUDE.md](CLAUDE.md)
2. Uruchom testy: `pytest tests/ -v`
3. Sprawdź coverage
4. Aktualizuj [PLAN.md](PLAN.md)

## 📝 Licencja

Projekt prywatny.

---

**Więcej:** [docs/README.md](docs/README.md)