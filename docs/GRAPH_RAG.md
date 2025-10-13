# Dokumentacja Graph RAG

## Cel modułu

Graph RAG łączy klasyczne wyszukiwanie semantyczne z analizą strukturalną
wiedzy zapisanej w grafie Neo4j. Dzięki temu odpowiedzi są bogatsze
kontekstowo i precyzyjnie osadzają węzły, wskaźniki oraz trendy.

## Najważniejsze komponenty

1. **`RAGDocumentService`** – serwis odpowiedzialny za ingest dokumentów,
   budowę grafu wiedzy i obsługę zapytań Graph RAG.
2. **`PolishSocietyRAG`** – warstwa hybrydowego wyszukiwania
   (vector + BM25 + Reciprocal Rank Fusion) wykorzystywana przy generowaniu
   person i klasycznych odpowiedzi.
3. **Router `app/api/rag.py`** – udostępnia endpointy REST dla uploadu,
   listowania dokumentów oraz zapytań RAG/Graph RAG.
4. **Schematy Pydantic** – modele `RAGQueryRequest`, `RAGQueryResponse`,
   `GraphRAGQuestionRequest` i `GraphRAGQuestionResponse` opisujące
   kontrakty API.

## Przepływ ingestu

1. Użytkownik przesyła dokument PDF lub DOCX na endpoint `/rag/documents/upload`.
2. Plik jest zapisywany w katalogu wskazanym przez `DOCUMENT_STORAGE_PATH`.
3. Zadanie w tle uruchamia `RAGDocumentService.ingest_document`, które:
   - wczytuje treść dokumentu,
   - dzieli go na chunki tekstu,
   - generuje embeddingi i zapisuje je w `Neo4jVector`,
   - tworzy dokumenty grafowe przy pomocy `LLMGraphTransformer` i zapisuje
     je w grafie Neo4j.
4. Status i liczba chunków są aktualizowane w tabeli `rag_documents`.

## Przepływ zapytań Graph RAG

1. Użytkownik wysyła pytanie na endpoint `/rag/query/graph`.
2. Serwis generuje zapytanie Cypher dopasowane do schematu grafu.
3. Wykonywane jest zapytanie grafowe oraz wyszukiwanie wektorowe
   wspierające odpowiedź.
4. Finalna odpowiedź LLM łączy kontekst strukturalny i semantyczny, aby
   dostarczyć wiarygodne wnioski.

## Obsługa błędów

* Brak połączenia z Neo4j skutkuje komunikatem `503` (dla klasycznego RAG)
  lub `500` (dla Graph RAG) w routerze API.
* Podczas ingestu wyjątkowe sytuacje są logowane, a status dokumentu jest
  aktualizowany na `failed` wraz z opisem błędu.

## Utrzymanie

* Przy dodawaniu nowych typów dokumentów pamiętaj o poszerzeniu listy
  loaderów oraz testach wydajnościowych.
* W razie zmiany schematu grafu należy zaktualizować listę dozwolonych
  węzłów i relacji w `LLMGraphTransformer` oraz dostosować prompt
  generujący zapytania Cypher.