# GRobot 酒店送物机器人底盘

这是一个基于 ROS2 Humble 的酒店送物机器人底盘工程，当前已经完成实机底盘驱动、激光雷达、轮式里程计、手动建图、AMCL 定位和 Nav2 单点导航验证。

工程主要包含：

- `free_lidar`：FREE 系列单线激光雷达驱动，发布 `/scan`
- `grobot_odrive_base`：ODrive 差速底盘驱动，订阅 `/cmd_vel`，发布 `/odom` 和 `odom -> base_link`
- `grobot_description`：机器人 URDF/xacro 描述，发布 `base_link -> scan` 等静态 TF
- `grobot_bringup`：统一启动机器人描述、底盘驱动和雷达驱动
- `grobot_mapping`：基于 `slam_toolbox` 的手动建图启动、参数和 RViz 配置
- `grobot_navigation`：基于 Nav2 的地图加载、AMCL 定位和自主导航启动

此外，实机上预留了 Orbbec 单目结构光相机的二进制安装和启动说明；当前相机暂未接入导航主流程。

目标 TF 树：

```text
map -> odom -> base_link -> scan
```

其中 `odom -> base_link` 由底盘轮式里程计提供，`base_link -> scan` 由机器人描述提供，`map -> odom` 在建图时由 `slam_toolbox` 提供，在导航定位时由 AMCL/Nav2 提供。

## 实测参数

- 外形：圆形底盘
- 外形直径：`0.505 m`
- 底盘实际高度：`0.30 m`
- Nav2 默认机器人半径：`0.26 m`
- 轮子直径：`0.1725 m`
- 轮距：`0.375 m`
- 轮子中心：位于 `base_link` 的 x 轴原点位置
- 雷达相对 `base_link` 的位置：`x=0.18 m`，`y=0.0 m`，`z=0.05 m`
- 雷达相对 `base_link` 的偏航角：`0.0 rad`，雷达正前方与机器人 `+X` 方向一致

相关参数文件：

- 底盘参数：[base_params.yaml](src/grobot_odrive_base/config/base_params.yaml)
- 机器人模型：[grobot.urdf.xacro](src/grobot_description/urdf/grobot.urdf.xacro)
- Nav2 参数：[nav2_params.yaml](src/grobot_navigation/config/nav2_params.yaml)

## 运行环境

实机运行环境：

- Ubuntu 22.04
- ROS2 Humble
- ODrive v3.6
- FREE 系列单线激光雷达
- Orbbec 单目结构光相机，可选，当前暂未参与导航

先确保已经安装 ROS2 Humble，并在每个新终端加载 ROS 环境：

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

安装工程运行需要的 ROS 功能包：

```bash
sudo apt install -y \
  ros-humble-xacro \
  ros-humble-robot-state-publisher \
  ros-humble-rviz2 \
  ros-humble-tf2-ros \
  ros-humble-tf2-tools \
  ros-humble-slam-toolbox \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-nav2-map-server \
  ros-humble-nav2-amcl \
  ros-humble-teleop-twist-keyboard
```

安装 ODrive Python 工具：

```bash
sudo pip3 install odrive==0.5.1.post0
```

如果 ODrive USB 权限不足，执行：

```bash
odrivetool udev-setup
```

然后重新插拔 ODrive。

### 可选：Orbbec 相机二进制安装

本工程当前暂不依赖 Orbbec 相机完成导航，但实机已经预留单目结构光相机。这里记录的是二进制安装方式，不需要把 `OrbbecSDK_ROS2` 源码放进当前工作空间编译。

安装 Orbbec ROS2 wrapper 相关依赖和二进制包：

```bash
sudo apt update
sudo apt install -y \
  libgflags-dev \
  nlohmann-json3-dev \
  libdw-dev \
  libssl-dev \
  mesa-utils \
  libgl1 \
  libgoogle-glog-dev \
  ros-humble-image-transport \
  ros-humble-image-transport-plugins \
  ros-humble-compressed-image-transport \
  ros-humble-image-publisher \
  ros-humble-camera-info-manager \
  ros-humble-diagnostic-updater \
  ros-humble-diagnostic-msgs \
  ros-humble-statistics-msgs \
  ros-humble-backward-ros \
  ros-humble-orbbec-camera \
  ros-humble-orbbec-description
```

