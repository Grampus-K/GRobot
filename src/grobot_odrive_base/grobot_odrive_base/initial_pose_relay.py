"""
Initial Pose Relay for Cartographer Pure Localization

Cartographer's `cartographer_node` does NOT subscribe to `/initialpose` (the
topic RViz's "2D Pose Estimate" tool publishes to).  Its initial pose must be
set through the `/start_trajectory` service instead.

This node bridges the two: it subscribes to `/initialpose` and, on each click,
calls `/start_trajectory` with an empty configuration (reuse the config loaded
at launch) so Cartographer re-localizes at the clicked pose.
"""

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
from cartographer_ros_msgs.srv import StartTrajectory


class InitialPoseRelay(Node):
    def __init__(self):
        super().__init__("initial_pose_relay")

        self.client = self.create_client(StartTrajectory, "/start_trajectory")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(
                "Waiting for /start_trajectory service (cartographer_node) ..."
            )

        self.sub = self.create_subscription(
            PoseWithCovarianceStamped,
            "/initialpose",
            self._on_initial_pose,
            10,
        )
        self.get_logger().info(
            "Ready. Use RViz '2D Pose Estimate' to set Cartographer's initial pose."
        )

    def _on_initial_pose(self, msg: PoseWithCovarianceStamped):
        pose = msg.pose.pose
        q = pose.orientation
        yaw = 2.0 * math.atan2(q.z, q.w)

        req = StartTrajectory.Request()
        req.configuration_directory = ""
        req.configuration_basename = ""
        req.use_initial_pose = True
        req.initial_pose = pose
        req.relative_to_trajectory_id = 0

        self.get_logger().info(
            "Setting initial pose: x=%.2f y=%.2f yaw=%.2f rad",
            pose.position.x,
            pose.position.y,
            yaw,
        )
        self.client.call_async(req)


def main():
    rclpy.init()
    node = InitialPoseRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
