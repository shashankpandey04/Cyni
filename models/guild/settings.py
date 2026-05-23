from pydantic import (
    BaseModel,
    Field,
    ConfigDict
)

from models.guild.customization import (
    Customization
)

from models.guild.moderation import (
    ModerationModule
)

from models.guild.anti_ping import (
    AntiPingModule
)


class GuildSettings(BaseModel):

    model_config = ConfigDict(
        extra="allow"
    )

    schema_version: int = 1

    customization: Customization = (
        Field(default_factory=Customization)
    )

    moderation_module: ModerationModule = (
        Field(default_factory=ModerationModule)
    )

    anti_ping_module: AntiPingModule = (
        Field(default_factory=AntiPingModule)
    )