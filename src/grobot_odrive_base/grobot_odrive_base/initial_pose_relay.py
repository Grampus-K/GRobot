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
            f"Setting initial pose: x={pose.position.x:.2f} "
            f"y={pose.position.y:.2f} yaw={yaw:.2f} rad"
        )
        future = self.client.call_async(req)
        future.add_done_callback(self._on_start_trajectory_done)

    def _on_start_trajectory_done(self, future):
        try:
            response = future.result()
        except Exception as exc:
            self.get_logger().error(f"start_trajectory call failed: {exc}")
            return
        self.get_logger().info(f"start_trajectory response: {response}")


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
