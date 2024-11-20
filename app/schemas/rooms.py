from pydantic import BaseModel, ConfigDict

class RoomIn(BaseModel):
    title: str
    description: str | None = None
    price: int
    quantity: int
    facilities_ids: list[int] = []

class RoomOut(RoomIn):
    id: int
    hotel_id: int

class RoomPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    price: int | None = None
    quantity: int | None = None
    facilities_ids: list[int] | None = None