#!/usr/bin/env python3
"""
mdp_ws/src/mdp_perception/mdp_perception/yolo_inference.py
Inference wrapper for object detection.

This module is intentionally isolated from ROS so that:
- It can be tested standalone without a ROS environment
- Swapping the backend (ONNX Runtime -> TensorRT) is a contained change here

Current backend: ONNX Runtime (for development machine)
To swap to TensorRT: replace OnnxDetector with a TensorRTDetector class
that exposes the same interface (load, infer).
"""

import numpy as np
import onnxruntime as ort
import cv2


# YOLO class names (COCO dataset, used by pretrained YOLOv8)
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
    'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag',
    'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite',
    'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana',
    'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
    'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table',
    'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock',
    'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]


class Detection:
    """Simple dataclass for a single detection result."""
    def __init__(self, x_center, y_center, width, height, confidence, class_id):
        self.x_center = float(x_center)
        self.y_center = float(y_center)
        self.width = float(width)
        self.height = float(height)
        self.confidence = float(confidence)
        self.class_id = int(class_id)
        self.class_name = COCO_CLASSES[self.class_id] if self.class_id < len(COCO_CLASSES) else 'unknown'


class OnnxDetector:
    """
    ONNX Runtime backend for YOLOv8 detection.

    Expected interface (keep stable when swapping to TensorRT):
        detector = OnnxDetector(model_path, confidence_threshold)
        detections = detector.infer(bgr_image)  # returns List[Detection]
    """

    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.input_size = 640

        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)

        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def _preprocess(self, bgr_image: np.ndarray):
        """Resize, normalize, and reformat image for YOLOv8 input."""
        original_h, original_w = bgr_image.shape[:2]

        # Letterbox resize to 640x640
        scale = min(self.input_size / original_w, self.input_size / original_h)
        new_w = int(original_w * scale)
        new_h = int(original_h * scale)
        resized = cv2.resize(bgr_image, (new_w, new_h))

        # Pad to square
        pad_w = (self.input_size - new_w) // 2
        pad_h = (self.input_size - new_h) // 2
        padded = cv2.copyMakeBorder(resized, pad_h, pad_h, pad_w, pad_w,
                                    cv2.BORDER_CONSTANT, value=(114, 114, 114))
        padded = cv2.resize(padded, (self.input_size, self.input_size))

        # BGR -> RGB, HWC -> NCHW, normalize to [0, 1]
        rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
        tensor = rgb.transpose(2, 0, 1).astype(np.float32) / 255.0
        tensor = np.expand_dims(tensor, axis=0)

        return tensor, scale, pad_w, pad_h, original_w, original_h

    def _postprocess(self, output, scale, pad_w, pad_h, orig_w, orig_h):
        """
        Parse YOLOv8 ONNX output into Detection objects.
        YOLOv8 ONNX output shape: [1, 84, 8400]
        84 = 4 box coords + 80 class scores
        """
        predictions = output[0].squeeze(0).T  # [8400, 84]

        boxes = predictions[:, :4]            # cx, cy, w, h (in 640x640 space)
        class_scores = predictions[:, 4:]     # [8400, 80]

        confidences = class_scores.max(axis=1)
        class_ids = class_scores.argmax(axis=1)

        mask = confidences > self.confidence_threshold
        boxes = boxes[mask]
        confidences = confidences[mask]
        class_ids = class_ids[mask]

        detections = []
        for box, conf, cls_id in zip(boxes, confidences, class_ids):
            cx, cy, w, h = box

            # Undo padding and scale back to original image coords
            cx = (cx - pad_w) / scale
            cy = (cy - pad_h) / scale
            w = w / scale
            h = h / scale

            # Normalize to [0, 1] relative to original image size
            detections.append(Detection(
                x_center=cx / orig_w,
                y_center=cy / orig_h,
                width=w / orig_w,
                height=h / orig_h,
                confidence=conf,
                class_id=cls_id
            ))

        return detections

    def infer(self, bgr_image: np.ndarray):
        """
        Run inference on a BGR image (as returned by OpenCV).
        Returns a list of Detection objects.
        """
        tensor, scale, pad_w, pad_h, orig_w, orig_h = self._preprocess(bgr_image)
        output = self.session.run([self.output_name], {self.input_name: tensor})
        return self._postprocess(output, scale, pad_w, pad_h, orig_w, orig_h)