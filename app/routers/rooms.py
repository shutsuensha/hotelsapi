from fastapi import APIRouter, status, HTTPException, Query
from app.routers.dependencies import db
from app.schemas.rooms import RoomIn, RoomOut, RoomPatch
from sqlalchemy import insert, select, delete, update, not_, or_, and_
from app.models import RoomsOrm, HotelsOrm, BookingsOrm, rooms_facilities
from datetime import date
from sqlalchemy.orm import selectinload


router = APIRouter(prefix="/hotels", tags=["rooms"])


@router.get("/{hotel_id}/rooms", response_model=list[RoomOut])
async def get_rooms(
    hotel_id: int,
    db: db,
    date_from: date = Query(example="2024-09-08"),
    date_to: date = Query(example="2024-09-20"),
):
    if date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The 'date_from' must be earlier than 'date_to'.",
        )
    hotel = await db.scalar(select(HotelsOrm).where(HotelsOrm.id == hotel_id))
    if hotel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="hotel not found")

    query = (
        select(RoomsOrm)
        .where(
            RoomsOrm.hotel_id == hotel_id,
            not_(
                select(BookingsOrm.room_id)
                .where(
                    BookingsOrm.room_id == RoomsOrm.id,
                    or_(
                        and_(
                            BookingsOrm.date_from <= date_to,
                            BookingsOrm.date_to >= date_from,
                        ),
                        and_(
                            BookingsOrm.date_from >= date_from,
                            BookingsOrm.date_to <= date_to,
                        ),
                    ),
                )
                .exists()
            ),
        )
        .options(selectinload(RoomsOrm.facilities))  # Eager load facilities
    )

    # Execute the query
    rooms = await db.scalars(query)

    result = []
    for room in rooms:
        room_data = {
            "id": room.id,
            "hotel_id": room.hotel_id,
            "title": room.title,
            "description": room.description,
            "price": room.price,
            "quantity": room.quantity,
            "facilities_ids": [facility.id for facility in room.facilities],
        }
        result.append(room_data)
    return result


@router.get("/{hotel_id}/rooms/{room_id}", response_model=RoomOut)
async def get_room(hotel_id: int, room_id: int, db: db):
    hotel = await db.scalar(select(HotelsOrm).where(HotelsOrm.id == hotel_id))
    if hotel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="hotel not found")
    room = await db.scalar(
        select(RoomsOrm)
        .where(RoomsOrm.hotel_id == hotel_id, RoomsOrm.id == room_id)
        .options(selectinload(RoomsOrm.facilities))
    )
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="room not found")
    room_data = {
        "id": room.id,
        "hotel_id": room.hotel_id,
        "title": room.title,
        "description": room.description,
        "price": room.price,
        "quantity": room.quantity,
        "facilities_ids": [facility.id for facility in room.facilities],
    }
    return room_data


@router.post("/{hotel_id}/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create_room(hotel_id: int, db: db, room_in: RoomIn):
    hotel = await db.scalar(select(HotelsOrm).where(HotelsOrm.id == hotel_id))
    if hotel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="hotel not found")
    room = await db.scalar(
        insert(RoomsOrm)
        .values(hotel_id=hotel_id, **room_in.model_dump(exclude={"facilities_ids"}))
        .returning(RoomsOrm)
    )

    insert_values = [
        {"room_id": room.id, "facility_id": facility_id} for facility_id in room_in.facilities_ids
    ]
    await db.execute(insert(rooms_facilities), insert_values)
    await db.commit()
    room_data = {
        "id": room.id,
        "hotel_id": room.hotel_id,
        "title": room.title,
        "description": room.description,
        "price": room.price,
        "quantity": room.quantity,
        "facilities_ids": room_in.facilities_ids,
    }
    return room_data


@router.put("/{hotel_id}/rooms/{room_id}", response_model=RoomOut)
async def edit_room(hotel_id: int, room_id: int, db: db, room_in: RoomIn):
    # Ensure room exists
    await get_room(hotel_id, room_id, db)

    # Update the room's main attributes
    room = await db.scalar(
        update(RoomsOrm)
        .where(RoomsOrm.hotel_id == hotel_id, RoomsOrm.id == room_id)
        .values(hotel_id=hotel_id, **room_in.model_dump(exclude={"facilities_ids"}))
        .returning(RoomsOrm)
    )

    # Remove existing facilities associations for this room
    await db.execute(delete(rooms_facilities).where(rooms_facilities.c.room_id == room_id))

    # Insert the new facilities associations
    insert_values = [
        {"room_id": room.id, "facility_id": facility_id} for facility_id in room_in.facilities_ids
    ]
    if insert_values:
        await db.execute(insert(rooms_facilities), insert_values)

    # Commit the transaction to save the changes
    await db.commit()

    # Prepare the response data, including the updated facilities
    room_data = {
        "id": room.id,
        "hotel_id": room.hotel_id,
        "title": room.title,
        "description": room.description,
        "price": room.price,
        "quantity": room.quantity,
        "facilities_ids": room_in.facilities_ids,
    }
    return RoomOut(**room_data)


@router.patch("/{hotel_id}/rooms/{room_id}", response_model=RoomOut)
async def partially_edit_room(hotel_id: int, room_id: int, db: db, room_in: RoomPatch):
    await get_room(hotel_id, room_id, db)

    # Update the room's main attributes
    room = await db.scalar(
        update(RoomsOrm)
        .where(RoomsOrm.hotel_id == hotel_id, RoomsOrm.id == room_id)
        .values(
            hotel_id=hotel_id,
            **room_in.model_dump(exclude_unset=True, exclude={"facilities_ids"}),
        )
        .returning(RoomsOrm)
        .options(selectinload(RoomsOrm.facilities))
    )

    # Remove existing facilities associations for this room
    room_facility = []
    if room_in.facilities_ids:
        room_facility = room_in.facilities_ids
        await db.execute(delete(rooms_facilities).where(rooms_facilities.c.room_id == room_id))

        # Insert the new facilities associations
        insert_values = [
            {"room_id": room.id, "facility_id": facility_id}
            for facility_id in room_in.facilities_ids
        ]
        if insert_values:
            await db.execute(insert(rooms_facilities), insert_values)
    else:
        room_facility = [facility.id for facility in room.facilities]

    # Commit the transaction to save the changes
    await db.commit()

    # Prepare the response data, including the updated facilities
    room_data = {
        "id": room.id,
        "hotel_id": room.hotel_id,
        "title": room.title,
        "description": room.description,
        "price": room.price,
        "quantity": room.quantity,
        "facilities_ids": room_facility,
    }
    return RoomOut(**room_data)


@router.delete("/{hotel_id}/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(hotel_id: int, room_id: int, db: db):
    # Ensure the room exists
    await get_room(hotel_id, room_id, db)

    # Delete associations in rooms_facilities first
    await db.execute(delete(rooms_facilities).where(rooms_facilities.c.room_id == room_id))

    # Delete the room
    await db.execute(delete(RoomsOrm).where(RoomsOrm.hotel_id == hotel_id, RoomsOrm.id == room_id))

    # Commit the transaction
    await db.commit()
