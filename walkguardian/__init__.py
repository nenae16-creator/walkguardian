"""
walkguardian — 걸음지기 / GUARDIAN-Walk
시각장애인 AI 청각 보행 보조 (GUARDIAN 이륜차 HUD 연구의 청각 확장)

⚠️ 이 시스템은 흰지팡이·안내견·보행훈련을 대체하지 않는 '보조 정보 제공' 도구입니다.
   사고 방지·정확한 거리·완전 자율 보행을 보장하지 않습니다.
"""
from .risk import WalkingRiskEngine, Hazard, L1_IMMEDIATE, L2_CAUTION, L3_GUIDE, L4_INFO
from .scheduler import AlertScheduler, Alert
from . import geometry, phrases

__all__ = [
    "WalkingRiskEngine", "Hazard", "AlertScheduler", "Alert",
    "geometry", "phrases",
    "L1_IMMEDIATE", "L2_CAUTION", "L3_GUIDE", "L4_INFO",
]
__version__ = "0.1.0"
