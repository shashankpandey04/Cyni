from cyni import bot
from tokens import get_token
if __name__ == "__main__":
    TOKEN = get_token()
    bot.run(TOKEN)
