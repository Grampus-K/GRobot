# FREE Lidar ROS2 Driver

这是用于富锐光电 FREE 系列单线激光雷达的 ROS2 驱动整理版。当前工程已按 C200 网口雷达调通，默认通过以太网连接雷达 `192.168.10.7`，发布 `sensor_msgs/msg/LaserScan` 到 `/scan`。

当前版本只编译网口驱动，不依赖串口 `serial` 库。

## 当前稳定配置

当前这台 C200 雷达已验证的稳定参数如下：

| 参数 | 当前值 | 说明 |
| --- | --- | --- |
| `scanner_ip` | `192.168.10.7` | 雷达 IP |
| `topic_name` | `/scan` | LaserScan 输出话题 |
| `frame_id` | `scan` | LaserScan 消息坐标系 |
| `scan_frequency` | `30` | 下发给雷达的扫描配置；实际 `/scan` 频率约 15Hz |
| `scan_resolution` | `1000` | 雷达配置分辨率，1000 表示 0.1 度 |
| `start_angle` | `-45` | 雷达硬件接受的原始起始角度，不建议随意改 |
| `stop_angle` | `225` | 雷达硬件接受的原始停止角度，不建议随意改 |
| `offset_angle` | `-45` | 坐标系整体旋转，当前安装下正前方对齐 ROS `+X` |
| `angle_scale` | `2.0` | 角度映射缩放，修正 RViz 中角度被压缩的问题 |
| `angle_anchor` | `0.0` | 角度缩放中心，0 度对应 ROS `+X` |
| `output_angle_min` | `-175.0` | 发布到 `/scan` 的最小角度，单位度 |
| `output_angle_max` | `175.0` | 发布到 `/scan` 的最大角度，单位度 |

坐标约定：

```text
X / 0度      机器人正前方
+Y / +90度   机器人左侧
-Y / -90度   机器人右侧
180度        机器人后方
```

## 网络设置

雷达默认 IP 为：

```text
192.168.10.7
```

Ubuntu 有线网卡需要和雷达在同一个网段。推荐把连接雷达的有线网卡设置成静态 IP：

```text
IP:      192.168.10.100
Mask:    255.255.255.0
Gateway: 留空即可
DNS:     留空即可
```

设置好后可以测试：

```bash
ping 192.168.10.7
```

能 ping 通之后再启动 ROS2 驱动。

## 编译

把驱动放在 ROS2 工作空间的 `src` 下，例如：

```bash
~/GRobot_ws/src/FREE_Lidar_Driver
```

编译：

```bash
cd ~/GRobot_ws
rm -rf build/free_lidar install/free_lidar
colcon build --packages-select free_lidar
source install/setup.bash
```

如果只改了 launch 或 README，不一定需要重新编译；如果改了 `src` 或 `include` 里的 C++ 文件，需要重新编译。

## 启动

默认启动：

```bash
ros2 launch free_lidar free_lidar_launch.py
```

默认会同时启动：

- `free_lidar_node`
- `rviz2`

如果不想启动 RViz，可以复制 launch 文件自行删掉 RViz 节点，或者后续单独做一个无 RViz 的 launch。

## 检查输出

查看话题：

```bash
ros2 topic list | grep scan
```

查看频率：

```bash
ros2 topic hz /scan
```

当前稳定状态下，实际 `/scan` 频率约为 15Hz。这个频率用于 Nav2 通常已经够用，不建议为了追 30Hz 牺牲稳定性。

查看角度：

```bash
ros2 topic echo /scan --once | grep -E "angle_min|angle_max|angle_increment|scan_time"
```

当前默认输出范围约为：

```text
angle_min: -3.05
angle_max:  3.05
```

也就是大约 `-175度` 到 `+175度`。

## 角度裁剪

角度裁剪只影响发布到 `/scan` 的输出，不会改雷达底层扫描配置。

只保留前方 240 度：

```bash
ros2 launch free_lidar free_lidar_launch.py output_angle_min:=-120 output_angle_max:=120
```

只保留前方 180 度：

```bash
ros2 launch free_lidar free_lidar_launch.py output_angle_min:=-90 output_angle_max:=90
```

只保留前方 120 度：

```bash
ros2 launch free_lidar free_lidar_launch.py output_angle_min:=-60 output_angle_max:=60
```

如果要永久修改默认裁剪范围，改 `launch/free_lidar_launch.py` 里的：

```python
DeclareLaunchArgument(
    "output_angle_min",
    default_value="-175.0",
)

DeclareLaunchArgument(
    "output_angle_max",
    default_value="175.0",
)
```

## 坐标和角度校准

当前已验证：

```bash
offset_angle:=-45
angle_scale:=2.0
angle_anchor:=0.0
```

含义：

