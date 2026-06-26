from pydantic import BaseModel


class Location(BaseModel):
    LocationX: float
    LocationZ: float
    PostalCode: str
    StreetName: str
    BuildingNumber: str
