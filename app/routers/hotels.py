from app.routers.dependencies import filter, db
from fastapi import APIRouter, status, HTTPException

from sqlalchemy import insert, select, func, delete, update, and_, or_

from app.schemas.hotels import HotelIn, HotelOut, HotelPatch
from app.models import HotelsOrm, RoomsOrm, BookingsOrm
from fastapi_cache.decorator import cache



router = APIRouter(prefix="/hotels", tags=["hotels"])


@router.get('/', response_model=list[HotelOut])
@cache(expire=10)
async def get_hotels(filter: filter, db: db):
    if filter.date_to and filter.date_from:
        if filter.date_from > filter.date_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The 'date_from' must be earlier than 'date_to'."
            )
        room_count_subquery = (
            select(RoomsOrm.hotel_id, func.count().label('room_count'))
            .group_by(RoomsOrm.hotel_id)
            .subquery()
        )

        booked_rooms_subquery = (
            select(RoomsOrm.hotel_id, func.count().label('booked_rooms'))
            .where(RoomsOrm.id.in_(
                select(BookingsOrm.room_id)
                .where(
                    or_(
                        BookingsOrm.date_from.between(filter.date_from, filter.date_to),
                        BookingsOrm.date_to.between(filter.date_from, filter.date_to)
                    )
                )
                .group_by(BookingsOrm.room_id)
            ))
            .group_by(RoomsOrm.hotel_id)
            .subquery()
        )

        query = (
            select(HotelsOrm)
            .join(room_count_subquery, HotelsOrm.id == room_count_subquery.c.hotel_id)
            .outerjoin(booked_rooms_subquery, HotelsOrm.id == booked_rooms_subquery.c.hotel_id)
            .where((room_count_subquery.c.room_count - func.coalesce(booked_rooms_subquery.c.booked_rooms, 0)) != 0)
        )
    else:
        query = select(HotelsOrm)
    if filter.location:
        query = query.filter(func.lower(HotelsOrm.location).contains(filter.location.strip().lower()))
    if filter.title:
        query = query.filter(func.lower(HotelsOrm.title).contains(filter.title.strip().lower()))
    query = query.offset(filter.offset).limit(filter.limit)
    hotels = await db.scalars(query, {'date_from': filter.date_from, 'date_to': filter.date_to})
    return [HotelOut.model_validate(el.__dict__) for el in hotels]


@router.post('/', response_model=HotelOut, status_code=status.HTTP_201_CREATED)
async def create_hotel(hotel: HotelIn, db: db):
    hotel = await db.scalar(insert(HotelsOrm).values(**hotel.model_dump()).returning(HotelsOrm))
    await db.commit()
    return hotel


@router.get('/{hotel_id}', response_model=HotelOut)
async def get_hotel(hotel_id: int, db: db):
    hotel = await db.scalar(select(HotelsOrm).where(HotelsOrm.id == hotel_id))
    if hotel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='hotel not found'
        )
    return hotel


@router.put('/{hotel_id}', response_model=HotelOut)
async def edit_hotel(hotel_id: int, hotel: HotelIn, db: db):
    hotel_db = await db.scalar(select(HotelsOrm).where(HotelsOrm.id == hotel_id))
    if hotel_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='hotel not found'
        )
    hotel = await db.scalar(update(HotelsOrm).where(HotelsOrm.id == hotel_id).values(**hotel.model_dump()).returning(HotelsOrm))
    await db.commit()
    return hotel


@router.patch('/{hotel_id}', response_model=HotelOut)
async def partially_edit_hotel(hotel_id: int, hotel: HotelPatch, db: db):
    hotel_db = await db.scalar(select(HotelsOrm).where(HotelsOrm.id == hotel_id))
    if hotel_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='hotel not found'
        )
    hotel = await db.scalar(update(HotelsOrm).values(**hotel.model_dump(exclude_unset=True)).returning(HotelsOrm))
    await db.commit()
    return hotel


@router.delete('/{hotel_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_hotel(hotel_id: int, db: db):
    hotel = await db.scalar(select(HotelsOrm).where(HotelsOrm.id == hotel_id))
    if hotel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='hotel not found'
        )
    await db.execute(delete(HotelsOrm).where(HotelsOrm.id == hotel_id))
    await db.commit()