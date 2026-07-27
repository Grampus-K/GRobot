# GRobot ODrive Base Driver

ROS2 Python driver for the hotel robot differential chassis using ODrive v3.6 over MicroUSB.

## Measured Chassis Parameters

- Wheel diameter: `0.1725 m`
- Wheel circumference: `0.1725 * pi = 0.542 m`
- Track width: `0.375 m`
- Left wheel: `axis1`, positive `input_vel` moves forward
- Right wheel: `axis0`, positive `input_vel` moves backward, so the driver uses a negative command sign

## Ubuntu 22 / ROS2 Build

Install ROS2 dependencies and ODrive Python tools:

```bash
sudo apt update
sudo apt install -y python3-pip python3-colcon-common-extensions
sudo pip3 install odrive==0.5.1.post0
```

Build:

```bash
cd ~/GRobot_ws
colcon build --symlink-install
source install/setup.bash
```

Run:

```bash
ros2 launch grobot_odrive_base odrive_base.launch.py
```

Test forward motion at low speed. `/cmd_vel` is a continuous velocity command, so publish it at a rate higher than `cmd_timeout`:

```bash
ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.15}, angular: {z: 0.0}}"
```

Test left rotation:

```bash
ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.3}}"
```

Stop the test with `Ctrl+C`; the node will command zero velocity after `cmd_timeout`.

Inspect odometry:

```bash
ros2 topic echo /odom
ros2 run tf2_ros tf2_echo odom base_link
```

If ODrive USB permissions fail, run ODrive's udev setup on Ubuntu and reconnect the board:

```bash
odrivetool udev-setup
```

## Safety Notes

- Keep the robot lifted for the first launch.
- The node enters `CLOSED_LOOP_CONTROL` on startup.
- If `/cmd_vel` stops arriving for `0.5 s`, the node commands zero speed.
- On shutdown, the node commands zero speed and sets both axes to `IDLE`.
- If any axis, motor, encoder, or controller error appears, the node stops and sets both axes to `IDLE`.
