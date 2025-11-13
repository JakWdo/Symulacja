"""
Testy RBAC + Team Membership - Faza 1

Testy sprawdzające:
- Tworzenie teamów
- Dostęp do teamów (member, owner, viewer)
- Dodawanie/usuwanie członków
- Scoping projektów przez team membership
- Role-based access control (200/403)
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.models import User, Project, Team, TeamMembership
from app.models.team import TeamRole
from app.models.user import SystemRole
from app.core.security import create_access_token, get_password_hash


@pytest_asyncio.fixture
async def team_owner(db_session):
    """Użytkownik będący właścicielem teamu."""
    user = User(
        id=uuid4(),
        email="owner@example.com",
        hashed_password=get_password_hash("SecurePass123"),
        full_name="Team Owner",
        system_role=SystemRole.RESEARCHER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def team_member(db_session):
    """Użytkownik będący członkiem teamu."""
    user = User(
        id=uuid4(),
        email="member@example.com",
        hashed_password=get_password_hash("SecurePass123"),
        full_name="Team Member",
        system_role=SystemRole.RESEARCHER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def team_viewer(db_session):
    """Użytkownik będący viewerem teamu."""
    user = User(
        id=uuid4(),
        email="viewer@example.com",
        hashed_password=get_password_hash("SecurePass123"),
        full_name="Team Viewer",
        system_role=SystemRole.RESEARCHER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def non_member(db_session):
    """Użytkownik NIE będący członkiem teamu."""
    user = User(
        id=uuid4(),
        email="nonmember@example.com",
        hashed_password=get_password_hash("SecurePass123"),
        full_name="Non Member",
        system_role=SystemRole.RESEARCHER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session):
    """Użytkownik z rolą ADMIN."""
    user = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password=get_password_hash("SecurePass123"),
        full_name="Admin User",
        system_role=SystemRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_team(db_session, team_owner, team_member, team_viewer):
    """Team z trzema członkami: owner, member, viewer."""
    team = Team(
        id=uuid4(),
        name="Test Team",
        description="Team for testing RBAC",
        is_active=True,
    )
    db_session.add(team)
    await db_session.flush()

    # Dodaj członków
    owner_membership = TeamMembership(
        team_id=team.id,
        user_id=team_owner.id,
        role_in_team=TeamRole.OWNER,
    )
    member_membership = TeamMembership(
        team_id=team.id,
        user_id=team_member.id,
        role_in_team=TeamRole.MEMBER,
    )
    viewer_membership = TeamMembership(
        team_id=team.id,
        user_id=team_viewer.id,
        role_in_team=TeamRole.VIEWER,
    )

    db_session.add_all([owner_membership, member_membership, viewer_membership])
    await db_session.commit()
    await db_session.refresh(team)

    return team


@pytest_asyncio.fixture
async def team_project(db_session, test_team, team_owner):
    """Projekt należący do teamu."""
    project = Project(
        id=uuid4(),
        owner_id=team_owner.id,
        team_id=test_team.id,
        name="Team Project",
        description="Project for testing team access",
        target_demographics={
            "age_group": {"18-24": 0.5, "25-34": 0.5},
            "gender": {"male": 0.5, "female": 0.5},
        },
        target_sample_size=20,
        is_active=True,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


def get_auth_headers(user: User) -> dict:
    """Generuj auth headers dla użytkownika."""
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestTeamCreation:
    """Testy tworzenia teamów."""

    @pytest.mark.asyncio
    async def test_researcher_can_create_team(self, db_session, team_owner):
        """RESEARCHER może tworzyć teamy."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_owner)

        response = client.post(
            "/api/v1/teams",
            headers=headers,
            json={"name": "New Team", "description": "Test team"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Team"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_team(self, db_session):
        """VIEWER nie może tworzyć teamów."""
        # Utwórz użytkownika z rolą VIEWER
        viewer = User(
            id=uuid4(),
            email="viewer_only@example.com",
            hashed_password=get_password_hash("SecurePass123"),
            full_name="Viewer Only",
            system_role=SystemRole.VIEWER,
            is_active=True,
        )
        db_session.add(viewer)
        await db_session.commit()

        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(viewer)

        response = client.post(
            "/api/v1/teams",
            headers=headers,
            json={"name": "New Team", "description": "Test team"}
        )

        assert response.status_code == 403
        assert "view-only users cannot perform this action" in response.json()["detail"]


class TestTeamAccess:
    """Testy dostępu do teamów."""

    @pytest.mark.asyncio
    async def test_owner_can_get_team(self, db_session, test_team, team_owner):
        """Owner może pobierać dane teamu."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_owner)

        response = client.get(f"/api/v1/teams/{test_team.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Team"
        assert data["member_count"] == 3

    @pytest.mark.asyncio
    async def test_member_can_get_team(self, db_session, test_team, team_member):
        """Member może pobierać dane teamu."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_member)

        response = client.get(f"/api/v1/teams/{test_team.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Team"

    @pytest.mark.asyncio
    async def test_viewer_can_get_team(self, db_session, test_team, team_viewer):
        """Viewer może pobierać dane teamu."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_viewer)

        response = client.get(f"/api/v1/teams/{test_team.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Team"

    @pytest.mark.asyncio
    async def test_non_member_cannot_get_team(self, db_session, test_team, non_member):
        """Non-member NIE może pobierać danych teamu."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(non_member)

        response = client.get(f"/api/v1/teams/{test_team.id}", headers=headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_admin_can_get_any_team(self, db_session, test_team, admin_user):
        """Admin może pobierać dane każdego teamu."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(admin_user)

        response = client.get(f"/api/v1/teams/{test_team.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Team"


class TestTeamManagement:
    """Testy zarządzania teamem."""

    @pytest.mark.asyncio
    async def test_owner_can_update_team(self, db_session, test_team, team_owner):
        """Owner może aktualizować team."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_owner)

        response = client.put(
            f"/api/v1/teams/{test_team.id}",
            headers=headers,
            json={"name": "Updated Team Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Team Name"

    @pytest.mark.asyncio
    async def test_member_cannot_update_team(self, db_session, test_team, team_member):
        """Member NIE może aktualizować teamu."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_member)

        response = client.put(
            f"/api/v1/teams/{test_team.id}",
            headers=headers,
            json={"name": "Updated Name"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_owner_can_delete_team(self, db_session, test_team, team_owner):
        """Owner może usuwać team."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_owner)

        response = client.delete(f"/api/v1/teams/{test_team.id}", headers=headers)

        assert response.status_code == 204


class TestProjectAccess:
    """Testy dostępu do projektów przez team membership."""

    @pytest.mark.asyncio
    async def test_member_can_access_team_project(self, db_session, team_project, team_member):
        """Member teamu może dostać się do projektu teamu."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_member)

        response = client.get(f"/api/v1/projects/{team_project.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Team Project"

    @pytest.mark.asyncio
    async def test_viewer_can_access_team_project(self, db_session, team_project, team_viewer):
        """Viewer teamu może dostać się do projektu teamu."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_viewer)

        response = client.get(f"/api/v1/projects/{team_project.id}", headers=headers)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_non_member_cannot_access_team_project(self, db_session, team_project, non_member):
        """Non-member NIE może dostać się do projektu teamu."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(non_member)

        response = client.get(f"/api/v1/projects/{team_project.id}", headers=headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_admin_can_access_any_project(self, db_session, team_project, admin_user):
        """Admin może dostać się do każdego projektu."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(admin_user)

        response = client.get(f"/api/v1/projects/{team_project.id}", headers=headers)

        assert response.status_code == 200


class TestMemberManagement:
    """Testy zarządzania członkami teamu."""

    @pytest.mark.asyncio
    async def test_owner_can_add_member(self, db_session, test_team, team_owner, non_member):
        """Owner może dodawać członków."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_owner)

        response = client.post(
            f"/api/v1/teams/{test_team.id}/members",
            headers=headers,
            json={
                "user_id": str(non_member.id),
                "role_in_team": "member"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(non_member.id)

    @pytest.mark.asyncio
    async def test_member_cannot_add_member(self, db_session, test_team, team_member, non_member):
        """Member NIE może dodawać członków."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_member)

        response = client.post(
            f"/api/v1/teams/{test_team.id}/members",
            headers=headers,
            json={
                "user_id": str(non_member.id),
                "role_in_team": "member"
            }
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_owner_can_remove_member(self, db_session, test_team, team_owner, team_member):
        """Owner może usuwać członków."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_owner)

        response = client.delete(
            f"/api/v1/teams/{test_team.id}/members/{team_member.id}",
            headers=headers
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_member_cannot_remove_member(self, db_session, test_team, team_member, team_viewer):
        """Member NIE może usuwać innych członków."""
        client = TestClient(app, raise_server_exceptions=False)
        headers = get_auth_headers(team_member)

        response = client.delete(
            f"/api/v1/teams/{test_team.id}/members/{team_viewer.id}",
            headers=headers
        )

        assert response.status_code == 403
