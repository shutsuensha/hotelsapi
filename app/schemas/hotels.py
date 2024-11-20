from pydantic import BaseModel


class HotelIn(BaseModel):
    title: str
    location: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Отель Сочи 5 звезд у моря",
                    "location": "ул. Моря, 1",
                }
            ]
        }
    }


class HotelOut(HotelIn):
    id: int


class HotelPatch(BaseModel):
    title: str | None = None
    location: str | None = None


    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Отель Сочи 5 звезд у моря",
                    "location": "ул. Моря, 1",
                }
            ]
        }
    }