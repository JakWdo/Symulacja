"""
Dashboard Cache Invalidation Helpers

Provides functions to invalidate dashboard-related Redis cache keys
after mutations (create, update, delete, restore operations).

Cache keys invalidated:
- dashboard:overview:{user_id}
- dashboard:overview:last-state:{user_id}
- dashboard:weekly:{user_id}:*
- dashboard:usage:{user_id}
- dashboard:analytics:insights:{user_id}:*
"""

import logging
from uuid import UUID

from app.core.redis import redis_delete, redis_delete_pattern

logger = logging.getLogger(__name__)


async def invalidate_dashboard_cache(user_id: UUID) -> None:
    """
    Invalidate all dashboard cache keys for a user.

    Call this after:
    - Project created/deleted/restored
    - Persona created/deleted/restored
    - FocusGroup created/deleted/restored/completed
    - InsightEvidence created
    - Budget settings changed

    Args:
        user_id: UUID of the user whose cache should be invalidated
    """
    user_id_str = str(user_id)

    # Exact key deletions
    await redis_delete(f"dashboard:overview:{user_id_str}")
    await redis_delete(f"dashboard:overview:last-state:{user_id_str}")
    await redis_delete(f"dashboard:usage:{user_id_str}")

    # Pattern deletions (wildcards)
    await redis_delete_pattern(f"dashboard:weekly:{user_id_str}:*")
    await redis_delete_pattern(f"dashboard:analytics:insights:{user_id_str}:*")

    logger.debug(f"Dashboard cache invalidated for user {user_id_str}")


async def invalidate_project_cache(user_id: UUID, project_id: UUID) -> None:
    """
    Invalidate cache for a specific project.

    Call this for project-specific mutations that don't affect
    the entire dashboard (e.g., project settings update).

    Args:
        user_id: UUID of the project owner
        project_id: UUID of the project
    """
    user_id_str = str(user_id)
    project_id_str = str(project_id)

    # Invalidate project-specific caches
    await redis_delete_pattern(f"dashboard:weekly:{user_id_str}:*:{project_id_str}")
    await redis_delete_pattern(f"dashboard:analytics:insights:{user_id_str}:{project_id_str}:*")

    # Also invalidate overview since project count/status may change
    await redis_delete(f"dashboard:overview:{user_id_str}")

    logger.debug(f"Project cache invalidated for user {user_id_str}, project {project_id_str}")
