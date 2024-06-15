import mysql.connector as mysql
from dotenv import load_dotenv
import os

load_dotenv()
try:
    mycon = mysql.connect(
        host=os.getenv('LOCAL_HOST'),
        user=os.getenv('LOCAL_USER'),
        passwd=os.getenv('LOCAL_PASSWD'),
        database=os.getenv('LOCAL_DB')
    )
    print("Connected to database on localhost.")
except Exception as e:
    print(f"Error connecting to database: {e}")
    try:
        mycon = mysql.connect(
            host=os.getenv('HOST'),
            user=os.getenv('USER'),
            passwd=os.getenv('PASSWD'),
            database=os.getenv('DB')
        )
        print("Connected to database.")
    except Exception as e:
        print(f"Error connecting to database: {e}")