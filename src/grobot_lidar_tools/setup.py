from setuptools import find_packages, setup

package_name = "grobot_lidar_tools"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Grampus.K",
    maintainer_email="654369841@qq.com",
    description="Small lidar debugging tools for GRobot.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "front_intensity_monitor = grobot_lidar_tools.front_intensity_monitor:main",
        ],
    },
)
