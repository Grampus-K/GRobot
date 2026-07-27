import math
import time
from typing import Optional, Tuple

import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import TransformBroadcaster

try:
    import odrive
    from odrive.enums import AXIS_STATE_CLOSED_LOOP_CONTROL, AXIS_STATE_IDLE
except ImportError:
    odrive = None
    AXIS_STATE_CLOSED_LOOP_CONTROL = 8
    AXIS_STATE_IDLE = 1


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def yaw_to_quaternion(yaw: float) -> Tuple[float, float, float, float]:
    half = yaw * 0.5
    return 0.0, 0.0, math.sin(half), math.cos(half)


class ODriveBaseNode(Node):
    def __init__(self) -> None:
        super().__init__("odrive_base_node")

        self._declare_parameters()
        self._load_parameters()

        self.odom_pub = self.create_publisher(Odometry, "odom", 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.cmd_sub = self.create_subscription(Twist, "cmd_vel", self.cmd_vel_callback, 10)

        self.cmd_vx = 0.0
        self.cmd_wz = 0.0
        self.last_cmd_time = self.get_clock().now()

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_left_pos: Optional[float] = None
        self.last_right_pos: Optional[float] = None
        self.faulted = False
        self.error_check_countdown = 1
        self.error_check_period_ticks = max(1, round(self.control_rate_hz / self.error_check_rate_hz))

        self.odrv = None
        self.left_axis_obj = None
        self.right_axis_obj = None

        try:
            self.connect_odrive()
            self.check_bus_voltage()
            self.check_all_axis_errors(raise_on_error=True)

            if self.enter_closed_loop_on_start:
                self.enter_closed_loop()

            self.last_left_pos = self.read_wheel_position_turns(self.left_axis_obj, self.left_feedback_sign)
            self.last_right_pos = self.read_wheel_position_turns(self.right_axis_obj, self.right_feedback_sign)

            timer_period = 1.0 / self.control_rate_hz
            self.timer = self.create_timer(timer_period, self.control_loop)
            self.get_logger().info(
                "ODrive base node ready: wheel_diameter=%.3fm, wheel_circumference=%.3fm, track_width=%.3fm"
                % (self.wheel_diameter, self.wheel_circumference, self.track_width)
            )
        except Exception:
            self.safe_stop(send_idle=True)
            raise

    def _declare_parameters(self) -> None:
        self.declare_parameter("wheel_diameter", 0.1725)
        self.declare_parameter("track_width", 0.375)
        self.declare_parameter("left_axis", 1)
        self.declare_parameter("right_axis", 0)
        self.declare_parameter("left_cmd_sign", 1.0)
        self.declare_parameter("right_cmd_sign", -1.0)
        self.declare_parameter("left_feedback_sign", 1.0)
        self.declare_parameter("right_feedback_sign", -1.0)
        self.declare_parameter("max_wheel_turn_s", 2.0)
        self.declare_parameter("cmd_timeout", 0.5)
        self.declare_parameter("control_rate_hz", 50.0)
        self.declare_parameter("error_check_rate_hz", 2.0)
        self.declare_parameter("min_bus_voltage", 21.5)
        self.declare_parameter("max_bus_voltage", 31.0)
        self.declare_parameter("connect_timeout", 10.0)
        self.declare_parameter("enter_closed_loop_on_start", True)
        self.declare_parameter("idle_on_shutdown", True)
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("publish_tf", True)

    def _load_parameters(self) -> None:
        self.wheel_diameter = float(self.get_parameter("wheel_diameter").value)
        self.wheel_circumference = self.wheel_diameter * math.pi
        self.track_width = float(self.get_parameter("track_width").value)
        self.left_axis_id = int(self.get_parameter("left_axis").value)
        self.right_axis_id = int(self.get_parameter("right_axis").value)
        self.left_cmd_sign = float(self.get_parameter("left_cmd_sign").value)
        self.right_cmd_sign = float(self.get_parameter("right_cmd_sign").value)
        self.left_feedback_sign = float(self.get_parameter("left_feedback_sign").value)
        self.right_feedback_sign = float(self.get_parameter("right_feedback_sign").value)
        self.max_wheel_turn_s = float(self.get_parameter("max_wheel_turn_s").value)
        self.cmd_timeout = float(self.get_parameter("cmd_timeout").value)
        self.control_rate_hz = float(self.get_parameter("control_rate_hz").value)
        self.error_check_rate_hz = float(self.get_parameter("error_check_rate_hz").value)
        self.min_bus_voltage = float(self.get_parameter("min_bus_voltage").value)
        self.max_bus_voltage = float(self.get_parameter("max_bus_voltage").value)
        self.connect_timeout = float(self.get_parameter("connect_timeout").value)
        self.enter_closed_loop_on_start = bool(self.get_parameter("enter_closed_loop_on_start").value)
        self.idle_on_shutdown = bool(self.get_parameter("idle_on_shutdown").value)
        self.odom_frame = str(self.get_parameter("odom_frame").value)
        self.base_frame = str(self.get_parameter("base_frame").value)
        self.publish_tf = bool(self.get_parameter("publish_tf").value)

    def connect_odrive(self) -> None:
        if odrive is None:
            raise RuntimeError("Python package 'odrive' is not installed. Install it with: pip3 install odrive==0.5.1.post0")

        self.get_logger().info("Searching for ODrive over USB...")
        try:
            self.odrv = odrive.find_any(timeout=self.connect_timeout)
        except TypeError:
            self.odrv = odrive.find_any()

        self.left_axis_obj = getattr(self.odrv, f"axis{self.left_axis_id}")
        self.right_axis_obj = getattr(self.odrv, f"axis{self.right_axis_id}")
        self.get_logger().info(
            f"Connected to ODrive. left=axis{self.left_axis_id}, right=axis{self.right_axis_id}"
        )

    def check_bus_voltage(self) -> None:
        bus_voltage = float(getattr(self.odrv, "vbus_voltage"))
        self.get_logger().info(f"ODrive bus voltage: {bus_voltage:.2f} V")
        if bus_voltage < self.min_bus_voltage or bus_voltage > self.max_bus_voltage:
            raise RuntimeError(
                f"Bus voltage {bus_voltage:.2f} V outside allowed range "
                f"[{self.min_bus_voltage:.2f}, {self.max_bus_voltage:.2f}] V"
            )

    def read_axis_errors(self, axis) -> Tuple[int, int, int, int]:
        return (
            int(getattr(axis, "error", 0)),
            int(getattr(axis.motor, "error", 0)),
            int(getattr(axis.encoder, "error", 0)),
            int(getattr(axis.controller, "error", 0)),
        )

    def check_axis_errors(self, axis, axis_name: str) -> bool:
        axis_error, motor_error, encoder_error, controller_error = self.read_axis_errors(axis)
        has_error = any((axis_error, motor_error, encoder_error, controller_error))
        if has_error:
            self.get_logger().error(
                f"{axis_name} errors: axis={axis_error}, motor={motor_error}, "
                f"encoder={encoder_error}, controller={controller_error}"
            )
        return has_error

    def check_all_axis_errors(self, raise_on_error: bool = False) -> bool:
        left_error = self.check_axis_errors(self.left_axis_obj, f"axis{self.left_axis_id}/left")
        right_error = self.check_axis_errors(self.right_axis_obj, f"axis{self.right_axis_id}/right")
        has_error = left_error or right_error
        if has_error and raise_on_error:
            raise RuntimeError("ODrive axis error detected. Check with odrivetool dump_errors(odrv0).")
        return has_error

    def enter_closed_loop(self) -> None:
        self.get_logger().info("Entering CLOSED_LOOP_CONTROL...")
        self.left_axis_obj.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.right_axis_obj.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        time.sleep(0.5)
        self.check_all_axis_errors(raise_on_error=True)
        self.get_logger().info("Both axes requested CLOSED_LOOP_CONTROL.")

    def cmd_vel_callback(self, msg: Twist) -> None:
        self.cmd_vx = float(msg.linear.x)
        self.cmd_wz = float(msg.angular.z)
        self.last_cmd_time = self.get_clock().now()

    def command_is_stale(self) -> bool:
        age = (self.get_clock().now() - self.last_cmd_time).nanoseconds * 1e-9
        return age > self.cmd_timeout

    def twist_to_wheel_turns(self, vx: float, wz: float) -> Tuple[float, float]:
        left_mps = vx - wz * self.track_width * 0.5
        right_mps = vx + wz * self.track_width * 0.5
        left_turn_s = left_mps / self.wheel_circumference
        right_turn_s = right_mps / self.wheel_circumference
        left_turn_s = clamp(left_turn_s, -self.max_wheel_turn_s, self.max_wheel_turn_s)
        right_turn_s = clamp(right_turn_s, -self.max_wheel_turn_s, self.max_wheel_turn_s)
        return left_turn_s, right_turn_s

    def write_wheel_commands(self, left_turn_s: float, right_turn_s: float) -> None:
        self.left_axis_obj.controller.input_vel = self.left_cmd_sign * left_turn_s
        self.right_axis_obj.controller.input_vel = self.right_cmd_sign * right_turn_s

    def read_wheel_position_turns(self, axis, feedback_sign: float) -> float:
        return feedback_sign * float(axis.encoder.pos_estimate)

    def update_odometry(self, now) -> None:
        left_pos = self.read_wheel_position_turns(self.left_axis_obj, self.left_feedback_sign)
        right_pos = self.read_wheel_position_turns(self.right_axis_obj, self.right_feedback_sign)

        if self.last_left_pos is None or self.last_right_pos is None:
            self.last_left_pos = left_pos
            self.last_right_pos = right_pos
            return

        delta_left_m = (left_pos - self.last_left_pos) * self.wheel_circumference
        delta_right_m = (right_pos - self.last_right_pos) * self.wheel_circumference
        self.last_left_pos = left_pos
        self.last_right_pos = right_pos

        delta_s = 0.5 * (delta_right_m + delta_left_m)
        delta_theta = (delta_right_m - delta_left_m) / self.track_width
        heading_mid = self.theta + 0.5 * delta_theta

        self.x += delta_s * math.cos(heading_mid)
        self.y += delta_s * math.sin(heading_mid)
        self.theta = math.atan2(math.sin(self.theta + delta_theta), math.cos(self.theta + delta_theta))

        left_vel_mps = float(self.left_axis_obj.encoder.vel_estimate) * self.left_feedback_sign * self.wheel_circumference
        right_vel_mps = float(self.right_axis_obj.encoder.vel_estimate) * self.right_feedback_sign * self.wheel_circumference
        linear_vel = 0.5 * (right_vel_mps + left_vel_mps)
        angular_vel = (right_vel_mps - left_vel_mps) / self.track_width

        self.publish_odometry(now, linear_vel, angular_vel)

    def publish_odometry(self, now, linear_vel: float, angular_vel: float) -> None:
        qx, qy, qz, qw = yaw_to_quaternion(self.theta)

        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.x = qx
        odom.pose.pose.orientation.y = qy
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = linear_vel
        odom.twist.twist.angular.z = angular_vel

        odom.pose.covariance[0] = 0.02
        odom.pose.covariance[7] = 0.02
        odom.pose.covariance[35] = 0.05
        odom.twist.covariance[0] = 0.05
        odom.twist.covariance[35] = 0.1
        self.odom_pub.publish(odom)

        if self.publish_tf:
            tf_msg = TransformStamped()
            tf_msg.header.stamp = now.to_msg()
            tf_msg.header.frame_id = self.odom_frame
            tf_msg.child_frame_id = self.base_frame
            tf_msg.transform.translation.x = self.x
            tf_msg.transform.translation.y = self.y
            tf_msg.transform.translation.z = 0.0
            tf_msg.transform.rotation.x = qx
            tf_msg.transform.rotation.y = qy
            tf_msg.transform.rotation.z = qz
            tf_msg.transform.rotation.w = qw
            self.tf_broadcaster.sendTransform(tf_msg)

    def control_loop(self) -> None:
        if self.faulted:
            return

        now = self.get_clock().now()
        try:
            if self.command_is_stale():
                left_turn_s = 0.0
                right_turn_s = 0.0
            else:
                left_turn_s, right_turn_s = self.twist_to_wheel_turns(self.cmd_vx, self.cmd_wz)

            self.write_wheel_commands(left_turn_s, right_turn_s)
            self.update_odometry(now)

            self.error_check_countdown -= 1
            if self.error_check_countdown <= 0:
                self.error_check_countdown = self.error_check_period_ticks
                if self.check_all_axis_errors(raise_on_error=False):
                    self.get_logger().error("ODrive fault detected. Stopping and idling both axes.")
                    self.faulted = True
                    self.safe_stop(send_idle=True)
        except Exception as exc:
            self.get_logger().error(f"Control loop exception: {exc}")
            self.faulted = True
            self.safe_stop(send_idle=True)

    def safe_stop(self, send_idle: bool = False) -> None:
        if self.odrv is None or self.left_axis_obj is None or self.right_axis_obj is None:
            return

        try:
            self.write_wheel_commands(0.0, 0.0)
            time.sleep(0.05)
        except Exception as exc:
            self.get_logger().warn(f"Failed to write zero velocity during stop: {exc}")

        if send_idle:
            try:
                self.left_axis_obj.requested_state = AXIS_STATE_IDLE
                self.right_axis_obj.requested_state = AXIS_STATE_IDLE
            except Exception as exc:
                self.get_logger().warn(f"Failed to set IDLE during stop: {exc}")


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = ODriveBaseNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        if node is not None:
            node.get_logger().error(f"Fatal error: {exc}")
        else:
            print(f"Fatal error before node startup: {exc}")
    finally:
        if node is not None:
            node.safe_stop(send_idle=node.idle_on_shutdown)
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
