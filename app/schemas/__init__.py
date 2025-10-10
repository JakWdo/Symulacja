"""
Schematy Pydantic dla walidacji danych (request/response)

Ten pakiet zawiera modele Pydantic używane do:
1. Walidacji danych wejściowych (request schemas) - co API przyjmuje
2. Serializacji odpowiedzi (response schemas) - co API zwraca
3. Transformacji danych między warstwami aplikacji

Pydantic automatycznie:
- Waliduje typy danych
- Konwertuje typy (np. string -> int)
- Generuje błędy walidacji
- Tworzy dokumentację OpenAPI/Swagger

Pliki:
- project.py - schematy dla projektów badawczych
- persona.py - schematy dla person
- focus_group.py - schematy dla grup fokusowych
- survey.py - schematy dla ankiet syntetycznych
- graph.py - schematy dla analizy grafowej
"""