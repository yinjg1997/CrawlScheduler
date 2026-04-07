"""Test crawlers API endpoints"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_crawler(client: AsyncClient, auth_headers, test_project):
    """Test creating a new crawler"""
    response = await client.post(
        "/api/v1/crawlers/",
        headers=auth_headers,
        json={
            "project_id": test_project.id,
            "name": "New Crawler",
            "description": "A new test crawler",
            "command": "python scrape.py --verbose"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Crawler"
    assert data["project_id"] == test_project.id
    assert data["command"] == "python scrape.py --verbose"


@pytest.mark.asyncio
async def test_create_crawler_invalid_project(client: AsyncClient, auth_headers):
    """Test creating a crawler with invalid project"""
    response = await client.post(
        "/api/v1/crawlers/",
        headers=auth_headers,
        json={
            "project_id": 999,
            "name": "Invalid Crawler",
            "command": "python scrape.py"
        }
    )


@pytest.mark.asyncio
async def test_get_crawlers(client: AsyncClient, auth_headers, test_crawler):
    """Test getting all crawlers"""
    response = await client.get(
        "/api/v1/crawlers/",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert any(c["name"] == "Test Crawler" for c in data["items"])


@pytest.mark.asyncio
async def test_get_crawlers_by_project(client: AsyncClient, auth_headers, test_crawler, test_project):
    """Test filtering crawlers by project"""
    response = await client.get(
        f"/api/v1/crawlers/?project_id={test_project.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["project_id"] == test_project.id


@pytest.mark.asyncio
async def test_get_crawlers_unauthorized(client: AsyncClient, test_crawler):
    """Test getting crawlers without authentication"""
    response = await client.get("/api/v1/crawlers/")
    assert response.status_code in [401, 403]  # May return either 401 or 403


@pytest.mark.asyncio
async def test_get_crawler_by_id(client: AsyncClient, auth_headers, test_crawler):
    """Test getting a crawler by ID"""
    response = await client.get(
        f"/api/v1/crawlers/{test_crawler.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Crawler"
    assert data["id"] == test_crawler.id


@pytest.mark.asyncio
async def test_get_crawler_not_found(client: AsyncClient, auth_headers):
    """Test getting a non-existent crawler"""
    response = await client.get(
        "/api/v1/crawlers/999",
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_crawler(client: AsyncClient, auth_headers, test_crawler):
    """Test updating a crawler"""
    response = await client.put(
        f"/api/v1/crawlers/{test_crawler.id}",
        headers=auth_headers,
        json={
            "name": "Updated Crawler",
            "description": "Updated description",
            "command": "python main.py --updated"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Crawler"
    assert data["command"] == "python main.py --updated"


@pytest.mark.asyncio
async def test_update_crawler_not_found(client: AsyncClient, auth_headers):
    """Test updating a non-existent crawler"""
    response = await client.put(
        "/api/v1/crawlers/999",
        headers=auth_headers,
        json={"name": "Updated"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_crawler(client: AsyncClient, auth_headers, test_crawler):
    """Test deleting a crawler"""
    response = await client.delete(
        f"/api/v1/crawlers/{test_crawler.id}",
        headers=auth_headers
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = await client.get(
        f"/api/v1/crawlers/{test_crawler.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_execute_crawler(client: AsyncClient, auth_headers, test_crawler):
    """Test executing a crawler manually"""
    response = await client.post(
        f"/api/v1/crawlers/{test_crawler.id}/execute",
        headers=auth_headers
    )
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["message"] == "Task execution started"


@pytest.mark.asyncio
async def test_execute_crawler_not_found(client: AsyncClient, auth_headers):
    """Test executing a non-existent crawler"""
    response = await client.post(
        "/api/v1/crawlers/999/execute",
        headers=auth_headers
    )
    assert response.status_code == 404
