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

class DummyNode(Node):
    def __init__(self):
        name = 'display'
        super().__init__(name)
        print(name, 'is started')

        # profile = rclpy.qos.qos_profile_sensor_data
        # profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)
        profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_RELIABLE,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)

        self.subscription = self.create_subscription(Image, '/camera/color/image_raw', self.listener_callback, 2)
        self.hz_update = 20
        self.timer = self.create_timer(1.0 / self.hz_update, self.timer_callback)

        self.br = CvBridge()
        self.current_time = self.get_clock().now()

        self.image = np.zeros((720, 1280, 3), np.uint8)
        self.image_changed = False
        # print(os.getcwd())
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5n')

        print('init done')

    def timer_callback(self):
        if self.image_changed:
            print('receive image fps: ', 1.0 / (self.get_clock().now().nanoseconds - self.current_time.nanoseconds) * 1e9)
            self.current_time = self.get_clock().now()
            self.image = cv2.resize(self.image, (640, 480))
            results = self.model(self.image)
            print(results.xyxy[0])
            # for *xyxy, conf, cls in results.xyxy[0]:
            #     x1, y1, x2, y2 = map(int, xyxy)
            #     label = self.model.names[int(cls)]
            #     cv2.rectangle(self.image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            #     cv2.putText(self.image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            # cv2.imshow('image', self.image)
            cv2.waitKey(1)
            self.image_changed = False


    def listener_callback(self, data):
        #check time for fps

        #convert ros image to cv2 image
        self.image = self.br.imgmsg_to_cv2(data, "bgr8")
        self.image_changed = True
        #print size array


def main(args=None):
    rclpy.init(args=args)
    node = DummyNode()
    try:
        while rclpy.ok():
            rclpy.spin_once(node)
    except KeyboardInterrupt:
        print('repeater stopped cleanly')
    except BaseException:
        print('exception in repeater:', file=sys.stderr)
        raise
    finally:
        node.destroy_node()
        rclpy.shutdown() 

if __name__=='__main__':
    main()
