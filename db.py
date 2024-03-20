import mysql.connector as msc
mycon=msc.connect(host='localhost',user='root',passwd='root',database='cyni')
mycur=mycon.cursor()