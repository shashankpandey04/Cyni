import logging
import asyncio

from core.bot import CyniBot
from core.config import Config


# -------- LOGGING -------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


async def main():
    token = Config.get_token()

    if not token:
        raise ValueError("❌ No bot token found in environment variables")

    bot = CyniBot()

    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped manually")
    except Exception:
        logging.exception("Fatal error occurred")