from models.guild.base_module import (
    BaseModule
)


class ModerationModule(BaseModule):

    mod_log_channel: int | None = None
    ban_appeal_channel: int | None = None
    audit_log: int | None = None