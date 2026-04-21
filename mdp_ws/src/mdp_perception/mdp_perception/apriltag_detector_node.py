#!/usr/bin/env python3
# mdp_ws/src/mdp_perception/mdp_perception/apriltag_detector_node.py

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import Image
from apriltag_msgs.msg import AprilTagDetection, AprilTagDetectionArray
from cv_bridge import CvBridge
import cv2
from pupil_apriltags import Detector

class AprilTagDetectorNode(Node):

    def __init__(self):
        super().__init__('apriltag_detector_node')

        # --- Parameters ---
        self.declare_parameter('image_topic', '/image_raw')
        self.declare_parameter('tag_family', 'tag36h11')
        self.declare_parameter('publish_annotated_image', True)

        # Get parameters from the YAML config file
        image_topic = self.get_parameter('image_topic').get_parameter_value().string_value
        tag_family = self.get_parameter('tag_family').get_parameter_value().string_value
        self.publish_annotated = self.get_parameter('publish_annotated_image').get_parameter_value().bool_value

        self.bridge = CvBridge()

        # --- AprilTag Detector Initialization ---
        self.get_logger().info(f"Initializing AprilTag detector for family '{tag_family}'...")
        try:
            self.tag_detector = Detector(families=tag_family,
                                         nthreads=1,
                                         quad_decimate=1.0,
                                         quad_sigma=0.0,
                                         refine_edges=1,
                                         decode_sharpening=0.25,
                                         debug=0)
        except Exception as e:
            self.get_logger().error(f"Failed to initialize AprilTag detector: {e}")
            raise RuntimeError("Detector initialization failed")
            
        self.get_logger().info('AprilTag detector initialized.')

        # --- QoS Profile for sensor data ---
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # --- ROS 2 Subscriptions & Publishers ---
        self.sub = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            sensor_qos
        )
        
        self.detection_pub = self.create_publisher(
            AprilTagDetectionArray,
            '/tags/detections',
            10
        )
        
        # Only create the annotated image publisher if requested
        if self.publish_annotated:
            self.annotated_pub = self.create_publisher(
                Image,
                '/tags/annotated_image',
                10
            )
        else:
            self.annotated_pub = None

        self.get_logger().info(f'AprilTag node ready, listening on {image_topic}')

    def image_callback(self, msg: Image):
        try:
            bgr_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            gray_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        except Exception as e:
            self.get_logger().error(f'cv_bridge conversion failed: {e}')
            return

        tags = self.tag_detector.detect(gray_image)

        detection_array_msg = AprilTagDetectionArray()
        detection_array_msg.header = msg.header

        for tag in tags:
            detection_msg = AprilTagDetection()
            detection_msg.family = tag.tag_family.decode('utf-8')
            detection_msg.id = tag.tag_id
            detection_msg.hamming = tag.hamming
            detection_msg.decision_margin = tag.decision_margin
            detection_msg.centre.x = tag.center[0]
            detection_msg.centre.y = tag.center[1]
            for i, corner in enumerate(tag.corners):
                detection_msg.corners[i].x = corner[0]
                detection_msg.corners[i].y = corner[1]
            detection_msg.homography = tag.homography.flatten().tolist()
            
            detection_array_msg.detections.append(detection_msg)

        if tags:
            self.detection_pub.publish(detection_array_msg)
        
        # Publish the annotated image only if the publisher was created
        if self.annotated_pub:
            annotated_image = self._draw_tags(bgr_image, tags)
            annotated_msg = self.bridge.cv2_to_imgmsg(annotated_image, encoding='bgr8')
            annotated_msg.header = msg.header
            self.annotated_pub.publish(annotated_msg)

    def _draw_tags(self, image, tags):
        annotated = image.copy()
        for tag in tags:
            (ptA, ptB, ptC, ptD) = tag.corners
            ptB = (int(ptB[0]), int(ptB[1])); ptC = (int(ptC[0]), int(ptC[1]))
            ptD = (int(ptD[0]), int(ptD[1])); ptA = (int(ptA[0]), int(ptA[1]))
            cv2.line(annotated, ptA, ptB, (0, 255, 0), 2)
            cv2.line(annotated, ptB, ptC, (0, 255, 0), 2)
            cv2.line(annotated, ptC, ptD, (0, 255, 0), 2)
            cv2.line(annotated, ptD, ptA, (0, 255, 0), 2)
            (cX, cY) = (int(tag.center[0]), int(tag.center[1]))
            cv2.circle(annotated, (cX, cY), 5, (0, 0, 255), -1)
            cv2.putText(annotated, str(tag.tag_id), (ptA[0], ptA[1] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return annotated

def main(args=None):
    rclpy.init(args=args)
    node = AprilTagDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()