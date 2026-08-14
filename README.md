# GRobot 酒店送物机器人底盘

基于 ROS2 Humble 的酒店送物机器人底盘工程，已完成实机底盘驱动、激光雷达、轮式里程计、IMU、Cartographer 建图与定位、Nav2 导航。

传感器：激光雷达 + 轮式里程计 + IMU。

## 构建

Ubuntu 22.04 + ROS2 Humble，每个新终端先加载环境：

```bash
source /opt/ros/humble/setup.bash
```

依赖（navigation2 及配套控制器，cartographer_ros 需源码编译）：

```bash
sudo apt install -y \
  ros-humble-xacro \
  ros-humble-robot-state-publisher \
  ros-humble-rviz2 \
  ros-humble-tf2-ros \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-nav2-mppi-controller \
  ros-humble-nav2-rotation-shim-controller \
  ros-humble-teleop-twist-keyboard
```

构建工作空间：

```bash
cd ~/GRobot
colcon build --symlink-install
source install/setup.bash
```

## 一、启动底盘

```bash
ros2 launch grobot_bringup robot.launch.py
```

一个命令同时启动：机器人描述（URDF）、ODrive 底盘驱动、激光雷达、IMU（含扫描畸变校正）。

常用启动参数（`robot.launch.py`）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `scanner_ip` | `192.168.10.7` | 雷达 IP |
| `lidar_range_max` | `15.0` | 雷达最大使用距离 |
| `lidar_filter_switch` | `1` | 雷达拖尾/孤立点滤波开关 |
| `intensity_min` | `0.0` | 最小强度阈值，滤玻璃噪声 |

底盘核心参数在 [base_params.yaml](src/grobot_odrive_base/config/base_params.yaml)：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `wheel_diameter` | `0.1725` | 轮径，影响里程计精度 |
| `track_width` | `0.375` | 轮距 |
| `max_linear_accel` | `0.5` | 最大线加速度 |
| `max_angular_accel` | `2.5` | 最大角加速度 |
| `cmd_timeout` | `0.5` | 无速度命令多久后自动停车 |

## 二、建图

先启动底盘，再另开终端启动建图：

```bash
ros2 launch grobot_mapping mapping.launch.py
```

用键盘遥控慢速移动，边走边建图：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

建图完成后保存 pbstream 地图：

```bash
mkdir -p ~/GRobot/maps
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState "{filename: '$HOME/GRobot/maps/hotel.pbstream'}"
```

建图参数在 [cartographer.lua](src/grobot_mapping/config/cartographer.lua)：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `TRAJECTORY_BUILDER_2D.max_range` | `20.0` | 雷达最大使用距离 |
| `TRAJECTORY_BUILDER_2D.submaps.num_range_data` | `80` | 子图帧数 |
| `TRAJECTORY_BUILDER_2D.motion_filter.max_distance_meters` | `0.05` | 节点间距，越小节点越密 |
| `POSE_GRAPH.constraint_builder.min_score` | `0.50` | 回环检测阈值，越小越易闭环 |

## 三、导航

先启动底盘，再启动导航（Cartographer 纯定位，加载 pbstream 地图）：

```bash
ros2 launch grobot_navigation navigation.launch.py
```

默认加载 `~/GRobot/maps/hotel.pbstream`，地图在别处时指定：

```bash
ros2 launch grobot_navigation navigation.launch.py pbstream_file:=/path/to/hotel.pbstream
```

启动后尽量让机器人停在建图原点附近，Cartographer 会通过全局扫描匹配自动定位；定位稳定后在 RViz 里用 `Nav2 Goal` 给目标点。

导航参数在 [nav2_params.yaml](src/grobot_navigation/config/nav2_params.yaml)：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `robot_radius` | `0.26` | 机器人半径，膨胀与规划安全余量 |
| `inflation_radius` | `0.80` | 障碍物膨胀半径 |
| `cost_scaling_factor` | `3.0` | 膨胀代价衰减系数 |
| `FollowPath.vx_max` | `1.20` | 最大线速度 |
| `FollowPath.wz_max` | `2.0` | 最大角速度 |

定位参数在 [cartographer_localization.lua](src/grobot_mapping/config/cartographer_localization.lua)：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `POSE_GRAPH.constraint_builder.global_localization_min_score` | `0.55` | 全局重定位匹配分数 |
| `pure_localization_trimmer.max_submaps_to_keep` | `5` | 保留子图数量 |

地图二值化阈值在 [navigation.launch.py](src/grobot_navigation/launch/navigation.launch.py) 的 `map_threshold` 节点（`threshold: 10`）：把 Cartographer 连续概率二值化为障碍/空闲，解决膨胀环缺失。
