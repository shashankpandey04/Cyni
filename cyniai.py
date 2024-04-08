from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import mysql.connector as mysql
racial_slurs = ["nigger", "nigga"]
mycon = mysql.connect(host='localhost',user='root',passwd='root',database='cyni')
mycur = mycon.cursor()

def punishai(reason,punish):
    reason = reason.lower()
    punish = punish.lower()
    mycur.execute("SELECT reason, punishment FROM training_data")
    data = mycur.fetchall()
    reasons, punishments = zip(*data)
    reasons = list(reasons)
    punishments = list(punishments)
    try:
        if reason in reasons:
            idx = reasons.index(reason)
            existing_punishment = punishments[idx]
            #print(existing_punishment)
            if existing_punishment != punish:
                #print(f"Cyni AI predicts {existing_punishment}.")
                return existing_punishment
        else:
            mycur.execute("INSERT INTO training_data (reason, punishment) VALUES (%s, %s)", (reason, punish))
            #print(f"Punishment for {reason} logged as {punish}")
            mycon.commit()
            return punish
    except Exception as error:
        print(f"Error: {error}")

def prediction():
    print("Welcome to Cyni AI Beta")
    reason = input("Reason: ")
    punish = input("Punishment: ")
    predit = punishai(reason,punish)
    if predit == punish:
        print("Warning Logged.")
    else:
        print(f"Cyni AI predicts {predit}")
    print(" ")

while True:
    prediction()