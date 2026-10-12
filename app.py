import streamlit as st
import pandas as pd
import cv2
import time
from pathlib import Path

from src.db import *
from src.pothole import PotholeSegmenter
from src.streetlight import StreetLightDetector

ROOT = Path(__file__).resolve().parent
UP = ROOT / 'detections' / 'uploads'
UP.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title='RAAH AI', page_icon='🛣️', layout='wide')
init_db()

@st.cache_resource
def models():
    return PotholeSegmenter(conf=.25), StreetLightDetector(conf=.25)

pothole, lights = models()

st.title('🛣️ RAAH AI — Colony Road Infrastructure Intelligence')
st.caption('Potholes • Street lights • Human verification • Maintenance • Image/video/webcam inspection')

if not pothole.custom:
    st.warning('Pothole AI weights missing: add models/pothole_seg.pt. The app will NOT fake pothole detections with COCO.')
if not lights.available:
    st.info('Street-light AI weights missing: add models/streetlight.pt. Manual asset/report workflow still works.')


def detect_frame(frame, source, save=True):
    pa, pdets = pothole.infer(frame)
    _la, ldets = lights.infer(frame)
    out = pa.copy()
    for d in ldets:
        x1, y1, x2, y2 = d['bbox']
        cv2.rectangle(out, (x1, y1), (x2, y2), (255, 255, 255), 2)
        cv2.putText(
            out,
            f"LIGHT {d['status']} {d['confidence']:.2f}",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            .55,
            (255, 255, 255),
            2,
        )
    path = ''
    if save and (pdets or ldets):
        path = str(UP / f"{source}_{int(time.time()*1000)}.jpg")
        cv2.imwrite(path, out)
        for d in pdets:
            add_pothole(d['confidence'], d['area_ratio'], d['severity'], path, source)
    return out, pdets, ldets, path


tabs = st.tabs([
    '🏠 Dashboard',
    '📤 AI Inspect',
    '📷 Webcam Snapshot',
    '🕳️ Review Queue',
    '💡 Street Lights',
    '📝 Manual Reports',
    '🗺️ Colony Map',
    '🔧 Maintenance History',
])

with tabs[0]:
    p = pd.DataFrame(get_potholes(), columns=['ID','Timestamp','Confidence','Area Ratio','Severity','Image','Source','Review','Notes'])
    s = pd.DataFrame(get_streetlights(), columns=['ID','Asset ID','Location','Status','Issue','Updated','Latitude','Longitude','Priority'])
    r = pd.DataFrame(get_manual_reports(), columns=['ID','Timestamp','Type','Asset ID','Location','Description','Priority','Status','Evidence'])
    a,b,c,d,e = st.columns(5)
    a.metric('AI Potholes', len(p))
    b.metric('Street Lights', len(s))
    c.metric('Faulty/Flickering', int(s['Status'].isin(['Faulty','Flickering']).sum()) if len(s) else 0)
    d.metric('Pending AI Review', int((p['Review']=='Pending').sum()) if len(p) else 0)
    e.metric('Open Reports', int((r['Status']!='Resolved').sum()) if len(r) else 0)
    st.subheader('Priority view')
    if len(s):
        st.dataframe(s[s['Status']!='Working'][['Asset ID','Location','Status','Priority','Issue','Updated']], use_container_width=True, hide_index=True)
    else:
        st.info('No street-light records yet.')

with tabs[1]:
    st.subheader('Inspect uploaded photo or video')
    f = st.file_uploader(
        'Upload JPG/PNG or MP4/AVI/MOV',
        type=['jpg','jpeg','png','bmp','mp4','avi','mov','mkv'],
        key='inspect_upload'
    )
    conf = st.slider('Detection confidence', .05, .9, .25, .05, key='inspect_conf')
    pothole.conf = conf
    lights.conf = conf

    if f:
        suffix = Path(f.name).suffix.lower()
        inp = UP / f"input_{int(time.time())}{suffix}"
        inp.write_bytes(f.getbuffer())

        if suffix in ['.jpg','.jpeg','.png','.bmp']:
            img = cv2.imread(str(inp))
            if img is None:
                st.error('Could not read that image.')
            else:
                st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption='Input', use_container_width=True)
                if st.button('Run AI inspection', type='primary', key='run_image_ai'):
                    out, pdets, ldets, path = detect_frame(img, 'uploaded_image')
                    st.image(cv2.cvtColor(out, cv2.COLOR_BGR2RGB), caption='Detection result', use_container_width=True)
                    st.success(f'{len(pdets)} pothole(s), {len(ldets)} street-light detection(s)')
                    if pdets:
                        st.dataframe(pd.DataFrame(pdets).drop(columns=['bbox']), use_container_width=True)
                    if ldets:
                        st.dataframe(pd.DataFrame(ldets).drop(columns=['bbox']), use_container_width=True)
                    if not pdets and not ldets:
                        st.warning('No infrastructure objects detected. If weights are missing, add the trained .pt files first.')
        else:
            if st.button('Analyze video', type='primary', key='run_video_ai'):
                cap = cv2.VideoCapture(str(inp))
                fps = cap.get(cv2.CAP_PROP_FPS) or 25
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
                outp = UP / f"annotated_{int(time.time())}.mp4"
                wr = cv2.VideoWriter(str(outp), cv2.VideoWriter_fourcc(*'mp4v'), fps, (w,h))
                totalp = totall = frame = 0
                prog = st.progress(0)
                n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                lastlog = -999
                while True:
                    ok, im = cap.read()
                    if not ok:
                        break
                    ann, pdets, ldets, _ = detect_frame(im, 'uploaded_video', save=False)
                    wr.write(ann)
                    totalp += len(pdets)
                    totall += len(ldets)
                    sec = frame / fps
                    if pdets and sec - lastlog >= 2:
                        snap = str(UP / f"video_{int(time.time()*1000)}.jpg")
                        cv2.imwrite(snap, ann)
                        for x in pdets:
                            add_pothole(x['confidence'], x['area_ratio'], x['severity'], snap, 'uploaded_video')
                        lastlog = sec
                    frame += 1
                    if n:
                        prog.progress(min(frame/n, 1.0))
                cap.release()
                wr.release()
                prog.empty()
                st.success(f'Finished. Detection events: potholes {totalp}, street lights {totall}')
                st.video(str(outp))

with tabs[2]:
    st.subheader('Webcam snapshot inspection')
    st.write('This uses your browser camera for a photo. For continuous live video, run **run_live.bat** from the project folder.')
    shot = st.camera_input('Take a road photo', key='camera_snapshot')
    cam_conf = st.slider('Webcam snapshot confidence', .05, .9, .25, .05, key='cam_conf')
    pothole.conf = cam_conf
    lights.conf = cam_conf
    if shot is not None:
        data = shot.getvalue()
        arr = cv2.imdecode(pd.Series([data]).iloc[0] if False else __import__('numpy').frombuffer(data, dtype='uint8'), cv2.IMREAD_COLOR)
        if arr is None:
            st.error('Could not decode camera image.')
        elif st.button('Analyze webcam photo', type='primary', key='run_cam_snapshot'):
            out, pdets, ldets, path = detect_frame(arr, 'webcam_snapshot')
            st.image(cv2.cvtColor(out, cv2.COLOR_BGR2RGB), caption='Webcam detection result', use_container_width=True)
            st.success(f'{len(pdets)} pothole(s), {len(ldets)} street-light detection(s)')

with tabs[3]:
    df = pd.DataFrame(get_potholes(), columns=['ID','Timestamp','Confidence','Area Ratio','Severity','Image','Source','Review','Notes'])
    pending = df[df['Review']=='Pending'] if len(df) else df
    st.write('AI detections stay pending until a human confirms/rejects them.')
    if pending.empty:
        st.info('No pending detections.')
    else:
        st.dataframe(pending[['ID','Timestamp','Confidence','Area Ratio','Severity','Source']], use_container_width=True, hide_index=True)
        pid = st.selectbox('Detection ID', pending['ID'].tolist(), key='review_detection_id')
        note = st.text_input('Reviewer note', key='review_note')
        c1,c2 = st.columns(2)
        if c1.button('✅ Confirm', key='review_confirm'):
            review_pothole(pid, 'Confirmed', note)
            st.rerun()
        if c2.button('❌ Reject', key='review_reject'):
            review_pothole(pid, 'Rejected', note)
            st.rerun()

with tabs[4]:
    df = pd.DataFrame(get_streetlights(), columns=['ID','Asset ID','Location','Status','Issue','Updated','Latitude','Longitude','Priority'])
    st.dataframe(df, use_container_width=True, hide_index=True)
    with st.expander('Update a light', expanded=True):
        if len(df):
            aid = st.selectbox('Asset ID', df['Asset ID'].tolist(), key='light_asset_id')
            status = st.selectbox('Status', ['Working','Faulty','Under Repair','Flickering'], key='light_status')
            priority = st.selectbox('Priority', ['LOW','MEDIUM','HIGH'], key='light_priority')
            issue = st.text_input('Issue/note', key='light_issue')
            lat = st.number_input('Latitude (0 = leave unchanged)', value=0.0, format='%.6f', key='light_lat')
            lon = st.number_input('Longitude (0 = leave unchanged)', value=0.0, format='%.6f', key='light_lon')
            if st.button('Save street-light update', key='save_light'):
                update_streetlight(aid, status, issue, priority, lat or None, lon or None)
                st.success('Updated')
                st.rerun()
        else:
            st.info('Add a street light below first.')
    with st.expander('Add another numbered light'):
        aid2 = st.text_input('New ID', placeholder='S11', key='new_light_id')
        loc2 = st.text_input('Location/landmark', key='new_light_location')
        if st.button('Add light', key='add_light') and aid2:
            add_streetlight(aid2.strip().upper(), loc2)
            st.rerun()

with tabs[5]:
    st.subheader('Resident / committee manual fault report')
    typ = st.selectbox('Problem', ['Street Light','Pothole','Other'], key='report_problem_type')
    sdf = pd.DataFrame(get_streetlights(), columns=['ID','Asset ID','Location','Status','Issue','Updated','Latitude','Longitude','Priority'])
    aid = st.selectbox('Street-light asset (optional)', [''] + sdf['Asset ID'].tolist(), key='report_asset_id')
    loc = st.text_input('Location / landmark', key='report_location')
    desc = st.text_area('Describe the problem', key='report_description')
    pri = st.selectbox('Priority', ['LOW','MEDIUM','HIGH'], key='report_priority')
    ev = st.file_uploader('Optional evidence photo', type=['jpg','jpeg','png'], key='report_evidence')
    if st.button('Submit report', type='primary', key='submit_report'):
        ep = ''
        if ev:
            ep = str(UP / f"report_{int(time.time())}_{ev.name}")
            Path(ep).write_bytes(ev.getbuffer())
        add_manual_report(typ, aid, loc, desc, pri, ep)
        st.success('Report submitted for committee review.')

    rdf = pd.DataFrame(get_manual_reports(), columns=['ID','Timestamp','Type','Asset ID','Location','Description','Priority','Status','Evidence'])
    st.dataframe(rdf, use_container_width=True, hide_index=True)
    if len(rdf):
        rid = st.selectbox('Report to update', rdf['ID'].tolist(), key='report_to_update')
        rs = st.selectbox('Report status', ['Reported','Verified','Assigned','Under Repair','Resolved'], key='report_status_update')
        if st.button('Update report status', key='update_report_status'):
            update_report(rid, rs)
            st.rerun()

with tabs[6]:
    st.subheader('Numbered colony street-light map')
    df = pd.DataFrame(get_streetlights(), columns=['ID','Asset ID','Location','Status','Issue','Updated','Latitude','Longitude','Priority'])
    mapped = df[(df['Latitude'].notna()) & (df['Longitude'].notna()) & (df['Latitude']!=0) & (df['Longitude']!=0)].copy()
    if mapped.empty:
        st.info('Add latitude/longitude to street lights in the Street Lights tab. Then S01, S02… will appear here.')
    else:
        st.map(mapped.rename(columns={'Latitude':'lat','Longitude':'lon'})[['lat','lon']], use_container_width=True)
        st.dataframe(mapped[['Asset ID','Location','Status','Priority','Latitude','Longitude']], use_container_width=True, hide_index=True)

with tabs[7]:
    h = pd.DataFrame(get_history(), columns=['ID','Asset Type','Asset ID','Event','Status','Priority','Note','Timestamp'])
    st.dataframe(h, use_container_width=True, hide_index=True)

st.divider()
st.caption('RAAH AI uses visual AI assistance. Pothole severity is image-area severity, not physical depth. Street-light ON/OFF is a visual estimate and should be human-verified before maintenance action.')
