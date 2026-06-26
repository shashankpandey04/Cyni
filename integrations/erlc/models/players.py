from pydantic import BaseModel


class Location(BaseModel):
    LocationX: float
    LocationZ: float
    PostalCode: str
    StreetName: str
    BuildingNumber: str


class Player(BaseModel):
    Team: str
    Player: str
    Callsign: str
    Location: Location
    Permission: str
    WantedStars: int
