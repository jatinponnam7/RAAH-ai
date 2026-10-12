import cv2,time,torch
from pathlib import Path
from src.db import init_db,add_pothole
from src.pothole import PotholeSegmenter
from src.streetlight import StreetLightDetector
ROOT=Path(__file__).resolve().parent; SAVE=ROOT/'detections'/'live'; SAVE.mkdir(parents=True,exist_ok=True)
def main():
 init_db(); device=0 if torch.cuda.is_available() else 'cpu'; p=PotholeSegmenter(.25) if False else PotholeSegmenter(conf=.25); l=StreetLightDetector(.25); cap=cv2.VideoCapture(0, cv2.CAP_DSHOW if hasattr(cv2, 'CAP_DSHOW') else 0); last=0
 if not cap.isOpened():
  cap=cv2.VideoCapture(1)
 if not cap.isOpened(): raise RuntimeError('Could not open webcam on camera index 0 or 1. Close Teams/Zoom/Camera app and try again.')
 while True:
  ok,f=cap.read();
  if not ok:break
  out,pd=p.infer(f,device); _,ld=l.infer(f,device)
  for d in ld:
   x1,y1,x2,y2=d['bbox']; cv2.rectangle(out,(x1,y1),(x2,y2),(255,255,255),2); cv2.putText(out,f"LIGHT {d['status']}",(x1,max(20,y1-8)),cv2.FONT_HERSHEY_SIMPLEX,.55,(255,255,255),2)
  cv2.putText(out,f'Potholes:{len(pd)} Lights:{len(ld)} | Q quit',(20,35),cv2.FONT_HERSHEY_SIMPLEX,.8,(255,255,255),2)
  now=time.time()
  if pd and now-last>2:
   path=SAVE/f"live_{time.strftime('%Y%m%d_%H%M%S')}.jpg"; cv2.imwrite(str(path),out)
   for d in pd:add_pothole(d['confidence'],d['area_ratio'],d['severity'],str(path),'webcam')
   last=now
  cv2.imshow('RAAH AI - Live Inspection',out)
  if cv2.waitKey(1)&0xff==ord('q'):break
 cap.release(); cv2.destroyAllWindows()
if __name__=='__main__':main()
