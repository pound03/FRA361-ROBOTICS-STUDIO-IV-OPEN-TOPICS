#!/usr/bin/env python3

import pyrealsense2 as rs2

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point32
from sensor_msgs.msg import CameraInfo


class Estimate_coordinate(Node):
    def __init__(self):
        super().__init__('estimate_coordinate_node')
        print('estimate_coordinate_node activate')
            # Create the publisher. This publisher will publish target_position (xyz [float32]) through topic 'position_from_rs2'.
        self.position_publisher = self.create_publisher(Point32, 'position_from_rs2', 10)

        self.CameraInfo_subscription = self.create_subscription(        # Subscribe Camera massage through topic '/camera/depth/camera_info'.
            CameraInfo,                                                 # Get Camera info for use to estimate position (x, y, z) in real world coordinate.
            '/camera/depth/camera_info', 
            self.CameraInfo_listener_callback, 
            10)
        self.CameraInfo_subscription                                    # prevent unused variable warning.

        self.Position_subscription = self.create_subscription(          # Subscribe Point32 massage through topic 'position_for_estimate_coordinate'.
            Point32,                                                    # Get position for use to estimate position (x, y, z) in real world coordinate.
            'position_for_estimate_coordinate', 
            self.Position_subscription_callback, 
            10)
        self.Position_subscription                                      # prevent unused variable warning.

        self.depth = 0.0                                                # Initial depth value.

    def CameraInfo_listener_callback(self, msg:CameraInfo):
        self.camera_info = msg

    def Position_subscription_callback(self, msg:Point32):
        self.depth = msg.z
        result = self.convert_depth_to_phys_coord_using_realsense(      # Estimate real-world postion by pixel (x,y), depth, and camera info.
            x = msg.x, 
            y = msg.y, 
            depth = msg.z, 
            cameraInfo = self.camera_info)
        self.Position_publish(result)                                   # Publish target_position.
        print(result)
        
    def Position_publish(self,result):
        msg = Point32()
        msg.x = result[0]
        msg.y = result[1]
        msg.z = self.depth
        self.position_publisher.publish(msg)

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
