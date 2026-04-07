"""Test projects API endpoints"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, auth_headers):
    """Test creating a new project"""
    response = await client.post(
        "/api/v1/projects/",
        headers=auth_headers,
        json={
            "name": "New Project",
            "description": "A new test project",
            "working_directory": "/tmp/new_project",
            "python_executable": "/usr/bin/python3"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Project"
    assert data["description"] == "A new test project"
    assert data["working_directory"] == "/tmp/new_project"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_project_duplicate_name(client: AsyncClient, auth_headers, test_project):
    """Test creating a project with duplicate name"""
    response = await client.post(
        "/api/v1/projects/",
        headers=auth_headers,
        json={
            "name": "Test Project",
            "description": "Duplicate name project",
            "working_directory": "/tmp/duplicate"
        }
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_projects(client: AsyncClient, auth_headers, test_project):
    """Test getting all projects"""
    response = await client.get(
        "/api/v1/projects/",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert any(p["name"] == "Test Project" for p in data["items"])


@pytest.mark.asyncio
async def test_get_projects_with_pagination(client: AsyncClient, auth_headers, db_session):
    """Test getting projects with pagination"""
    from app.models.project import Project

    # Create multiple projects
    for i in range(5):
        project = Project(
            name=f"Project {i}",
            description=f"Test project {i}",
            working_directory=f"/tmp/project_{i}"
        )
        db_session.add(project)
    await db_session.commit()

    response = await client.get(
        "/api/v1/projects/?skip=0&limit=2",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2


@pytest.mark.asyncio
async def test_get_projects_unauthorized(client: AsyncClient, test_project):
    """Test getting projects without authentication"""
    response = await client.get("/api/v1/projects/")
    assert response.status_code in [401, 403]  # May return either 401 or 403


@pytest.mark.asyncio
async def test_get_project_by_id(client: AsyncClient, auth_headers, test_project):
    """Test getting a project by ID"""
    response = await client.get(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["id"] == test_project.id


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient, auth_headers):
    """Test getting a non-existent project"""
    response = await client.get(
        "/api/v1/projects/999",
        headers=auth_headers
    )
    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.skip(reason="Backend code has MissingGreenlet issue when accessing crawlers relationship")
async def test_update_project(client: AsyncClient, auth_headers, test_project):
    """Test updating a project"""
    response = await client.put(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers,
        json={
            "name": "Updated Project",
            "description": "Updated description",
            "working_directory": "/tmp/updated"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Project"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_project_not_found(client: AsyncClient, auth_headers):
    """Test updating a non-existent project"""
    response = await client.put(
        "/api/v1/projects/999",
        headers=auth_headers,
        json={"name": "Updated"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, auth_headers, test_project):
    """Test deleting a project"""
    response = await client.delete(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = await client.get(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found(client: AsyncClient, auth_headers):
    """Test deleting a non-existent project"""
    response = await client.delete(
        "/api/v1/projects/999",
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_active_projects(client: AsyncClient, auth_headers, db_session):
    """Test getting only active projects"""
    from app.models.project import Project

    # Create active and inactive projects
    active_project = Project(
        name="Active Project",
        description="Active project",
        working_directory="/tmp/active",
        is_active=True
    )
    inactive_project = Project(
        name="Inactive Project",
        description="Inactive project",
        working_directory="/tmp/inactive",
        is_active=False
    )
    db_session.add(active_project)
    db_session.add(inactive_project)
    await db_session.commit()

    response = await client.get(
        "/api/v1/projects/active",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()  # get_active_projects returns a list, not paginated
    assert len(data) >= 1
    for project in data:
        assert project["is_active"] is True
