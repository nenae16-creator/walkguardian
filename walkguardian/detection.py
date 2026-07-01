"""
detection.py — 객체 탐지기 (GUARDIAN 재사용)

두 가지 소스:
  1) YOLOv8Detector  — ultralytics 실시간 추론(CPU 가능, model.track 으로 id 부여)
  2) OfflineCache    — GUARDIAN 이 만들어둔 yolo_json 캐시 재사용 (GPU 불필요)

출력 스키마(공통): [{'cls','conf','xyxy':[x1,y1,x2,y2],'id'(opt)}...]
관심 클래스는 GUARDIAN INTEREST_CLASSES 와 동일 계열.
"""
from __future__ import annotations
import json
from pathlib import Path

# GUARDIAN 과 동일한 관심 클래스(보행 맥락)
INTEREST = {"person", "bicycle", "car", "motorcycle", "bus", "truck",
            "traffic light", "stop sign", "bench", "chair", "pole",
            "fire hydrant", "potted plant"}


class YOLOv8Detector:
    """ultralytics YOLOv8. 미설치면 import 시점에서 알려줌."""
    def __init__(self, weights: str = "yolov8n.pt", conf: float = 0.3,
                 imgsz: int = 640, use_track: bool = True):
        from ultralytics import YOLO   # lazy import
        self.model = YOLO(weights)
        self.conf = conf
        self.imgsz = imgsz
        self.use_track = use_track
        self.names = self.model.names

    def __call__(self, frame):
        if self.use_track:
            res = self.model.track(frame, persist=True, conf=self.conf,
                                   imgsz=self.imgsz, verbose=False)[0]
        else:
            res = self.model(frame, conf=self.conf, imgsz=self.imgsz, verbose=False)[0]
        out = []
        if res.boxes is None:
            return out
        for b in res.boxes:
            cls = self.names[int(b.cls[0])]
            if cls not in INTEREST:
                continue
            x1, y1, x2, y2 = [float(v) for v in b.xyxy[0]]
            det = {"cls": cls, "conf": float(b.conf[0]), "xyxy": [x1, y1, x2, y2]}
            if b.id is not None:
                det["id"] = int(b.id[0])
            out.append(det)
        return out


class OfflineCache:
    """GUARDIAN yolo_json 캐시 재사용. frames[i]['objects'] 를 그대로 반환."""
    def __init__(self, json_path: str):
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        self.frames = data["frames"]
        self.width = data.get("width")
        self.height = data.get("height")
        self.fps = data.get("fps", 30)

    def __len__(self):
        return len(self.frames)

    def at(self, i):
        if i < 0 or i >= len(self.frames):
            return []
        objs = self.frames[i].get("objects", [])
        # 캐시엔 id 가 없을 수 있음 → 그대로 통과(ApproachTracker 가 근사 처리)
        return [{"cls": o["cls"], "conf": o.get("conf", 0.5), "xyxy": o["xyxy"]}
                for o in objs if o["cls"] in INTEREST]
