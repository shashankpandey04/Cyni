from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import discord


# =========================
# Constants
# =========================

DEFAULT_CATEGORY = "general"

CATEGORY_COLORS: dict[str, discord.Color] = {
    "logging": discord.Color.yellow(),
    "moderation": discord.Color.red(),
    "info": discord.Color.blurple(),
    "success": discord.Color.green(),
    "error": discord.Color.dark_red(),
    "general": discord.Color.dark_gray(),
    "automod": discord.Color.teal(),
    "customization": discord.Color.purple(),
}


# =========================
# Utils
# =========================

def safe_parse_color(color_value: str | int | None) -> discord.Color:
    """
    Safely parse a hex/int color into discord.Color.
    Falls back to dark gray if invalid.
    """

    if color_value is None:
        return discord.Color.dark_gray()

    try:
        if isinstance(color_value, int):
            return discord.Color(color_value)

        color_value = color_value.strip().replace("#", "")

        if len(color_value) != 6:
            raise ValueError("Invalid hex length")

        return discord.Color(int(color_value, 16))

    except Exception:
        return discord.Color.dark_gray()


def get_embed_color(
    category: str,
    premium: bool = False,
    custom_colors: dict[str, str] | None = None,
) -> discord.Color:
    """
    Resolve embed color safely.
    """

    category = (category or DEFAULT_CATEGORY).lower()

    if premium and custom_colors:
        custom_hex = custom_colors.get(category)

        if custom_hex:
            return safe_parse_color(custom_hex)

    return CATEGORY_COLORS.get(category, discord.Color.dark_gray())


# =========================
# Main Embed Generator
# =========================

def generate_embed(
    guild: discord.Guild | None,
    title: str,
    *,
    category: str = DEFAULT_CATEGORY,
    description: str | None = None,
    fields: list[dict[str, Any]] | None = None,
    footer: str | None = None,
    timestamp: bool = False,
    premium: bool = False,
    custom_colors: dict[str, str] | None = None,
    thumbnail: str | None = None,
    image: str | None = None,
    author_name: str | None = None,
    author_icon: str | None = None,
    url: str | None = None,
) -> discord.Embed:
    """
    Universal embed helper for Cyni.
    """

    embed = discord.Embed(
        title=title[:256],
        description=(description or "")[:4096],
        color=get_embed_color(
            category=category,
            premium=premium,
            custom_colors=custom_colors,
        ),
        url=url,
    )

    # -------------------------
    # Fields
    # -------------------------

    if fields:
        for field in fields[:25]:
            embed.add_field(
                name=str(field.get("name", "—"))[:256],
                value=str(field.get("value", "—"))[:1024],
                inline=bool(field.get("inline", False)),
            )

    # -------------------------
    # Footer
    # -------------------------

    guild_icon = guild.icon.url if guild and guild.icon else None

    footer_text = footer or ""

    if not premium:
        footer_text = f"{footer_text} • By Cyni".strip(" •")

    embed.set_footer(
        text=footer_text[:2048],
        icon_url=guild_icon,
    )

    # -------------------------
    # Timestamp
    # -------------------------

    if timestamp:
        embed.timestamp = datetime.now(timezone.utc)

    # -------------------------
    # Media
    # -------------------------

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    if image:
        embed.set_image(url=image)

    # -------------------------
    # Author
    # -------------------------

    if author_name:
        embed.set_author(
            name=author_name[:256],
            icon_url=author_icon,
        )

    return embed