import cv2
import numpy as np

#한글이 path에 있는 경우 
def imread(filename, flags=cv2.IMREAD_COLOR, dtype=np.uint8): 
    try: 
        n = np.fromfile(filename, dtype) 
        img = cv2.imdecode(n, flags)
        img = cv2.resize(img, dsize=(640, 480), interpolation=cv2.INTER_AREA)
        return img 
    except Exception as e: 
        print(e) 
        return None

img1 = imread('IMAGE_query/오뚜기)맛있는북엇국34G.jpg')
img2 = imread('IMAGE_train/오뚜기)맛있는북엇국34G.jpg')

orb = cv2.ORB_create(nfeatures = 1000)
kp1, des1 = orb.detectAndCompute(img1,None)
kp2, des2 = orb.detectAndCompute(img2, None)

# imgKp1 = cv2.drawKeypoints(img1, kp1, None)
# imgKp2 = cv2.drawKeypoints(img2, kp2, None)

bf = cv2.BFMatcher()
matches = bf.knnMatch(des1, des2, k=2) #have two values to compare

good = []
for m, n in matches:
  if m.distance<0.75*n.distance:
    good.append([m])

print(len(good))
img3 = cv2.drawMatchesKnn(img1, kp1, img2, kp2, good, None, flags = 2)



# cv2.imshow(imgKp1)
# cv2.imshow(imgKp2)
# cv2.imshow(img1)
# cv2.imshow(img2)


# cv2.imshow('img1',img1)
# cv2.imshow('img2',img2)
cv2.imshow('img3',img3)

cv2.waitKey(0)