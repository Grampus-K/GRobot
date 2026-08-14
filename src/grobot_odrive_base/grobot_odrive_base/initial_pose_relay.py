"""
Initial Pose Relay for Cartographer Pure Localization

Cartographer's `cartographer_node` does NOT subscribe to `/initialpose` (the
topic RViz's "2D Pose Estimate" tool publishes to), and with
`-load_state_filename` it does not reliably auto-start a localization
trajectory, so the `map -> odom` transform is never published and the `map`
frame never appears.

This node bridges the gap:

1. On startup it fires `/start_trajectory` once (identity pose) to force the
   localization trajectory to start, so `map -> odom` is published. The global
   localization configured in cartographer_localization.lua then corrects the
   identity pose to the robot's true position.
2. It also subscribes to `/initialpose` so RViz "2D Pose Estimate" can override
   the pose manually at any time.
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

        # Auto-start the localization trajectory after a short delay so
        # cartographer_node has time to finish loading the pbstream state.
        self._auto_start_timer = self.create_timer(3.0, self._auto_start)

    def _auto_start(self):
        self._auto_start_timer.cancel()
        self.get_logger().info("Auto-starting localization trajectory at map origin ...")
        self._start_trajectory(initial_pose=None)

    def _start_trajectory(self, initial_pose):
        req = StartTrajectory.Request()
        # Empty configuration reuses the config loaded at launch.
        req.configuration_directory = ""
        req.configuration_basename = ""
        req.use_initial_pose = initial_pose is not None
        if initial_pose is not None:
            req.initial_pose = initial_pose
        req.relative_to_trajectory_id = 0

        future = self.client.call_async(req)
        future.add_done_callback(self._on_start_trajectory_done)

    def _on_initial_pose(self, msg: PoseWithCovarianceStamped):
        pose = msg.pose.pose
        q = pose.orientation
        yaw = 2.0 * math.atan2(q.z, q.w)

        self.get_logger().info(
            f"Setting initial pose: x={pose.position.x:.2f} "
            f"y={pose.position.y:.2f} yaw={yaw:.2f} rad"
        )
        self._start_trajectory(initial_pose=pose)

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
