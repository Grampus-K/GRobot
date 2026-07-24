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
    slam = LaunchConfiguration("slam")
    use_sim_time = LaunchConfiguration("use_sim_time")
    autostart = LaunchConfiguration("autostart")
    use_composition = LaunchConfiguration("use_composition")
    use_respawn = LaunchConfiguration("use_respawn")
    rviz = LaunchConfiguration("rviz")
    robot_radius = LaunchConfiguration("robot_radius")

    default_map_file = PathJoinSubstitution(
        [EnvironmentVariable("HOME"), "GRobot", "maps", "hotel_test_map.yaml"]
    )
    default_params_file = PathJoinSubstitution(
        [FindPackageShare("grobot_navigation"), "config", "nav2_params.yaml"]
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
            "robot_radius": robot_radius,
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
                "slam",
                default_value="False",
                description="Run SLAM instead of localization",
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
                default_value="False",
                description="Use component composition if true",
            ),
            DeclareLaunchArgument(
                "use_respawn",
                default_value="False",
                description="Respawn nodes if they crash",
            ),
            DeclareLaunchArgument(
                "rviz",
                default_value="true",
                description="Start RViz with the Nav2 display config",
            ),
            DeclareLaunchArgument(
                "robot_radius",
                default_value="0.26",
                description="Circular robot radius used by Nav2 costmaps, meters",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(bringup_launch_file),
                launch_arguments={
                    "namespace": namespace,
                    "map": map_file,
                    "slam": slam,
                    "use_sim_time": use_sim_time,
                    "params_file": configured_params,
                    "autostart": autostart,
                    "use_composition": use_composition,
                    "use_respawn": use_respawn,
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
