#!/usr/bin/python3

from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import rclpy
from rclpy.node import Node
import sys
from std_msgs.msg import String

class DummyNode(Node):
    def __init__(self):
        super().__init__('dummy_node')
        profile = rclpy.qos.qos_profile_sensor_data
        # profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)
        # profile = QoSProfile(  depth=1, reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_RELIABLE,history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST)

        self.publisher_ = self.create_publisher(String, '/qos', profile)
        self.timer = self.create_timer(1, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = String()
        msg.data = 'Hello World: {0}'.format(self.i)
        self.publisher_.publish(msg)
        print('Publishing: "{0}"'.format(msg.data))
        self.i += 1

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
