from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_description_file = PathJoinSubstitution(
        [FindPackageShare("grobot_description"), "urdf", "grobot.urdf.xacro"]
    )

    declared_arguments = [
        DeclareLaunchArgument("base_diameter", default_value="0.505"),
        DeclareLaunchArgument("base_height", default_value="0.30"),
        DeclareLaunchArgument("wheel_radius", default_value="0.08625"),
        DeclareLaunchArgument("wheel_width", default_value="0.045"),
        DeclareLaunchArgument("track_width", default_value="0.375"),
        DeclareLaunchArgument("lidar_x", default_value="0.18"),
        DeclareLaunchArgument("lidar_y", default_value="0.0"),
        DeclareLaunchArgument("lidar_z", default_value="0.05"),
        DeclareLaunchArgument("lidar_yaw", default_value="0.0"),
        DeclareLaunchArgument("imu_x", default_value="0.0"),
        DeclareLaunchArgument("imu_y", default_value="0.0"),
        DeclareLaunchArgument("imu_z", default_value="0.10"),
        DeclareLaunchArgument("imu_roll", default_value="0.0"),
        DeclareLaunchArgument("imu_pitch", default_value="0.0"),
        DeclareLaunchArgument("imu_yaw", default_value="0.0"),
    ]

    robot_description = {
        "robot_description": Command(
            [
                "xacro ",
                robot_description_file,
                " base_diameter:=",
                LaunchConfiguration("base_diameter"),
                " base_height:=",
                LaunchConfiguration("base_height"),
                " wheel_radius:=",
                LaunchConfiguration("wheel_radius"),
                " wheel_width:=",
                LaunchConfiguration("wheel_width"),
                " track_width:=",
                LaunchConfiguration("track_width"),
                " lidar_x:=",
                LaunchConfiguration("lidar_x"),
                " lidar_y:=",
                LaunchConfiguration("lidar_y"),
                " lidar_z:=",
                LaunchConfiguration("lidar_z"),
                " lidar_yaw:=",
                LaunchConfiguration("lidar_yaw"),
                " imu_x:=",
                LaunchConfiguration("imu_x"),
                " imu_y:=",
                LaunchConfiguration("imu_y"),
                " imu_z:=",
                LaunchConfiguration("imu_z"),
                " imu_roll:=",
                LaunchConfiguration("imu_roll"),
                " imu_pitch:=",
                LaunchConfiguration("imu_pitch"),
                " imu_yaw:=",
                LaunchConfiguration("imu_yaw"),
            ]
        )
    }

    return LaunchDescription(
        declared_arguments
        + [
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[robot_description],
            )
        ]
    )
