# 걸음지기 (GUARDIAN-Walk)

**시각장애인 AI 청각 보행 보조** — GUARDIAN(이륜차 상황인식 AR HUD) 연구의 청각 확장.

> ⚠️ 이 시스템은 흰지팡이·안내견·보행훈련을 **대체하지 않는 보조 정보 제공 도구**입니다.
> 사고 방지·정확한 거리·완전 자율 보행을 **보장하지 않습니다.**

---

## GUARDIAN에서 무엇을 재사용했나

| GUARDIAN (이륜차 HUD) | 걸음지기 (보행 청각) | 파일 |
|---|---|---|
| `box_to_distance` 역제곱근 거리추정 | 상대 근접 밴드(NEAR/MID/FAR) — 미터는 말하지 않음 | `geometry.py` |
| SAFE/CAUTION/WARNING/DANGER 상태머신 | L1~L4 음성 우선순위 | `risk.py` |
| `LDWState` 히스테리시스(연속 N프레임+디바운싱) | 알림 persist 디바운스 + 쿨다운 + 인터럽트 | `scheduler.py` |
| YOLOv8 객체탐지 + yolo_json 캐시 | 동일 스키마 재사용 (`OfflineCache`) | `detection.py` |
| HUD(PIL 오버레이) 출력 | **교체** → 짧은 음성(TTS)/진동 | `voice.py` |
| YOLOPv2 차선 | **교체 예정** → 보행환경(점자블록/보도경계/횡단보도) | `pipeline.py env` |

## 위험 우선순위 (핵심)

| 등급 | 의미 | 출력 | 예시 |
|---|---|---|---|
| L1 | 즉시 위험 | 음성+진동, **인터럽트**(하위 완전 억제) | "정지, 오른쪽 차량 접근" |
| L2 | 주의 | 음성+약진동 | "앞 장애물", "앞 계단 주의" |
| L3 | 길 안내 | 음성 | "왼쪽 점자블록" |
| L4 | 참고 | 음성(저빈도), 정지 시 침묵 | "앞 횡단보도" |

피로 방지: persist 디바운스(오탐 blip 억제) · 등급별 쿨다운(중복 억제) · L3/L4 레이트리밋 · L1 인터럽트 · 정지 침묵 · 신뢰도 게이트.

---

## 실행

```bash
# 1) 코어 로직 검증 (GPU/카메라/음성 불필요 — 지금 바로)
python tests/test_logic.py

# 2) 전체 파이프라인 통합 데모 (합성 시나리오, 콘솔 출력)
python demo_sim.py

# 3) 실제 영상 라이브 데모
pip install ultralytics pyttsx3
python run_video.py --video "샘플.mp4" --out demo_out.mp4 --max-sec 20
```

> Windows 콘솔 한글/이모지가 깨지면 `set PYTHONUTF8=1` 후 실행.

## 구조

```
walkguardian/
  geometry.py   근접 밴드 / 방향 / 접근 추적   (GUARDIAN box_to_distance 재사용)
  risk.py       WalkingRiskEngine — L1~L4 위험 판단
  scheduler.py  AlertScheduler — 피로 방지(디바운스/쿨다운/인터럽트/레이트리밋)
  phrases.py    짧은 한국어 음성 문안
  voice.py      TTS 출력(pyttsx3 오프라인, 미설치 시 콘솔 폴백)
  detection.py  YOLOv8Detector + GUARDIAN 캐시 OfflineCache
  pipeline.py   WalkGuardian — 프레임→탐지→환경→위험→스케줄→음성
run_video.py    영상 파일 라이브 데모
demo_sim.py     합성 시나리오 통합 데모
tests/          순수 로직 테스트(6/6 통과)
```

## 아직 안 된 것 (정직한 한계)
- 보행환경(점자블록/횡단보도/계단) 전용 탐지 모델 미학습 → 현재 `env` 는 주입식 인터페이스(placeholder). 세그멘테이션 모델 또는 공공데이터 지오펜스로 교체 예정.
- 근접 밴드 임계값은 카메라 화각별 **현장 캘리브레이션 필요**.
- TTS 는 MVP에서 블로킹 → 실기기는 비동기 큐 + 스테레오 좌/우 패닝 권장.
