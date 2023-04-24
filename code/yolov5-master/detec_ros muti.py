#!/usr/bin/env python3

import cv2
import torch
import numpy as np
import pandas as pd
import time

# import pyrealsense2 as rs2
from cv_bridge import CvBridge                      

import rclpy
import sys
import os

from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import Image
from rclpy.executors import MultiThreadedExecutor

image_global = None
image_changed = False
results = None
results_changed = False

class Interface(Node):
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
        global image_global , image_changed
        image_global = cv2.resize(self.br.imgmsg_to_cv2(msg, "bgr8"), (640, 480))
        image_global = cv2.cvtColor(image_global, cv2.COLOR_BGR2RGB)
        image_changed = True
        print('receive image')

class Process(Node):
    def __init__(self):
        name = 'display'
        super().__init__(name)
        print(name, 'is started')
        self.hz_update = 1
        self.timer = self.create_timer(1.0 / self.hz_update, self.timer_callback)
        self.current_time = self.get_clock().now()

        path = '/home/kim/open_topic/code/yolov5-master/best.pt'
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=path, force_reload=True)

        print('init done')

    

    def timer_callback(self):
        global image_global, image_changed, results , results_changed
        if image_changed:
            print('process image fps: ', 1.0 / (self.get_clock().now().nanoseconds - self.current_time.nanoseconds) * 1e9)
            self.current_time = self.get_clock().now()
            results = self.model(image_global)
            results_changed = True

            frame_result = np.squeeze(results.render())
            frame_result = cv2.cvtColor(frame_result, cv2.COLOR_RGB2BGR)
            cv2.imshow('image', results.render()[0])
            cv2.waitKey(1)
            df = pd.DataFrame(results.pandas().xyxy[0])
            print(df)


def main(args=None):
    rclpy.init(args=args)
    node = Process()
    try:
        node_1 = Process()
        node_2 = Interface()
        executor = MultiThreadedExecutor(num_threads=16)
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
