import cv2
import numpy as np
import sqlite3
import os
import os.path

def getUser(username):
    
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # print(BASE_DIR)
    db_path = os.path.join(os.path.dirname(BASE_DIR), "fpt_implement.sqlite")

    conn = sqlite3.connect(db_path)
    
    query = "SELECT * FROM users WHERE username= '"+str(username)+"'"
    # print(query)
    cursor = conn.execute(query)
    # print('zczxczx')
    # print(cursor.fetchone()[0])
    return cursor.fetchone()
    
    
def getFace(username):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    #  id = cursor.fetchone()[0]
    sampleNum = 0
    cap = cv2.VideoCapture(0)
    user = getUser(username)
    while(True): 
        ret, frame = cap.read()
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = face_cascade.detectMultiScale(gray,1.3,5)
        
        for(x,y,w,h) in faces:
            cv2.rectangle(frame, (x,y),(x+w,y+h),(0,255,0),2)
            
            if not os.path.exists('dataSet'):
                os.makedirs('dataSet')
            
            sampleNum+=1
            
            # cv2.imwrite('dataSet/User.'+str(user[0])+'.'+str(sampleNum)+'.jpg',gray[y: y+h,x: x+w])
            cv2.imwrite('dataSet/User.'+str(user[0])+'.'+str(sampleNum)+'.jpg',gray[y: y+h,x: x+w])

        cv2.imshow('DETECTING FACE',frame)
        cv2.waitKey(1)
        if(sampleNum > 100):
            break
        
    cap.release()
    cv2.destroyWindow('DETECTING FACE')
    return True





# insert to db
# username = input("Enter your username: ")
# user = insertOrGetUser(username)
# print(id[0])


    
