import mysql.connector as mysql
from dotenv import load_dotenv
import os

load_dotenv()

mycon = mysql.connect(
    host=os.getenv('REMOTE_HOST'),
    user=os.getenv('REMOTE_USER'),
    passwd=os.getenv('REMOTE_PASSWD'),
    database=os.getenv('REMOTE_DB')
)
