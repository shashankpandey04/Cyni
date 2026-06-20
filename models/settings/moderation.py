from pydantic import BaseModel


class ModerationSettings(BaseModel):
    enabled: bool = False
    audit_log: int | None = None
