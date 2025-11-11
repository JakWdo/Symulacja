"""Graph Query Builder - Generowanie zapytań Cypher na podstawie pytań użytkownika.

Odpowiedzialny za:
- Translację pytań w języku naturalnym na zapytania Cypher
- Wykorzystanie LLM do generowania strukturalnych zapytań
- Ekstrakcję encji z pytań
"""

import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from app.schemas.rag import GraphRAGQuery

logger = logging.getLogger(__name__)


def generate_cypher_query(
    llm: Any,
    graph_store: Any,
    question: str
) -> GraphRAGQuery:
    """Używa LLM do przełożenia pytania użytkownika na zapytanie Cypher.

    Args:
        llm: LangChain LLM instance
        graph_store: Neo4j graph store instance
        question: Pytanie użytkownika w języku naturalnym

    Returns:
        GraphRAGQuery z wygenerowanym zapytaniem Cypher i encjami

    Raises:
        RuntimeError: Jeśli graph_store nie jest dostępny
    """
    if not graph_store:
        raise RuntimeError("Graph RAG nie jest dostępny – brak połączenia z Neo4j Graph.")

    # Pobierz prompt z config/prompts/rag/cypher_generation.yaml
    from config import prompts
    cypher_prompt_template = prompts.get("rag.cypher_generation")

    # Renderuj prompt ze zmiennymi
    graph_schema = graph_store.get_schema()
    rendered_messages = cypher_prompt_template.render(
        question=question,
        graph_schema=graph_schema
    )

    # Buduj LangChain prompt z renderowanych wiadomości
    cypher_prompt = ChatPromptTemplate.from_messages([
        (msg["role"], msg["content"]) for msg in rendered_messages
    ])

    chain = cypher_prompt | llm.with_structured_output(GraphRAGQuery)
    return chain.invoke({})
