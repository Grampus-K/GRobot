# GRobot 酒店送物机器人底盘

这是一个基于 ROS2 的酒店送物机器人底盘工程。目前包含：

- `free_lidar`：FREE 系列单线激光雷达驱动，发布 `/scan`
- `grobot_odrive_base`：ODrive 差速底盘驱动，订阅 `/cmd_vel`，发布 `/odom` 和 `odom -> base_link`
- `grobot_description`：机器人 URDF/xacro 描述，发布 `base_link -> scan` 等机器人静态坐标关系

目标 TF 树：

```text
map -> odom -> base_link -> scan
```

当前第一阶段先完成：

```text
odom -> base_link -> scan
```

其中 `map -> odom` 后续由 SLAM 或 AMCL/Nav2 提供。

## Ubuntu 22.04 / ROS2 Humble 环境

先确保已经安装 ROS2 Humble，并加载 ROS 环境：

```bash
source /opt/ros/humble/setup.bash
```

安装基础开发工具：

```bash
sudo apt update
sudo apt install -y \
  python3-pip \
  python3-colcon-common-extensions \
  python3-rosdep
```

安装当前工程运行所需 ROS 功能包：

```bash
sudo apt install -y \
  ros-humble-xacro \
  ros-humble-robot-state-publisher \
  ros-humble-rviz2 \
  ros-humble-tf2-ros \
  ros-humble-tf2-tools
```

安装底盘 ODrive Python 工具：

```bash
sudo pip3 install odrive==0.5.1.post0
```

如果 ODrive USB 权限不足，执行：

```bash
odrivetool udev-setup
```

然后重新插拔 ODrive。

## 后续 Nav2 / 建图导航依赖

后续进入 SLAM 建图、定位和自主导航阶段时，建议继续安装：

```bash
sudo apt install -y \
  ros-humble-slam-toolbox \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-nav2-map-server \
  ros-humble-nav2-amcl \
  ros-humble-teleop-twist-keyboard
```

其中：

- `slam_toolbox`：用于手动遥控建图
- `navigation2` / `nav2_bringup`：Nav2 导航框架
- `nav2_map_server`：保存和加载地图
- `nav2_amcl`：基于已有地图定位
- `teleop_twist_keyboard`：早期测试时手动遥控底盘

## 构建工程

在 Ubuntu 上进入工作空间根目录：

```bash
cd ~/GRobot_ws
colcon build --symlink-install
source install/setup.bash
```

如果是新终端，记得重新 source：

```bash
source /opt/ros/humble/setup.bash
source ~/GRobot_ws/install/setup.bash
```

## 第一阶段：验证机器人坐标系

启动机器人描述：

```bash
ros2 launch grobot_description description.launch.py
```

检查 `base_link -> scan`：

```bash
ros2 run tf2_ros tf2_echo base_link scan
```

默认雷达安装参数：

- `lidar_x: 0.0`
- `lidar_y: 0.0`
- `lidar_z: 0.20`
- `lidar_yaw: 0.0`

如果实物雷达不在底盘中心，可以通过 launch 参数临时调整：

```bash
ros2 launch grobot_description description.launch.py lidar_x:=0.10 lidar_y:=0.0 lidar_z:=0.22 lidar_yaw:=0.0
```

确认实测位置后，再修改 `src/grobot_description/urdf/grobot.urdf.xacro` 里的默认值。

## 第一阶段：联合启动底盘和雷达

分别启动底盘、雷达和机器人描述：

```bash
ros2 launch grobot_odrive_base odrive_base.launch.py
ros2 launch free_lidar free_lidar_launch.py
ros2 launch grobot_description description.launch.py
```

检查话题：

```bash
ros2 topic echo /odom
ros2 topic hz /scan
ros2 topic echo /scan --once
```

检查 TF：

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link scan
```

如果这些都正常，第一阶段坐标系基础就搭好了。

## 手动底盘测试

低速前进测试：

```bash
ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.15}, angular: {z: 0.0}}"
```

低速旋转测试：

```bash
ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.3}}"
```

停止发布后，底盘节点会在 `cmd_timeout` 超时后自动下发零速度。

## 后续路线

建议按下面顺序继续推进：

1. 完成 `grobot_description` 实物尺寸校准
2. 新增 `grobot_bringup`，统一启动底盘、雷达和机器人描述
3. 使用 `slam_toolbox` 手动建图并保存地图
4. 新增 `grobot_navigation`，维护 Nav2 参数和导航 launch
5. 使用 RViz 测试单点导航
6. 使用 Nav2 `FollowWaypoints` 做简单航点任务

