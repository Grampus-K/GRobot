import math
import statistics
from typing import List, Tuple

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


def normalize_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


class FrontIntensityMonitor(Node):
    def __init__(self) -> None:
        super().__init__("front_intensity_monitor")

        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("filtered_topic", "/front_scan")
        self.declare_parameter("center_angle_deg", 90.0)
        self.declare_parameter("window_deg", 10.0)
        self.declare_parameter("print_rate_hz", 1.0)
        self.declare_parameter("publish_filtered_scan", True)
        self.declare_parameter("max_points_to_print", 12)

        self.scan_topic = str(self.get_parameter("scan_topic").value)
        self.filtered_topic = str(self.get_parameter("filtered_topic").value)
        self.center_angle = math.radians(float(self.get_parameter("center_angle_deg").value))
        self.half_window = math.radians(float(self.get_parameter("window_deg").value)) * 0.5
        self.print_period = 1.0 / max(0.1, float(self.get_parameter("print_rate_hz").value))
        self.publish_filtered_scan = bool(self.get_parameter("publish_filtered_scan").value)
        self.max_points_to_print = max(0, int(self.get_parameter("max_points_to_print").value))

        self.last_print_time = self.get_clock().now()
        self.printed_scan_info = False
        self.filtered_pub = None
        if self.publish_filtered_scan:
            self.filtered_pub = self.create_publisher(LaserScan, self.filtered_topic, qos_profile_sensor_data)

        self.scan_sub = self.create_subscription(
            LaserScan,
            self.scan_topic,
            self.scan_callback,
            qos_profile_sensor_data,
        )

        self.get_logger().info(
            "Monitoring %s around %.2f deg +/- %.2f deg; filtered scan topic: %s"
            % (
                self.scan_topic,
                math.degrees(self.center_angle),
                math.degrees(self.half_window),
                self.filtered_topic if self.publish_filtered_scan else "disabled",
            )
        )

    def scan_callback(self, msg: LaserScan) -> None:
        if not self.printed_scan_info:
            self.printed_scan_info = True
            self.get_logger().info(
                "raw scan frame=%s angle_min=%.2f deg angle_max=%.2f deg angle_increment=%.3f deg points=%d intensities=%d"
                % (
                    msg.header.frame_id,
                    math.degrees(msg.angle_min),
                    math.degrees(msg.angle_max),
                    math.degrees(msg.angle_increment),
                    len(msg.ranges),
                    len(msg.intensities),
                )
            )

        front_points, filtered_ranges, filtered_intensities = self.extract_front_points(msg)

        if self.filtered_pub is not None:
            filtered_msg = LaserScan()
            filtered_msg.header = msg.header
            filtered_msg.angle_min = msg.angle_min
            filtered_msg.angle_max = msg.angle_max
            filtered_msg.angle_increment = msg.angle_increment
            filtered_msg.time_increment = msg.time_increment
            filtered_msg.scan_time = msg.scan_time
            filtered_msg.range_min = msg.range_min
            filtered_msg.range_max = msg.range_max
            filtered_msg.ranges = filtered_ranges
            filtered_msg.intensities = filtered_intensities
            self.filtered_pub.publish(filtered_msg)

        now = self.get_clock().now()
        if (now - self.last_print_time).nanoseconds * 1e-9 < self.print_period:
            return
        self.last_print_time = now
        self.print_summary(front_points, msg)

    def extract_front_points(self, msg: LaserScan) -> Tuple[List[Tuple[float, float, float]], List[float], List[float]]:
        ranges = list(msg.ranges)
        has_intensity = len(msg.intensities) == len(ranges)
        filtered_ranges = [math.inf] * len(ranges)
        filtered_intensities = [0.0] * len(ranges)
        front_points: List[Tuple[float, float, float]] = []

        for i, scan_range in enumerate(ranges):
            angle = msg.angle_min + i * msg.angle_increment
            if abs(normalize_angle(angle - self.center_angle)) > self.half_window:
                continue

            intensity = float(msg.intensities[i]) if has_intensity else math.nan
            if math.isfinite(scan_range) and msg.range_min <= scan_range <= msg.range_max:
                front_points.append((angle, float(scan_range), intensity))
                filtered_ranges[i] = float(scan_range)
                filtered_intensities[i] = 0.0 if math.isnan(intensity) else intensity

        return front_points, filtered_ranges, filtered_intensities

    def print_summary(self, points: List[Tuple[float, float, float]], msg: LaserScan) -> None:
        if not points:
            self.get_logger().info(
                "front window center=%.1f deg width=%.1f deg: no valid range points, frame=%s"
                % (
                    math.degrees(self.center_angle),
                    math.degrees(self.half_window) * 2.0,
                    msg.header.frame_id,
                )
            )
            return

        intensities = [p[2] for p in points if math.isfinite(p[2])]
        distances = [p[1] for p in points]
        if intensities:
            intensity_text = (
                "intensity min/mean/median/max = %.1f / %.1f / %.1f / %.1f"
                % (
                    min(intensities),
                    sum(intensities) / len(intensities),
                    statistics.median(intensities),
                    max(intensities),
                )
            )
        else:
            intensity_text = "scan has no intensity array"

        nearest = sorted(points, key=lambda p: p[1])[: self.max_points_to_print]
        nearest_text = ", ".join(
            "angle=%+.2fdeg range=%.3fm intensity=%s"
            % (
                math.degrees(angle),
                scan_range,
                "%.1f" % intensity if math.isfinite(intensity) else "nan",
            )
            for angle, scan_range, intensity in nearest
        )

        self.get_logger().info(
            "front %.1f deg: valid=%d, range min/mean/max=%.3f/%.3f/%.3f m, %s"
            % (
                math.degrees(self.half_window) * 2.0,
                len(points),
                min(distances),
                sum(distances) / len(distances),
                max(distances),
                intensity_text,
            )
        )
        if nearest_text:
            self.get_logger().info("nearest samples: %s" % nearest_text)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FrontIntensityMonitor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
