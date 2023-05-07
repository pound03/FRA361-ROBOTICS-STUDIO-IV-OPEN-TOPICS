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
from std_msgs.msg import String
#geometry_msgs/PoseArray Message
from geometry_msgs.msg import PoseArray
from geometry_msgs.msg import Pose

image_global = None
image_changed = False
results = None
results_changed = False

class Process(Node):
    def __init__(self):
        name = 'Node_detection'
        super().__init__(name)
        print(name, 'is started')
        hz = 0.5
        self.timer = self.create_timer(1/hz, self.timer_callback)
        self.current_time = self.get_clock().now()

        path = '/home/kim/open_topic/code/yolov5-master/best.pt'
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=path, force_reload=True)

        profile = rclpy.qos.qos_profile_sensor_data
        # profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)
        # profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_RELIABLE,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)

        self.subscription = self.create_subscription(
            Image,
            '/camera/color/image_raw',
            self.listener_callback,
            profile)
        self.br = CvBridge()
        self.original_image_size = (640, 480)
        self.size_to_process = (420, 240)

        self.publisher_ = self.create_publisher(PoseArray, '/pixel_target', 10)

        print('init done')

    def listener_callback(self, msg):
        global image_global , image_changed
        image_orginal_cv2 = self.br.imgmsg_to_cv2(msg, "bgr8")
        cv2.imshow('original', image_orginal_cv2)
        cv2.waitKey(1)
        #self.original_image_size = image_orginal_cv2.shape[:2][::-1]
        self.original_image_size = image_orginal_cv2.shape[:2]
        self.original_image_size = self.original_image_size[::-1]

        image_to_process = cv2.cvtColor(image_orginal_cv2, cv2.COLOR_BGR2RGB)
        image_to_process = cv2.resize(image_to_process, self.size_to_process)
        # cv2.imshow('resize', image_to_process)
        # cv2.waitKey(1)
        image_global = image_to_process
        image_changed = True

        print('receive image')

    def timer_callback(self):
        global image_global, image_changed, results , results_changed
        if image_changed:
            time_Start = time.time()
            self.current_time = self.get_clock().now()

            results = self.model(image_global)
            print('time process: ', time.time() - time_Start)
            image_changed = False

            frame_result = np.squeeze(results.render())
            frame_result = cv2.cvtColor(frame_result, cv2.COLOR_RGB2BGR)
            frame_result = cv2.resize(frame_result, (self.original_image_size[0], self.original_image_size[1]))

            df = pd.DataFrame(results.pandas().xyxy[0])

            df['xmin'] = df['xmin'] * self.original_image_size[0] / self.size_to_process[0]
            df['xmax'] = df['xmax'] * self.original_image_size[0] / self.size_to_process[0]
            df['ymin'] = df['ymin'] * self.original_image_size[1] / self.size_to_process[1]
            df['ymax'] = df['ymax'] * self.original_image_size[1] / self.size_to_process[1]
            df['center_x'] = (df['xmin'] + df['xmax']) / 2
            df['center_y'] = (df['ymin'] + df['ymax']) / 2


            fps = 1.0 / (self.get_clock().now().nanoseconds - self.current_time.nanoseconds) * 1e9
            #floor .2f
            fps = round(fps, 2)
            frame_result = cv2.putText(frame_result, 'fps: ' + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            #add point to image
            for i in range(len(df)):
                frame_result = cv2.circle(frame_result, (int(df['center_x'][i]), int(df['center_y'][i])), 5, (0, 0, 255), -1)

            cv2.imshow('image', frame_result)
            cv2.waitKey(1)
            #df to csv string
            df = df[df['confidence'] > 0.5]
            #name == Motorcycle
            df = df[df['name'] == 'Motorcycle']
            df = df[['center_x', 'center_y']]
            #reset index
            df = df.reset_index(drop=True)
            msg = PoseArray()
            msg.header.stamp = self.get_clock().now().to_msg()
            for i in range(len(df)):
                pose = Pose()
                pose.position.x = df['center_x'][i]
                pose.position.y = df['center_y'][i]
                msg.poses.append(pose)
            self.publisher_.publish(msg)
            print('time: ', time.time() - time_Start)



def main(args=None):
    rclpy.init(args=args)
    node = Process()
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
