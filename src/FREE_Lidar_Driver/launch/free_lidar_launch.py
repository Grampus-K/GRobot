from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    scanner_ip = LaunchConfiguration("scanner_ip")
    offset_angle = LaunchConfiguration("offset_angle")
    start_angle = LaunchConfiguration("start_angle")
    stop_angle = LaunchConfiguration("stop_angle")
    angle_scale = LaunchConfiguration("angle_scale")
    angle_anchor = LaunchConfiguration("angle_anchor")
    output_angle_min = LaunchConfiguration("output_angle_min")
    output_angle_max = LaunchConfiguration("output_angle_max")

    rviz_config_dir = os.path.join(
        get_package_share_directory("free_lidar"),
        "rviz",
        "free_lidar.rviz",
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "scanner_ip",
            default_value="192.168.10.7",
            description="Lidar Ethernet IP address",
        ),
        DeclareLaunchArgument(
            "offset_angle",
            default_value="-45",
            description="LaserScan angle offset in degrees. Front should point to +X in RViz.",
        ),
        DeclareLaunchArgument(
            "start_angle",
            default_value="-45",
            description="Raw lidar start angle in degrees",
        ),
        DeclareLaunchArgument(
            "stop_angle",
            default_value="225",
            description="Raw lidar stop angle in degrees",
        ),
        DeclareLaunchArgument(
            "angle_scale",
            default_value="2.0",
            description="Scale LaserScan angles around angle_anchor",
        ),
        DeclareLaunchArgument(
            "angle_anchor",
            default_value="0.0",
            description="Fixed angle for angle scaling, degrees",
        ),
        DeclareLaunchArgument(
            "output_angle_min",
            default_value="-120.0",
            description="Minimum published angle in ROS coordinates, degrees",
        ),
        DeclareLaunchArgument(
            "output_angle_max",
            default_value="120.0",
            description="Maximum published angle in ROS coordinates, degrees",
        ),
        Node(
            package="free_lidar",
            executable="free_lidar_node",
            name="free_lidar_node",
            output="screen",
            emulate_tty=True,
            respawn=True,
            parameters=[{
                "frame_id": "scan",
                "is_ethernet": True,
                "scanner_ip": scanner_ip,
                "scan_frequency": 30,
                "scan_resolution": 1000,
                "start_angle": ParameterValue(start_angle, value_type=int),
                "stop_angle": ParameterValue(stop_angle, value_type=int),
                "offset_angle": ParameterValue(offset_angle, value_type=int),
                "angle_scale": ParameterValue(angle_scale, value_type=float),
                "angle_anchor": ParameterValue(angle_anchor, value_type=float),
                "output_angle_min": ParameterValue(output_angle_min, value_type=float),
                "output_angle_max": ParameterValue(output_angle_max, value_type=float),
                "filter_switch": 0,
                "cluster_num": 10,
                "broad_filter_num": 20,
                "NOR_switch": 1,
                "is_reverse_postion": False,
                "topic_name": "/scan",
            }],
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            arguments=["-d", rviz_config_dir],
            output="screen",
        ),
    ])
