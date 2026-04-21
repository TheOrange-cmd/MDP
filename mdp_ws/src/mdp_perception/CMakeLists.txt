cmake_minimum_required(VERSION 3.10)
project(mdp_perception)

# C++17 for modern features
set(CMAKE_CXX_STANDARD 17)

# Find all necessary packages
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(rclpy REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(vision_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(apriltag_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(image_transport REQUIRED)
find_package(OpenCV REQUIRED)

# Find apriltag library - try ROS package first, then system
find_package(apriltag QUIET)
if(NOT apriltag_FOUND)
  find_package(PkgConfig REQUIRED)
  pkg_check_modules(APRILTAG REQUIRED apriltag)
endif()

# Include the headers
include_directories(include)

# C++ Minimal Node
add_executable(minimal_cpp_node src/minimal_cpp_node.cpp)
ament_target_dependencies(minimal_cpp_node rclcpp)

# C++ AprilTag Detector Node as a Component
add_library(apriltag_detector_component SHARED
  src/apriltag_detector_node.cpp
)
ament_target_dependencies(apriltag_detector_component
  rclcpp
  rclcpp_components
  sensor_msgs
  apriltag_msgs
  cv_bridge
  OpenCV
  visualization_msgs
)

# Link apriltag library
if(apriltag_FOUND)
  target_link_libraries(apriltag_detector_component apriltag::apriltag)
else()
  target_include_directories(apriltag_detector_component PUBLIC ${APRILTAG_INCLUDE_DIRS})
  target_link_libraries(apriltag_detector_component ${APRILTAG_LIBRARIES})
endif()

# Register the component
rclcpp_components_register_nodes(apriltag_detector_component "AprilTagDetectorNode")

# Also create a standalone executable for the AprilTag detector
add_executable(apriltag_detector_node_exe src/apriltag_detector_node_main.cpp)
target_link_libraries(apriltag_detector_node_exe apriltag_detector_component)
ament_target_dependencies(apriltag_detector_node_exe rclcpp)

# Install C++ targets
install(TARGETS
  minimal_cpp_node
  apriltag_detector_node_exe
  DESTINATION lib/${PROJECT_NAME}
)

install(TARGETS
  apriltag_detector_component
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# Python Installation 
ament_python_install_package(${PROJECT_NAME})

# Install Python executables
install(PROGRAMS
  mdp_perception/object_detector_node.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

# Install config files
install(DIRECTORY
  config
  DESTINATION share/${PROJECT_NAME}/
)

# Install model files
install(DIRECTORY
  models
  DESTINATION share/${PROJECT_NAME}/
)

ament_package()