import aioredis

from sqlalchemy.orm import sessionmaker
from core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

POSTGRES_DATABASE_URL = settings.POSTGRES_DATABASE_URL
postgres_engine = create_async_engine(POSTGRES_DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    bind=postgres_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_postgres_db():
    async with AsyncSessionLocal() as session:
        yield session

class RedisClient:
    _redis = None

    @classmethod
    async def get_redis(cls):
        if cls._redis is None:
            cls._redis = await aioredis.from_url(f"redis://{settings.REDIS_HOST}", decode_responses=True)
        return cls._redis

    @classmethod
    async def close_redis(cls):
        if cls._redis:
            await cls._redis.close()
            cls._redis = None
