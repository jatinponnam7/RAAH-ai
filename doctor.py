import importlib
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
print("=" * 65)
print("RAAH AI - System Doctor")
print("=" * 65)
print("Python:", sys.version.replace("\n", " "))
print("Executable:", sys.executable)
print("OS:", platform.platform())
print("Project:", ROOT)
print()

required = ["streamlit", "pandas", "cv2", "PIL", "ultralytics", "torch"]
all_ok = True
for name in required:
    try:
        mod = importlib.import_module(name)
        version = getattr(mod, "__version__", "installed")
        print(f"[OK] {name}: {version}")
    except Exception as exc:
        all_ok = False
        print(f"[MISSING] {name}: {exc}")

print()
for rel in ["models/pothole_seg.pt", "models/streetlight.pt"]:
    p = ROOT / rel
    print(("[OK]" if p.exists() else "[OPTIONAL/MISSING]"), rel)

try:
    test = ROOT / ".write_test"
    test.write_text("ok", encoding="utf-8")
    test.unlink(missing_ok=True)
    print("[OK] Project folder is writable")
except Exception as exc:
    all_ok = False
    print("[ERROR] Project folder is not writable:", exc)

print()
if all_ok:
    print("Core Python environment looks good.")
else:
    print("Something above is missing. Run setup.bat, then run doctor.bat again.")
print("Note: AI pothole detection needs models/pothole_seg.pt.")
print("Note: AI street-light detection needs models/streetlight.pt.")
print("=" * 65)
input("Press Enter to close...")
