#!/usr/bin/env python3

import torch
from models.experimental import attempt_load
from utils import torch_utils
import cv2
import numpy as np
import time
from utils.general import non_max_suppression
import pandas as pd

cam = cv2.VideoCapture(0)

# Load model
path = 'best.pt'
model = torch.hub.load('ultralytics/yolov5', 'custom', path=path, force_reload=True)  # load FP32 model
time_now = time.time()
while True:
    ret, frame = cam.read()
    if not ret:
        print("failed to grab frame")
        break
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    time_process = time.time()
    results = model(frame)
    # print("process time: ", time.time() - time_process)
    #add fps on frame
    frame_result = np.squeeze(results.render())
    frame_result = cv2.cvtColor(frame_result, cv2.COLOR_RGB2BGR)
    fps = 1.0 / (time.time() - time_now)
    cv2.putText(frame_result, "FPS: {:.2f}".format(fps), (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    cv2.imshow("test", frame_result)
    time_now = time.time()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