- `offset_angle` 负责整体旋转坐标系。
- `angle_scale` 负责修正角度压缩。
- `angle_anchor=0.0` 表示以正前方为中心缩放，保证正前方不会被缩放带偏。

如果安装位置变化，优先调 `offset_angle`：

```bash
ros2 launch free_lidar free_lidar_launch.py offset_angle:=-40
```

如果左侧或右侧角度仍有比例误差，再微调 `angle_scale`：

```bash
ros2 launch free_lidar free_lidar_launch.py angle_scale:=1.9
ros2 launch free_lidar free_lidar_launch.py angle_scale:=2.1
```

不要随意改 `start_angle` 和 `stop_angle`。这两个参数会下发到雷达硬件；之前测试过 C200 不接受 `-130` 到 `220`，会报：

```text
Set scan angle failed!
```

## Nav2 适配

当前 `/scan` 已经是标准 `sensor_msgs/msg/LaserScan`，可以用于 Nav2。一般不需要再改驱动代码，但需要确认下面几件事。

### 1. TF 必须连通

`/scan` 的 `frame_id` 默认是：

```text
scan
```

Nav2 的 costmap 需要能从机器人底盘坐标系找到雷达坐标系，例如：

```text
map -> odom -> base_link -> scan
```

如果你的机器人底盘坐标系是 `base_link`，可以先用静态 TF 测试：

```bash
ros2 run tf2_ros static_transform_publisher 0 0 0.2 0 0 0 base_link scan
```

实际机器人上应该把这里的 `x y z roll pitch yaw` 改成雷达相对底盘的真实安装位置。

检查 TF：

```bash
ros2 run tf2_ros tf2_echo base_link scan
```

### 2. Nav2 costmap 示例配置

Nav2 的 local costmap 可以这样订阅 `/scan`：

```yaml
local_costmap:
  local_costmap:
    ros__parameters:
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        enabled: true
        observation_sources: scan
        scan:
          topic: /scan
          data_type: "LaserScan"
          marking: true
          clearing: true
          max_obstacle_height: 2.0
          obstacle_max_range: 3.0
          raytrace_max_range: 4.0
```

如果你的 Nav2 版本对 QoS 比较严格，可以在 costmap 里启用 sensor data QoS。不同 ROS2/Nav2 版本参数名字可能略有差异，核心原则是：订阅端要能兼容 `/scan` 的 `BEST_EFFORT` QoS。

查看 `/scan` QoS：

```bash
ros2 topic info /scan -v
```

当前驱动发布 `/scan` 使用 `BEST_EFFORT`，这对雷达数据是常见设置。

### 3. 频率建议

当前实测 `/scan` 约 15Hz。对 Nav2 来说，15Hz 通常足够：

- 低速或中速移动机器人：保持 15Hz 即可。
- 机器人速度很高、避障距离很短、局部代价地图更新很激进：可以再考虑提高。

不建议现在为了追 30Hz 改动底层收包和拼帧逻辑。当前优先级应该是稳定、角度正确、TF 正确。

## 本版本主要改动

- 改成网口专用编译，不再依赖串口 `serial` 包。
- 修复 Ethernet 点云拼帧抖动问题。
- 将雷达数据包中的 `points_index` 按 `int16_t` 解析，避免负角度索引被当成大正数。
- 不再按 TCP 包到达顺序拼接点云，而是按角度槽位放回固定位置。
- 新增 `offset_angle` 默认配置，使当前安装下正前方对齐 ROS `+X`。
- 新增 `angle_scale` 和 `angle_anchor`，修正 RViz 中角度被压缩的问题。
- 新增 `output_angle_min` 和 `output_angle_max`，支持按 ROS 坐标系裁剪输出角度。
- 保留 `BEST_EFFORT` QoS，适合雷达传感器数据。

## 常见问题

### 编译时报找不到 serial

当前整理版已经不需要串口 `serial` 包。如果又出现类似：

```text
Could not find a package configuration file provided by "serial"
```

说明你编译的不是当前网口专用版本，或者 CMakeLists 又被恢复成串口版本了。

### 能连接但 RViz 没有点

检查：

```bash
ros2 topic list | grep scan
ros2 topic hz /scan
ros2 topic echo /scan --once
```

如果 `/scan` 有数据但 RViz 不显示，检查 RViz 的 topic、Fixed Frame 和 QoS 设置。

### RViz 有 QoS warning

如果 `/scan` 能正常显示，这个 warning 可以先忽略。可以用下面命令确认发布端和订阅端 QoS：

```bash
ros2 topic info /scan -v
```

### Set scan angle failed

不要把 `start_angle/stop_angle` 改成雷达不支持的范围。当前 C200 稳定值是：

```text
start_angle=-45
stop_angle=225
```

需要屏蔽后方遮挡时，改 `output_angle_min/output_angle_max`，不要改硬件扫描角度。

