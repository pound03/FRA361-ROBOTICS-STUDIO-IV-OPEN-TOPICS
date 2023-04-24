#!/usr/bin/env python3

import cv2
# import torch
# import numpy as np
# import pandas as pd
# import time

# import pyrealsense2 as rs2
from cv_bridge import CvBridge                      

import rclpy
import sys

from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import Image

class DummyNode(Node):
    def __init__(self):
        name = 'simple_detection_node'
        super().__init__(name)
        print(name, 'is started')

        # profile = rclpy.qos.qos_profile_sensor_data
        # profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)
        profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_RELIABLE,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)

        self.subscription = self.create_subscription(Image, '/color/image_raw', self.listener_callback, 2)

        self.br = CvBridge()
        self.current_time = self.get_clock().now()

        self.image = None

    def listener_callback(self, data):
        #check time for fps
        print('receive image fps: ', 1.0 / (self.get_clock().now().nanoseconds - self.current_time.nanoseconds) * 1e9)
        self.current_time = self.get_clock().now()
        
        #convert ros image to cv2 image
        cv_image = self.br.imgmsg_to_cv2(data, "bgr8")
        cv2.imshow('image', cv_image)
        cv2.waitKey(1)



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
