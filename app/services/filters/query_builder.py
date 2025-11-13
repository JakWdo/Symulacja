"""
SQL Query Builder - konwersja AST do zapytań SQL

Buduje zapytania SQL z Abstract Syntax Tree (AST) wygenerowanego przez DSL parser.
Obsługuje operatory AND, OR, NOT oraz paginację kursorem dla wydajności.

Strategie translacji:
    - AND: HAVING COUNT(DISTINCT tag_id) = N (wszystkie tagi muszą być obecne)
    - OR: UNION (dowolny tag)
    - NOT: LEFT JOIN + IS NULL (anti-join, wykluczenie tagów)

Przykład:
    DSL: "dem:age-25-34 AND geo:warsaw"
    SQL: SELECT DISTINCT resource_id FROM resource_tags
         WHERE tag_id IN (...)
         GROUP BY resource_id
         HAVING COUNT(DISTINCT tag_id) = 2

    DSL: "psy:high-openness OR psy:high-extraversion"
    SQL: SELECT DISTINCT resource_id FROM resource_tags
         WHERE tag_id IN (...)
         UNION ...

    DSL: "NOT dem:age-55-plus"
    SQL: SELECT p.id FROM personas p
         LEFT JOIN resource_tags rt ON (p.id = rt.resource_id AND rt.tag_id IN (...))
         WHERE rt.id IS NULL
"""

from __future__ import annotations

from typing import List, Tuple, Optional, Set
from uuid import UUID

from sqlalchemy import select, text, func, and_, or_, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models import Tag, ResourceTag, Persona, Workflow
from app.services.filters.dsl_parser import (
    ASTNode,
    TagNode,
    AndNode,
    OrNode,
    NotNode,
    parse_dsl,
)


class QueryBuilderError(ValueError):
    """Błąd budowania zapytania SQL."""
    pass


