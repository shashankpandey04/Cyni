import mysql.connector as mysql
mycon = mysql.connect(
        host='cynibot_cyni',
        user='mysql',
        passwd='995ef7a66cb1feb880bd',
        database='cyni'
)
mycur = mycon.cursor()
