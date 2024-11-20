from pydantic import BaseModel
from datetime import date

class BookingIn(BaseModel):
    room_id: int
    date_from: date
    date_to: date

class BookingOut(BookingIn):
    id: int
    user_id: int
    price: int