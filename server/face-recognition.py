import cv2
import numpy as np
import os
import sqlite3
from PIL import Image

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
recognizer = cv2.face.LBPHFaceRecognizer_create()

recognizer.read("E://DoAn4//ftp-python//server//recoginzer//trainingData.yml")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "fpt_implement.sqlite")

fontface = cv2.FONT_HERSHEY_SIMPLEX

# get profile by id
def getProfile(id):
    conn = sqlite3.connect(db_path)
    
    query = "SELECT * FROM users WHERE id= '"+str(id)+"'"
    cursor = conn.execute(query)
    
    profile = None
    
    for row in cursor:
        profile = row
        
    conn.close()
    # print(profile)
    return profile

def openCV():
    cap = cv2.VideoCapture(0)
    while(True): 
        ret, frame = cap.read()
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = face_cascade.detectMultiScale(gray)
        
        isCheck = False
        
        for(x,y,w,h) in faces:
            cv2.rectangle(frame, (x,y),(x+w,y+h),(0,255,0),2)
            
            roi_gray = gray[y:y+h, x:x+w]
            
            id,confidence = recognizer.predict(roi_gray)
            
            if confidence < 40:
                profile = getProfile(id)
                if(profile != None):
                    cv2.putText(frame, ""+str(profile[1]),(x+10,y+h+30),fontface,1,(0,255,0),2)
                    # if(profile[1] == "ndphuc"): 
                    #     isCheck = True
                    #     break
                else:
                    cv2.putText(frame, "Unknown",(x+10,y+h+30),fontface,1,(0,255,0),2)
                    
        cv2.imshow('FACE-RECOGNITION',frame)
        if(cv2.waitKey(1) == ord('q')):
            break
        
    cap.release()
    cv2.destroyAllWindows()
    
openCV()
        