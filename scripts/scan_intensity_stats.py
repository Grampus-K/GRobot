#!/usr/bin/env python3

"""Collect range and intensity statistics from a LaserScan angular sector."""

import argparse
import csv
import math
import time

import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


PERCENTILES = (0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)
HISTOGRAM_EDGES = (0, 5, 10, 20, 30, 50, 100, 200, 500, 1000, 2000, 4096, 65536)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Collect LaserScan intensity statistics in a selected angular sector. "
            "Keep the robot and target stationary while sampling."
        )
    )
    parser.add_argument("--topic", default="/scan", help="LaserScan topic (default: /scan)")
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Sampling duration in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--center-angle",
        type=float,
        default=0.0,
        help="Sector center in degrees, where 0 is forward (default: 0.0)",
    )
    parser.add_argument(
        "--half-angle",
        type=float,
        default=5.0,
        help="Half width of the sector in degrees (default: 5.0)",
    )
    parser.add_argument(
        "--min-range",
        type=float,
        default=None,
        help="Optional minimum accepted range in meters",
    )
    parser.add_argument(
        "--max-range",
        type=float,
        default=None,
        help="Optional maximum accepted range in meters",
    )
    parser.add_argument(
        "--csv",
        metavar="PATH",
        help="Optionally write angle, range, and intensity samples to a CSV file",
    )
    args = parser.parse_args()

    if args.duration <= 0.0:
        parser.error("--duration must be greater than zero")
    if args.half_angle <= 0.0 or args.half_angle > 180.0:
        parser.error("--half-angle must be in the range (0, 180]")
    if args.min_range is not None and args.min_range < 0.0:
        parser.error("--min-range cannot be negative")
    if (
        args.min_range is not None
        and args.max_range is not None
        and args.min_range >= args.max_range
    ):
        parser.error("--min-range must be less than --max-range")

    return args


def percentile(sorted_values, percent):
    index = round((len(sorted_values) - 1) * percent / 100.0)
    return sorted_values[index]


def print_percentiles(name, values, unit=""):
    sorted_values = sorted(values)
    print(f"\n{name} percentiles:")
    for percent in PERCENTILES:
        value = percentile(sorted_values, percent)
        print(f"  P{percent:>3}: {value:10.3f}{unit}")


def print_histogram(values):
    print("\nIntensity histogram:")
    total = len(values)
    for lower, upper in zip(HISTOGRAM_EDGES, HISTOGRAM_EDGES[1:]):
        count = sum(lower <= value < upper for value in values)
        if count:
            ratio = count * 100.0 / total
            print(f"  [{lower:>5}, {upper:>5}): {count:>7} ({ratio:6.2f}%)")


def main():
    args = parse_args()
    samples = []
    scan_count = 0
    scans_without_intensity = 0

    center = math.radians(args.center_angle)
    half_width = math.radians(args.half_angle)

    rclpy.init()
    node = rclpy.create_node("scan_intensity_stats")

    def scan_callback(message):
        nonlocal scan_count, scans_without_intensity
        scan_count += 1

        if not message.intensities:
            scans_without_intensity += 1
            return

        point_count = min(len(message.ranges), len(message.intensities))
        minimum_range = message.range_min if args.min_range is None else args.min_range
        maximum_range = message.range_max if args.max_range is None else args.max_range

        for index in range(point_count):
            angle = message.angle_min + index * message.angle_increment
            distance = message.ranges[index]
            intensity = message.intensities[index]

            if (
                abs(angle - center) <= half_width
                and math.isfinite(distance)
                and math.isfinite(intensity)
                and minimum_range <= distance <= maximum_range
            ):
                samples.append((math.degrees(angle), distance, intensity))

    node.create_subscription(
        LaserScan,
        args.topic,
        scan_callback,
        qos_profile_sensor_data,
    )

    print(
        f"Sampling {args.topic} for {args.duration:.1f}s in "
        f"[{args.center_angle - args.half_angle:.1f}, "
        f"{args.center_angle + args.half_angle:.1f}] deg..."
    )

    end_time = time.monotonic() + args.duration
    try:
        while rclpy.ok() and time.monotonic() < end_time:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

    print(f"Received scans: {scan_count}")
    print(f"Valid samples: {len(samples)}")

    if not samples:
        if scans_without_intensity:
            print("No samples collected because the received scans had no intensity data.")
        else:
            print("No valid samples collected. Check the topic, angle sector, and range limits.")
        return 1

    ranges = [sample[1] for sample in samples]
    intensities = [sample[2] for sample in samples]
    print_percentiles("Range", ranges, " m")
    print_percentiles("Intensity", intensities)
    print_histogram(intensities)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as output_file:
            writer = csv.writer(output_file)
            writer.writerow(("angle_deg", "range_m", "intensity"))
            writer.writerows(samples)
        print(f"\nWrote {len(samples)} samples to {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
