# mdp_ws/src/mdp_worlds/CMakeLists.txt

cmake_minimum_required(VERSION 3.8)
project(mdp_worlds)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(gazebo_msgs REQUIRED)

install(DIRECTORY models worlds
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  mdp_worlds/spawn_environment.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()