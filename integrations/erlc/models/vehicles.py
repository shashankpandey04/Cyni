from pydantic import BaseModel


class Vehicle(BaseModel):
    Name: str
    Owner: str
    Plate: str
    Texture: str
    ColorHex: str
    ColorName: str
