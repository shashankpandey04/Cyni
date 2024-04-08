import mysql.connector as mysql

try:
    mycon = mysql.connect(
        host='cynibot_cyni',
        user='mysql',
        passwd='995ef7a66cb1feb880bd',
        database='cyni'
    )
    mycur = mycon.cursor()

except mysql.Error as e:
    print(f"Connection error to 'cynibot_cyni': {e}")
    try:
        print("Attempting fallback connection to 'localhost'...")
        mycon = mysql.connect(
            host='localhost',
            user='root',
            passwd='root',
            database='cyni'
        )
        mycur = mycon.cursor()
        print("Connected to 'localhost' successfully.")
    except mysql.Error as e:
        print(f"Connection error to 'localhost' as well: {e}")
        exit()