安装 Orbbec 相机 udev 规则：

```bash
sudo cp /opt/ros/$ROS_DISTRO/share/orbbec_camera/udev/99-obsensor-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

执行后重新插拔相机。如果没有设置 `$ROS_DISTRO`，也可以把路径中的 `$ROS_DISTRO` 换成 `humble`。

检查相机是否识别：

```bash
ros2 run orbbec_camera list_devices_node
```

启动 Astra 系列相机：

```bash
ros2 launch orbbec_camera astra.launch.py
```

相机启动后可用下面命令检查话题：

```bash
ros2 topic list | grep camera
```

## 构建

在 Ubuntu 上进入工作空间根目录：

```bash
cd ~/GRobot
colcon build --symlink-install
source install/setup.bash
```

新终端建议固定执行：

```bash
source /opt/ros/humble/setup.bash
source ~/GRobot/install/setup.bash
```

## 启动机器人本体

推荐使用统一启动入口：

```bash
ros2 launch grobot_bringup robot.launch.py
```

这个 launch 会同时启动：

- `grobot_description`
- `grobot_odrive_base`
- `free_lidar`

如果雷达 IP 不是默认的 `192.168.10.7`，可以启动时指定：

```bash
ros2 launch grobot_bringup robot.launch.py scanner_ip:=192.168.10.7
```

当前雷达默认开启驱动自带拖尾/孤立点滤波，并把 `/scan` 最大距离限制为 `15.0 m`，用于降低玻璃反射和远距离异常点对定位的影响。如需现场 A/B 测试，可以临时覆盖：

```bash
ros2 launch grobot_bringup robot.launch.py lidar_filter_switch:=0 lidar_range_max:=25.0
```

如果需要打开雷达 RViz 调试界面：

```bash
ros2 launch grobot_bringup robot.launch.py lidar_rviz:=true
```

也可以分别启动底盘、雷达和机器人描述：

```bash
ros2 launch grobot_odrive_base odrive_base.launch.py
ros2 launch free_lidar free_lidar_launch.py
ros2 launch grobot_description description.launch.py
```

常用检查命令：

```bash
ros2 topic echo /odom
ros2 topic hz /scan
ros2 topic echo /scan --once
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link scan
```

## 手动底盘测试

`/cmd_vel` 是连续速度命令，测试时建议按固定频率发布。低速前进：

```bash
ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.15}, angular: {z: 0.0}}"
```

低速旋转：

```bash
ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.3}}"
```

停止发布后，底盘节点会在 `cmd_timeout` 超时后自动下发零速度。当前底盘参数在 [base_params.yaml](src/grobot_odrive_base/config/base_params.yaml) 中配置，包括轮径、轮距、左右轮方向、速度限制和 ODrive 电压保护。

## 建图

先启动机器人本体：

```bash
ros2 launch grobot_bringup robot.launch.py
```

另开一个终端启动建图：

```bash
source /opt/ros/humble/setup.bash
source ~/GRobot/install/setup.bash
ros2 launch grobot_mapping mapping.launch.py
```

如果不需要打开 RViz：

```bash
ros2 launch grobot_mapping mapping.launch.py rviz:=false
```

再开一个终端，用键盘遥控底盘慢速移动：

```bash
source /opt/ros/humble/setup.bash
source ~/GRobot/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

建图建议：

- 先在空旷区域低速直行、低速转弯
- 沿墙或走廊慢慢走，不要快速原地旋转
- 尽量闭环回到起点附近，让地图自动闭环
- 如果地图明显扭曲，优先检查轮式里程计方向、雷达方向和 TF

检查建图输出：

```bash
ros2 topic echo /map --once
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo odom base_link
```

保存地图：

```bash
mkdir -p ~/GRobot/maps
ros2 run nav2_map_server map_saver_cli -f ~/GRobot/maps/hotel_test_map
```

保存成功后会生成：

```text
~/GRobot/maps/hotel_test_map.yaml
~/GRobot/maps/hotel_test_map.pgm
```

如果 `slam_toolbox` 一直提示类似下面的消息：

```text
Message Filter dropping message: frame 'scan' ...
the timestamp on the message is earlier than all the data in the transform cache
```

