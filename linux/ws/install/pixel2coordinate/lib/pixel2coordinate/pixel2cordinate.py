#!/usr/bin/env python3

import cv2 as cv
import numpy as np
import pyrealsense2 as rs2

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point32
from sensor_msgs.msg import CameraInfo
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseArray
from geometry_msgs.msg import Pose


class Estimate_coordinate(Node):
    def __init__(self):
        super().__init__('estimate_coordinate_node')
        print('estimate_coordinate_node activate')

        self.CameraInfo_subscription = self.create_subscription(        # Subscribe Camera massage through topic '/camera/depth/camera_info'.
            CameraInfo,                                                 # Get Camera info for use to estimate position (x, y, z) in real world coordinate.
            '/camera/depth/camera_info', 
            self.CameraInfo_listener_callback, 
            10)

        self.image_sub = self.create_subscription(
            Image,
            '/camera/color/image_raw',
            self.image_sub_callback,
            10)
        
        self.depth_sub = self.create_subscription(
            Image,
            '/camera/depth/image_rect_raw',
            self.depth_sub_callback,
            10)
        self.target_sub = self.create_subscription(
            PoseArray,
            '/pixel_target',
            self.target_sub_callback,
            1)
        
        self.br = CvBridge()
        hz = 30
        self.timer = self.create_timer(1/hz, self.timer_callback)

        self.depth = 0.0                                                # Initial depth value.
        self.camera_info = CameraInfo()
        self.image = np.zeros((480, 640, 3), np.uint8)
        self.depth_image = np.zeros((480, 640, 1), np.uint8)
        #np.array false *4 
        self.start = np.array([False, False, False, False])

        self.mode_send_pose = True
        if self.mode_send_pose:
            self.pub_pose = self.create_publisher(PoseArray, '/world_pose', 1)
        
    def target_sub_callback(self, msg:PoseArray):
        self.target = msg.poses
        # print(self.target)
        self.start[3] = True


    def CameraInfo_listener_callback(self, msg:CameraInfo):
        self.camera_info = msg
        if self.start[0] == False:
            print('receive camera info')
        self.start[0] = True
        # print('start')

    def image_sub_callback(self, msg):
        self.image = self.br.imgmsg_to_cv2(msg, "bgr8")
        if self.start[1] == False:
            print('receive image')
        self.start[1] = True
        
    def depth_sub_callback(self, msg):
        self.depth_image = self.br.imgmsg_to_cv2(msg, "passthrough")
        if self.start[2] == False:
            print('receive depth')
        self.start[2] = True


    def timer_callback(self):
        Image = self.image.copy()
        depth_image = self.depth_image
        # print(self.start)
        if self.start[0] and self.start[1] and self.start[2]:
            if self.start[3]:
                for i in range(len(self.target)):
                    self.pos = self.target[i].position
                    z = float(depth_image[int(self.pos.y), int(self.pos.x)])
                    self.point = self.convert_depth_to_phys_coord_using_realsense(self.pos.x, self.pos.y, z, self.camera_info)
                    #round to 2 decimal places
                    self.point = np.round(self.point, 2)
                    print('i : ', i, 'x : ', self.point[0], 'y : ', self.point[1], 'z : ', self.point[2])
                    cv.circle(Image, (int(self.pos.x), int(self.pos.y)), 5, (0, 0, 255), -1)
                    cv.putText(Image, 'x: ' + str(self.point[0]), (int(self.pos.x), int(self.pos.y) + 20), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv.putText(Image, 'y: ' + str(self.point[1]), (int(self.pos.x), int(self.pos.y) + 40), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv.putText(Image, 'z: ' + str(self.point[2]), (int(self.pos.x), int(self.pos.y) + 60), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)


                if self.mode_send_pose:
                    msg = PoseArray()
                    msg.header.frame_id = 'camera_link'
                    msg.header.stamp = self.get_clock().now().to_msg()
                    for i in range(len(self.target)):
                        #calculate position of x, y, z
                        self.pos = self.target[i].position
                        z = float(depth_image[int(self.pos.y), int(self.pos.x)])
                        self.point = self.convert_depth_to_phys_coord_using_realsense(self.pos.x, self.pos.y, z, self.camera_info)
                        #round to 2 decimal places
                        self.point = np.round(self.point, 2)
                        msg_pos = Pose()
                        msg_pos.position.x = self.point[2]/1000
                        msg_pos.position.x = 0.9*msg_pos.position.x
                        msg_pos.position.y = self.point[0]/1000
                        msg_pos.position.z = self.point[1]/1000
                        msg.poses.append(msg_pos)
                    self.pub_pose.publish(msg)

            cv.imshow('Cordinate node', cv.resize(Image , (480,240)))
            cv.imshow('Depth node', cv.resize(depth_image , (480,240))*10)
        cv.waitKey(1)


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
    estimate_coordinate = Estimate_coordinate()
    rclpy.spin(estimate_coordinate)
    estimate_coordinate.destroy_node()
    estimate_coordinate.shutdown()
    rclpy.shutdown()

if __name__=='__main__':
    main()
