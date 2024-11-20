from app.schemas.hotels import HotelIn
from sqlalchemy import insert
from app.models import HotelsOrm


async def test_add_hotel(db):
    hotel = HotelIn(title="Hotel 5", location="Сочи")
    hotel = await db.scalar(
        insert(HotelsOrm).values(**hotel.model_dump()).returning(HotelsOrm)
    )
    await db.commit()
