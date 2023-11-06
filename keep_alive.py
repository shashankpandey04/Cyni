from threading import Thread

from flask import Flask

app = Flask('')


@app.route('/')
def home():
  print("Site is Online")
  return "Hello, Bot is Online"


def run():
  app.run(host="0.0.0.0", port=7070)


def keep_alive():
  server = Thread(target=run)
  server.start()
