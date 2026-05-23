from pydantic import (
    BaseModel,
    ConfigDict
)


class Customization(BaseModel):

    model_config = ConfigDict(
        extra="allow"
    )

    prefix: str = ":"