from glob import glob
from setuptools import find_packages, setup

package_name = "grobot_odrive_base"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Ke",
    maintainer_email="ke@example.com",
    description="ROS2 differential drive base driver for GRobot using ODrive over USB.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "odrive_base_node = grobot_odrive_base.odrive_base_node:main",
            "imu_scan_corrector = grobot_odrive_base.imu_scan_corrector:main",
            "front_intensity = grobot_odrive_base.front_intensity:main",
            "scan_relay = grobot_odrive_base.scan_relay:main",
        ],
    },
)
