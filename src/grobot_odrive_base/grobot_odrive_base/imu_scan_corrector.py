import math
from collections import deque

import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node
from sensor_msgs.msg import Imu, LaserScan


class ImuScanCorrector(Node):
    def __init__(self):
        super().__init__("imu_scan_corrector")

        self.declare_parameter("max_imu_age", 0.1)
        self.max_imu_age = float(self.get_parameter("max_imu_age").value)

        self.imu_buffer = deque(maxlen=200)
        self._pending_scan = None

        self.imu_sub = self.create_subscription(Imu, "/imu/data", self.imu_callback, 10)
        self.scan_sub = self.create_subscription(LaserScan, "/scan", self.scan_callback, 10)
        self.corrected_pub = self.create_publisher(LaserScan, "/scan_corrected", 10)

        self.get_logger().info("IMU scan corrector ready, publishing to /scan_corrected")

    def imu_callback(self, msg: Imu):
        self.imu_buffer.append(msg)

    def scan_callback(self, scan_msg: LaserScan):
        angular_z = self._get_angular_vel_at(scan_msg.header.stamp)
        if angular_z is None or scan_msg.ranges is None or len(scan_msg.ranges) == 0:
            self.corrected_pub.publish(scan_msg)
            return

        scan_time = scan_msg.scan_time
        angle_inc = scan_msg.angle_increment
        if scan_time <= 0.0 or angle_inc <= 0.0:
            self.corrected_pub.publish(scan_msg)
            return

        rotation_during_scan = angular_z * scan_time
        idx_shift = int(round(rotation_during_scan / angle_inc))
        if idx_shift == 0:
            self.corrected_pub.publish(scan_msg)
            return

        n = len(scan_msg.ranges)
        idx_shift = idx_shift % n
        if idx_shift < 0:
            idx_shift += n

        corrected = LaserScan()
        corrected.header = scan_msg.header
        corrected.header.frame_id = scan_msg.header.frame_id
        corrected.angle_min = scan_msg.angle_min
        corrected.angle_max = scan_msg.angle_max
        corrected.angle_increment = angle_inc
        corrected.time_increment = scan_msg.time_increment
        corrected.scan_time = scan_time
        corrected.range_min = scan_msg.range_min
        corrected.range_max = scan_msg.range_max
        corrected.ranges = scan_msg.ranges[idx_shift:] + scan_msg.ranges[:idx_shift]
        corrected.intensities = (
            scan_msg.intensities[idx_shift:] + scan_msg.intensities[:idx_shift]
            if len(scan_msg.intensities) == n
            else []
        )

        self.corrected_pub.publish(corrected)

    def _get_angular_vel_at(self, stamp):
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

        return float(best_msg.angular_velocity.z)


def main():
    rclpy.init()
    node = ImuScanCorrector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
