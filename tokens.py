import mysql.connector as msc
mycon=msc.connect(host='localhost',user='root',passwd='root',database='cyni')
mycur=mycon.cursor()

def get_token():
    mycur.execute('SELECT token FROM token where name = "Cyni Beta"')
    return mycur.fetchone()[0]