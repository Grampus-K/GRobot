import math
from collections import deque

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu
from tf2_ros import TransformBroadcaster


class OdomImuFuser(Node):
    def __init__(self):
        super().__init__("odom_imu_fuser")

        self.declare_parameter("max_imu_age", 0.5)
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")
        self.max_imu_age = float(self.get_parameter("max_imu_age").value)
        self.odom_frame = str(self.get_parameter("odom_frame").value)
        self.base_frame = str(self.get_parameter("base_frame").value)

        self.imu_buffer = deque(maxlen=500)
        self.initial_yaw = None

        self.imu_sub = self.create_subscription(Imu, "/imu/data", self.imu_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, "/odom_raw", self.odom_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, "/odom", 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.get_logger().info("Odom-IMU fuser ready: /odom_raw + IMU -> /odom + TF")

    def imu_callback(self, msg: Imu):
        self.imu_buffer.append(msg)

    def odom_callback(self, odom_raw: Odometry):
        imu_yaw = self._get_imu_yaw_at(odom_raw.header.stamp)
        if imu_yaw is None:
            self.odom_pub.publish(odom_raw)
            self._publish_tf(odom_raw.header, odom_raw.pose.pose.orientation, odom_raw.pose.pose.position)
            return

        if self.initial_yaw is None:
            self.initial_yaw = imu_yaw

        corrected_yaw = imu_yaw

        corrected_quat = self._yaw_to_quat(corrected_yaw)

        odom = Odometry()
        odom.header = odom_raw.header
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position = odom_raw.pose.pose.position
        odom.pose.pose.orientation = corrected_quat
        odom.pose.covariance = odom_raw.pose.covariance
        odom.twist = odom_raw.twist
        if self.imu_buffer:
            odom.twist.twist.angular.z = float(self.imu_buffer[-1].angular_velocity.z)

        self.odom_pub.publish(odom)
        self._publish_tf(odom_raw.header, corrected_quat, odom_raw.pose.pose.position)

    def _publish_tf(self, header, quat, position=None):
        tf_msg = TransformStamped()
        tf_msg.header.stamp = header.stamp
        tf_msg.header.frame_id = self.odom_frame
        tf_msg.child_frame_id = self.base_frame
        if position is not None:
            tf_msg.transform.translation.x = position.x
            tf_msg.transform.translation.y = position.y
            tf_msg.transform.translation.z = position.z
        else:
            tf_msg.transform.translation.x = 0.0
            tf_msg.transform.translation.y = 0.0
            tf_msg.transform.translation.z = 0.0
        tf_msg.transform.rotation = quat
        self.tf_broadcaster.sendTransform(tf_msg)

    def _get_imu_yaw_at(self, stamp):
        if not self.imu_buffer:
            return None
        t_target = stamp.sec + stamp.nanosec * 1e-9
        best_msg = None
        best_dt = float("inf")
        for msg in self.imu_buffer:
            t_imu = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            dt = abs(t_imu - t_target)
            if dt < best_dt:
                best_dt = dt
                best_msg = msg
        if best_msg is None or best_dt > self.max_imu_age:
            return None
        q = best_msg.orientation
        return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))

    @staticmethod
    def _quat_to_yaw(q):
        return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))

    @staticmethod
    def _yaw_to_quat(yaw):
        half = yaw * 0.5
        from geometry_msgs.msg import Quaternion
        q = Quaternion()
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(half)
        q.w = math.cos(half)
        return q


def main():
    rclpy.init()
    node = OdomImuFuser()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
