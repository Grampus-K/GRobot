cmake_minimum_required(VERSION 3.5)
project(free_lidar)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(Boost REQUIRED COMPONENTS thread)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(lifecycle_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)

set(dependencies
  rclcpp
  rclcpp_lifecycle 
  lifecycle_msgs 
  sensor_msgs
  std_msgs
  )

add_executable(free_lidar_node
  src/rosnode/free_lidar_node.cpp
  src/driver/free_eth_driver.cpp
  src/driver/trailing_filter.cpp
  )

target_compile_definitions(free_lidar_node PRIVATE FREE_LIDAR_HAS_SERIAL=0)

ament_target_dependencies(free_lidar_node ${dependencies})

target_include_directories(free_lidar_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
  )


target_link_libraries(free_lidar_node
${rclcpp_lifecycle_LIBRARIES}
${lifecycle_msgs_LIBRARIES}
${Boost_LIBRARIES}
)


install(DIRECTORY
launch
rviz
DESTINATION share/${PROJECT_NAME}/
)

install(TARGETS free_lidar_node
  EXPORT export_${PROJECT_NAME}
  DESTINATION lib/${PROJECT_NAME})


if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # uncomment the line when a copyright and license is not present in all source files
  #set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # uncomment the line when this package is not in a git repo
  #set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

#TODO lookup what this does
# For message creation,if used in this message
ament_export_dependencies(${dependencies})

ament_package()
