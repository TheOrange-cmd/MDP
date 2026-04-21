#ifndef MDP_PERCEPTION_APRILTAG_DETECTOR_NODE_HPP
#define MDP_PERCEPTION_APRILTAG_DETECTOR_NODE_HPP

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <apriltag_msgs/msg/april_tag_detection_array.hpp>
#include <visualization_msgs/msg/marker_array.hpp>
#include <cv_bridge/cv_bridge.h>
#include <opencv2/opencv.hpp>

extern "C" {
#include <apriltag/apriltag.h>
#include <apriltag/tag36h11.h>
}

class AprilTagDetectorNode : public rclcpp::Node
{
public:
  explicit AprilTagDetectorNode(const rclcpp::NodeOptions & options);
  ~AprilTagDetectorNode();

private:
  void imageCallback(const sensor_msgs::msg::Image::SharedPtr msg);
  cv::Mat drawDetections(const cv::Mat& image, zarray_t* detections);
  
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
  rclcpp::Publisher<apriltag_msgs::msg::AprilTagDetectionArray>::SharedPtr detection_pub_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr annotated_image_pub_;
  rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr marker_pub_;
  
  apriltag_detector_t* td_;
  apriltag_family_t* tf_;
  
  bool publish_annotated_;
  bool publish_markers_;
};

#endif  // MDP_PERCEPTION_APRILTAG_DETECTOR_NODE_HPP