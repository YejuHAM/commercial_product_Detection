import numpy as np
import pandas as pd
import cv2 
from skimage import io
from PIL import Image 
import matplotlib.pylab as plt
import os
from PIL import ImageFont, ImageDraw, Image

videofile = 'testvideo.mp4'
path = 'C:/Users/Administrator/Downloads/Object_Detection_Files/IMAGE_query'
orb = cv2.ORB_create(nfeatures = 1000)

###import Images
images = []
classNames = []
myList = os.listdir(path)
print('total classes detected', len(myList))

def imread(filename, flags=cv2.IMREAD_COLOR, dtype=np.uint8): 
    try: 
        n = np.fromfile(filename, dtype) 
        img = cv2.imdecode(n, flags)
        img = cv2.resize(img, dsize=(640, 640), interpolation=cv2.INTER_AREA)
        return img 
    except Exception as e: 
        print(e) 
        return None

for cl in myList:
  imgCur = imread(f'{path}/{cl}')
  images.append(imgCur)
  classNames.append(os.path.splitext(cl)[0]) #split을 하지 않으면 jpg까지 같이 나온다.
print(classNames)


def findDes(images):
  desList =[]
  for img in images:
    kp, des = orb.detectAndCompute(img, None)
    desList.append(des)
  return desList

def findID(img,desList, thres =15):
    kp2,des2 = orb.detectAndCompute(img,None)
    bf = cv2.BFMatcher()
    matchList = []
    finalVal = -1
    try:
        for des in desList:
            matches = bf.knnMatch(des, des2, k=2) #have two values to compare
            good = []
            for m,n in matches:
                if m.distance< 0.75*n.distance:
                    good.append([m])
            matchList.append(len(good))
    except:
        pass
    # print(matchList)
    if len(matchList) !=0:
        if max(matchList)> thres:
            finalVal = matchList.index(max(matchList))
    return finalVal


desList = findDes(images)
print(len(desList))

cap = cv2.VideoCapture(videofile)

while(cap.isOpened()):

  success,img2 = cap.read()
  imgOriginal = img2.copy()
  img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
  
  id = findID(img2,desList)

  if id != -1:
      cv2.putText(imgOriginal, classNames[id], (50,50), cv2.FONT_HERSHEY_COMPLEX,0.7, (0,0,255),1 )
    # im_p = Image.fromarray(imgOriginal)
    # b,g,r,a = 255,255,255,0
    # fontpath = "fonts/gulim.ttc"
    # font = ImageFont.truetype(fontpath, 20)
    # draw = ImageDraw.Draw(im_p)
    # draw.text((50, 80), classNames[id], font = font, fill = (b, g, r, a))
  cv2.imshow('img2',imgOriginal)
  cv2.waitKey(1)
  

