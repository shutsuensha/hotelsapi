from unittest import mock

mock.patch("fastapi_cache.decorator.cache", lambda *args, **kwargs: lambda f: f).start()

import pytest # noqa: E402
from app.database import Base # noqa: E402
from app.models import * # noqa: E402, F403
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine # noqa: E402
from sqlalchemy import NullPool # noqa: E402
from httpx import AsyncClient # noqa: E402
from app.main import app # noqa: E402
from app.routers.dependencies import get_db # noqa: E402
import json # noqa: E402

db_url = "postgresql+asyncpg://evalshine:docent1315@booking_db_test:5432/booking"

engine_null_pool = create_async_engine(db_url, poolclass=NullPool)
async_session_maker_null_pool = async_sessionmaker(bind=engine_null_pool, expire_on_commit=False)


async def get_db_null_pool():
    async with async_session_maker_null_pool() as session:
        yield session


@pytest.fixture(scope="function")
async def db(): 
    async for db in get_db_null_pool():
        yield db


app.dependency_overrides[get_db] = get_db_null_pool


@pytest.fixture(scope="session")
async def ac() -> AsyncClient:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine_null_pool.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    with open("tests/mock_hotels.json", encoding="utf-8") as file_hotels:
        hotels = json.load(file_hotels)
    with open("tests/mock_rooms.json", encoding="utf-8") as file_rooms:
        rooms = json.load(file_rooms)

    async with async_session_maker_null_pool() as session:
        # Insert hotels
        hotel_instances = []
        for hotel in hotels:
            hotel_instance = HotelsOrm( # noqa: F405
                title=hotel["title"],
                location=hotel["location"]
            )
            hotel_instances.append(hotel_instance)
        session.add_all(hotel_instances)
        await session.commit()
        
        # Insert rooms
        room_instances = []
        for room in rooms:
            room_instance = RoomsOrm(  # noqa: F405
                hotel_id=room["hotel_id"],
                title=room["title"],
                description=room.get("description"),
                price=room["price"],
                quantity=room["quantity"]
            )
            room_instances.append(room_instance)
        session.add_all(room_instances)
        await session.commit()
        


@pytest.fixture(scope="session", autouse=True)
async def register_user(ac, setup_database):
    await ac.post(
        "/auth/register",
        json={
            "email": "kot@pes.com",
            "password": "1234"
        }
    )


@pytest.fixture(scope="session")
async def authenticated_ac(register_user, ac):
    await ac.post(
        "/auth/login",
        json={
            "email": "kot@pes.com",
            "password": "1234"
        }
    )
    assert ac.cookies["access_token"]
    yield ac