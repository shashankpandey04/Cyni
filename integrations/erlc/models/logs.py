from pydantic import BaseModel


class JoinLog(BaseModel):
    Join: bool
    Timestamp: int
    Player: str


class KillLog(BaseModel):
    Killed: str
    Timestamp: int
    Killer: str


class CommandLog(BaseModel):
    Player: str
    Timestamp: int
    Command: str


class ModCall(BaseModel):
    Caller: str
    Moderator: str
    Timestamp: int


class EmergencyCall(BaseModel):
    Team: str
    Caller: int
    Players: list[int]
    Position: list[float]
    StartedAt: int
    CallNumber: int
    Description: str
    PositionDescriptor: str