优先检查雷达驱动是否使用当前 ROS 时间发布 `/scan`，然后重新 `colcon build` 并重新启动建图。

## 导航

推荐启动顺序：

```bash
ros2 launch grobot_bringup robot.launch.py
ros2 launch grobot_navigation navigation.launch.py
```

导航默认读取：

```text
~/GRobot/maps/hotel_test_map.yaml
```

如果地图文件在别的路径：

```bash
ros2 launch grobot_navigation navigation.launch.py map_file:=/path/to/your_map.yaml
```

打开 RViz 后先做两件事：

1. 用 `2D Pose Estimate` 设定机器人初始位姿
2. 用 `Nav2 Goal` 点一个目标点测试导航

如果不需要打开 RViz：

```bash
ros2 launch grobot_navigation navigation.launch.py rviz:=false
```

Nav2 默认使用项目内参数文件：

```text
src/grobot_navigation/config/nav2_params.yaml
```

当前这份参数以 ROS2 Humble 的 Nav2 官方默认参数为基准，只把默认 `robot_radius` 改成 `0.26 m`，比实测半径 `0.2525 m` 稍微留了一点余量。如果后续想额外留安全余量，可以启动时继续调大：

```bash
ros2 launch grobot_navigation navigation.launch.py robot_radius:=0.28
```

机器人当前没有后视传感器，`grobot_navigation` 默认加载项目内的无倒车恢复行为树：

```text
src/grobot_navigation/behavior_trees/navigate_to_pose_no_backup.xml
src/grobot_navigation/behavior_trees/navigate_through_poses_no_backup.xml
```

这两份行为树保留清理代价地图、原地旋转和等待恢复动作，但移除了 Nav2 默认行为树里的 `BackUp` 恢复节点。键盘手动控制不受这个限制。

注意：`grobot_description` 里同时提供了 `base_link` 和 `base_footprint`，其中 `base_footprint` 是 `base_link` 的固定子坐标系，主要用于兼容 Nav2 的默认 frame 习惯。

## 航点任务

单点导航稳定后，可以继续使用 Nav2 的航点能力做简单送物路线。建议先在 RViz 中连续测试多个 `Nav2 Goal`，确认定位、路径规划和避障行为稳定，再接入 `FollowWaypoints` 或上层任务节点。

后续如果要加入酒店送物业务逻辑，可以在 Nav2 之上继续扩展：

- 航点列表管理
- 房间号到地图点位的映射
- 电梯、闸机或门禁交互
- 到达后的语音/屏幕提示
- 异常恢复和人工接管

## 常用排查

检查话题频率：

```bash
ros2 topic hz /cmd_vel
ros2 topic hz /odom
ros2 topic hz /scan
```

检查导航时的速度命令：

```bash
ros2 topic echo /cmd_vel
```

如果机器人 yaw 频繁摆动，先判断是 Nav2 命令问题还是底盘反馈问题：

- `/cmd_vel.angular.z` 频繁正负跳动：优先检查 Nav2 局部控制器、路径和代价地图
- `/cmd_vel.angular.z` 平滑，但 `/odom.twist.twist.angular.z` 抖动：优先检查 ODrive 速度环、轮胎打滑、编码器反馈和机械间隙

检查 TF：

```bash
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link scan
```

检查 AMCL 是否已经输出定位：

```bash
ros2 topic echo /amcl_pose --once
```

如果 RViz 里看不到雷达或地图，常见原因包括：

- 没有启动 `grobot_bringup`
- 没有 source 当前工作空间
- `/scan` QoS 与 RViz 显示配置不一致
- TF 缺失或时间戳异常
- 地图文件路径不正确

## Git 同步

Windows 端修改并推送后，Ubuntu 实机端同步：

```bash
cd ~/GRobot
git pull origin main
colcon build --symlink-install
source install/setup.bash
```

如果有新的地图文件需要纳入仓库：

```bash
git add maps/hotel_test_map.yaml maps/hotel_test_map.pgm
git commit -m "Add hotel test map"
git push origin main
```

多人协作时建议每次修改前先拉取最新代码：

```bash
git pull origin main
```

修改完成后再提交并推送：

```bash
git status
git add <changed-files>
git commit -m "Describe your change"
git push origin main
```
