#!/usr/bin/python3

from sensor_msgs.msg import CameraInfo
from sensor_msgs.msg import Image
import numpy as np
import rclpy
from rclpy.node import Node
import sys

class DelayFrame(Node):
    def __init__(self):
        super().__init__('delay_frame')

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
        
        hz = 5
        self.timer = self.create_timer(1, self.timer_callback)

        self.start = np.array([False, False])

        self.publisher_depth = self.create_publisher(Image, '/camera/depth/image_rect_raw/fake', 10)
        self.publisher_image = self.create_publisher(Image, '/camera/color/image_raw/fake', 10)


    def image_sub_callback(self, msg):
        self.image = msg
        self.start[0] = True

    def depth_sub_callback(self, msg):
        self.depth_image = msg
        self.start[1] = True

    def timer_callback(self):
        if self.start.all():
            self.publisher_depth.publish(self.depth_image)
            self.publisher_image.publish(self.image)
            # self.get_logger().info('Publishing fake image and depth')

def main(args=None):
    rclpy.init(args=args)
    node = DelayFrame()
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
