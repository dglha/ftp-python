from PyQt5.QtWidgets import QDialog
import cv2
import numpy as np
import os
from PIL import Image

recognizer = cv2.face.LBPHFaceRecognizer_create()


def training(path):
    
    imagePaths = [os.path.join(path,f) for f in os.listdir(path)]
    # print(imagePaths)
    
    faces = []
    usernames = []
    
    for imagePath in imagePaths:
        faceImg = Image.open(imagePath).convert('L')
        faceNp = np.array(faceImg,'uint8')
        
        # imagePath = dataSet\\User.username.sampleName.jpg
        # imagePath.split('\\') => [0] = dataSet [1] = User.username.sampleName.jpg
        # [1].split('.')[1] = username
        username = int(imagePath.split('\\')[1].split('.')[1])
         
        faces.append(faceNp)
        usernames.append(username)
        
        cv2.imshow('TRAINING',faceNp)
        cv2.waitKey(10)
        
    # return faces,usernames
    recognizer.train(faces, np.array(usernames))
    
    if not os.path.exists("recoginzer"):
        os.makedirs("recoginzer")

    recognizer.save('recoginzer/trainingData.yml')
    cv2.destroyWindow('TRAINING')
    return True
    
# faces,usernames = getImageWithUsername(path)

# recognizer.train(faces, np.array(usernames))



# cv2.destroyAllWindows()