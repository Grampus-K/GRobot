"""
Map Threshold Node

Cartographer's occupancy grid publishes continuous probability values (0-100)
but Nav2 static_layer (lethal_cost_threshold=100 default) only treats value=100
as an obstacle.  This node thresholds to binary 0/100 so all occupied-looking
cells get recognised and inflated.

Pipeline: /map_raw (from cartographer) → threshold → /map (to costmap)
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from nav_msgs.msg import OccupancyGrid


class MapThreshold(Node):
    def __init__(self):
        super().__init__("map_threshold")

        self.declare_parameter("threshold", 10)
        self.threshold = self.get_parameter("threshold").value

        map_qos = QoSProfile(
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )

        self.sub = self.create_subscription(
            OccupancyGrid, "/map_raw", self.callback, map_qos
        )
        self.pub = self.create_publisher(OccupancyGrid, "/map", map_qos)

        self.get_logger().info(
            f"Thresholding /map_raw → /map (threshold={self.threshold})"
        )

    def callback(self, msg: OccupancyGrid):
        filtered = OccupancyGrid()
        filtered.header = msg.header
        filtered.info = msg.info
        filtered.data = [self._threshold(v) for v in msg.data]
        self.pub.publish(filtered)

    def _threshold(self, value: int) -> int:
        if value < 0:
            return -1  # unknown stays unknown
        if value == 0:
            return 0  # free stays free
        if value >= self.threshold:
            return 100  # occupied
        return 0  # sub-threshold → free


def main():
    rclpy.init()
    node = MapThreshold()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
