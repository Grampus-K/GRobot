include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "base_link",
  published_frame = "odom",
  odom_frame = "odom",
  provide_odom_frame = false,
  publish_frame_projected_to_2d = true,
  use_odometry = true,
  use_nav_sat = false,
  use_landmarks = false,
  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,
  lookup_transform_timeout_sec = 1.0,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 0.05,
  trajectory_publish_period_sec = 30e-3,
  rangefinder_sampling_ratio = 1.0,
  odometry_sampling_ratio = 1.0,
  fixed_frame_pose_sampling_ratio = 1.0,
  imu_sampling_ratio = 0.2,
  landmarks_sampling_ratio = 1.0,
}

MAP_BUILDER.use_trajectory_builder_2d = true

TRAJECTORY_BUILDER.pure_localization_trimmer = {
  max_submaps_to_keep = 5,
}

TRAJECTORY_BUILDER_2D.min_range = 0.05
TRAJECTORY_BUILDER_2D.max_range = 20.0
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 5.0
TRAJECTORY_BUILDER_2D.use_imu_data = true
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.linear_search_window = 0.3
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.angular_search_window = math.rad(45.)
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.translation_delta_cost_weight = 10.
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.rotation_delta_cost_weight = 1.
TRAJECTORY_BUILDER_2D.submaps.num_range_data = 80
TRAJECTORY_BUILDER_2D.motion_filter.max_distance_meters = 0.05
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(1.)
TRAJECTORY_BUILDER_2D.motion_filter.max_time_seconds = 0.2

-- Ceres 扫描匹配器参数
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.occupied_space_weight = 20.0
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.translation_weight = 10.0
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.rotation_weight = 40.0

POSE_GRAPH.optimization_problem.huber_scale = 1e2
POSE_GRAPH.optimize_every_n_nodes = 40
POSE_GRAPH.constraint_builder.min_score = 0.50
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.55

-- 全局重定位（绑架重定位）：扩大后端分支定界全局扫描匹配的搜索窗口，
-- 让机器人从地图任意位置启动时，后端能自动在整张地图中找回真实位姿，
-- 无需手动给初始位姿。linear_search_window 需覆盖地图对角线长度（米），
-- 请按实际地图大小调整（默认 30 米）。
POSE_GRAPH.constraint_builder.fast_correlative_scan_matcher = {
  linear_search_window = 30.,
  angular_search_window = math.rad(179.),
  branch_and_bound_depth = 7,
}
POSE_GRAPH.global_sampling_ratio = 0.9
POSE_GRAPH.constraint_builder.sampling_ratio = 0.5

return options
