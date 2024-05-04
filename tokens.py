from db import mycon

def get_token():
    try:
        mycur = mycon.cursor()
        mycur.execute('SELECT token FROM token where name = "Cyni Beta"')
        return mycur.fetchone()[0]
    except Exception as e:
        print(f"Error: {e}")
    finally:
        mycur.close()

def cyni_token():
    try:
        mycur = mycon.cursor()
        mycur.execute('Select token FROM token where name = "Cyni"')
        return mycur.fetchone()[0]
    except Exception as e:
        print(f"Error: {e}")
    finally:
        mycur.close()