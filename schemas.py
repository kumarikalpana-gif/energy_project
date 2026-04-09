from pydantic import BaseModel

# USER CREATE 
class UserCreate(BaseModel):
    username: str
    password: str


# USER RESPONSE 
class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


# APPLIANCE 
class ApplianceCreate(BaseModel):
    name: str
    power: float
    hours_per_day: float


class ApplianceResponse(BaseModel):
    id: int
    name: str
    power: float
    hours_per_day: float
    daily_energy: float

    class Config:
        from_attributes = True   