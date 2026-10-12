import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "smartroad.db"

def connect():
    con=sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory=sqlite3.Row
    return con

def now(): return datetime.now().isoformat(timespec='seconds')

def init_db():
    con=connect(); c=con.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS pothole_detections(
      id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp TEXT NOT NULL,confidence REAL,area_ratio REAL,
      severity TEXT,image_path TEXT,source TEXT,review_status TEXT DEFAULT 'Pending',notes TEXT DEFAULT '')""")
    # migrate old DBs
    cols={r['name'] for r in c.execute('PRAGMA table_info(pothole_detections)')}
    if 'review_status' not in cols: c.execute("ALTER TABLE pothole_detections ADD COLUMN review_status TEXT DEFAULT 'Pending'")
    if 'notes' not in cols: c.execute("ALTER TABLE pothole_detections ADD COLUMN notes TEXT DEFAULT ''")
    c.execute("""CREATE TABLE IF NOT EXISTS streetlights(
      id INTEGER PRIMARY KEY AUTOINCREMENT,asset_id TEXT UNIQUE NOT NULL,location TEXT,status TEXT DEFAULT 'Working',
      issue TEXT,updated_at TEXT,latitude REAL,longitude REAL,priority TEXT DEFAULT 'LOW')""")
    cols={r['name'] for r in c.execute('PRAGMA table_info(streetlights)')}
    for col,typ,default in [('latitude','REAL','NULL'),('longitude','REAL','NULL'),('priority','TEXT',"'LOW'")]:
        if col not in cols: c.execute(f"ALTER TABLE streetlights ADD COLUMN {col} {typ} DEFAULT {default}")
    c.execute("""CREATE TABLE IF NOT EXISTS maintenance_history(
      id INTEGER PRIMARY KEY AUTOINCREMENT,asset_type TEXT NOT NULL,asset_id TEXT NOT NULL,event TEXT NOT NULL,
      status TEXT,priority TEXT,note TEXT,timestamp TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS manual_reports(
      id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp TEXT NOT NULL,report_type TEXT NOT NULL,asset_id TEXT,
      location TEXT,description TEXT,priority TEXT,status TEXT DEFAULT 'Reported',evidence_path TEXT DEFAULT '')""")
    for i in range(1,11):
        c.execute("INSERT OR IGNORE INTO streetlights(asset_id,location,status,updated_at,priority) VALUES(?,?,?,?,?)",
                  (f'S{i:02d}',f'Road Segment {i}','Working',now(),'LOW'))
    con.commit(); con.close()

def add_pothole(confidence,area_ratio,severity,image_path='',source='camera',review_status='Pending',notes=''):
    con=connect(); c=con.cursor(); c.execute("INSERT INTO pothole_detections(timestamp,confidence,area_ratio,severity,image_path,source,review_status,notes) VALUES(?,?,?,?,?,?,?,?)",
      (now(),float(confidence),float(area_ratio),severity,str(image_path),source,review_status,notes)); rid=c.lastrowid; con.commit(); con.close(); return rid

def get_potholes(limit=500):
    con=connect(); rows=con.execute("SELECT id,timestamp,confidence,area_ratio,severity,image_path,source,review_status,notes FROM pothole_detections ORDER BY id DESC LIMIT ?",(limit,)).fetchall(); con.close(); return [tuple(r) for r in rows]

def review_pothole(pid,status,notes=''):
    con=connect(); con.execute("UPDATE pothole_detections SET review_status=?,notes=? WHERE id=?",(status,notes,pid)); con.commit(); con.close()

def get_streetlights():
    con=connect(); rows=con.execute("SELECT id,asset_id,location,status,issue,updated_at,latitude,longitude,priority FROM streetlights ORDER BY asset_id").fetchall(); con.close(); return [tuple(r) for r in rows]

def update_streetlight(asset_id,status,issue='',priority='LOW',latitude=None,longitude=None):
    con=connect(); c=con.cursor(); c.execute("UPDATE streetlights SET status=?,issue=?,priority=?,latitude=COALESCE(?,latitude),longitude=COALESCE(?,longitude),updated_at=? WHERE asset_id=?",
      (status,issue,priority,latitude,longitude,now(),asset_id)); c.execute("INSERT INTO maintenance_history(asset_type,asset_id,event,status,priority,note,timestamp) VALUES(?,?,?,?,?,?,?)",
      ('Street Light',asset_id,'Status update',status,priority,issue,now())); con.commit(); con.close()

def add_streetlight(asset_id,location,latitude=None,longitude=None):
    con=connect(); con.execute("INSERT OR IGNORE INTO streetlights(asset_id,location,status,updated_at,latitude,longitude,priority) VALUES(?,?,?,?,?,?,?)",(asset_id,location,'Working',now(),latitude,longitude,'LOW')); con.commit(); con.close()

def add_manual_report(report_type,asset_id,location,description,priority,evidence_path=''):
    con=connect(); c=con.cursor(); c.execute("INSERT INTO manual_reports(timestamp,report_type,asset_id,location,description,priority,status,evidence_path) VALUES(?,?,?,?,?,?,?,?)",(now(),report_type,asset_id,location,description,priority,'Reported',evidence_path)); rid=c.lastrowid; con.commit(); con.close(); return rid

def get_manual_reports():
    con=connect(); rows=con.execute("SELECT id,timestamp,report_type,asset_id,location,description,priority,status,evidence_path FROM manual_reports ORDER BY id DESC").fetchall(); con.close(); return [tuple(r) for r in rows]

def update_report(rid,status):
    con=connect(); con.execute("UPDATE manual_reports SET status=? WHERE id=?",(status,rid)); con.commit(); con.close()

def get_history(limit=500):
    con=connect(); rows=con.execute("SELECT id,asset_type,asset_id,event,status,priority,note,timestamp FROM maintenance_history ORDER BY id DESC LIMIT ?",(limit,)).fetchall(); con.close(); return [tuple(r) for r in rows]
