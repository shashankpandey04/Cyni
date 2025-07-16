from cyni import run as run_bot
from dashboard import run_production
import threading

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    dashboard_thread = threading.Thread(target=run_production, daemon=True)
    bot_thread.start()
    dashboard_thread.start()
    try:
        bot_thread.join()
        dashboard_thread.join()
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
