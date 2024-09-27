import mysql.connector
from mysql.connector import Error
from DataBase.database import Database
import os
import dotenv
import logging

dotenv.load_dotenv()

class MySQLHandler(Database):
    def __init__(self):
        self.db = None

    def connect(self):
        """Connect to the MySQL database."""
        try:
            ENV = os.getenv('ENV', 'DEVELOPMENT')  # Default to DEVELOPMENT
            DB = 'cyni' if ENV == 'PRODUCTION' else 'cyni-dev'
            HOST = os.getenv('HOST')
            USER = os.getenv('USER')
            PASSWORD = os.getenv('PASSWORD')

            self.db = mysql.connector.connect(
                host=HOST,
                user=USER,
                password=PASSWORD,
                database=DB
            )
            logging.info(f"Connected to MySQL database ({DB})")
        except Error as e:
            logging.error(f"Error connecting to MySQL: {e}")
            raise

    def save_settings(self, settings: dict):
        """
        Save the settings to the MySQL database.
        :param settings (dict): The settings to save.
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "INSERT INTO settings (guild_id, customization) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE customization = VALUES(customization)",
                (settings['guild_id'], settings['customization'])
            )
            self.db.commit()
        except Error as e:
            logging.error(f"Error saving settings: {e}")
            raise