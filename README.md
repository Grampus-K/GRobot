# GRobot 酒店送物机器人底盘

这是一个基于 ROS2 的酒店送物机器人底盘工程。目前包含：

- `free_lidar`：FREE 系列单线激光雷达驱动，发布 `/scan`
- `grobot_odrive_base`：ODrive 差速底盘驱动，订阅 `/cmd_vel`，发布 `/odom` 和 `odom -> base_link`
- `grobot_description`：机器人 URDF/xacro 描述，发布 `base_link -> scan` 等机器人静态坐标关系
- `grobot_bringup`：统一启动机器人描述、底盘驱动和雷达驱动
- `grobot_mapping`：基于 `slam_toolbox` 的手动建图启动和参数配置
- `grobot_navigation`：基于 Nav2 的定位和自主导航启动

目标 TF 树：

```text
map -> odom -> base_link -> scan
```

当前已完成第一阶段：

```text
odom -> base_link -> scan
```

其中 `map -> odom` 后续由 SLAM 或 AMCL/Nav2 提供。

## 机器人实测参数

- 外形：圆形底盘
- 外形直径：`0.505 m`
- 底盘实际高度：`0.30 m`
- Nav2 默认机器人半径：`0.2525 m`
- 轮子直径：`0.17 m`
- 轮距：`0.375 m`
- 轮子中心：位于 `base_link` 的 x 轴原点位置
- 雷达相对 `base_link` 的位置：`x=0.18 m`，`y=0.0 m`，`z=0.05 m`
- 雷达相对 `base_link` 的偏航角：`0.0 rad`，雷达正前方与机器人 `+X` 方向一致

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
cd ~/GRobot
colcon build --symlink-install
source install/setup.bash
```

如果是新终端，记得重新 source：

```bash
source /opt/ros/humble/setup.bash
source ~/GRobot/install/setup.bash
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

- `lidar_x: 0.18`
- `lidar_y: 0.0`
- `lidar_z: 0.05`
- `lidar_yaw: 0.0`

如果后续重新测量了雷达安装位置，可以通过 launch 参数临时覆盖：

```bash
ros2 launch grobot_description description.launch.py lidar_x:=0.18 lidar_y:=0.0 lidar_z:=0.05 lidar_yaw:=0.0
```

确认实测位置后，再修改 `src/grobot_description/urdf/grobot.urdf.xacro` 里的默认值。

## 第一阶段：联合启动底盘和雷达

推荐使用统一启动入口：

```bash
ros2 launch grobot_bringup robot.launch.py
```

这个 launch 会同时启动：

- `grobot_description`
- `grobot_odrive_base`
- `free_lidar`

如果雷达 IP 不是默认的 `192.168.10.7`，可以这样指定：

```bash
ros2 launch grobot_bringup robot.launch.py scanner_ip:=192.168.10.7
```

如果要临时调整雷达相对 `base_link` 的安装位置：

```bash
ros2 launch grobot_bringup robot.launch.py lidar_x:=0.18 lidar_y:=0.0 lidar_z:=0.05 lidar_yaw:=0.0
```

如果需要同时打开雷达 RViz 调试界面：

```bash
ros2 launch grobot_bringup robot.launch.py lidar_rviz:=true
```

也可以分别启动底盘、雷达和机器人描述：


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

## 第二阶段：手动建图

建图目标是让 `slam_toolbox` 根据 `/scan`、`odom -> base_link` 和 `base_link -> scan` 生成 `map -> odom`，形成完整 TF 树：

```text
map -> odom -> base_link -> scan
```

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

如果机器人主机没有显示器，或者不想打开 RViz：

```bash
ros2 launch grobot_mapping mapping.launch.py rviz:=false
```

再开一个终端，用键盘遥控底盘慢速移动：

```bash
source /opt/ros/humble/setup.bash
source ~/GRobot/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

建图时建议：

- 先在空旷区域低速直行、低速转弯
- 沿墙或走廊慢慢走，不要快速原地旋转
- 尽量闭环回到起点附近，让地图自动闭环
- 如果地图明显扭曲，先停下来检查轮式里程计方向、雷达方向和 TF

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

这两个文件后续会给 Nav2 定位和导航使用。确认地图可用后，可以提交到 Git 仓库：

```bash
git add maps/hotel_test_map.yaml maps/hotel_test_map.pgm
git commit -m "Add initial hotel test map"
git push origin main
```

如果 `slam_toolbox` 一直提示类似下面的消息：

```text
Message Filter dropping message: frame 'scan' ...
the timestamp on the message is earlier than all the data in the transform cache
```

优先检查雷达驱动是否使用当前 ROS 时间发布 `/scan`，然后重新 `colcon build` 并重新启动建图。

## 第三阶段：定位和导航

保存好地图后，启动导航：

```bash
ros2 launch grobot_navigation navigation.launch.py
```

默认会读取：

```text
~/GRobot/maps/hotel_test_map.yaml
```

如果你的地图文件在别的路径：

```bash
ros2 launch grobot_navigation navigation.launch.py map_file:=/path/to/your_map.yaml
```

推荐启动顺序：

```bash
ros2 launch grobot_bringup robot.launch.py
ros2 launch grobot_navigation navigation.launch.py
```

打开 RViz 后先做两件事：

1. 用 `2D Pose Estimate` 设定机器人初始位姿
2. 用 `Nav2 Goal` 点一个目标点测试导航

如果要关掉 RViz：

```bash
ros2 launch grobot_navigation navigation.launch.py rviz:=false
```

如果后续要做航点任务，可以先用多个 `Nav2 Goal` 验证路径规划和避障，再进入 `FollowWaypoints`。

说明一下：`grobot_description` 里同时提供了 `base_link` 和 `base_footprint`，其中 `base_footprint` 是 `base_link` 的固定子坐标系，主要是为了兼容 Nav2 的默认 frame 习惯。

如果你手动改过 `slam` 参数，记得在这个启动里保持定位模式，不要传小写 `false`。当前默认已经是 `False`。

`use_composition` 和 `use_respawn` 也保持大写布尔默认值，和 Humble 的 Nav2 启动脚本一致。

Nav2 默认使用圆形机器人模型，`grobot_navigation` 会把 `robot_radius` 覆盖成 `0.2525 m`。如果后续想额外留安全余量，可以启动时调大一些：

```bash
ros2 launch grobot_navigation navigation.launch.py robot_radius:=0.28
```

## 后续路线

建议按下面顺序继续推进：

1. 完成 `grobot_description` 实物尺寸校准
2. 使用 `grobot_bringup` 统一启动底盘、雷达和机器人描述
3. 使用 `grobot_mapping` 和 `slam_toolbox` 手动建图并保存地图
4. 使用 `grobot_navigation` 做定位和单点导航测试
5. 使用 RViz 测试单点导航
6. 使用 Nav2 `FollowWaypoints` 做简单航点任务
