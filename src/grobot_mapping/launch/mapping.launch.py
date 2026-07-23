from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    params_file = LaunchConfiguration("params_file")
    rviz = LaunchConfiguration("rviz")

    default_params_file = PathJoinSubstitution(
        [FindPackageShare("grobot_mapping"), "config", "slam_toolbox.yaml"]
    )
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
                "params_file",
                default_value=default_params_file,
                description="Full path to the slam_toolbox parameter file",
            ),
            DeclareLaunchArgument(
                "rviz",
                default_value="true",
                description="Start RViz with the mapping display config",
            ),
            Node(
                package="slam_toolbox",
                executable="async_slam_toolbox_node",
                name="slam_toolbox",
                output="screen",
                parameters=[
                    params_file,
                    {"use_sim_time": use_sim_time},
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
