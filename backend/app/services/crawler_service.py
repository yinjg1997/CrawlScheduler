from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from ..models import Crawler
from ..schemas.crawler import CrawlerCreate, CrawlerUpdate, CrawlerResponse


class CrawlerService:
    """Service for managing crawler operations"""

    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all crawlers"""
        # Get total count
        count_result = await db.execute(select(func.count()).select_from(Crawler))
        total = count_result.scalar() or 0

        # Get paginated results
        result = await db.execute(
            select(Crawler)
            .options(selectinload(Crawler.project))
            .offset(skip)
            .limit(limit)
            .order_by(Crawler.created_at.desc())
        )
        crawlers = list(result.scalars().all())

        # Serialize through CrawlerResponse to get project_name
        items = [CrawlerResponse.model_validate(crawler) for crawler in crawlers]

        return {
            "total": total,
            "items": items
        }

    @staticmethod
    async def get_by_id(db: AsyncSession, crawler_id: int) -> Optional[CrawlerResponse]:
        """Get a crawler by ID"""
        result = await db.execute(
            select(Crawler)
            .options(selectinload(Crawler.schedules))
            .options(selectinload(Crawler.project))
            .where(Crawler.id == crawler_id)
        )
        crawler = result.scalar_one_or_none()
        if crawler:
            return CrawlerResponse.model_validate(crawler)
        return None

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Crawler]:
        """Get a crawler by name"""
        result = await db.execute(
            select(Crawler).where(Crawler.name == name)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, crawler: CrawlerCreate) -> CrawlerResponse:
        """Create a new crawler"""
        # Check if crawler with same name exists
        existing = await CrawlerService.get_by_name(db, crawler.name)
        if existing:
            raise ValueError(f"Crawler with name '{crawler.name}' already exists")

        db_crawler = Crawler(**crawler.model_dump())
        db.add(db_crawler)
        await db.commit()
        await db.refresh(db_crawler)

        # Reload with project relationship
        await db.refresh(db_crawler, ['project'])
        return CrawlerResponse.model_validate(db_crawler)

    @staticmethod
    async def update(
        db: AsyncSession,
        crawler_id: int,
        crawler_update: CrawlerUpdate
    ) -> Optional[CrawlerResponse]:
        """Update a crawler"""
        # Get the actual crawler model, not the response
        result = await db.execute(
            select(Crawler)
            .where(Crawler.id == crawler_id)
        )
        db_crawler = result.scalar_one_or_none()
        if not db_crawler:
            return None

        # Check if new name conflicts with existing crawler
        if crawler_update.name and crawler_update.name != db_crawler.name:
            existing = await CrawlerService.get_by_name(db, crawler_update.name)
            if existing:
                raise ValueError(f"Crawler with name '{crawler_update.name}' already exists")

        update_data = crawler_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_crawler, field, value)

        await db.commit()
        await db.refresh(db_crawler)

        # Reload with project relationship
        await db.refresh(db_crawler, ['project'])
        return CrawlerResponse.model_validate(db_crawler)

    @staticmethod
    async def delete(db: AsyncSession, crawler_id: int) -> bool:
        """Delete a crawler"""
        result = await db.execute(
            select(Crawler).where(Crawler.id == crawler_id)
        )
        db_crawler = result.scalar_one_or_none()
        if not db_crawler:
            return False

        await db.execute(
            delete(Crawler).where(Crawler.id == crawler_id)
        )
        await db.commit()
        return True
