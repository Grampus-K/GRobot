from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    package_share = get_package_share_directory("grobot_odrive_base")
    params_file = os.path.join(package_share, "config", "base_params.yaml")

    return LaunchDescription(
        [
            Node(
                package="grobot_odrive_base",
                executable="odrive_base_node",
                name="odrive_base_node",
                output="screen",
                parameters=[params_file],
            )
        ]
    )
