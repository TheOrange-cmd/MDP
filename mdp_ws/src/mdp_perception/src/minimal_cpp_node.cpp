#include "rclcpp/rclcpp.hpp"

int main(int argc, char * argv[])
{
  // Initialize the ROS 2 client library
  rclcpp::init(argc, argv);

  // Create a new node named 'minimal_cpp_node'
  auto node = std::make_shared<rclcpp::Node>("minimal_cpp_node");

  // Use the node's logger to print an informational message
  RCLCPP_INFO(node->get_logger(), "Hello from the C++ test node!");

  // Shutdown the ROS 2 client library
  rclcpp::shutdown();
  
  return 0;
}