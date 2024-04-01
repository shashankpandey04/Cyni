import mysql.connector as mysql
try:
    mycon = mysql.connect(
        host='cynibot_cyni',
        user='mysql',
        passwd='995ef7a66cb1feb880bd',
        database='cyni'
    )
    mycur = mycon.cursor()
except mysql.Error as err:
    print("Error connecting to database:", err)
finally:
    if mycon:
        mycon.close()
