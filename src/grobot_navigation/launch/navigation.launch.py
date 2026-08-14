from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    params_file = LaunchConfiguration("params_file")
    pbstream_file = LaunchConfiguration("pbstream_file")
    rviz = LaunchConfiguration("rviz")
    robot_radius = LaunchConfiguration("robot_radius")
    autostart = LaunchConfiguration("autostart")

    cartographer_config_dir = PathJoinSubstitution(
        [FindPackageShare("grobot_mapping"), "config"]
    )
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("nav2_bringup"), "rviz", "nav2_default_view.rviz"]
    )
    default_params_file = PathJoinSubstitution(
        [FindPackageShare("grobot_navigation"), "config", "nav2_params.yaml"]
    )
    default_pbstream_file = PathJoinSubstitution(
        [EnvironmentVariable("HOME"), "GRobot", "maps", "hotel.pbstream"]
    )

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key="",
        param_rewrites={
            "robot_radius": robot_radius,
        },
        convert_types=True,
    )

    declared_arguments = [
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("params_file", default_value=default_params_file),
        DeclareLaunchArgument(
            "pbstream_file",
            default_value=default_pbstream_file,
            description="Path to .pbstream file for Cartographer localization",
        ),
        DeclareLaunchArgument("rviz", default_value="true"),
        DeclareLaunchArgument("robot_radius", default_value="0.26"),
        DeclareLaunchArgument("autostart", default_value="true"),
    ]

    error_only = ["--ros-args", "--log-level", "ERROR"]

    cartographer_node = Node(
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
            "-configuration_basename", "cartographer_localization.lua",
            "-load_state_filename", pbstream_file,
            "--ros-args", "--log-level", "ERROR",
        ],
        remappings=[
            ("/scan", "/scan_corrected"),
            ("/imu", "/imu/data"),
        ],
    )

    occupancy_grid_node = Node(
        package="cartographer_ros",
        executable="cartographer_occupancy_grid_node",
        name="occupancy_grid_node",
        output="screen",
        parameters=[
            {"use_sim_time": use_sim_time},
            {"resolution": 0.05},
            {"publish_period_sec": 1.0},
        ],
        remappings=[
            ("/map", "/map_raw"),
        ],
        arguments=error_only,
    )

    # Threshold Cartographer's continuous probability map into binary 0/100
    # so Nav2 static_layer can recognise all occupied cells as obstacles.
    map_threshold_node = Node(
        package="grobot_odrive_base",
        executable="map_threshold",
        name="map_threshold",
        output="screen",
        parameters=[{
            "threshold": 10,
        }],
        arguments=error_only,
    )

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        output="screen",
        parameters=[{
            "use_sim_time": use_sim_time,
            "autostart": autostart,
            "node_names": [
                "controller_server",
                "smoother_server",
                "planner_server",
                "behavior_server",
                "bt_navigator",
                "waypoint_follower",
                "velocity_smoother",
            ],
        }],
        arguments=error_only,
    )

    controller_server = Node(
        package="nav2_controller",
        executable="controller_server",
        name="controller_server",
        output="screen",
        parameters=[configured_params],
        arguments=error_only,
    )

    smoother_server = Node(
        package="nav2_smoother",
        executable="smoother_server",
        name="smoother_server",
        output="screen",
        parameters=[configured_params],
        arguments=error_only,
    )

    planner_server = Node(
        package="nav2_planner",
        executable="planner_server",
        name="planner_server",
        output="screen",
        parameters=[configured_params],
        arguments=error_only,
    )

    behavior_server = Node(
        package="nav2_behaviors",
        executable="behavior_server",
        name="behavior_server",
        output="screen",
        parameters=[configured_params],
        arguments=error_only,
    )

    bt_navigator = Node(
        package="nav2_bt_navigator",
        executable="bt_navigator",
        name="bt_navigator",
        output="screen",
        parameters=[configured_params],
        arguments=error_only,
    )

    waypoint_follower = Node(
        package="nav2_waypoint_follower",
        executable="waypoint_follower",
        name="waypoint_follower",
        output="screen",
        parameters=[configured_params],
        arguments=error_only,
    )

    velocity_smoother = Node(
        package="nav2_velocity_smoother",
        executable="velocity_smoother",
        name="velocity_smoother",
        output="screen",
        parameters=[configured_params],
        arguments=error_only,
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2_navigation",
        arguments=["-d", rviz_config_file, "--ros-args", "--log-level", "ERROR"],
        output="screen",
        condition=IfCondition(rviz),
    )

    return LaunchDescription(
        declared_arguments
        + [
            cartographer_node,
            occupancy_grid_node,
            map_threshold_node,
            lifecycle_manager,
            controller_server,
            smoother_server,
            planner_server,
            behavior_server,
            bt_navigator,
            waypoint_follower,
            velocity_smoother,
            rviz_node,
        ]
    )
