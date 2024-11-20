from contextlib import asynccontextmanager

import logging

from fastapi import FastAPI
from app.routers import hotels, rooms, auth, bookings, facilities, images

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from app.config import settings

logging.basicConfig(level=logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info('vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv')
    logging.info(f"Начинаю подключение к Redis {settings.REDIS_URL}")
    redis = aioredis.from_url(settings.REDIS_URL)
    logging.info(f"Успешное подключение к Redis {settings.REDIS_URL}")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    logging.info("FastAPI cache initialized")
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(hotels.router)
app.include_router(rooms.router)
app.include_router(bookings.router)
app.include_router(facilities.router)
app.include_router(images.router)