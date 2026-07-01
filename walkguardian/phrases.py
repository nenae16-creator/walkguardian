"""
phrases.py — 짧은 한국어 음성 문안 매핑
원칙: 2~4어절 초단문. 방향은 단어(왼쪽/오른쪽/앞)로 인코딩.
과장 금지: '멈추세요'는 즉시위험(L1)에만.
"""

# (kind) -> 문안 템플릿. {side} 는 '왼쪽/오른쪽/앞' 으로 치환.
PHRASES = {
    # L1 즉시 위험
    "vehicle_imminent": "정지, {side} 차량 접근",
    "moto_imminent": "정지, {side} 오토바이 접근",
    "drop_imminent": "정지, 앞 낭떠러지",
    # L2 주의
    "vehicle_caution": "{side} 차량 주의",
    "moto_caution": "{side} 오토바이 주의",
    "obstacle_front": "앞 장애물",
    "person_front": "앞 사람",
    "stairs_front": "앞 계단 주의",
    "curb_front": "앞 턱 주의",
    "boundary_edge": "보도 끝 주의",
    "construction_front": "앞 공사구간",
    # L3 길 안내
    "braille_guide": "{side} 점자블록",
    "braille_on": "점자블록 위",
    # L4 참고
    "crosswalk_front": "앞 횡단보도",
    "signal_wait": "신호 대기",
}


def render(kind: str, side_word: str = "앞") -> str:
    tmpl = PHRASES.get(kind, kind)
    return tmpl.format(side=side_word)
