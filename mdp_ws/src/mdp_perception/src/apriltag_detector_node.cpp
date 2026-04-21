#include "mdp_perception/apriltag_detector_node.hpp"

AprilTagDetectorNode::AprilTagDetectorNode(const rclcpp::NodeOptions & options)
: Node("apriltag_detector", options)
{
  RCLCPP_INFO(this->get_logger(), "AprilTag Detector Node starting...");

  // Declare parameters with defaults
  this->declare_parameter<std::string>("image_topic", "/image_raw");
  this->declare_parameter<std::string>("tag_family", "tag36h11");
  this->declare_parameter<bool>("publish_annotated_image", true);
  this->declare_parameter<bool>("publish_markers", true);
  this->declare_parameter<double>("quad_decimate", 2.0);
  this->declare_parameter<int>("nthreads", 4);

  // Get parameters
  std::string image_topic = this->get_parameter("image_topic").as_string();
  std::string tag_family_str = this->get_parameter("tag_family").as_string();
  publish_annotated_ = this->get_parameter("publish_annotated_image").as_bool();
  publish_markers_ = this->get_parameter("publish_markers").as_bool();
  double quad_decimate = this->get_parameter("quad_decimate").as_double();
  int nthreads = this->get_parameter("nthreads").as_int();

  // Initialize AprilTag detector
  td_ = apriltag_detector_create();
  
  // Select tag family
  if (tag_family_str == "tag36h11") {
    tf_ = tag36h11_create();
  } else {
    RCLCPP_WARN(this->get_logger(), "Unknown tag family '%s', using tag36h11", 
                tag_family_str.c_str());
    tf_ = tag36h11_create();
  }
  
  apriltag_detector_add_family(td_, tf_);

  // Configure detector parameters
  td_->quad_decimate = quad_decimate;
  td_->quad_sigma = 0.0;
  td_->nthreads = nthreads;
  td_->debug = 0;
  td_->refine_edges = 1;

  // Create subscriber
  image_sub_ = this->create_subscription<sensor_msgs::msg::Image>(
    image_topic, 10,
    std::bind(&AprilTagDetectorNode::imageCallback, this, std::placeholders::_1));

  // Create publishers
  detection_pub_ = this->create_publisher<apriltag_msgs::msg::AprilTagDetectionArray>(
    "/apriltag_detections", 10);

  if (publish_annotated_) {
    annotated_image_pub_ = this->create_publisher<sensor_msgs::msg::Image>(
      "/apriltag_detections/annotated_image", 10);
  }

  if (publish_markers_) {
    marker_pub_ = this->create_publisher<visualization_msgs::msg::MarkerArray>(
      "/apriltag_detections/markers", 10);
  }

  RCLCPP_INFO(this->get_logger(), "AprilTag Detector Node initialized");
  RCLCPP_INFO(this->get_logger(), "Subscribed to: %s", image_topic.c_str());
  RCLCPP_INFO(this->get_logger(), "Publishing annotated image: %s", publish_annotated_ ? "true" : "false");
  RCLCPP_INFO(this->get_logger(), "Publishing markers: %s", publish_markers_ ? "true" : "false");
}

AprilTagDetectorNode::~AprilTagDetectorNode()
{
  apriltag_detector_destroy(td_);
  tag36h11_destroy(tf_);
}

cv::Mat AprilTagDetectorNode::drawDetections(const cv::Mat& image, zarray_t* detections)
{
  cv::Mat annotated;
  if (image.channels() == 1) {
    cv::cvtColor(image, annotated, cv::COLOR_GRAY2BGR);
  } else {
    annotated = image.clone();
  }

  for (int i = 0; i < zarray_size(detections); i++) {
    apriltag_detection_t* det;
    zarray_get(detections, i, &det);

    // Draw corners
    std::vector<cv::Point> corners;
    for (int j = 0; j < 4; j++) {
      corners.push_back(cv::Point(det->p[j][0], det->p[j][1]));
    }

    // Draw outline
    for (int j = 0; j < 4; j++) {
      cv::line(annotated, corners[j], corners[(j + 1) % 4], cv::Scalar(0, 255, 0), 2);
    }

    // Draw center
    cv::Point center(det->c[0], det->c[1]);
    cv::circle(annotated, center, 5, cv::Scalar(0, 0, 255), -1);

    // Draw ID
    std::string id_text = "ID: " + std::to_string(det->id);
    cv::putText(annotated, id_text, 
                cv::Point(center.x - 20, center.y - 10),
                cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(255, 255, 0), 2);
  }

  return annotated;
}

