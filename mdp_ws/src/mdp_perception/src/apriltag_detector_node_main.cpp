#include "mdp_perception/apriltag_detector_node.hpp"

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  
  rclcpp::NodeOptions options;
  auto node = std::make_shared<AprilTagDetectorNode>(options);
  
  rclcpp::spin(node);
  rclcpp::shutdown();
  
  return 0;
}