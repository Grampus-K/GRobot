import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class FrontIntensity(Node):
    def __init__(self):
        super().__init__("front_intensity")
        self.scan_sub = self.create_subscription(
            LaserScan, "/scan", self.scan_callback, 10
        )

    def scan_callback(self, msg: LaserScan):
        idx = int(round((0.0 - msg.angle_min) / msg.angle_increment))
        if 0 <= idx < len(msg.intensities):
            intensity = msg.intensities[idx]
            range_val = msg.ranges[idx]
            self.get_logger().info(
                f"Front: intensity={intensity:.1f}  range={range_val:.3f}m"
            )


def main():
    rclpy.init()
    node = FrontIntensity()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
