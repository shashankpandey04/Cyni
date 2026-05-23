from pydantic import BaseModel, ConfigDict


class BaseModule(BaseModel):

    model_config = ConfigDict(
        extra="allow"
    )

    enabled: bool = False