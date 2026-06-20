from pydantic import BaseModel, Field


class AntiPingSettings(BaseModel):
    enabled: bool = False
    affected_roles: list[int] = Field(default_factory=list)
