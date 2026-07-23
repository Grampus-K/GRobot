from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import LaunchConfigAsBool


def generate_launch_description():
    scanner_ip = LaunchConfiguration("scanner_ip")
    lidar_x = LaunchConfiguration("lidar_x")
    lidar_y = LaunchConfiguration("lidar_y")
    lidar_z = LaunchConfiguration("lidar_z")
    lidar_yaw = LaunchConfiguration("lidar_yaw")
    lidar_rviz = LaunchConfigAsBool("lidar_rviz")

    description_launch = PathJoinSubstitution(
        [FindPackageShare("grobot_description"), "launch", "description.launch.py"]
    )
    base_launch = PathJoinSubstitution(
        [FindPackageShare("grobot_odrive_base"), "launch", "odrive_base.launch.py"]
    )
    lidar_launch = PathJoinSubstitution(
        [FindPackageShare("free_lidar"), "launch", "free_lidar_launch.py"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "scanner_ip",
                default_value="192.168.10.7",
                description="Lidar Ethernet IP address",
            ),
            DeclareLaunchArgument(
                "lidar_x",
                default_value="0.0",
                description="Lidar X offset from base_link, meters",
            ),
            DeclareLaunchArgument(
                "lidar_y",
                default_value="0.0",
                description="Lidar Y offset from base_link, meters",
            ),
            DeclareLaunchArgument(
                "lidar_z",
                default_value="0.20",
                description="Lidar Z offset from base_link, meters",
            ),
            DeclareLaunchArgument(
                "lidar_yaw",
                default_value="0.0",
                description="Lidar yaw relative to base_link, radians",
            ),
            DeclareLaunchArgument(
                "lidar_rviz",
                default_value="false",
                description="Start the lidar RViz config from free_lidar",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(description_launch),
                launch_arguments={
                    "lidar_x": lidar_x,
                    "lidar_y": lidar_y,
                    "lidar_z": lidar_z,
                    "lidar_yaw": lidar_yaw,
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(base_launch),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(lidar_launch),
                launch_arguments={
                    "scanner_ip": scanner_ip,
                    "rviz": lidar_rviz,
                }.items(),
            ),
        ]
    )
