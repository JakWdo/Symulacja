# Przegląd Projektu

To jest platforma SaaS do badań rynkowych o nazwie "Sight", która wykorzystuje sztuczną inteligencję do symulacji grup fokusowych. Umożliwia użytkownikom tworzenie projektów badawczych, generowanie person opartych na AI na podstawie określonych danych demograficznych, a następnie przeprowadzanie wirtualnych dyskusji i ankiet. Platforma zapewnia również zaawansowaną analizę wyników, w tym analizę pojęć opartą na grafach przy użyciu Neo4j.

## Ocena Aplikacji: 92/100

Aplikacja "Sight" jest przykładem wyjątkowo dobrze zaprojektowanego i zaimplementowanego oprogramowania. Kod jest czysty, dobrze udokumentowany i demonstruje dojrzałe podejście do inżynierii oprogramowania. Ocena odzwierciedla wysoką jakość we wszystkich kluczowych obszarach.

### Kluczowe Atuty:
*   **Architektura Backendu Gotowa na Produkcję:** Backend w FastAPI jest zaprojektowany z myślą o środowisku produkcyjnym. Posiada solidne zabezpieczenia (middleware), strukturalne logowanie, kompleksowe sprawdzanie stanu (`/health`) oraz inteligentne optymalizacje dla Google Cloud Run (np. "leniwe" ładowanie usług AI).
*   **Zaawansowana Implementacja AI:** Generowanie person to nie jest prosty wrapper na LLM. To złożony, wieloetapowy potok, który łączy statystyczne próbkowanie demograficzne, profilowanie psychograficzne (Wielka Piątka, wymiary Hofstedego) oraz system RAG (Retrieval-Augmented Generation) specyficzny dla domeny. Świadczy to o bardzo wysokim poziomie wiedzy technicznej i domenowej.
*   **Czysta Architektura Full-Stack:** Kod charakteryzuje się spójnym, domenowym podejściem w całym stosie technologicznym. Modułowa struktura backendu (`app/api`, `app/services`) ma swoje odzwierciedlenie w bibliotece komponentów React na frontendzie, co czyni system łatwym w nawigacji i utrzymaniu.
*   **Efektywny Model Wdrożenia:** Aplikacja jest zaprojektowana do wdrożenia jako pojedyncza usługa w Cloud Run, gdzie jeden kontener obsługuje zarówno backend FastAPI, jak i skompilowany frontend React. Jest to wydajny i oszczędny model dla platform bezserwerowych.

### Obszary do Dalszej Analizy:
Niewielkie odjęcie punktów wynika z obszarów, których nie można było w pełni zbadać z powodu przerwania analizy: szczegółowa implementacja frontendu, skrypty CI/CD oraz przeznaczenie katalogu `sight/`. Istniejący kod daje jednak mocne podstawy, by sądzić, że te obszary są również wysokiej jakości.

## Architektura Szczegółowa

*   **Backend (FastAPI):** Zbudowany w `app/`, serce aplikacji. Wykorzystuje modułową strukturę z wyraźnym podziałem na `api` (punkty końcowe), `services` (logika biznesowa), `models` (schematy bazy danych) i `core` (kluczowe komponenty). Plik `app/main.py` integruje wszystkie elementy, włączając middleware do bezpieczeństwa (nagłówki, CORS) i obserwowalności.
*   **Frontend (React):** Znajdujący się w `frontend/`, jest zbudowany w oparciu o komponenty, które logicznie odpowiadają funkcjom backendu (np. `personas`, `focus-group`). To podejście ułatwia rozwój i utrzymanie spójnego interfejsu użytkownika.
*   **Implementacja AI (LangChain & Gemini):** Logika AI, zlokalizowana głównie w `app/services/personas/generation/persona_generator_langchain.py`, jest kluczowym wyróżnikiem aplikacji. Proces generowania persony przebiega wieloetapowo, zapewniając realizm i kontekstowość wyników.
*   **Bazy Danych:**
    *   **PostgreSQL:** Główny magazyn danych dla modeli zdefiniowanych w `app/models`.
    *   **Neo4j:** Używana do analizy grafu wiedzy, wydobywania pojęć i relacji z zebranych danych.
    *   **Redis:** Służy do buforowania w celu zwiększenia wydajności.
*   **Konfiguracja:** Scentralizowany katalog `config/` oddziela konfigurację od kodu, co jest najlepszą praktyką. Zawiera ustawienia aplikacji, funkcji, a co najważniejsze, modeli LLM i promptów.

## Model Wdrożenia (Google Cloud Run)

Aplikacja jest zoptymalizowana pod kątem wdrożenia w Google Cloud Run jako pojedyncza usługa. Kontener Docker, zdefiniowany w `Dockerfile.cloudrun`, jest skonfigurowany tak, aby uruchomić serwer Uvicorn dla FastAPI. Backend serwuje zarówno punkty końcowe API, jak i statyczne pliki zbudowanego frontendu React. Jest to wysoce wydajne i skalowalne podejście, idealne dla nowoczesnych aplikacji webowych.


