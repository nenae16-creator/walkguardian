"""
geometry.py — 근접도 / 방향 / 접근 판정
GUARDIAN(이륜차 HUD)의 box_to_distance 를 그대로 재사용하되,
보행 보조에서는 '정확한 미터(m)'를 주장하지 않고 '근접 밴드(NEAR/MID/FAR)'로만 쓴다.

재사용 출처: 가디언 프로젝트/코드/v9_all_in_one.py 의 box_to_distance / analyze_forward_vehicle
"""
from __future__ import annotations
import math
from collections import deque, defaultdict

# ---- 근접 밴드 (영역 비율 기준) --------------------------------------------
# 주의: 이 임계값은 휴대폰/목걸이 카메라 화각에 따라 현장 캘리브레이션 필요.
#       절대 거리(m)가 아니라 상대적 '가까움' 신호로만 사용한다.
NEAR = "NEAR"   # 매우 가까움
MID = "MID"     # 중간
FAR = "FAR"     # 멀리
BAND_NEAR_RATIO = 0.060   # 화면의 6% 이상 차지 → 가까움
BAND_MID_RATIO = 0.015    # 1.5% 이상 → 중간

# ---- 수평 구역 -------------------------------------------------------------
LEFT, CENTER, RIGHT = "LEFT", "CENTER", "RIGHT"
ZONE_LEFT_MAX = 0.38
ZONE_RIGHT_MIN = 0.62


def box_to_distance(area: float, frame_area: float) -> float:
    """GUARDIAN v3 공식(역제곱근). 캘리브레이션 안 된 '상대' 추정치.
    보행 보조에서는 밴드 판정의 보조 지표로만 쓰고 사용자에게 미터를 말하지 않는다."""
    if frame_area <= 0:
        return 150.0
    ratio = area / frame_area
    if ratio <= 1e-6:
        return 150.0
    d = 1.64 / math.sqrt(ratio)
    return max(1.0, min(150.0, d))


def area_ratio(xyxy, frame_w: int, frame_h: int) -> float:
    x1, y1, x2, y2 = xyxy
    a = max(0.0, (x2 - x1)) * max(0.0, (y2 - y1))
    fa = float(frame_w * frame_h)
    return (a / fa) if fa > 0 else 0.0


def proximity_band(xyxy, frame_w: int, frame_h: int) -> str:
    r = area_ratio(xyxy, frame_w, frame_h)
    if r >= BAND_NEAR_RATIO:
        return NEAR
    if r >= BAND_MID_RATIO:
        return MID
    return FAR


def horizontal_zone(xyxy, frame_w: int) -> str:
    x1, _, x2, _ = xyxy
    cx = (x1 + x2) / 2.0 / max(1, frame_w)
    if cx < ZONE_LEFT_MAX:
        return LEFT
    if cx > ZONE_RIGHT_MIN:
        return RIGHT
    return CENTER


def side_word(zone: str) -> str:
    return {"LEFT": "왼쪽", "RIGHT": "오른쪽", "CENTER": "앞"}[zone]


class ApproachTracker:
    """객체 박스 면적의 시간적 증가율로 '접근 중' 판정.
    GUARDIAN 후방 레이더(intensity) 아이디어를 실제 면적 추적으로 대체.
    - id 가 있으면 id 별로, 없으면 (cls, zone) 버킷으로 근사 추적.
    """

    def __init__(self, history: int = 6, grow_ratio: float = 1.18):
        self.history = history
        self.grow_ratio = grow_ratio       # 최근 창에서 면적이 18% 이상 커지면 접근
        self._buf = defaultdict(lambda: deque(maxlen=history))

    def _key(self, det, zone):
        return det.get("id", f"{det['cls']}:{zone}")

    def update(self, det, area: float, zone: str) -> bool:
        key = self._key(det, zone)
        buf = self._buf[key]
        buf.append(area)
        if len(buf) < max(3, self.history // 2):
            return False
        first = buf[0] if buf[0] > 0 else 1e-9
        return (buf[-1] / first) >= self.grow_ratio

    def reset(self):
        self._buf.clear()
