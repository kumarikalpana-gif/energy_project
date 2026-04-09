from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# User Table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)

    appliances = relationship("Appliance", back_populates="owner")


# Appliance Table
class Appliance(Base):
    __tablename__ = "appliances"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    power = Column(Float)        # watts
    hours_per_day = Column(Float)
    daily_energy = Column(Float)

    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="appliances")