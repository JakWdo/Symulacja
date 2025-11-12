"""
Authorization decorators and utilities for role-based access control (RBAC).

Ten moduł zawiera decoratory i funkcje autoryzacyjne dla ról systemowych:
- @requires_role: Decorator wymagający określonej roli dla endpointów
- check_user_has_role: Helper function sprawdzająca czy użytkownik ma wymaganą rolę
- Hierarchia ról: ADMIN > RESEARCHER > VIEWER
"""
from functools import wraps
from typing import Callable
import logging

from fastapi import HTTPException, status
from app.models.user import SystemRole, User

logger = logging.getLogger(__name__)


# Hierarchia ról (wyższa rola ma wszystkie uprawnienia niższych)
ROLE_HIERARCHY = {
    SystemRole.ADMIN: 3,
    SystemRole.RESEARCHER: 2,
    SystemRole.VIEWER: 1,
}


def check_user_has_role(user: User, required_role: SystemRole, *, hierarchical: bool = True) -> bool:
    """
    Sprawdza czy użytkownik ma wymaganą rolę.

    Args:
        user: User object
        required_role: Wymagana rola (SystemRole ENUM)
        hierarchical: Czy używać hierarchii ról (domyślnie True)
            - True: ADMIN ma dostęp do endpointów RESEARCHER i VIEWER
            - False: Wymagana dokładna rola

    Returns:
        True jeśli użytkownik ma wystarczającą rolę, False w przeciwnym razie

    Example:
        >>> user = User(system_role=SystemRole.ADMIN)
        >>> check_user_has_role(user, SystemRole.RESEARCHER)  # hierarchical=True
        True
        >>> check_user_has_role(user, SystemRole.ADMIN)
        True
        >>> check_user_has_role(user, SystemRole.VIEWER)
        True
    """
    if hierarchical:
        user_level = ROLE_HIERARCHY.get(user.system_role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level
    else:
        return user.system_role == required_role


def requires_role(required_role: SystemRole, *, hierarchical: bool = True):
    """
    Decorator wymagający określonej roli dla endpointu FastAPI.

    Args:
        required_role: Wymagana rola (SystemRole.ADMIN, SystemRole.RESEARCHER, SystemRole.VIEWER)
        hierarchical: Czy używać hierarchii ról (domyślnie True)

    Raises:
        HTTPException 403: Jeśli użytkownik nie ma wymaganej roli

    Usage:
        from app.core.auth import requires_role
        from app.models.user import SystemRole

        @router.get("/admin/users")
        @requires_role(SystemRole.ADMIN)
        async def list_all_users(current_user: User = Depends(get_current_user)):
            # Tylko administratorzy mogą uzyskać dostęp
            return {"users": [...]}

        @router.post("/projects")
        @requires_role(SystemRole.RESEARCHER)  # ADMIN też ma dostęp (hierarchical=True)
        async def create_project(current_user: User = Depends(get_current_user)):
            # RESEARCHER i ADMIN mogą tworzyć projekty
            return {"project_id": "..."}

        @router.get("/projects/{id}")
        @requires_role(SystemRole.VIEWER)  # Wszyscy mają dostęp (VIEWER jest najniższą rolą)
        async def get_project(current_user: User = Depends(get_current_user)):
            # VIEWER, RESEARCHER i ADMIN mogą przeglądać projekty
            return {"project": {...}}
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Wyciągnij current_user z kwargs (dependency injection)
            current_user = kwargs.get('current_user')

            if current_user is None:
                # Fallback: Spróbuj znaleźć w args (jeśli user jest przekazany jako positional arg)
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break

            if current_user is None:
                logger.error(
                    "RBAC check failed: current_user not found in endpoint args/kwargs",
                    extra={"endpoint": func.__name__}
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authorization check error: user not found"
                )

            # Sprawdź rolę
            if not check_user_has_role(current_user, required_role, hierarchical=hierarchical):
                logger.warning(
                    "RBAC access denied",
                    extra={
                        "user_id": str(current_user.id),
                        "user_email": current_user.email,
                        "user_role": current_user.system_role.value,
                        "required_role": required_role.value,
                        "endpoint": func.__name__,
                        "hierarchical": hierarchical
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: {required_role.value} role required"
                )

            logger.debug(
                "RBAC access granted",
                extra={
                    "user_id": str(current_user.id),
                    "user_role": current_user.system_role.value,
                    "required_role": required_role.value,
                    "endpoint": func.__name__
                }
            )

            # Wywołaj oryginalną funkcję
            return await func(*args, **kwargs)

        return wrapper
    return decorator
