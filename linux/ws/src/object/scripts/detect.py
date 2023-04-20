#!/usr/bin/env python3

import cv2
import torch
import numpy as np
# import pandas as pd
# import time

# import pyrealsense2 as rs2
from cv_bridge import CvBridge                      

import rclpy
import sys
import os

from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import Image
from rclpy.executors import MultiThreadedExecutor

image = np.zeros((720, 1280, 3), np.uint8)
image_changed = False

class Subscriber(Node):
    def __init__(self):
        super().__init__('subscriber')
        print('subscriber is started')

        # profile = rclpy.qos.qos_profile_sensor_data
        # profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)
        profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_RELIABLE,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)

        self.subscription = self.create_subscription(
            Image,
            '/camera/color/image_raw',
            self.listener_callback,
            profile)
        self.br = CvBridge()

    def listener_callback(self, msg):
        global image , image_changed
        image = self.br.imgmsg_to_cv2(msg, "bgr8")
        image_changed = True
        

class DummyNode(Node):
    def __init__(self):
        name = 'display'
        super().__init__(name)
        print(name, 'is started')
        self.hz_update = 20
        self.timer = self.create_timer(1.0 / self.hz_update, self.timer_callback)
        self.current_time = self.get_clock().now()
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5n')
        print('init done')

    def timer_callback(self):
        global image, image_changed
        if image_changed:
            print('receive image fps: ', 1.0 / (self.get_clock().now().nanoseconds - self.current_time.nanoseconds) * 1e9)
            self.current_time = self.get_clock().now()
            self.image = cv2.resize(image, (640, 480))
            results = self.model(self.image)
            print(results.xyxy[0])
            # for *xyxy, conf, cls in results.xyxy[0]:
            #     x1, y1, x2, y2 = map(int, xyxy)
            #     label = self.model.names[int(cls)]
            #     cv2.rectangle(self.image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            #     cv2.putText(self.image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.imshow('image', self.image)
            cv2.waitKey(1)
            image_changed = False

def main(args=None):
    rclpy.init(args=args)
    node = DummyNode()
    try:
        node_1 = DummyNode()
        node_2 = Subscriber()
        executor = MultiThreadedExecutor(num_threads=4)
        executor.add_node(node_1)
        executor.add_node(node_2)
        try:
            executor.spin()
        finally:
            executor.shutdown()
            node_1.destroy_node()
            node_2.destroy_node()
    finally:
        rclpy.shutdown()

if __name__=='__main__':
    main()
