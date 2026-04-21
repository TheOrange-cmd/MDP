#!/usr/bin/env python3
"""
mdp_ws/src/mdp_perception/mdp_perception/object_detector_node.py
Detector ROS 2 node.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, BoundingBox2D, ObjectHypothesisWithPose
from std_msgs.msg import Header

from ament_index_python.packages import get_package_share_directory

from cv_bridge import CvBridge
import cv2
import numpy as np
import os
import sys
import traceback

from mdp_perception.yolo_inference import OnnxDetector


class DetectorNode(Node):

    def __init__(self):
        super().__init__('detector_node')

        # Parameters
        self.declare_parameter('model_filename', 'yolov8n.onnx')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('image_topic', '/image_raw')
        self.declare_parameter('publish_annotated_image', True)

        # Get the parameters
        model_filename = self.get_parameter('model_filename').get_parameter_value().string_value
        confidence = self.get_parameter('confidence_threshold').get_parameter_value().double_value
        image_topic = self.get_parameter('image_topic').get_parameter_value().string_value
        self.publish_annotated = self.get_parameter('publish_annotated_image').get_parameter_value().bool_value

        # Construct the full model path
        try:
            pkg_share_path = get_package_share_directory('mdp_perception')
            model_path = os.path.join(pkg_share_path, 'models', model_filename)
        except Exception as e:
            self.get_logger().error(f'Failed to get package share directory: {e}')
            raise

        if not os.path.exists(model_path):
            self.get_logger().error(f'Model file not found at: {model_path}')
            self.get_logger().error(f'Package share path: {pkg_share_path}')
            self.get_logger().error(f'Looking for: {model_filename}')
            raise RuntimeError(f'Model file not found: {model_path}')

        # Load model
        self.get_logger().info(f'Loading model from {model_path}')
        try:
            self.detector = OnnxDetector(model_path, confidence_threshold=confidence)
            self.get_logger().info('Model loaded successfully')
        except Exception as e:
            self.get_logger().error(f'Failed to load model: {e}')
            raise

        self.bridge = CvBridge()

        # Use sensor QoS
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.sub = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            sensor_qos
        )

        self.detection_pub = self.create_publisher(
            Detection2DArray,
            '/detections',
            10
        )

        if self.publish_annotated:
            self.annotated_pub = self.create_publisher(
                Image,
                '/detections/annotated_image',
                10
            )

        self.get_logger().info(f'Detector node ready, listening on {image_topic}')

    def image_callback(self, msg: Image):
        try:
            bgr_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'cv_bridge conversion failed: {e}')
            return

        # Run inference
        detections = self.detector.infer(bgr_image)

        # Publish detections
        detection_array = self._build_detection_msg(detections, msg.header)
        self.detection_pub.publish(detection_array)

        # Optionally publish annotated image
        if self.publish_annotated:
            annotated = self._draw_detections(bgr_image, detections)
            annotated_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
            annotated_msg.header = msg.header
            self.annotated_pub.publish(annotated_msg)

    def _build_detection_msg(self, detections, header: Header) -> Detection2DArray:
        array_msg = Detection2DArray()
        array_msg.header = header

        for det in detections:
            d = Detection2D()
            d.header = header

            bbox = BoundingBox2D()
            bbox.center.position.x = det.x_center
            bbox.center.position.y = det.y_center
            bbox.size_x = det.width
            bbox.size_y = det.height
            d.bbox = bbox

            hyp = ObjectHypothesisWithPose()
            hyp.hypothesis.class_id = det.class_name
            hyp.hypothesis.score = det.confidence
            d.results.append(hyp)

            array_msg.detections.append(d)

        return array_msg

    def _draw_detections(self, bgr_image: np.ndarray, detections) -> np.ndarray:
        annotated = bgr_image.copy()
        h, w = annotated.shape[:2]

        for det in detections:
            cx = int(det.x_center * w)
            cy = int(det.y_center * h)
            bw = int(det.width * w)
            bh = int(det.height * h)

            x1 = cx - bw // 2
            y1 = cy - bh // 2
            x2 = cx + bw // 2
            y2 = cy + bh // 2

            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f'{det.class_name} {det.confidence:.2f}'
            cv2.putText(annotated, label, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        return annotated


def main(args=None):
    try:
        rclpy.init(args=args)
        node = DetectorNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("Keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"Error in main: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1
    finally:
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())