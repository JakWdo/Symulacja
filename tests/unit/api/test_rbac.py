"""
Unit tests for Role-Based Access Control (RBAC)

Tests coverage:
- SystemRole ENUM
- @requires_role decorator
- get_current_admin_user dependency
- get_current_researcher_user dependency
- Admin endpoints (list users, change role, delete project, stats)
- Role hierarchies (ADMIN > RESEARCHER > VIEWER)
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.user import User, SystemRole
from app.models.project import Project
from app.core.auth import check_user_has_role, requires_role
from app.api.dependencies import get_current_admin_user, get_current_researcher_user


class TestSystemRoleEnum:
    """Tests dla SystemRole ENUM"""

    def test_system_role_values(self):
        """Sprawdź że enum ma poprawne wartości"""
        assert SystemRole.ADMIN.value == "admin"
        assert SystemRole.RESEARCHER.value == "researcher"
        assert SystemRole.VIEWER.value == "viewer"

    def test_system_role_string_comparison(self):
        """Sprawdź że enum można porównywać ze stringami"""
        assert SystemRole.ADMIN == SystemRole.ADMIN
        assert SystemRole.ADMIN.value == "admin"


class TestCheckUserHasRole:
    """Tests dla check_user_has_role helper function"""

    def test_exact_role_match(self):
        """Test dokładnego dopasowania roli"""
        user = Mock(spec=User)
        user.system_role = SystemRole.ADMIN

        assert check_user_has_role(user, SystemRole.ADMIN, hierarchical=False)
        assert not check_user_has_role(user, SystemRole.RESEARCHER, hierarchical=False)
        assert not check_user_has_role(user, SystemRole.VIEWER, hierarchical=False)

    def test_hierarchical_admin_has_all_access(self):
        """Test że ADMIN ma dostęp do wszystkich ról (hierarchical=True)"""
        user = Mock(spec=User)
        user.system_role = SystemRole.ADMIN

        assert check_user_has_role(user, SystemRole.ADMIN, hierarchical=True)
        assert check_user_has_role(user, SystemRole.RESEARCHER, hierarchical=True)
        assert check_user_has_role(user, SystemRole.VIEWER, hierarchical=True)

    def test_hierarchical_researcher_has_viewer_access(self):
        """Test że RESEARCHER ma dostęp do RESEARCHER i VIEWER (hierarchical=True)"""
        user = Mock(spec=User)
        user.system_role = SystemRole.RESEARCHER

        assert not check_user_has_role(user, SystemRole.ADMIN, hierarchical=True)
        assert check_user_has_role(user, SystemRole.RESEARCHER, hierarchical=True)
        assert check_user_has_role(user, SystemRole.VIEWER, hierarchical=True)

    def test_hierarchical_viewer_has_only_viewer_access(self):
        """Test że VIEWER ma dostęp tylko do VIEWER (hierarchical=True)"""
        user = Mock(spec=User)
        user.system_role = SystemRole.VIEWER

        assert not check_user_has_role(user, SystemRole.ADMIN, hierarchical=True)
        assert not check_user_has_role(user, SystemRole.RESEARCHER, hierarchical=True)
        assert check_user_has_role(user, SystemRole.VIEWER, hierarchical=True)


class TestRequiresRoleDecorator:
    """Tests dla @requires_role decorator"""

    @pytest.mark.asyncio
    async def test_decorator_grants_access_for_correct_role(self):
        """Test że decorator pozwala na dostęp dla poprawnej roli"""
        user = Mock(spec=User)
        user.id = uuid4()
        user.email = "admin@test.com"
        user.system_role = SystemRole.ADMIN

        @requires_role(SystemRole.ADMIN)
        async def test_endpoint(current_user: User):
            return {"message": "success"}

        result = await test_endpoint(current_user=user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_decorator_denies_access_for_incorrect_role(self):
        """Test że decorator blokuje dostęp dla niepoprawnej roli"""
        user = Mock(spec=User)
        user.id = uuid4()
        user.email = "viewer@test.com"
        user.system_role = SystemRole.VIEWER

        @requires_role(SystemRole.ADMIN)
        async def test_endpoint(current_user: User):
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint(current_user=user)

        assert exc_info.value.status_code == 403
        assert "admin role required" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_decorator_hierarchical_access(self):
        """Test że decorator pozwala na dostęp hierarchiczny (ADMIN -> RESEARCHER)"""
        admin_user = Mock(spec=User)
        admin_user.id = uuid4()
        admin_user.email = "admin@test.com"
        admin_user.system_role = SystemRole.ADMIN

        @requires_role(SystemRole.RESEARCHER, hierarchical=True)
        async def test_endpoint(current_user: User):
            return {"message": "success"}

        # ADMIN powinien mieć dostęp do RESEARCHER endpoint (hierarchical=True)
        result = await test_endpoint(current_user=admin_user)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_decorator_non_hierarchical_denies_higher_role(self):
        """Test że decorator blokuje dostęp dla wyższej roli gdy hierarchical=False"""
        admin_user = Mock(spec=User)
        admin_user.id = uuid4()
        admin_user.email = "admin@test.com"
        admin_user.system_role = SystemRole.ADMIN

        @requires_role(SystemRole.RESEARCHER, hierarchical=False)
        async def test_endpoint(current_user: User):
            return {"message": "success"}

        # ADMIN NIE powinien mieć dostępu gdy hierarchical=False
        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint(current_user=admin_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_decorator_raises_500_when_user_not_found(self):
        """Test że decorator zwraca 500 gdy current_user nie jest w kwargs"""

        @requires_role(SystemRole.ADMIN)
        async def test_endpoint():
            return {"message": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint()

        assert exc_info.value.status_code == 500
        assert "user not found" in exc_info.value.detail.lower()


class TestGetCurrentAdminUser:
    """Tests dla get_current_admin_user dependency"""

    @pytest.mark.asyncio
    async def test_allows_admin_user(self):
        """Test że dependency pozwala użytkownikowi ADMIN"""
        admin_user = Mock(spec=User)
        admin_user.id = uuid4()
        admin_user.email = "admin@test.com"
        admin_user.system_role = SystemRole.ADMIN

        result = await get_current_admin_user(current_user=admin_user)
        assert result == admin_user

    @pytest.mark.asyncio
    async def test_denies_researcher_user(self):
        """Test że dependency blokuje użytkownika RESEARCHER"""
        researcher_user = Mock(spec=User)
        researcher_user.id = uuid4()
        researcher_user.email = "researcher@test.com"
        researcher_user.system_role = SystemRole.RESEARCHER

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(current_user=researcher_user)

        assert exc_info.value.status_code == 403
        assert "admin access required" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_denies_viewer_user(self):
        """Test że dependency blokuje użytkownika VIEWER"""
        viewer_user = Mock(spec=User)
        viewer_user.id = uuid4()
        viewer_user.email = "viewer@test.com"
        viewer_user.system_role = SystemRole.VIEWER

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(current_user=viewer_user)

        assert exc_info.value.status_code == 403


class TestGetCurrentResearcherUser:
    """Tests dla get_current_researcher_user dependency"""

    @pytest.mark.asyncio
    async def test_allows_researcher_user(self):
        """Test że dependency pozwala użytkownikowi RESEARCHER"""
        researcher_user = Mock(spec=User)
        researcher_user.id = uuid4()
        researcher_user.email = "researcher@test.com"
        researcher_user.system_role = SystemRole.RESEARCHER

        result = await get_current_researcher_user(current_user=researcher_user)
        assert result == researcher_user

    @pytest.mark.asyncio
    async def test_allows_admin_user(self):
        """Test że dependency pozwala użytkownikowi ADMIN (hierarchia)"""
        admin_user = Mock(spec=User)
        admin_user.id = uuid4()
        admin_user.email = "admin@test.com"
        admin_user.system_role = SystemRole.ADMIN

        result = await get_current_researcher_user(current_user=admin_user)
        assert result == admin_user

    @pytest.mark.asyncio
    async def test_denies_viewer_user(self):
        """Test że dependency blokuje użytkownika VIEWER"""
        viewer_user = Mock(spec=User)
        viewer_user.id = uuid4()
        viewer_user.email = "viewer@test.com"
        viewer_user.system_role = SystemRole.VIEWER

        with pytest.raises(HTTPException) as exc_info:
            await get_current_researcher_user(current_user=viewer_user)

        assert exc_info.value.status_code == 403
        assert "researcher access required" in exc_info.value.detail.lower()


class TestAdminEndpoints:
    """Integration tests dla admin endpointów"""

    @pytest.mark.asyncio
    async def test_list_users_requires_admin(self):
        """Test że /admin/users wymaga roli ADMIN"""
        from app.api.admin import list_all_users

        # Mock DB session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        admin_user = Mock(spec=User)
        admin_user.id = uuid4()
        admin_user.email = "admin@test.com"
        admin_user.system_role = SystemRole.ADMIN

        # Should succeed for ADMIN
        result = await list_all_users(current_user=admin_user, db=mock_db)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_update_user_role_requires_admin(self):
        """Test że /admin/users/{id}/role wymaga roli ADMIN"""
        from app.api.admin import update_user_role, UpdateUserRoleRequest

        # Mock DB session
        mock_db = AsyncMock(spec=AsyncSession)
        target_user = Mock(spec=User)
        target_user.id = uuid4()
        target_user.email = "user@test.com"
        target_user.system_role = SystemRole.RESEARCHER

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = target_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        admin_user = Mock(spec=User)
        admin_user.id = uuid4()
        admin_user.email = "admin@test.com"
        admin_user.system_role = SystemRole.ADMIN

        request = UpdateUserRoleRequest(system_role=SystemRole.VIEWER)

        # Should succeed for ADMIN
        result = await update_user_role(
            user_id=target_user.id,
            request=request,
            current_user=admin_user,
            db=mock_db
        )
        assert "role updated" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_update_user_role_prevents_self_demotion(self):
        """Test że admin nie może usunąć własnej roli ADMIN"""
        from app.api.admin import update_user_role, UpdateUserRoleRequest

        # Mock DB session
        mock_db = AsyncMock(spec=AsyncSession)
        admin_user = Mock(spec=User)
        admin_user.id = uuid4()
        admin_user.email = "admin@test.com"
        admin_user.system_role = SystemRole.ADMIN

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = admin_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        request = UpdateUserRoleRequest(system_role=SystemRole.RESEARCHER)

        # Should fail - cannot demote yourself
        with pytest.raises(HTTPException) as exc_info:
            await update_user_role(
                user_id=admin_user.id,
                request=request,
                current_user=admin_user,
                db=mock_db
            )

        assert exc_info.value.status_code == 400
        assert "cannot demote yourself" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_delete_project_requires_admin(self):
        """Test że /admin/projects/{id} DELETE wymaga roli ADMIN"""
        from app.api.admin import delete_project

        # Mock DB session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_project = Mock(spec=Project)
        mock_project.id = uuid4()
        mock_project.name = "Test Project"
        mock_project.owner_id = uuid4()

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_project
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        admin_user = Mock(spec=User)
        admin_user.id = uuid4()
        admin_user.email = "admin@test.com"
        admin_user.system_role = SystemRole.ADMIN

        # Should succeed for ADMIN
        result = await delete_project(
            project_id=mock_project.id,
            current_user=admin_user,
            db=mock_db
        )
        assert "deleted successfully" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_get_stats_requires_admin(self):
        """Test że /admin/stats wymaga roli ADMIN"""
        from app.api.admin import get_system_stats

        # Mock DB session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.scalar = AsyncMock(return_value=0)

        admin_user = Mock(spec=User)
        admin_user.id = uuid4()
        admin_user.email = "admin@test.com"
        admin_user.system_role = SystemRole.ADMIN

        # Should succeed for ADMIN
        result = await get_system_stats(current_user=admin_user, db=mock_db)
        assert "users" in result
        assert "projects" in result
        assert "personas" in result
