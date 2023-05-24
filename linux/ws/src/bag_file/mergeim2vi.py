#!/usr/bin/python3
import cv2
import os

image_folder = 'bag_file'
video_name = 'video.avi'

images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
images.sort()
frame = cv2.imread(os.path.join(image_folder, images[0]))
height, width, layers = frame.shape

video = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'DIVX'), 10, (width,height))
i= 0
for image in images:
    i = i+1
    print(i)
    img = cv2.imread(os.path.join(image_folder, image))
    video.write(img)
    #add frame to img
    cv2.putText(img, str(i), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    cv2.imshow('image', img)
    cv2.waitKey(1)

cv2.destroyAllWindow