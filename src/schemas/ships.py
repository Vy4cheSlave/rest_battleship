from sqlmodel import SQLModel, Field, Column, JSON
from enum import Enum
import json

class ShipType(str, Enum):
    SPEEDBOAT = "speedboat"
    DESTROYER = "destroyer"
    BATTLESHIP = "battleship"
    CRUISER = "cruiser"

class ShipPublic(SQLModel):
    name: str
    location: list[str] = Field(sa_column=Column(JSON))

    def remove_location(self, location: str):
        self.location.remove(location)

class GameBoardBase(SQLModel):
    pass

class GameBoardPublic(GameBoardBase):
    ships: list[ShipPublic]