from datetime import date
from app.models import * # noqa: F403
from sqlalchemy import select, update, delete

async def test_booking_crud(db):
    #create
    new_booking = BookingsOrm( # noqa: F405
            user_id=1,
            room_id=1,
            date_from=date(year=2024, month=8, day=10),
            date_to=date(year=2024, month=8, day=20),
            price=100
        )
    db.add(new_booking)
    await db.commit()

    #read
    result = await db.execute(select(BookingsOrm).where(BookingsOrm.id == new_booking.id)) # noqa: F405 
    booking = result.scalars().first()

    assert booking
    assert booking.id == new_booking.id
    assert booking.room_id == new_booking.room_id
    assert booking.user_id == new_booking.user_id

    #update
    update_values = {}
    update_values["user_id"] = 1
    update_values["room_id"] = 1
    update_values["date_from"] = date(year=2024, month=8, day=10)
    update_values["date_to"] = date(year=2024, month=8, day=25)
    update_values["price"] = 100

    await db.execute(
            update(BookingsOrm) # noqa: F405
            .where(BookingsOrm.id == new_booking.id) # noqa: F405
            .values(**update_values)
        )
    await db.commit()

    result = await db.execute(select(BookingsOrm).where(BookingsOrm.id == new_booking.id)) # noqa: F405
    booking = result.scalars().first()

    assert booking
    assert booking.id == new_booking.id
    assert booking.date_to == date(year=2024, month=8, day=25)

    #delete
    await db.execute(delete(BookingsOrm).where(BookingsOrm.id == new_booking.id)) # noqa: F405
    await db.commit()
    
    result = await db.execute(select(BookingsOrm).where(BookingsOrm.id == new_booking.id)) # noqa: F405
    booking = result.scalars().first()
    assert not booking