from pydantic import BaseModel, EmailStr

class UserIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr