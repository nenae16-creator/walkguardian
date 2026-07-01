"""탐지/근접 밴드 진단: 실제 영상에서 무엇이 잡히고 어떤 밴드인지 확인."""
import sys, os, cv2, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from walkguardian.detection import YOLOv8Detector
from walkguardian.risk import WalkingRiskEngine
from walkguardian import geometry as G

vid = sys.argv[1]
max_sec = float(sys.argv[2]) if len(sys.argv) > 2 else 6
cap = cv2.VideoCapture(vid)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
det = YOLOv8Detector()
eng = WalkingRiskEngine()
W = 640
band_hist = collections.Counter()
cls_hist = collections.Counter()
raw_hazards = collections.Counter()
i = 0
while i < int(max_sec * fps):
    ret, fr = cap.read()
    if not ret:
        break
    h0, w0 = fr.shape[:2]
    fr = cv2.resize(fr, (W, int(h0 * W / w0)))
    H = fr.shape[0]
    dets = det(fr)
    for d in dets:
        cls_hist[d["cls"]] += 1
        band_hist[G.proximity_band(d["xyxy"], W, H)] += 1
    for hz in eng.process(dets, {}, W, H):
        raw_hazards[f"L{hz.level}:{hz.kind}:{hz.side}"] += 1
    i += 1
cap.release()
print(f"[{os.path.basename(vid)}] {i}프레임")
print("  클래스:", dict(cls_hist.most_common()))
print("  밴드  :", dict(band_hist))
print("  원시위험(스케줄러 전):", dict(raw_hazards.most_common(8)) or "없음")
