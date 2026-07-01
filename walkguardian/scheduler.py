"""
scheduler.py — 알림 스케줄러 (피로 방지 로직)  ★기획서 7항의 핵심★

GUARDIAN 재사용:
  - LDWState 히스테리시스(연속 N프레임 + off 디바운싱) → 오탐 1프레임 blip 억제
재설계:
  - 등급별 쿨다운(중복 안내 방지)
  - L3/L4 레이트리밋(창당 개수 제한)
  - L1 인터럽트(하위 등급 즉시 중단)
  - 정지 시 참고정보(L4) 침묵
  - 상태 변화 우선(같은 키 연속 반복 억제는 쿨다운이 담당)

feed(hazards, t, moving) → 이번 tick 에 '실제로 말할' Alert 리스트(보통 0~1개).
시간 t(초)는 외부에서 주입 → 결정적/테스트 가능.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, deque

from . import phrases as P
from . import geometry as G


@dataclass
class Alert:
    level: int
    kind: str
    side: str
    text: str


# 등급별 파라미터
PERSIST_FRAMES = {1: 1, 2: 3, 3: 4, 4: 5}   # 이 프레임 수 이상 연속돼야 발화 (L1은 즉시)
COOLDOWN_SEC = {1: 1.2, 2: 3.0, 3: 6.0, 4: 8.0}  # 같은 key 재안내 최소 간격
RATE_WINDOW_SEC = 4.0
RATE_MAX_LOW = 2            # 창(4초) 내 L3/L4 최대 발화 수


class AlertScheduler:
    def __init__(self):
        self._persist = defaultdict(int)     # key -> 연속 관측 프레임
        self._last_spoken = {}               # key -> t
        self._low_emits = deque()            # 최근 L3/L4 발화 시각들
        self._seen_this_tick = set()

    def feed(self, hazards, t: float, moving: bool = True):
        # 1) 지속(persist) 카운트 갱신 — 이번 tick 에 보인 key 만 +1, 나머지는 리셋
        seen = set()
        by_key = {}
        for h in hazards:
            seen.add(h.key)
            self._persist[h.key] += 1
            # 같은 key 여러개면 등급 높은(숫자 작은) 것 유지
            if h.key not in by_key or h.level < by_key[h.key].level:
                by_key[h.key] = h
        for k in list(self._persist.keys()):
            if k not in seen:
                self._persist[k] = 0

        # 2) persist 충족한 '활성' 위험만 (오탐 1프레임 blip 억제)
        active = [h for key, h in by_key.items()
                  if self._persist[key] >= PERSIST_FRAMES.get(h.level, 3)]
        if not active:
            return []
        active.sort(key=lambda h: (h.level, -h.conf))

        # 3) 인터럽트: L1 이 활성이면 하위 등급 '완전 억제'.
        #    L1 은 쿨다운 통과 시에만 재발화, 아니면 침묵(하위 누수 방지).
        l1 = [h for h in active if h.level == 1]
        if l1:
            top = l1[0]
            return [self._emit(top, t)] if self._cooldown_ok(top, t) else []

        # 4) L2~L4: 우선순위 순으로 쿨다운/레이트리밋/정지침묵 통과하는 첫 항목 1개만 발화
        for h in active:
            if h.level >= 4 and not moving:      # 정지 중 참고정보 침묵
                continue
            if not self._cooldown_ok(h, t):       # 중복 안내 방지
                continue
            if h.level >= 3:                      # L3/L4 레이트리밋
                self._prune_low(t)
                if len(self._low_emits) >= RATE_MAX_LOW:
                    continue
                self._low_emits.append(t)
            return [self._emit(h, t)]             # 한 tick 에 한 마디 (음성 채널 직렬)
        return []

    def _cooldown_ok(self, h, t):
        last = self._last_spoken.get(h.key)
        return last is None or (t - last) >= COOLDOWN_SEC.get(h.level, 3.0)

    def _emit(self, h, t):
        self._last_spoken[h.key] = t
        text = P.render(h.kind, G.side_word(h.side))
        return Alert(h.level, h.kind, h.side, text)

    def _prune_low(self, t):
        while self._low_emits and (t - self._low_emits[0]) > RATE_WINDOW_SEC:
            self._low_emits.popleft()
