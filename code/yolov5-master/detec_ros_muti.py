#!/usr/bin/env python3

import cv2
import torch
import numpy as np
import pandas as pd
import time
import multiprocessing
import threading

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


def process_image(stop_event):
    global image_global , image_changed , results , results_changed
    path = '/home/carver/kim_open_topic/code/yolov5-master/best.pt'
    torch.hub._validate_not_a_forked_repo=lambda a,b,c: True
    model = torch.hub.load('ultralytics/yolov5', 'custom', path=path, force_reload=True)
    while  not stop_event.is_set():
        if image_changed:
            time_start = time.time()
            image_changed = False
            results = model(image_global)
            results_changed = True
            print('anothor thread use time to process:', time.time() - time_start)

class Interface(Node):
    def __init__(self):
        name = 'Node_detection_interface'
        super().__init__(name)
        print(name, 'is started')
        hz = 30
        self.timer = self.create_timer(1/hz, self.timer_callback)
        self.current_time = self.get_clock().now()

        profile = rclpy.qos.qos_profile_sensor_data
        # profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)
        # profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_RELIABLE,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)

        self.subscription = self.create_subscription(
            Image,
            '/camera/color/image_raw',
            self.listener_callback,
            profile)
        self.br = CvBridge()
        self.original_image_size = (1280, 720)
        self.size_to_process = (420, 240)

        self.publisher_ = self.create_publisher(PoseArray, '/pixel_target', 10)
        self.current_time = self.get_clock().now()
        self.msg = PoseArray()
        print('init done')

    def listener_callback(self, msg):
        global image_global , image_changed
        image_orginal_cv2 = self.br.imgmsg_to_cv2(msg, "bgr8")
        # cv2.imshow('original', image_orginal_cv2)
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


        # print('receive image')

    def timer_callback(self):
        global image_global, image_changed, results , results_changed
        # if results_changed:
        if None != results:
            time_Start = time.time()
            results_changed = False
            #copy results to local
            results_local = results

            frame_result = np.squeeze(results_local.render())
            frame_result = cv2.cvtColor(frame_result, cv2.COLOR_RGB2BGR)
            frame_result = cv2.resize(frame_result, (self.original_image_size[0], self.original_image_size[1]))

            df = pd.DataFrame(results_local.pandas().xyxy[0])

            df['xmin'] = df['xmin'] * self.original_image_size[0] / self.size_to_process[0]
            df['xmax'] = df['xmax'] * self.original_image_size[0] / self.size_to_process[0]
            df['ymin'] = df['ymin'] * self.original_image_size[1] / self.size_to_process[1]
            df['ymax'] = df['ymax'] * self.original_image_size[1] / self.size_to_process[1]
            df['center_x'] = (df['xmin'] + df['xmax']) / 2
            df['center_y'] = (df['ymin'] + df['ymax']) / 2

            fps = 1.0 / (self.get_clock().now().nanoseconds - self.current_time.nanoseconds) * 1e9
            self.current_time = self.get_clock().now()
            #floor .2f
            fps = round(fps, 2)
            frame_result = cv2.putText(frame_result, 'fps: ' + str(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            #add point to image
            for i in range(len(df)):
                frame_result = cv2.circle(frame_result, (int(df['center_x'][i]), int(df['center_y'][i])), 5, (0, 0, 255), -1)

            #df to csv string
            df = df[df['confidence'] > 0.5]
            #name == Motorcycle
            # df = df[df['name'] == 'Motorcycle']
            df = df[['center_x', 'center_y']]
            #reset index
            df = df.reset_index(drop=True)
            self.msg = PoseArray()
            self.msg.header.stamp = self.get_clock().now().to_msg()
            for i in range(len(df)):
                pose = Pose()
                pose.position.x = df['center_x'][i]
                pose.position.y = df['center_y'][i]
                self.msg.poses.append(pose)
                # print('i: ', i , 'x: ', df['center_x'][i], 'y: ', df['center_y'][i])
            print('main thread time: ', time.time() - time_Start)
            cv2.imshow('detect node', cv2.resize(frame_result , (480,240)))
        self.publisher_.publish(self.msg)
        cv2.waitKey(1)




def main(args=None):
    rclpy.init(args=args)
    stop_event = threading.Event()
    thread1 = threading.Thread(target=process_image, args=(stop_event,))
    try:
        Node2 = Interface()

        thread1.daemon = True
        thread1.start()

        while rclpy.ok():
            rclpy.spin_once(Node2)

    except KeyboardInterrupt:
        #thread stop
        print('KeyboardInterrupt')
    finally:
        print('finally')

if __name__=='__main__':
    main()
