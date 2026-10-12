from pathlib import Path
import shutil
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
MODELS.mkdir(exist_ok=True)

TARGET = MODELS / "pothole_seg.pt"
TEMP = MODELS / "pothole_seg.download"
BACKUP = MODELS / "pothole_seg.backup.pt"

# Public academic/demo YOLOv8 pothole detector.
# Source project documents this checkpoint as Apache-2.0 licensed.
URL = "https://huggingface.co/peterhdd/pothole-detection-yolov8/resolve/main/best.pt"

def progress(blocks, block_size, total):
    if total <= 0:
        return
    downloaded = min(blocks * block_size, total)
    pct = int(downloaded * 100 / total)
    mb = downloaded / (1024 * 1024)
    total_mb = total / (1024 * 1024)
    print(f"\rDownloading model: {pct:3d}%  {mb:6.1f}/{total_mb:6.1f} MB", end="", flush=True)

print("=" * 64)
print("RAAH AI - Pothole Model Installer")
print("=" * 64)
print("Source: peterhdd/pothole-detection-yolov8")
print("Destination:", TARGET)
print()

try:
    if TARGET.exists():
        print("Existing pothole model found.")
        if BACKUP.exists():
            BACKUP.unlink()
        shutil.copy2(TARGET, BACKUP)
        print("Backed it up as:", BACKUP.name)

    if TEMP.exists():
        TEMP.unlink()

    urllib.request.urlretrieve(URL, TEMP, reporthook=progress)
    print("\nDownload complete.")

    # Validate with the exact Ultralytics installation in this environment.
    from ultralytics import YOLO
    model = YOLO(str(TEMP))
    names = model.names
    print("Model loaded successfully.")
    print("Task:", getattr(model, "task", "unknown"))
    print("Classes:", names)

    # Accept a pothole-labelled model or a one-class road-defect model.
    labels = [str(v).lower() for v in (names.values() if isinstance(names, dict) else names)]
    if len(labels) > 1 and not any("pothole" in x for x in labels):
        raise RuntimeError(f"Downloaded model does not expose a pothole class: {labels}")

    TEMP.replace(TARGET)
    print()
    print("[OK] Installed:", TARGET)
    print("[OK] RAAH AI can now perform real pothole detection.")
    print()
    print("Close/restart the Streamlit dashboard after this installer finishes.")

except Exception as exc:
    print()
    print("[ERROR]", exc)
    if TEMP.exists():
        try:
            TEMP.unlink()
        except Exception:
            pass
    print("No working model was installed.")
    sys.exit(1)
