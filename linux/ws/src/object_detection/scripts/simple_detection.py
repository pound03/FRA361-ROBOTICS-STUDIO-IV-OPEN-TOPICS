#!/usr/bin/env python3

import cv2
from cv_bridge import CvBridge                      
import torch
import numpy as np
import pandas as pd
import pyrealsense2 as rs2

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

class Simple_detection(Node):
    def __init__(self):
        super().__init__('simple_detection_node')
        print('simple_detection_node activate')

        self.subscription = self.create_subscription(
        Image, 
        '/camera/color/image_raw', 
        self.listener_callback, 
        10)
        self.subscription # prevent unused variable warning

            # Load model from path (path reference from where we run command. In this case we run node at workspace).
        self.model = torch.load('src/Software-Team/object_detection/src/model/yolov5_small_local.pt')
        self.model = self.model.eval()
            # Used to convert between ROS and OpenCV images
        self.br = CvBridge()

        self.current_frame = np.zeros((480,640,3))

    def listener_callback(self, data):
            # Convert ROS Image message to OpenCV image
        self.current_frame = self.br.imgmsg_to_cv2(data)

        results = self.model(self.current_frame)            # result from model yolov5.
        cv2.imshow('yolo',np.squeeze(results.render()))     # Display image.
        cv2.waitKey(1)                                      # keep frame display.

        print(results.pandas().xyxy[0])
        print()

def main(args=None):
    rclpy.init(args=args)
    simple_detection = Simple_detection()
    rclpy.spin(simple_detection)
    simple_detection.destroy_node()
    simple_detection.shutdown()
    rclpy.shutdown()

if __name__=='__main__':
    # main()