from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params_file = PathJoinSubstitution(
        [FindPackageShare("grobot_bringup"), "config", "imu_params.yaml"]
    )

    declared_arguments = [
        DeclareLaunchArgument(
            "imu_port",
            default_value="/dev/imu_usb",
            description="IMU serial port",
        ),
        DeclareLaunchArgument(
            "imu_baudrate",
            default_value="230400",
            description="IMU serial baudrate",
        ),
        DeclareLaunchArgument(
            "imu_protocol",
            default_value="TTL_STD",
            description="IMU protocol: TTL_STD, TTL_HIGH, CAN_STD, CAN_HIGH, RS485_STD, RS485_HIGH",
        ),
        DeclareLaunchArgument(
            "imu_modbus_id",
            default_value="0x50",
            description="Modbus slave ID (RS485 mode only)",
        ),
        DeclareLaunchArgument(
            "enable_scan_corrector",
            default_value="true",
            description="Enable IMU-based scan distortion correction. Set to false to bypass for debugging rotation drift.",
        ),
    ]

    error_only = ["--ros-args", "--log-level", "ERROR"]

    imu_node = Node(
        package="wit_ros2_imu",
        executable="wit_ros2_imu",
        name="imuDriverNode",
        output="screen",
        parameters=[
            params_file,
            {
                "port": LaunchConfiguration("imu_port"),
                "baudrate": LaunchConfiguration("imu_baudrate"),
                "protocol": LaunchConfiguration("imu_protocol"),
                "modbusID": LaunchConfiguration("imu_modbus_id"),
            },
        ],
        arguments=error_only,
    )

    # IMU-based scan distortion corrector
    corrector_node = Node(
        package="grobot_odrive_base",
        executable="imu_scan_corrector",
        name="imu_scan_corrector",
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_scan_corrector")),
        arguments=error_only,
    )

    # When corrector is disabled, relay /scan → /scan_corrected so
    # Cartographer and Nav2 still have data on /scan_corrected
    relay_node = Node(
        package="grobot_odrive_base",
        executable="scan_relay",
        name="scan_relay",
        output="screen",
        condition=UnlessCondition(LaunchConfiguration("enable_scan_corrector")),
        arguments=error_only,
    )

    return LaunchDescription(declared_arguments + [imu_node, corrector_node, relay_node])
