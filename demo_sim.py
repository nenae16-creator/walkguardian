"""
demo_sim.py — 전체 파이프라인 통합 데모 (GPU/카메라/스피커 불필요)

합성 보행 시나리오를 프레임 단위로 흘려보내며, 걸음지기가 '언제 무엇을 말하는지'를
콘솔에 출력한다. voice 는 콘솔 폴백이라 스피커 없이도 확인 가능.

시나리오(10fps, 총 8초):
  0.0~2.0s  왼쪽 점자블록(L3) + 앞 횡단보도(L4)  — 길안내/참고
  2.0~4.0s  전방 근접 장애물(L2)                — 주의
  4.0~6.0s  오른쪽에서 차량이 점점 접근(L1)      — 즉시 위험(인터럽트)
  6.0~8.0s  위험 해소, 다시 점자블록 안내
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from walkguardian.pipeline import WalkGuardian
from walkguardian.voice import Voice

W, H = 1280, 720
FPS = 10.0


def box(cx_frac, size):
    cx, cy = cx_frac * W, 0.6 * H
    half = size * min(W, H) / 2
    return [cx - half, cy - half, cx + half, cy + half]


def scenario(i):
    """frame idx → (detections, env)"""
    t = i / FPS
    if t < 2.0:
        return [], {"braille": "left", "crosswalk": True}
    if t < 4.0:
        return [{"cls": "chair", "conf": 0.8, "id": 10, "xyxy": box(0.5, 0.45)}], {}
    if t < 6.0:
        grow = 0.18 + (t - 4.0) * 0.10          # 0.18 → 0.38 : 프레임마다 커짐(접근)
        return [{"cls": "car", "conf": 0.9, "id": 20, "xyxy": box(0.80, grow)}], {}
    return [], {"braille": "left"}


def main():
    state = {"i": 0}
    wg = WalkGuardian(
        detector=lambda frame: scenario(state["i"])[0],
        env_detector=lambda frame, dets: scenario(state["i"])[1],
        voice=Voice(use_tts=False, echo=False),
    )
    print("🚶 걸음지기 통합 데모 (8초, 10fps) — 언제 무엇을 말하나\n" + "=" * 50)
    seg = None
    for i in range(int(8.0 * FPS)):
        state["i"] = i
        t = i / FPS
        cur = ("길안내" if t < 2 else "장애물" if t < 4 else "차량접근" if t < 6 else "해소")
        if cur != seg:
            seg = cur
            print(f"[{t:4.1f}s] ── {cur} 구간 ──")
        alerts, _, _ = wg.step(None, t, (W, H), moving=True)
        for a in alerts:
            tag = {1: "🔴즉시", 2: "🟠주의", 3: "🟡길", 4: "⚪참고"}[a.level]
            print(f"        t={t:4.1f}s  {tag}  «{a.text}»")
    print("=" * 50 + "\n✅ 데모 종료")


if __name__ == "__main__":
    main()
