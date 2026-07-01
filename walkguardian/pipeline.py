"""
pipeline.py — 걸음지기 파이프라인 조립

카메라/영상 프레임 → 객체탐지 → 보행환경 인식 → 위험 우선순위(WalkingRiskEngine)
                    → 알림 스케줄러(피로방지) → 짧은 음성/진동

env_detector 는 교체 가능한 인터페이스:
  - NullEnv       : 아무 환경신호 없음 (객체탐지만으로 데모)
  - (향후) 점자블록/횡단보도/계단 세그멘테이션 모델 또는 공공데이터 지오펜스
"""
from __future__ import annotations
from .risk import WalkingRiskEngine
from .scheduler import AlertScheduler
from .voice import Voice


class NullEnv:
    """환경 신호 없음(placeholder). 실제로는 seg 모델/공공데이터로 교체."""
    def __call__(self, frame, detections):
        return {}


class ScriptedEnv:
    """데모/테스트용: 프레임 인덱스별 env 를 미리 지정."""
    def __init__(self, timeline: dict):
        self.timeline = timeline    # {frame_idx: env_dict}
        self._i = 0

    def __call__(self, frame, detections):
        env = self.timeline.get(self._i, {})
        self._i += 1
        return env


class WalkGuardian:
    def __init__(self, detector, env_detector=None, voice: Voice | None = None,
                 conf_gate: float = 0.35):
        self.detector = detector
        self.env = env_detector or NullEnv()
        self.engine = WalkingRiskEngine(conf_gate=conf_gate)
        self.scheduler = AlertScheduler()
        self.voice = voice if voice is not None else Voice(use_tts=False)

    def step(self, frame, t: float, frame_wh, moving: bool = True):
        w, h = frame_wh
        detections = self.detector(frame) if callable(self.detector) else self.detector
        env = self.env(frame, detections)
        hazards = self.engine.process(detections, env, w, h)
        alerts = self.scheduler.feed(hazards, t, moving)
        for a in alerts:
            self.voice.announce(a)
        return alerts, detections, env
