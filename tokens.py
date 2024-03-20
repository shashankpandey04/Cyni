from db import *

def get_token():
    mycur.execute('SELECT token FROM token where name = "Cyni Beta"')
    return mycur.fetchone()[0]