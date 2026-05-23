from pydantic import Field

from models.guild.base_module import (
    BaseModule
)


class AntiPingModule(BaseModule):

    affected_roles: list[int] = (
        Field(default_factory=list)
    )

    exempt_roles: list[int] = (
        Field(default_factory=list)
    )