from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    namespace = LaunchConfiguration("namespace")
    map_file = LaunchConfiguration("map_file")
    params_file = LaunchConfiguration("params_file")
    use_sim_time = LaunchConfiguration("use_sim_time")
    autostart = LaunchConfiguration("autostart")
    use_composition = LaunchConfiguration("use_composition")
    rviz = LaunchConfiguration("rviz")

    default_map_file = PathJoinSubstitution(
        [EnvironmentVariable("HOME"), "GRobot", "maps", "hotel_test_map.yaml"]
    )
    default_params_file = PathJoinSubstitution(
        [FindPackageShare("nav2_bringup"), "params", "nav2_params.yaml"]
    )
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("nav2_bringup"), "rviz", "nav2_default_view.rviz"]
    )
    bringup_launch_file = PathJoinSubstitution(
        [FindPackageShare("nav2_bringup"), "launch", "bringup_launch.py"]
    )

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites={
            "use_sim_time": use_sim_time,
            "base_frame_id": "base_link",
            "robot_base_frame": "base_link",
            "odom_frame_id": "odom",
            "global_frame_id": "map",
            "scan_topic": "/scan",
        },
        convert_types=True,
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "namespace",
                default_value="",
                description="Top-level namespace for Nav2",
            ),
            DeclareLaunchArgument(
                "map_file",
                default_value=default_map_file,
                description="Path to the saved occupancy grid map",
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=default_params_file,
                description="Path to the Nav2 parameter file",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="Use simulation clock if true",
            ),
            DeclareLaunchArgument(
                "autostart",
                default_value="true",
                description="Automatically activate Nav2 lifecycle nodes",
            ),
            DeclareLaunchArgument(
                "use_composition",
                default_value="false",
                description="Use component composition if true",
            ),
            DeclareLaunchArgument(
                "rviz",
                default_value="true",
                description="Start RViz with the Nav2 display config",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(bringup_launch_file),
                launch_arguments={
                    "namespace": namespace,
                    "map": map_file,
                    "use_sim_time": use_sim_time,
                    "params_file": configured_params,
                    "autostart": autostart,
                    "use_composition": use_composition,
                }.items(),
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2_navigation",
                arguments=["-d", rviz_config_file],
                output="screen",
                condition=IfCondition(rviz),
            ),
        ]
    )
