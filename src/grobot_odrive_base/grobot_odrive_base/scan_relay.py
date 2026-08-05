"""
Simple relay node: subscribes to /scan and republishes to /scan_corrected.
Used when imu_scan_corrector is disabled for A/B testing rotation drift.
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy, QoSProfile
from sensor_msgs.msg import LaserScan


class ScanRelay(Node):
    def __init__(self):
        super().__init__("scan_relay")

        scan_qos = QoSProfile(
            depth=1,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
        )

        self.sub = self.create_subscription(LaserScan, "/scan", self.callback, scan_qos)
        self.pub = self.create_publisher(LaserScan, "/scan_corrected", scan_qos)
        self.get_logger().info("Relaying /scan → /scan_corrected (corrector bypassed)")

    def callback(self, msg: LaserScan):
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = ScanRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
