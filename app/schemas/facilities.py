from pydantic import BaseModel

class FacilityIn(BaseModel):
    title: str

class FacilityOut(FacilityIn):
    id: int