class QueryBuilder:
    """
    Query Builder - konwertuje AST na zapytania SQL.

    Obsługuje:
    - Filtrowanie zasobów po tagach (AND, OR, NOT)
    - Paginacja kursorem (cursor-based pagination)
    - Różne typy zasobów (persona, workflow, etc.)
    """

    def __init__(self, db: AsyncSession):
        """
        Inicjalizuje query builder.

        Args:
            db: Async database session
        """
        self.db = db

    async def build_query(
        self,
        dsl: str,
        resource_type: str,
        environment_id: UUID,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> Select:
        """
        Buduje zapytanie SQL z DSL query.

        Args:
            dsl: DSL query string
            resource_type: Typ zasobu (persona, workflow, etc.)
            environment_id: UUID środowiska
            limit: Limit wyników (default 100)
            cursor: Kursor dla paginacji (resource_id)

        Returns:
            SQLAlchemy Select statement

        Raises:
            QueryBuilderError: Jeśli nie można zbudować zapytania

        Examples:
            >>> query = await builder.build_query(
            ...     "dem:age-25-34 AND geo:warsaw",
            ...     "persona",
            ...     environment_id,
            ...     limit=50
            ... )
        """
        # Parse DSL do AST
        try:
            ast = parse_dsl(dsl)
        except Exception as e:
            raise QueryBuilderError(f"Failed to parse DSL: {e}")

        # Resolve tag IDs
        tag_ids = await self._resolve_tag_ids(ast)

        if not tag_ids:
            raise QueryBuilderError("No valid tags found in query")

        # Build SQL query from AST
        query = await self._build_from_ast(
            ast, tag_ids, resource_type, environment_id
        )

        # Apply limit
        query = query.limit(limit)

        # Apply cursor pagination
        if cursor:
            query = query.where(literal_column("resource_id") > cursor)

        # Order by resource_id for consistent pagination
        query = query.order_by(literal_column("resource_id"))

        return query

    async def _resolve_tag_ids(self, ast: ASTNode) -> dict[str, UUID]:
        """
        Rozwiązuje tag strings na tag IDs z bazy danych.

        Args:
            ast: AST node

        Returns:
            Dict {tag_string: tag_id}
        """
        # Extract wszystkie tagi z AST
        tags = self._extract_tags(ast)

        if not tags:
            return {}

        # Query dla tag IDs
        # Parse tagi na facet:key
        facet_key_pairs = []
        for tag in tags:
            facet, key = tag.split(':', 1)
            facet_key_pairs.append((facet, key))

        # Buduj WHERE clause dla wszystkich tagów
        # WHERE (facet = 'dem' AND key = 'age-25-34') OR (facet = 'geo' AND key = 'warsaw') ...
        conditions = []
        for facet, key in facet_key_pairs:
            conditions.append(and_(Tag.facet == facet, Tag.key == key))

        stmt = select(Tag.id, Tag.facet, Tag.key).where(or_(*conditions))
        result = await self.db.execute(stmt)
        rows = result.all()

        # Map tag strings to IDs
        tag_id_map = {}
        for row in rows:
            tag_string = f"{row.facet}:{row.key}"
            tag_id_map[tag_string] = row.id

        return tag_id_map

    def _extract_tags(self, node: ASTNode) -> Set[str]:
        """
        Ekstrahuje wszystkie tagi (leaf nodes) z AST.

        Args:
            node: AST node

        Returns:
            Set wszystkich tagów w AST
        """
        if isinstance(node, TagNode):
            return {node.tag}

        if isinstance(node, AndNode):
            return self._extract_tags(node.left) | self._extract_tags(node.right)

        if isinstance(node, OrNode):
            return self._extract_tags(node.left) | self._extract_tags(node.right)

        if isinstance(node, NotNode):
            return self._extract_tags(node.operand)

        return set()

    async def _build_from_ast(
        self,
        node: ASTNode,
        tag_ids: dict[str, UUID],
        resource_type: str,
        environment_id: UUID,
    ) -> Select:
        """
        Buduje SQL query z AST node.

        Args:
            node: AST node
            tag_ids: Map tag strings → tag IDs
            resource_type: Typ zasobu
            environment_id: UUID środowiska

        Returns:
            SQLAlchemy Select statement
        """
        if isinstance(node, TagNode):
            return self._build_tag_query(node, tag_ids, resource_type, environment_id)

        if isinstance(node, AndNode):
            return self._build_and_query(node, tag_ids, resource_type, environment_id)

        if isinstance(node, OrNode):
            return self._build_or_query(node, tag_ids, resource_type, environment_id)

        if isinstance(node, NotNode):
            return self._build_not_query(node, tag_ids, resource_type, environment_id)

        raise QueryBuilderError(f"Unknown AST node type: {type(node)}")

    async def _build_tag_query(
        self,
        node: TagNode,
        tag_ids: dict[str, UUID],
        resource_type: str,
        environment_id: UUID,
    ) -> Select:
        """
        Buduje query dla pojedynczego tagu.

        SQL: SELECT DISTINCT resource_id FROM resource_tags
             WHERE tag_id = ? AND resource_type = ? AND environment_id = ?
        """
        tag_id = tag_ids.get(node.tag)
        if not tag_id:
            # Tag nie istnieje w bazie - zwróć puste query
            return select(literal_column("NULL").label("resource_id")).where(text("1=0"))

        return (
            select(ResourceTag.resource_id)
            .where(
                and_(
                    ResourceTag.tag_id == tag_id,
                    ResourceTag.resource_type == resource_type,
                    ResourceTag.environment_id == environment_id,
                )
            )
            .distinct()
        )

    async def _build_and_query(
        self,
        node: AndNode,
        tag_ids: dict[str, UUID],
        resource_type: str,
        environment_id: UUID,
    ) -> Select:
        """
        Buduje query dla AND operator.

        Strategia: HAVING COUNT(DISTINCT tag_id) = N
        Wszystkie tagi muszą być obecne dla tego samego resource_id.

        SQL: SELECT resource_id FROM resource_tags
             WHERE tag_id IN (?, ?) AND resource_type = ? AND environment_id = ?
             GROUP BY resource_id
             HAVING COUNT(DISTINCT tag_id) = 2
        """
        # Collect wszystkie tagi z AND subtree
        tags = self._extract_tags(node)
        required_tag_ids = [tag_ids[tag] for tag in tags if tag in tag_ids]

        if not required_tag_ids:
            return select(literal_column("NULL").label("resource_id")).where(text("1=0"))

        required_count = len(required_tag_ids)

        return (
            select(ResourceTag.resource_id)
            .where(
                and_(
                    ResourceTag.tag_id.in_(required_tag_ids),
                    ResourceTag.resource_type == resource_type,
                    ResourceTag.environment_id == environment_id,
                )
            )
            .group_by(ResourceTag.resource_id)
            .having(func.count(ResourceTag.tag_id.distinct()) == required_count)
        )

    async def _build_or_query(
        self,
        node: OrNode,
        tag_ids: dict[str, UUID],
        resource_type: str,
        environment_id: UUID,
    ) -> Select:
        """
        Buduje query dla OR operator.

        Strategia: UNION
        Dowolny tag z lewej lub prawej strony.

        SQL: (SELECT DISTINCT resource_id FROM ...)
             UNION
             (SELECT DISTINCT resource_id FROM ...)
        """
        left_query = await self._build_from_ast(
            node.left, tag_ids, resource_type, environment_id
        )
        right_query = await self._build_from_ast(
            node.right, tag_ids, resource_type, environment_id
        )

        # UNION distinct (eliminuje duplikaty)
        return left_query.union(right_query)

    async def _build_not_query(
        self,
        node: NotNode,
        tag_ids: dict[str, UUID],
        resource_type: str,
        environment_id: UUID,
    ) -> Select:
        """
        Buduje query dla NOT operator.

        Strategia: Anti-join (LEFT JOIN + IS NULL)
        Wyklucza zasoby które mają dany tag.

        SQL: SELECT p.id as resource_id FROM personas p
             LEFT JOIN resource_tags rt ON (
                 p.id = rt.resource_id
                 AND rt.tag_id IN (...)
                 AND rt.resource_type = 'persona'
                 AND rt.environment_id = ?
             )
             WHERE rt.id IS NULL
        """
        # Określ model bazodanowy dla resource_type
        if resource_type == "persona":
            model = Persona
        elif resource_type == "workflow":
            model = Workflow
        else:
            raise QueryBuilderError(f"Unsupported resource_type: {resource_type}")

        # Collect tagi do wykluczenia
        excluded_tags = self._extract_tags(node.operand)
        excluded_tag_ids = [tag_ids[tag] for tag in excluded_tags if tag in tag_ids]

        if not excluded_tag_ids:
            # Brak tagów do wykluczenia - zwróć wszystkie zasoby
            return (
                select(model.id.label("resource_id"))
                .where(model.environment_id == environment_id)
            )

        # Anti-join
        rt = ResourceTag.__table__.alias("rt")

        return (
            select(model.id.label("resource_id"))
            .outerjoin(
                rt,
                and_(
                    model.id == rt.c.resource_id,
                    rt.c.tag_id.in_(excluded_tag_ids),
                    rt.c.resource_type == resource_type,
                    rt.c.environment_id == environment_id,
                ),
            )
            .where(
                and_(
                    model.environment_id == environment_id,
                    rt.c.id.is_(None),  # Anti-join condition
                )
            )
        )


# === Public API ===

async def filter_resources(
    db: AsyncSession,
    dsl: str,
    resource_type: str,
    environment_id: UUID,
    limit: int = 100,
    cursor: Optional[str] = None,
) -> List[UUID]:
    """
    Filtruje zasoby po tagach używając DSL query.

    Args:
        db: Async database session
        dsl: DSL query string
        resource_type: Typ zasobu (persona, workflow)
        environment_id: UUID środowiska
        limit: Limit wyników (default 100)
        cursor: Kursor dla paginacji (UUID resource)

    Returns:
        Lista UUID zasobów spełniających warunki

    Raises:
        QueryBuilderError: Jeśli nie można zbudować/wykonać zapytania

    Examples:
        >>> resource_ids = await filter_resources(
        ...     db,
        ...     "dem:age-25-34 AND geo:warsaw",
        ...     "persona",
        ...     environment_id,
        ...     limit=50
        ... )
    """
    builder = QueryBuilder(db)
    query = await builder.build_query(
        dsl, resource_type, environment_id, limit, cursor
    )

    # Execute query
    result = await db.execute(query)
    rows = result.all()

    return [row[0] for row in rows]  # Extract resource_ids
