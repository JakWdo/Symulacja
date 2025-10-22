"""
Moduł API - Endpointy REST API

Zawiera routery FastAPI dla wszystkich zasobów platformy:

- projects.py: CRUD operacje na projektach badawczych
- personas.py: Generowanie i zarządzanie personami (syntetycznymi uczestnikami)
- focus_groups.py: Tworzenie i uruchamianie grup fokusowych (dyskusje AI)
- surveys.py: Ankiety syntetyczne (4 typy pytań: single/multiple choice, rating, open text)
- analysis.py: Analizy AI i podsumowania wyników (Gemini Pro/Flash)
- rag.py: RAG Knowledge Base (document upload, hybrid search, Graph RAG)

Wszystkie endpointy używają:
- Pydantic schemas do walidacji
- SQLAlchemy async sessions
- Background tasks dla długich operacji (generowanie person, dyskusje)

Prefix API: /api/v1
"""