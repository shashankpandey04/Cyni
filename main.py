import logging

from core.bot import CyniBot
from core.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
)


def main():
    bot = CyniBot()
    bot.run(Config.get_token())


if __name__ == "__main__":
    main()
