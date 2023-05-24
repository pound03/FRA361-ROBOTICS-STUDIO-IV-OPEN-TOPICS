#!/usr/bin/env python3

import cv2
import torch
import numpy as np
import pandas as pd
import time

# import pyrealsense2 as rs2
from cv_bridge import CvBridge                      
import pyrealsense2 as rs2
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
from sensor_msgs.msg import CameraInfo
image_global = None
image_changed = False
results = None
results_changed = False

class Process(Node):
    def __init__(self):
        name = 'Node_detection'
        super().__init__(name)
        self.image_changed = False
        print(name, 'is started')
        hz = 30
        self.timer = self.create_timer(1/hz, self.timer_callback)
        self.current_time = self.get_clock().now()

        path = '/home/carver/kim_open_topic/code/yolov5-master/best.pt'
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=path, force_reload=True)

        profile = rclpy.qos.qos_profile_sensor_data
        # profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)
        # profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_RELIABLE,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)

        self.image_sub = self.create_subscription(
            Image,
            '/camera/color/image_raw',
            self.image_sub_callback,
            profile)
        self.CameraInfo_subscription = self.create_subscription(        # Subscribe Camera massage through topic '/camera/depth/camera_info'.
            CameraInfo,                                                 # Get Camera info for use to estimate position (x, y, z) in real world coordinate.
            '/camera/depth/camera_info', 
            self.CameraInfo_listener_callback, 
            10)
        self.depth_sub = self.create_subscription(
            Image,
            '/camera/depth/image_rect_raw',
            self.depth_sub_callback,
            10)
        self.start = np.array([False, False, False])



        self.br = CvBridge()
        self.original_image_size = (640, 480)
        self.size_to_process = (420, 240)

        self.publisher_ = self.create_publisher(PoseArray, '/pixel_target', 10)
        self.current_time = self.get_clock().now()
        print('init done')

    def image_sub_callback(self, msg):

        image_orginal_cv2 = self.br.imgmsg_to_cv2(msg, "bgr8")

        self.original_image_size = image_orginal_cv2.shape[:2]
        self.original_image_size = self.original_image_size[::-1]
        self.image = cv2.cvtColor(image_orginal_cv2, cv2.COLOR_BGR2RGB)
        self.image_orginal_cv2 = image_orginal_cv2
        self.image = cv2.resize(self.image, self.size_to_process)
        self.image_changed = True
        self.start[1] = True
        print('receive image')

    def CameraInfo_listener_callback(self, msg:CameraInfo):
        self.camera_info = msg
        if self.start[0] == False:
            print('receive camera info')
        self.start[0] = True

    def depth_sub_callback(self, msg):
        self.depth_image = self.br.imgmsg_to_cv2(msg, "passthrough")
        if self.start[0] == False:
            print('receive depth')
        self.start[2] = True


    def timer_callback(self):
        if self.image_changed:
            time_Start = time.time()


            results = self.model(self.image)
            print('time process: ', time.time() - time_Start)
            self.image_changed = False

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
            msg = PoseArray()
            msg.header.stamp = self.get_clock().now().to_msg()
            for i in range(len(df)):
                pose = Pose()
                pose.position.x = df['center_x'][i]
                pose.position.y = df['center_y'][i]
                msg.poses.append(pose)
            self.target = msg.poses
            # print(self.start)

            Image_coordinate = self.image_orginal_cv2
            # cv2.imshow('original' , cv2.resize(Image_coordinate , (480,240)))
            if self.start.all():
                depth_image = self.depth_image
                for i in range(len(self.target)):

                    self.pos = self.target[i].position
                    z = float(depth_image[int(self.pos.y), int(self.pos.x)])
                    self.point = self.convert_depth_to_phys_coord_using_realsense(self.pos.x, self.pos.y, z, self.camera_info)
                    #round to 2 decimal places
                    self.point = np.round(self.point, 2)

                    cv2.circle(Image_coordinate, (int(self.pos.x), int(self.pos.y)), 5, (0, 0, 255), -1)
                    cv2.putText(Image_coordinate, 'x: ' + str(self.point[0]), (int(self.pos.x) + 5, int(self.pos.y) - 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.putText(Image_coordinate, 'y: ' + str(self.point[1]), (int(self.pos.x) + 5, int(self.pos.y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.putText(Image_coordinate, 'z: ' + str(self.point[2]), (int(self.pos.x) + 5, int(self.pos.y) + 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow('Cordinate node', cv2.resize(Image_coordinate , (480,240)))
            cv2.imshow('detect node', cv2.resize(frame_result , (480,240)))
        cv2.waitKey(1)


        # Function for estimate real-world postion by pixel (x,y), depth, and camera info.
    def convert_depth_to_phys_coord_using_realsense(self, x, y, depth, cameraInfo):
            # Camera parameters
        _intrinsics = rs2.intrinsics()
        _intrinsics.width = cameraInfo.width
        _intrinsics.height = cameraInfo.height
        _intrinsics.ppx = cameraInfo.k[2]
        _intrinsics.ppy = cameraInfo.k[5]
        _intrinsics.fx = cameraInfo.k[0]
        _intrinsics.fy = cameraInfo.k[4]
        # _intrinsics.model = cameraInfo.distortion_model
        _intrinsics.model  = rs2.distortion.none
        _intrinsics.coeffs = [i for i in cameraInfo.d]
        result = rs2.rs2_deproject_pixel_to_point(_intrinsics, [x, y], depth)
        # result[0]: right, result[1]: down, result[2]: forward
            # return x, y and z in real world coordinate.
        return -result[0], -result[1], result[2]


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
