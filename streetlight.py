from pathlib import Path
import cv2
import numpy as np

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "models" / "streetlight.pt"


class StreetLightDetector:
    def __init__(self, conf=0.25, model_path=None):
        self.conf = float(conf)
        self.model_path = Path(model_path) if model_path else MODEL
        self.available = False
        self.model = None
        self.load_error = ""

        if not self.model_path.exists():
            return
        if YOLO is None:
            self.load_error = "Ultralytics is not installed. Run setup.bat first."
            return
        try:
            self.model = YOLO(str(self.model_path))
            self.available = True
        except Exception as exc:
            self.load_error = f"Could not load street-light model: {exc}"

    def infer(self, frame, device=None):
        if not self.available or self.model is None:
            return frame.copy(), []

        try:
            r = self.model.predict(
                source=frame,
                conf=self.conf,
                device=device,
                verbose=False,
            )[0]
        except Exception as exc:
            self.load_error = f"Inference failed: {exc}"
            return frame.copy(), []

        out = r.plot()
        dets = []
        if r.boxes is None:
            return out, dets

        names = r.names
        for b in r.boxes:
            cid = int(b.cls[0])
            name = str(names.get(cid, cid)) if isinstance(names, dict) else str(names[cid])
            is_single_class = len(names) == 1
            if not is_single_class and "light" not in name.lower() and "lamp" not in name.lower():
                continue

            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            crop = frame[max(0, y1):max(y1 + 1, y2), max(0, x1):max(x1 + 1, x2)]
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.size else np.zeros((1, 1), np.uint8)

            # Visual heuristic only; it is NOT an electrical measurement.
            bright = float((gray > 210).mean())
            status = "ON" if bright > 0.03 else "OFF/UNCERTAIN"

            dets.append(
                {
                    "class_name": name,
                    "confidence": float(b.conf[0]),
                    "status": status,
                    "brightness_ratio": bright,
                    "bbox": (x1, y1, x2, y2),
                }
            )

        return out, dets