void AprilTagDetectorNode::imageCallback(const sensor_msgs::msg::Image::SharedPtr msg)
{
  try {
    // Convert to grayscale for detection
    cv_bridge::CvImagePtr cv_ptr = cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::MONO8);
    
    image_u8_t im = {
      .width = cv_ptr->image.cols,
      .height = cv_ptr->image.rows,
      .stride = cv_ptr->image.cols,
      .buf = cv_ptr->image.data
    };

    zarray_t* detections = apriltag_detector_detect(td_, &im);

    // Build and publish detection array
    auto detection_array = apriltag_msgs::msg::AprilTagDetectionArray();
    detection_array.header = msg->header;

    for (int i = 0; i < zarray_size(detections); i++) {
      apriltag_detection_t* det;
      zarray_get(detections, i, &det);

      apriltag_msgs::msg::AprilTagDetection detection_msg;
      detection_msg.id = det->id;
      detection_msg.hamming = det->hamming;
      
      // Fill in corner positions
      for (int j = 0; j < 4; j++) {
        detection_msg.corners[j].x = det->p[j][0];
        detection_msg.corners[j].y = det->p[j][1];
      }
      
      detection_msg.centre.x = det->c[0];
      detection_msg.centre.y = det->c[1];

      detection_array.detections.push_back(detection_msg);
    }

    detection_pub_->publish(detection_array);

    // Publish annotated image
    if (publish_annotated_ && annotated_image_pub_->get_subscription_count() > 0) {
      cv::Mat annotated = drawDetections(cv_ptr->image, detections);
      sensor_msgs::msg::Image::SharedPtr annotated_msg = 
        cv_bridge::CvImage(msg->header, "bgr8", annotated).toImageMsg();
      annotated_image_pub_->publish(*annotated_msg);
    }

    // Publish markers for RViz
    if (publish_markers_ && marker_pub_->get_subscription_count() > 0) {
      visualization_msgs::msg::MarkerArray marker_array;
      
      for (int i = 0; i < zarray_size(detections); i++) {
        apriltag_detection_t* det;
        zarray_get(detections, i, &det);

        // Create text marker for ID
        visualization_msgs::msg::Marker marker;
        marker.header = msg->header;
        marker.ns = "apriltag_ids";
        marker.id = i;
        marker.type = visualization_msgs::msg::Marker::TEXT_VIEW_FACING;
        marker.action = visualization_msgs::msg::Marker::ADD;
        
        // Position in image coordinates (normalized to 0-1 for visualization)
        marker.pose.position.x = det->c[0] / static_cast<double>(cv_ptr->image.cols);
        marker.pose.position.y = det->c[1] / static_cast<double>(cv_ptr->image.rows);
        marker.pose.position.z = 0.0;
        marker.pose.orientation.w = 1.0;
        
        marker.scale.z = 0.05;  // Text height
        marker.color.r = 1.0;
        marker.color.g = 1.0;
        marker.color.b = 0.0;
        marker.color.a = 1.0;
        
        marker.text = "ID: " + std::to_string(det->id);
        marker_array.markers.push_back(marker);
      }
      
      marker_pub_->publish(marker_array);
    }

    apriltag_detections_destroy(detections);

  } catch (cv_bridge::Exception& e) {
    RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
  }
}

#include "rclcpp_components/register_node_macro.hpp"
RCLCPP_COMPONENTS_REGISTER_NODE(AprilTagDetectorNode)