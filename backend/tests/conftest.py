"""Test fixtures and configuration"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.security import get_password_hash


# Test database URL (SQLite in memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@pytest.fixture
async def db_session():
    """Get a database session for testing"""
    # Create tables for each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session):
    """Get a test client"""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user"""
    from app.models.user import User

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_superuser(db_session: AsyncSession):
    """Create a test superuser"""
    from app.models.user import User

    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user):
    """Get authentication headers for a regular user"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(client: AsyncClient, test_superuser):
    """Get authentication headers for a superuser"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user):
    """Create a test project"""
    from app.models.project import Project

    project = Project(
        name="Test Project",
        description="A test project",
        working_directory="/tmp/test_project",
        python_executable="/usr/bin/python3",
        is_active=True
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def test_crawler(db_session: AsyncSession, test_project):
    """Create a test crawler"""
    from app.models.crawler import Crawler

    crawler = Crawler(
        project_id=test_project.id,
        name="Test Crawler",
        description="A test crawler",
        command="python main.py --test",
        is_active=True
    )
    db_session.add(crawler)
    await db_session.commit()
    await db_session.refresh(crawler)
    return crawler


@pytest.fixture
async def test_schedule(db_session: AsyncSession, test_crawler):
    """Create a test schedule"""
    from app.models.schedule import Schedule

    schedule = Schedule(
        crawler_id=test_crawler.id,
        name="Test Schedule",
        description="A test schedule",
        cron_expression="0 0 * * *",
        is_active=True
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)
    return schedule
