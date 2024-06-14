import mysql.connector as mysql
from dotenv import load_dotenv
import os

load_dotenv()

try:
    mycon = mysql.connect(
        host=os.getenv('MACHINE_HOST'),
        user=os.getenv('MACHINE_USER'),
        passwd=os.getenv('MACHINE_PASSWD'),
        database=os.getenv('MACHINE_DB')
    )
    #print("Connected to 'Machine Host' successfully.")
except mysql.Error as e:
    #print(f"Connection error to 'Machine Host': {e}")
    try:
        #print("Attempting fallback connection to 'Remote Host'...")
        mycon = mysql.connect(
            host=os.getenv('REMOTE_HOST'),
            user=os.getenv('REMOTE_USER'),
            passwd=os.getenv('REMOTE_PASSWD'),
            database=os.getenv('REMOTE_DB')
        )
        #print("Connected to 'Remote Host' successfully.")
    except mysql.Error as e:
        print(f"Connection error to 'Remote Host' as well: {e}")
