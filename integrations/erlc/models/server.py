from pydantic import BaseModel, ConfigDict, Field

from .logs import (
    CommandLog,
    EmergencyCall,
    JoinLog,
    KillLog,
    ModCall,
)
from .players import Player
from .vehicles import Vehicle


class Staff(BaseModel):
    Admins: dict[str, str] = Field(default_factory=dict)
    Mods: dict[str, str] = Field(default_factory=dict)
    Helpers: dict[str, str] = Field(default_factory=dict)


class Server(BaseModel):
    model_config = ConfigDict(extra="ignore")

    Name: str
    OwnerId: int

    CoOwnerIds: list[int] = Field(default_factory=list)

    CurrentPlayers: int
    MaxPlayers: int

    JoinKey: str
    AccVerifiedReq: str
    TeamBalance: bool

    Players: list[Player] = Field(default_factory=list)

    Staff: Staff

    JoinLogs: list[JoinLog] = Field(default_factory=list)
    Queue: list[int] = Field(default_factory=list)
    KillLogs: list[KillLog] = Field(default_factory=list)
    CommandLogs: list[CommandLog] = Field(default_factory=list)
    ModCalls: list[ModCall] = Field(default_factory=list)
    EmergencyCalls: list[EmergencyCall] = Field(default_factory=list)

    Vehicles: list[Vehicle] = Field(default_factory=list)
