"""
test_logic.py — 순수 로직 검증 (GPU/카메라/TTS 불필요, 지금 바로 실행)
합성 탐지 시퀀스로 L1~L4 우선순위 / 인터럽트 / 쿨다운 / persist / 정지침묵 확인.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from walkguardian.risk import WalkingRiskEngine
from walkguardian.scheduler import AlertScheduler

W, H = 1280, 720


def box_center(frac_w, y_frac, size):
    """화면 비율로 박스 생성. size=한 변 비율."""
    cx, cy = frac_w * W, y_frac * H
    half = size * min(W, H) / 2
    return [cx - half, cy - half, cx + half, cy + half]


def run(seq, moving_seq=None, fps=10.0):
    eng, sch = WalkingRiskEngine(), AlertScheduler()
    spoken = []
    for i, (dets, env) in enumerate(seq):
        t = i / fps
        moving = True if moving_seq is None else moving_seq[i]
        hz = eng.process(dets, env, W, H)
        for a in sch.feed(hz, t, moving):
            spoken.append((round(t, 2), a.level, a.text))
    return spoken


def test_l1_vehicle_interrupt():
    """정면 근접 차량 + 동시에 횡단보도(L4) → L1만, L4는 억제."""
    big_car = {"cls": "car", "conf": 0.9, "id": 1, "xyxy": box_center(0.5, 0.6, 0.45)}
    env = {"crosswalk": True}
    seq = [([big_car], env)] * 6
    out = run(seq)
    assert any(l == 1 and "차량" in txt for _, l, txt in out), out
    assert not any(l == 4 for _, l, txt in out), f"L4 must be interrupted: {out}"
    print("  ✓ L1 차량 인터럽트 — L4 억제:", out[:2])


def test_persist_debounce():
    """1프레임 blip 은 L2를 발화하지 않아야 함 (L2 persist=3).
    ※ L1(즉시위험)은 persist=1 로 의도적으로 즉발 → 여기선 L2 장애물로 검증."""
    obst = {"cls": "chair", "conf": 0.9, "id": 2, "xyxy": box_center(0.5, 0.6, 0.45)}
    empty = ([], None)
    seq = [([obst], None), empty, empty, empty, empty]  # 딱 1프레임만 등장
    out = run(seq)
    assert out == [], f"single-frame L2 blip should not speak: {out}"
    print("  ✓ persist 디바운스 — 1프레임 blip 무시 (L2)")


def test_cooldown_no_repeat():
    """정면 근접 장애물이 계속 있어도 쿨다운 내 반복 발화 금지."""
    obst = {"cls": "chair", "conf": 0.9, "id": 3, "xyxy": box_center(0.5, 0.6, 0.45)}
    seq = [([obst], None)] * 20  # 2초간 지속
    out = run(seq, fps=10.0)
    l2 = [o for o in out if o[1] == 2]
    assert len(l2) == 1, f"cooldown should limit to 1 in 2s: {l2}"
    print("  ✓ 쿨다운 — 2초 지속에도 1회만:", l2)


def test_l4_silent_when_stopped():
    """정지(moving=False) 중 횡단보도(L4)는 침묵."""
    env = {"crosswalk": True}
    seq = [([], env)] * 10
    out = run(seq, moving_seq=[False] * 10)
    assert out == [], f"L4 must be silent when stopped: {out}"
    print("  ✓ 정지 침묵 — 정지 중 L4 미발화")


def test_l3_braille_guide():
    """왼쪽 점자블록 → L3 '왼쪽 점자블록'."""
    env = {"braille": "left"}
    seq = [([], env)] * 8
    out = run(seq)
    assert any(l == 3 and "왼쪽 점자블록" in txt for _, l, txt in out), out
    print("  ✓ L3 점자블록 방향 안내:", [o for o in out if o[1] == 3][:1])


def test_priority_order():
    """L2 장애물 + L3 점자블록 동시 → L2가 먼저(우선)."""
    obst = {"cls": "pole", "conf": 0.9, "id": 4, "xyxy": box_center(0.5, 0.6, 0.45)}
    env = {"braille": "right"}
    seq = [([obst], env)] * 6
    out = run(seq)
    first_levels = [l for _, l, _ in out]
    assert 2 in first_levels, out
    if 2 in first_levels and 3 in first_levels:
        assert first_levels.index(2) < first_levels.index(3), out
    print("  ✓ 우선순위 — L2가 L3보다 먼저:", out[:3])


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"\n🧪 걸음지기 로직 테스트 ({len(tests)}개)\n" + "-" * 44)
    fails = 0
    for fn in tests:
        try:
            fn()
        except AssertionError as e:
            fails += 1
            print(f"  ✗ FAIL {fn.__name__}: {e}")
    print("-" * 44)
    print("✅ 전부 통과" if fails == 0 else f"❌ {fails}개 실패")
    sys.exit(1 if fails else 0)
