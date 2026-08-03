from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
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
    ]

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
    )

    return LaunchDescription(declared_arguments + [imu_node])
