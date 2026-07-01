"""
risk.py — 보행 위험 우선순위 엔진 (Walking Risk Logic)

GUARDIAN 재사용:
  - SAFE/CAUTION/WARNING/DANGER 상태머신 아이디어 → L1~L4 음성 우선순위로 매핑
  - analyze_forward_vehicle 의 '전방 중앙 구역' 필터 → CENTER 판정
  - box_to_distance / 근접 밴드 → proximity

신규:
  - 청각 출력 특화 이벤트(kind) + 방향(side)
  - 보행 환경(점자블록/횡단보도/계단/보도끝)은 env 입력으로 주입 (탐지기 교체 가능)

입력 detection 스키마 (GUARDIAN yolo_json 과 동일):
  {'cls': 'car', 'conf': 0.8, 'xyxy': [x1,y1,x2,y2], 'id': 12(optional)}
"""
from __future__ import annotations
from dataclasses import dataclass, field
from . import geometry as G

# 음성 우선순위 등급
L1_IMMEDIATE = 1   # 즉시 위험 — 인터럽트, 강한 진동
L2_CAUTION = 2     # 주의 필요
L3_GUIDE = 3       # 길 안내
L4_INFO = 4        # 참고 정보

VEHICLE_CLASSES = {"car", "truck", "bus"}
MOTO_CLASSES = {"motorcycle", "bicycle"}
PERSON_CLASSES = {"person"}


@dataclass
class Hazard:
    level: int
    kind: str
    side: str = "CENTER"       # LEFT/CENTER/RIGHT
    conf: float = 1.0
    key: str = ""              # 중복 억제용 안정 키
    def __post_init__(self):
        if not self.key:
            self.key = f"{self.kind}:{self.side}"


class WalkingRiskEngine:
    def __init__(self, conf_gate: float = 0.35, approach_history: int = 6):
        self.conf_gate = conf_gate
        self.tracker = G.ApproachTracker(history=approach_history)

    def process(self, detections, env, frame_w, frame_h):
        """detections: list(dict) 객체탐지, env: dict 보행환경 신호 → list[Hazard]"""
        hazards = []

        # ---------- 1) 동적 객체 (차량/오토바이/사람) ----------
        for det in detections:
            if det.get("conf", 1.0) < self.conf_gate:
                continue
            cls = det["cls"]
            xyxy = det["xyxy"]
            zone = G.horizontal_zone(xyxy, frame_w)
            band = G.proximity_band(xyxy, frame_w, frame_h)
            area = G.area_ratio(xyxy, frame_w, frame_h)
            approaching = self.tracker.update(det, area, zone)
            side = G.side_word(zone)
            conf = det.get("conf", 1.0)

            if cls in VEHICLE_CLASSES or cls in MOTO_CLASSES:
                is_moto = cls in MOTO_CLASSES
                # L1: 가깝고 (접근중 or 정면) → 즉시 정지 안내
                if band == G.NEAR and (approaching or zone == G.CENTER):
                    kind = "moto_imminent" if is_moto else "vehicle_imminent"
                    hazards.append(Hazard(L1_IMMEDIATE, kind, zone, conf))
                # L2: 접근 중이거나 중간거리 정면 → 주의
                elif approaching or (band == G.MID and zone == G.CENTER):
                    kind = "moto_caution" if is_moto else "vehicle_caution"
                    hazards.append(Hazard(L2_CAUTION, kind, zone, conf))

            elif cls in PERSON_CLASSES:
                # 사람은 전방 근접 시에만 (측면 사람은 굳이 안 알림 → 피로 방지)
                if zone == G.CENTER and band == G.NEAR:
                    hazards.append(Hazard(L2_CAUTION, "person_front", zone, conf))

            else:
                # 그 외 COCO 객체 중 전방 근접한 것 = 일반 장애물
                if zone == G.CENTER and band == G.NEAR:
                    hazards.append(Hazard(L2_CAUTION, "obstacle_front", zone, conf))

        # ---------- 2) 보행 환경 (env 신호) ----------
        # env 예: {'stairs':'front', 'curb':'front', 'boundary':True,
        #          'construction':'front', 'braille':'left'|'right'|'on',
        #          'crosswalk':True, 'drop':'front'}
        if env:
            if env.get("drop") == "front":
                hazards.append(Hazard(L1_IMMEDIATE, "drop_imminent", "CENTER"))
            if env.get("stairs") == "front":
                hazards.append(Hazard(L2_CAUTION, "stairs_front", "CENTER"))
            if env.get("curb") == "front":
                hazards.append(Hazard(L2_CAUTION, "curb_front", "CENTER"))
            if env.get("boundary"):
                hazards.append(Hazard(L2_CAUTION, "boundary_edge", "CENTER"))
            if env.get("construction") == "front":
                hazards.append(Hazard(L2_CAUTION, "construction_front", "CENTER"))
            b = env.get("braille")
            if b in ("left", "right"):
                zone = G.LEFT if b == "left" else G.RIGHT
                hazards.append(Hazard(L3_GUIDE, "braille_guide", zone))
            elif b == "on":
                hazards.append(Hazard(L3_GUIDE, "braille_on", "CENTER"))
            if env.get("crosswalk"):
                hazards.append(Hazard(L4_INFO, "crosswalk_front", "CENTER"))
            if env.get("signal_wait"):
                hazards.append(Hazard(L4_INFO, "signal_wait", "CENTER"))

        # 낮은 등급(=높은 우선순위) 먼저
        hazards.sort(key=lambda h: (h.level, -h.conf))
        return hazards
