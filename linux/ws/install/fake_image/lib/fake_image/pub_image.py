#!/usr/bin/python3

import rclpy
from rclpy.node import Node
import sys
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

import cv2 as cv
class DummyNode(Node):
    def __init__(self):
        super().__init__('dummy_node')
        self.br = CvBridge()

        self.image = cv.imread('/home/carver/kim_open_topic/linux/ws/src/fake_image/images/1.jpg')
        # cv.imshow('image', self.image)
        # cv.waitKey(0)
        
        self.image = cv.resize(self.image, (1280, 720))
        self.image = cv.cvtColor(self.image, cv.COLOR_BGR2RGB)
        self.image = self.br.cv2_to_imgmsg(self.image, encoding="rgb8")
        self.image.header.frame_id = 'camera_color_optical_frame'
        self.image.header.stamp = self.get_clock().now().to_msg()

        self.publisher_ = self.create_publisher(Image, '/camera/color/image_raw', 10)
        self.timer = self.create_timer(1, self.timer_callback)

    def timer_callback(self):
        self.image.header.stamp = self.get_clock().now().to_msg()
        self.get_logger().info('publishing image')
        self.publisher_.publish(self.image)


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
