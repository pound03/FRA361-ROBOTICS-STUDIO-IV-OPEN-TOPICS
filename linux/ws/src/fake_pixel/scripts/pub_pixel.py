#!/usr/bin/python3

from geometry_msgs.msg import PoseArray
from geometry_msgs.msg import Pose
import numpy as np
import rclpy
from rclpy.node import Node
import sys

class DummyNode(Node):
    def __init__(self):
        super().__init__('dummy_node')
        self.publisher_ = self.create_publisher(PoseArray, '/pixel_target', 10)
        self.timer = self.create_timer(2, self.timer_callback)
        self.count = 2

    def timer_callback(self):
        msg = PoseArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        #1280, 720
        #x = linespace(0, 1280, 10)
        x = np.linspace(100, 1200, self.count)
        y = np.linspace(100, 620, self.count)
        for i in range(self.count):
            msg_sub = Pose()
            msg_sub.position.x = x[i]
            msg_sub.position.y = y[i]
            msg.poses.append(msg_sub)
        
        
        self.publisher_.publish(msg)
        self.count += 1
        if self.count > 5:
            self.count = 2
        print('Publishing: "%d"' % self.count)
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
