# 걸음지기 학습 셋업 (Colab)

로컬 GPU가 없으므로 **Google Colab(무료/Pro GPU)** 기준. 학습한 모델을 **웹앱(mobile/)** 에 그대로 꽂는 것까지가 목표.
공통 원칙: **탐지기(눈)만 국내 보도 특화로 교체**, 위험판단·에고보정·한국어음성·스케줄러(`walk_logic.js`)는 **재사용**.

## 두 가지 경로
| 경로 | 노트북 | 데이터 | 언제 |
|---|---|---|---|
| **A. 오늘 바로** (추천 시작) | [`train_now_roboflow_colab.ipynb`](train_now_roboflow_colab.ipynb) | Roboflow 공개셋(볼라드·연석·전봇대·쓰레기통 등, YOLO 즉시) | **지금** — 가입만 하면 승인 대기 없음 |
| **B. 국내 최강** | [`sideguide_walkguardian_colab.ipynb`](sideguide_walkguardian_colab.ipynb) | AI Hub #189 인도보행(29종, ~67만장) | AI Hub **이용신청 승인 후** |

→ **먼저 A로 오늘 감을 잡고**, #189 승인되면 B로 국내 정확도를 끌어올리는 순서를 권장.

---
## B. AI Hub #189 (인도보행 영상 / SideGuide)

## 목표 2가지
| 목표 | 무엇을 학습 | 걸음지기 어디에 |
|---|---|---|
| **A (우선)** | 보도 장애물 **29종 객체탐지**(YOLOv8) | 웹앱 '빠름' 모드의 COCO-SSD를 **국내 보도 특화 모델**로 교체/보강 (전봇대·볼라드·입간판 등) |
| B (선택) | 인도/도로/점자블록 **세그멘테이션** | '정밀 보행로' 모드의 DeepLab을 국내 세그로 교체 |

우선 **A(객체탐지)** 만: GUARDIAN에서 YOLOv8 파인튜닝 방식을 그대로 재활용 → TF.js로 export → 웹앱 교체.

## 데이터: AI Hub #189
- 페이지: https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=189 (인도보행 영상, = SideGuide, KAIST RCV+Testworks)
- 규모: ~67만 장 (BBox 35만 + Polygon 10만 + Surface 5만 + Depth 17만 스테레오), **장애물 29종** + 노면 ~20종 + 깊이
- ★ **접근 절차:** AI Hub **로그인 + 데이터 이용신청 → 승인**(연구용 무료, 국내계정) 후 다운로드. 즉시 X.
- ★ **용량 큼(수십 GB)** → 노트북은 **일부(BBox 세트 일부)만 받아 소규모로 먼저** 검증하도록 구성.
- 다운로드: AI Hub `aihubshell` CLI(공식 제공) 사용, `datasetkey=189`.

## 흐름
1. Colab GPU 확인 + ultralytics 설치
2. `aihubshell`로 #189 (BBox 파트) 다운로드·압축해제
3. AI Hub 주석 → **YOLO 포맷 변환**(★실제 주석 구조에 맞게 1곳 조정 필요)
4. `data.yaml`(29클래스) 작성 → **YOLOv8 파인튜닝**(GUARDIAN yolov8s 가중치 재사용 가능)
5. 검증(mAP) + 샘플 추론
6. **Export**: ONNX/TFLite, 그리고 **TF.js**(웹앱용)
7. 웹앱 교체: 클래스명 → 걸음지기 위험 문안 매핑

## 정직한 한계
- AI Hub #189의 **정확한 주석 파일 구조**(JSON/XML 스키마·필드명)는 승인 후 실제 파일을 봐야 확정됨 → 변환 셀(step 3)은 **자리표시자 + 조정 지점**으로 표시.
- **커스텀 TF.js 모델을 web에서 YOLO 후처리(NMS)** 하려면 약간의 글루 코드 필요 → 1차는 COCO-SSD 유지하고, 학습 모델은 **정확도 벤치마크·제안서 근거**로 먼저 활용 권장.
- 29종 전부보다 **걸음지기에 중요한 클래스(전봇대/볼라드/입간판/계단/차량 등) 위주 서브셋**으로 시작하면 빠름.

## 걸음지기 매핑(예시)
| #189 클래스(예) | 걸음지기 문안 |
|---|---|
| bollard, pole, 입간판, 화분 | "앞 장애물" (STATIC_OBST) |
| car/bus/truck, motorcycle/bicycle | 에고보정 → "차량 접근/정차/지나감" |
| person | "앞 사람" |
| stairs | "앞 계단 주의" |
