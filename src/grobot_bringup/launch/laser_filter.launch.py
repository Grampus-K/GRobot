from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params_file = PathJoinSubstitution(
        [FindPackageShare("grobot_bringup"), "config", "laser_filter.yaml"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "input_topic",
                default_value="/scan_corrected",
                description="Input scan topic",
            ),
            DeclareLaunchArgument(
                "output_topic",
                default_value="/scan_filtered",
                description="Output filtered scan topic",
            ),
            Node(
                package="laser_filters",
                executable="scan_to_scan_filter_chain",
                name="laser_filter",
                output="screen",
                parameters=[
                    params_file,
                    {
                        "input_topic": LaunchConfiguration("input_topic"),
                        "output_topic": LaunchConfiguration("output_topic"),
                    },
                ],
            ),
        ]
    )
