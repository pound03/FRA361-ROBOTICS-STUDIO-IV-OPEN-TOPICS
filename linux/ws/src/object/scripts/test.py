#!/usr/bin/env python3

import torch
import cv2
import numpy as np
from models.experimental import attempt_load

model = torch.load('object/scripts/yolov5_small_local.pt', map_location=torch.device('cpu'))['model'].float().fuse().eval()
# model = attempt_load('object/scripts/yolov5_small_local.pt', map_location=torch.device('cpu'))  # load FP32 model
# model = attempt_load('object/scripts/yolov7.pt', map_location=torch.device('cpu'))  # load FP32 model

img = cv2.imread('object/scripts/bus.jpg')

img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

img = cv2.resize(img, (640, 640))

img = torch.from_numpy(img).permute(2, 0, 1).float().div(255.0).unsqueeze(0)

