# RAAH AI v2.1 FIXED

This build fixes startup problems in the previous ZIP.

## Fastest way to run on Windows
1. Extract the whole ZIP to a normal folder such as `Desktop\RAAH_AI`.
2. Do **not** run files from inside the ZIP preview.
3. Double-click `start.bat`.
4. On the first run it creates `venv` and installs dependencies.
5. The dashboard opens in your browser.

If setup fails, run `doctor.bat` and copy the error shown in the black window.

## AI model files
The dashboard now starts even when AI weights are missing; it will not try to download a fake generic pothole model.

For real pothole detection, add a trained model here:

    models\pothole_seg.pt

For automatic street-light detection, add a trained model here:

    models\streetlight.pt

Without these files, the map, manual reporting, database, maintenance workflow and dashboard still work; the corresponding AI detector is simply disabled.

## Inputs supported
- uploaded JPG / JPEG / PNG / BMP
- uploaded MP4 / AVI / MOV / MKV
- live webcam via `run_live.bat`

## Why v2.0 could fail
- the batch files contained an accidental leading `\` line;
- the pothole detector tried to load/download `yolo11n-seg.pt` even when custom pothole weights were absent;
- launchers used the `streamlit` executable directly instead of the safer `python -m streamlit` form.

These are fixed in v2.1.
