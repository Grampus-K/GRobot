from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    channel_type = LaunchConfiguration("channel_type")
    serial_port = LaunchConfiguration("serial_port")
    serial_baudrate = LaunchConfiguration("serial_baudrate")
    scan_mode = LaunchConfiguration("scan_mode")
    inverted = LaunchConfiguration("inverted")
    angle_compensate = LaunchConfiguration("angle_compensate")
    scan_frequency = LaunchConfiguration("scan_frequency")
    base_diameter = LaunchConfiguration("base_diameter")
    base_height = LaunchConfiguration("base_height")
    lidar_x = LaunchConfiguration("lidar_x")
    lidar_y = LaunchConfiguration("lidar_y")
    lidar_z = LaunchConfiguration("lidar_z")
    lidar_yaw = LaunchConfiguration("lidar_yaw")

    description_launch = PathJoinSubstitution(
        [FindPackageShare("grobot_description"), "launch", "description.launch.py"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "channel_type",
                default_value="serial",
                description="RPLidar connection type",
            ),
            DeclareLaunchArgument(
                "serial_port",
                default_value="/dev/ttyUSB0",
                description="RPLidar serial device",
            ),
            DeclareLaunchArgument(
                "serial_baudrate",
                default_value="1000000",
                description="RPLidar serial baudrate",
            ),
            DeclareLaunchArgument(
                "scan_mode",
                default_value="DenseBoost",
                description="RPLidar scan mode",
            ),
            DeclareLaunchArgument(
                "inverted",
                default_value="false",
                description="Invert scan data",
            ),
            DeclareLaunchArgument(
                "angle_compensate",
                default_value="true",
                description="Enable angle compensation",
            ),
            DeclareLaunchArgument(
                "scan_frequency",
                default_value="10.0",
                description="RPLidar scan frequency, Hz",
            ),
            DeclareLaunchArgument(
                "base_diameter",
                default_value="0.505",
                description="Circular robot outer diameter, meters",
            ),
            DeclareLaunchArgument(
                "base_height",
                default_value="0.30",
                description="Robot base body height, meters",
            ),
            DeclareLaunchArgument(
                "lidar_x",
                default_value="0.18",
                description="Lidar X offset from base_link, meters",
            ),
            DeclareLaunchArgument(
                "lidar_y",
                default_value="0.0",
                description="Lidar Y offset from base_link, meters",
            ),
            DeclareLaunchArgument(
                "lidar_z",
                default_value="0.05",
                description="Lidar Z offset from base_link, meters",
            ),
            DeclareLaunchArgument(
                "lidar_yaw",
                default_value="0.0",
                description="Lidar yaw relative to base_link, radians",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(description_launch),
                launch_arguments={
                    "base_diameter": base_diameter,
                    "base_height": base_height,
                    "lidar_x": lidar_x,
                    "lidar_y": lidar_y,
                    "lidar_z": lidar_z,
                    "lidar_yaw": lidar_yaw,
                }.items(),
            ),
            Node(
                package="rplidar_ros",
                executable="rplidar_node",
                name="rplidar_node",
                output="screen",
                parameters=[
                    {
                        "channel_type": channel_type,
                        "serial_port": serial_port,
                        "serial_baudrate": ParameterValue(serial_baudrate, value_type=int),
                        "frame_id": "scan",
                        "inverted": ParameterValue(inverted, value_type=bool),
                        "angle_compensate": ParameterValue(angle_compensate, value_type=bool),
                        "scan_mode": scan_mode,
                        "scan_frequency": ParameterValue(scan_frequency, value_type=float),
                        "topic_name": "/scan",
                    }
                ],
            ),
        ]
    )
