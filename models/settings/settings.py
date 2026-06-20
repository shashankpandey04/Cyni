from pydantic import BaseModel, Field

from .anti_ping import AntiPingSettings
from .moderation import ModerationSettings


class GuildSettings(BaseModel):
    guild_id: int = Field(alias="_id")

    prefix: str = "!"

    anti_ping: AntiPingSettings = Field(
        alias="anti_ping_module", default_factory=AntiPingSettings
    )

    moderation: ModerationSettings = Field(
        alias="moderation_module", default_factory=ModerationSettings
    )

    model_config = {"populate_by_name": True}
