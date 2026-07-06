# 걸음지기 (GUARDIAN‑Walk)

**시각장애인 AI 청각 보행 보조** — 폰 카메라로 전방 위험을 인식해 **짧은 한국어 음성**으로 안내합니다.
(GUARDIAN: 이륜차 상황인식 AR HUD 연구의 청각 확장)

> ⚠️ 이 시스템은 흰지팡이·안내견·보행훈련을 **대체하지 않는 보조 정보 제공 도구**입니다.
> 사고 방지·정확한 거리·완전 자율 보행을 **보장하지 않습니다.**

### 🔗 라이브 데모 (안드로이드 Chrome 권장)
**https://nenae16-creator.github.io/walkguardian/mobile/**
→ 화면 아무 곳이나 눌러 시작. ⚙ 는 설정.

---

## 지금 되는 것
- 👆 **시각장애인용 단순 조작**: 화면 전체가 시작/정지 버튼 하나. 나머지는 ⚙ 설정에.
- 🗣️ **한국어 음성 안내(오프라인)**: 미리 만든 클립 재생 → 폰에 한국어 TTS 없어도 됨.
- 🎯 **4가지 인식 모드**
  | 모드 | 엔진 | 특징 |
  |---|---|---|
  | 빠름 | COCO‑SSD (TF.js) | 차·사람 등 일반 객체, 빠름 |
  | 정밀 보행로 | DeepLab Cityscapes | 인도/차도 방향, 전봇대(pole) |
  | **국내모델** | **직접 학습 YOLOv8 (onnx)** | 계단·전봇대·쓰레기통·입간판 (mAP 0.83) |
  | AI 설명 | GPT‑4o‑mini vision (백엔드) | 가장 똑똑, 3초 간격, 백엔드 필요 |
- 🧠 **위험 우선순위 L1~L4** + 피로 방지(디바운스·쿨다운·인터럽트·정지침묵)
- 🪜 **내리막 계단/턱 낙차 감지**: 단안 깊이(Depth Anything V2, 27MB onnx)로 "바닥이 꺼지는 곳"을 모양과 무관하게 감지 — ARCore 불필요, 카메라 모드에서 자동 동작
- 🚗 **에고 움직임 보정**: 손에 든 폰이라도 정차 vs 접근 차량 구분. 인도 보행 시 **옆 차도 차량 무시**.
- 📍 **위치안내(GPS)**: 공공데이터(음향신호기·횡단보도) CSV 로드 → 근처 안내.
- 🧪 앱 내 **자가검사** 20종(⚙ 설정 → 자가검사) — 로직 즉시 검증.

## 저장소 구조
```
mobile/            📱 웹앱 (핵심)
  index.html         UI + 카메라 + 4모드 + GPS + 설정
  walk_logic.js      위험판단·에고보정·스케줄러·지오펜스 (순수 JS, 자가검사 포함)
  wg_onnx.js         국내모델 onnxruntime-web 추론기
  models/walkguardian/best.onnx   학습한 YOLOv8 (42MB)
  clips.json + audio/*.wav        한국어 음성 클립 (Heami)
  poi.json           음향신호기/횡단보도 샘플
  serve_https.py     폰 LAN 테스트용 자체서명 HTTPS 서버

backend/           ☁️ AI 설명 모드 백엔드 (Cloudflare Worker) — 키는 여기 secret 에만
training/          🎓 Colab 학습 노트북 3종 (train_now / train_multi / sideguide #189)
walkguardian/      🐍 GUARDIAN 파생 Python 코어(참조 구현) + tests/
docs/references.md 📚 논문·데이터셋 레퍼런스(82/100 원문 검증)
```

## 개발/실행

### 웹앱 (mobile/)
```bash
# 로컬 미리보기 (카메라는 localhost·HTTPS 에서만 됨)
python -m http.server 8777 --directory mobile
# → PC 브라우저: http://localhost:8777 (여기선 카메라/동영상 테스트 가능)

# 폰(같은 Wi‑Fi)에서 카메라까지 테스트
pip install cryptography && python mobile/serve_https.py   # https://<PC-IP>:8443
```
> 배포는 **GitHub Pages(master 브랜치 root)** 로 자동. push 하면 몇 분 뒤 라이브 반영.

### 로직 자가검사 (브라우저 콘솔)
```js
window.__selfTest()   // 위험/내비/깊이/지오펜스/CSV 20종 → 전부 true 여야 함
```
Node 로도: `node -e "require('./mobile/walk_logic.js'); console.log(WalkLogic.selfTest())"`

### Python 코어 (walkguardian/)
```bash
python tests/test_logic.py     # 순수 로직 테스트
python demo_sim.py             # 합성 시나리오 데모
```

### 학습 (training/) — Colab
`train_now`/`train_multi` 노트북을 Colab에서 열어 GPU로 학습 → `best.onnx` → `mobile/models/` 교체.
자세히: [training/README_training.md](training/README_training.md)

### AI 백엔드 (backend/)
Cloudflare Worker 배포 + OpenAI 키를 secret 으로. 자세히: [backend/README.md](backend/README.md)
> ⚠️ **API 키는 절대 저장소/앱에 커밋하지 마세요.** Worker secret 에만 둡니다.

## 팀 개발
- 협업/브랜치 규칙: [CONTRIBUTING.md](CONTRIBUTING.md)
- 이슈/할 일은 GitHub Issues 사용 권장.

## 기술 스택
TensorFlow.js(COCO‑SSD/DeepLab) · onnxruntime‑web(WebGPU) · YOLOv8(Ultralytics) · Web Speech/사전 클립 · Geolocation · Cloudflare Workers · GitHub Pages.

## 정직한 한계
- 인식은 완벽하지 않습니다(특히 한국 특화 물체는 학습 데이터 도메인 갭). 내려가는 계단 등은 깊이 센서/AI 모드가 더 유리.
- 근접 밴드 임계값은 카메라 화각별 현장 캘리브레이션 필요.
- 실제 도로 실험 전 **통제 환경 실험** 및 당사자 동의·안전관리자 필요.

## 크레딧
GUARDIAN(이륜차 HUD) 선행 연구 · AI Hub 인도보행 데이터 · Roboflow 공개 데이터셋 · 참고문헌은 [docs/references.md](docs/references.md).
