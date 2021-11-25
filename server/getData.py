import cv2
import numpy as np
import sqlite3
import os
import os.path

def insertOrGetUser(username):
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "fpt_implement.sqlite")

    conn = sqlite3.connect(db_path)
    
    query = "SELECT * FROM users WHERE username= '"+str(username)+"'"
    # print(query)
    cursor = conn.execute(query)
    # print(cursor.fetchone())
    
    isRecordExist = 0
    
    for row in cursor:
        isRecordExist = 1
        
    if(isRecordExist == 0):
        query = "INSERT INTO users(username,password) VALUES('"+str(username)+"','123123')"
        conn.execute(query)
        conn.commit()
    query = "SELECT * FROM users WHERE username= '"+str(username)+"'"
    cursor = conn.execute(query)
    # print(cursor.fetchone()[0])
    return cursor.fetchone()


face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

cap = cv2.VideoCapture(0)

# insert to db
username = input("Enter your username: ")
user = insertOrGetUser(username)
# print(id[0])

sampleNum = 0

while(True): 
    ret, frame = cap.read()
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    faces = face_cascade.detectMultiScale(gray,1.3,5)
    
    for(x,y,w,h) in faces:
        cv2.rectangle(frame, (x,y),(x+w,y+h),(0,255,0),2)
        
        if not os.path.exists('dataSet'):
            os.makedirs('dataSet')
        
        sampleNum+=1
        
        cv2.imwrite('dataSet/User.'+str(user[0])+'.'+str(sampleNum)+'.jpg',gray[y: y+h,x: x+w])

    cv2.imshow('DETECTING FACE',frame)
    cv2.waitKey(1)
    if(sampleNum > 100):
        break
    
cap.release()
cv2.destroyAllWindows()