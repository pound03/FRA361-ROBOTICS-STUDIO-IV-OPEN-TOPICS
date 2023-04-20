#!/usr/bin/env python3

import torch
import cv2
import numpy as np
from models.experimental import attempt_load
# Load image
image = cv2.imread('object/bus.jpg')
 
# Convert image from OpenCV format (BGR) to PyTorch format (RGB)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# resize image
image = cv2.resize(image, (640, 640))

# Convert image to PyTorch tensor
tensor = torch.from_numpy(image).permute(2, 0, 1).float().div(255.0).unsqueeze(0)

# Load model
model = torch.load('object/scripts/yolov7.pt', map_location=torch.device('cpu'))['model'].float().fuse().eval()
# Make predictions using YOLOv5 model
predictions = model(tensor)

# # Print predicted labels and bounding boxes
# print(predictions.pandas().xyxy[0])
