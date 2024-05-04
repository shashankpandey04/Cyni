import mysql.connector as mysql

try:
    mycon = mysql.connect(
        host='cynibot_cyni',
        user='mysql',
        passwd='56ba27b994b10fe620e1',
        database='cynibot'
    )

except mysql.Error as e:
    print(f"Connection error to 'Machine Host': {e}")
    try:
        print("Attempting fallback connection to 'Remote Host'...")
        mycon = mysql.connect(
                host='localhost',
                user='root',
                passwd='root',
                database='cyni'
            )
        print("Connected to 'localhost' successfully.")
    except mysql.Error as e:
        print(f"Connection error to 'Remote Host' as well: {e}")
        try:
            mycon = mysql.connect(
            host='vps.imlimiteds.com',
            port = 9069,
            user='mysql',
            passwd='56ba27b994b10fe620e1',
            database='cynibot'
            )
            print("Connected to 'Remote Host' successfully.")
        except mysql.Error as e:
            print(f"Connection error to 'localhost' as well: {e}")
            exit()