from pathlib import Path
import cv2
from src.severity import severity_from_area_ratio

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

ROOT = Path(__file__).resolve().parent.parent
CUSTOM_MODEL = ROOT / "models" / "pothole_seg.pt"


class PotholeSegmenter:
    """Pothole segmenter that NEVER auto-downloads a generic COCO model.

    The app stays usable when custom weights are missing. Place a trained
    pothole model at models/pothole_seg.pt to enable AI pothole detection.
    """

    def __init__(self, model_path=None, conf=0.25):
        self.conf = float(conf)
        self.model_path = Path(model_path) if model_path else CUSTOM_MODEL
        self.custom = self.model_path.exists()
        self.model = None
        self.load_error = ""

        if not self.custom:
            return
        if YOLO is None:
            self.load_error = "Ultralytics is not installed. Run setup.bat first."
            self.custom = False
            return
        try:
            self.model = YOLO(str(self.model_path))
        except Exception as exc:
            self.load_error = f"Could not load pothole model: {exc}"
            self.custom = False
            self.model = None

    @property
    def available(self):
        return self.custom and self.model is not None

    def infer(self, frame, device=None):
        if not self.available:
            return frame.copy(), []

        try:
            result = self.model.predict(
                source=frame,
                conf=self.conf,
                device=device,
                verbose=False,
            )[0]
        except Exception as exc:
            self.load_error = f"Inference failed: {exc}"
            return frame.copy(), []

        annotated = result.plot()
        dets = []
        if result.boxes is None:
            return annotated, dets

        h, w = frame.shape[:2]
        frame_area = float(max(1, h * w))
        names = result.names

        for i, b in enumerate(result.boxes):
            cls_id = int(b.cls[0])
            if isinstance(names, dict):
                name = str(names.get(cls_id, cls_id))
            else:
                name = str(names[cls_id])

            # For a single-class custom dataset, accept that class even if it
            # has an unexpected label. For multi-class datasets require pothole.
            is_single_class = len(names) == 1
            if not is_single_class and "pothole" not in name.lower():
                continue

            conf = float(b.conf[0])
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())

            if result.masks is not None and i < len(result.masks.data):
                mask = result.masks.data[i].cpu().numpy()
                mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
                ratio = float((mask > 0.5).sum()) / frame_area
            else:
                ratio = max(0, x2 - x1) * max(0, y2 - y1) / frame_area

            dets.append(
                {
                    "class_name": name,
                    "confidence": conf,
                    "area_ratio": ratio,
                    "severity": severity_from_area_ratio(ratio),
                    "bbox": (x1, y1, x2, y2),
                }
            )

        return annotated, dets
