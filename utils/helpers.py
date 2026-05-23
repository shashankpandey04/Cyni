from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal


DiscordTimestampStyle = Literal[
    "t",  # Short Time
    "T",  # Long Time
    "d",  # Short Date
    "D",  # Long Date
    "f",  # Short Date/Time
    "F",  # Long Date/Time
    "R",  # Relative Time
]


def discord_time(
    dt: datetime | int | float,
    style: DiscordTimestampStyle = "R",
) -> str:
    """
    Convert a datetime or unix timestamp into a Discord timestamp.

    Examples:
        discord_time(datetime.utcnow())
        discord_time(time.time(), "F")

    Output:
        <t:1716469200:R>
    """

    # Handle unix timestamps directly
    if isinstance(dt, (int, float)):
        unix = int(dt)

    # Handle datetime objects
    elif isinstance(dt, datetime):
        # Ensure timezone-aware datetime
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        unix = int(dt.timestamp())

    else:
        raise TypeError(
            f"Expected datetime | int | float, got {type(dt).__name__}"
        )

    return f"<t:{unix}:{style}>"