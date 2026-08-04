from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    rviz = LaunchConfiguration("rviz")

    cartographer_config_dir = PathJoinSubstitution(
        [FindPackageShare("grobot_mapping"), "config"]
    )
    configuration_basename = "cartographer.lua"
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("grobot_mapping"), "rviz", "mapping.rviz"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="Use simulation clock if true",
            ),
            DeclareLaunchArgument(
                "rviz",
                default_value="true",
                description="Start RViz with the mapping display config",
            ),
            Node(
                package="cartographer_ros",
                executable="cartographer_node",
                name="cartographer_node",
                output="screen",
                parameters=[
                    {"use_sim_time": use_sim_time},
                    {
                        "qos_overrides./imu/data.subscription.reliability": "reliable",
                    },
                ],
                arguments=[
                    "-configuration_directory", cartographer_config_dir,
                    "-configuration_basename", configuration_basename,
                ],
                remappings=[
                    ("/scan", "/scan_filtered"),
                    ("/imu", "/imu/data"),
                ],
            ),
            Node(
                package="cartographer_ros",
                executable="cartographer_occupancy_grid_node",
                name="occupancy_grid_node",
                output="screen",
                parameters=[
                    {"use_sim_time": use_sim_time},
                    {"resolution": 0.05},
                    {"publish_period_sec": 1.0},
                ],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2_mapping",
                arguments=["-d", rviz_config_file],
                output="screen",
                condition=IfCondition(rviz),
            ),
        ]
    )
