from pathlib import Path
import hashlib
import shutil
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
MODELS.mkdir(parents=True, exist_ok=True)

TARGET = MODELS / "pothole_seg.pt"
TEMP = MODELS / "_pothole_download_tmp.pt"
BACKUP = MODELS / "pothole_seg.backup.pt"

URL = "https://huggingface.co/peterhdd/pothole-detection-yolov8/resolve/main/best.pt"
EXPECTED_SHA256 = "af2ac6ce7bfec72e71643659ac946caf80ced84869e526a60135c457abfbb200"

def progress(blocks, block_size, total):
    if total <= 0:
        return
    downloaded = min(blocks * block_size, total)
    pct = int(downloaded * 100 / total)
    mb = downloaded / (1024 * 1024)
    total_mb = total / (1024 * 1024)
    print(f"\rDownloading: {pct:3d}%  {mb:6.1f}/{total_mb:6.1f} MB", end="", flush=True)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

print("=" * 66)
print("RAAH AI - Pothole Model Installer V2")
print("=" * 66)
print("Model: YOLOv8s pothole detector")
print("Source: peterhdd/pothole-detection-yolov8")
print("Target:", TARGET)
print()

try:
    if TEMP.exists():
        TEMP.unlink()

    urllib.request.urlretrieve(URL, TEMP, reporthook=progress)
    print("\nDownload complete.")

    digest = sha256(TEMP)
    print("SHA256:", digest)
    if digest.lower() != EXPECTED_SHA256.lower():
        raise RuntimeError(
            "Downloaded file checksum does not match the expected model. "
            "The remote file may have changed; refusing to install it."
        )
    print("[OK] Download checksum verified.")

    # The temporary file intentionally ends in .pt so Ultralytics recognizes it.
    from ultralytics import YOLO
    model = YOLO(str(TEMP), task="detect")
    names = model.names
    print("[OK] Ultralytics loaded the model.")
    print("Task:", getattr(model, "task", "detect"))
    print("Classes:", names)

    labels = [str(v).lower() for v in (names.values() if isinstance(names, dict) else names)]
    if not any("pothole" in x for x in labels) and len(labels) != 1:
        raise RuntimeError(f"Unexpected model classes: {labels}")

    if TARGET.exists():
        if BACKUP.exists():
            BACKUP.unlink()
        shutil.copy2(TARGET, BACKUP)
        print("[OK] Existing model backed up as", BACKUP.name)

    shutil.move(str(TEMP), str(TARGET))
    print()
    print("=" * 66)
    print("[OK] POTHOLE MODEL INSTALLED SUCCESSFULLY")
    print("=" * 66)
    print("Installed to:", TARGET)
    print()
    print("Next:")
    print("1. Close any running RAAH AI dashboard/CMD.")
    print("2. Run run_dashboard.bat.")
    print("3. Open AI Inspect.")
    print("4. Upload a pothole image.")
    print("5. Try confidence 0.20 first.")
    print()

except Exception as exc:
    print()
    print("[ERROR]", exc)
    if TEMP.exists():
        try:
            TEMP.unlink()
        except Exception:
            pass
    print("No new model was installed.")
    sys.exit(1)
