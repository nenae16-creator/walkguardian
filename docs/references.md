# 걸음지기(GUARDIAN-Walk) 참고문헌 레퍼런스 가이드

시각장애/저시력 보행자용 한국어 음성 위험경고 앱을 위한 논문·데이터셋 정리본입니다. `⚠️`는 원문 미검증 항목(확인 필요), 별도 표시 없으면 confirmed입니다.

---

## 1. 논문

### (a) 시스템 / 서베이

**AI Guide Dog: Egocentric Path Prediction on Smartphone**
- 저자/연도/발표처: CMU 계열 / 2025 / arXiv (AAAI Symposium Series 2025)
- 링크: https://arxiv.org/abs/2501.07957
- 요약: 스마트폰 단일 카메라만으로 방향 명령을 예측하는 경량 멀티라벨 분류 기반 1인칭 실시간 내비게이션. GPS + 상위 지시 융합, 실내외 모두 지원, 데이터셋 공개.
- 걸음지기 관련성: **사용자가 지목한 바로 그 "AI Guide Dog CMU" 시스템**. 스마트폰 전용 비전 내비게이션의 최신 선도 사례이자 벤치마크 기준점.

**NavCog3: Smartphone-Based Blind Indoor Navigation Assistant with Semantic Features**
- 저자/연도/발표처: CMU + IBM Research (Chieko Asakawa, Kris Kitani) / 2017 / ACM ASSETS
- 링크: https://www.ri.cmu.edu/publications/navcog3-evaluation-smartphone-based-blind-indoor-navigation-assistant-semantic-features-large-scale-environment/
- 요약: BLE 비콘 측위 + 음성/진동 랜드마크 안내로 시각장애인 실내 턴바이턴 안내. 21,000㎡ 쇼핑몰에서 평가, 오픈소스 HULOP 기반.
- 걸음지기 관련성: AI Guide Dog와 같은 CMU 그룹의 시조격 스마트폰 시각장애 보행 안내 시스템. 턴바이턴 안내의 정석 베이스라인.

**NavCog3 in the Wild: Large-scale Blind Indoor Navigation Assistant** ⚠️likely
- 저자/연도/발표처: 2019 / ACM TACCESS Vol.12 No.3
- 링크: https://dl.acm.org/doi/10.1145/3340319 (DOI 403 페이로드 미검증, 메타데이터는 일치 — 확인 필요)
- 요약: NavCog3의 다지점 실환경 확장 배포 연구.
- 걸음지기 관련성: 시조격 라인의 대규모 실환경 평가 근거.

**DeepNAVI: A deep learning based smartphone navigation assistant for people with visual impairments** ⚠️likely
- 저자/연도/발표처: 2023 / Expert Systems with Applications (Elsevier)
- 링크: https://www.sciencedirect.com/science/article/pii/S0957417422017432 (403, 메타데이터 일치 — 확인 필요)
- 요약: 스마트폰 딥러닝 내비: 장애물 탐지 + 거리/위치 추정 + 장면 인식, 실시간 음성 피드백.
- 걸음지기 관련성: 엔드투엔드 스마트폰 CV 보행 보조의 대표 사례. AI Guide Dog 비교군.

**WalkVLM: Aid Visually Impaired People Walking by Vision Language Model**
- 저자/연도/발표처: 2024 / arXiv (walkvlm2024.github.io)
- 링크: https://arxiv.org/abs/2412.20903
- 요약: 12,000쌍 보행보조 벤치마크 공개. 계층적 계획 + 시간인지 예측으로 스트리밍 1인칭 영상에서 간결·적시 알림 생성, 일반 VLM의 출력/시간 중복 해결.
- 걸음지기 관련성: **VLM 기반 보행보조의 대표 시스템**. LLM/VLM 방향의 기준. (데이터셋 항목과 중복 → 데이터셋 2(a) 참조)

**Less Redundancy: WalkVLM-LR**
- 저자/연도/발표처: 2025 / arXiv (ICASSP 2026 Best Industry Paper)
- 링크: https://arxiv.org/abs/2508.16070
- 요약: GRPO 추론 + 간결성/유창성/키워드밀도/정확도 보상 + 장면위험 게이팅 판별기로 출력·시간 중복 감축. SOTA.
- 걸음지기 관련성: **VLM 보행보조의 실전화·SOTA**. 위험도 기반 알림 게이팅은 걸음지기의 "언제 말할지" 설계에 직결.

**PathFinder: Real-Time Assistive Navigation (Scalable Indoor/Outdoor)**
- 저자/연도/발표처: 2025 / arXiv
- 링크: https://arxiv.org/abs/2504.20976
- 요약: 지도 없이 완전 오프라인, 단안 깊이추정 + 경로탐색으로 장애물 없는 경로 선택. BLV 15명 평가(73% 1분 내 습득, 80% 정확/반응성 호평).
- 걸음지기 관련성: 오프라인 스마트폰(단안 깊이) 내비 + 실제 시각장애인 평가. AI Guide Dog/DeepNAVI 직접 비교군. (하자 탐지 항목과 중복)

**SLAM for Visually Impaired People: A Survey**
- 저자/연도/발표처: ETH/ZHAW 그룹 / 2022(2024 개정) / arXiv
- 링크: https://arxiv.org/abs/2212.04745
- 요약: SLAM 기반 시각장애 내비 54편 체계적 리뷰(측위/매핑, 센서, 연산자원, ML, 동적환경·실사용 과제).
- 걸음지기 관련성: 측위 측면의 정석 서베이.

**What do Blind and Low-Vision People Really Want from Assistive Smart Devices?**
- 저자/연도/발표처: Monash University / 2025 / arXiv
- 링크: https://arxiv.org/abs/2505.19325
- 요약: 646편 리뷰 + BLV 24명 인터뷰. 연구자 초점과 사용자 체감 중요도의 상관 약함, 사용자는 대화형 인터페이스·헤드마운트 선호.
- 걸음지기 관련성: **BVI 사용자가 실제로 원하는 것**을 짚는 니즈분석. 제품 설계·동기 근거로 가치 큼.

**A comprehensive review of navigation systems for visually impaired individuals** ⚠️likely
- 저자/연도/발표처: 2024 / Heliyon (Elsevier)
- 링크: https://www.sciencedirect.com/science/article/pii/S2405844024078563 (403, 저자 미확정 — 확인 필요)
- 요약: 착용형 vs 휴대형, 센서원(RGB 우세), 기능 격차 다룬 오픈액세스 리뷰.
- 걸음지기 관련성: SLAM 서베이 보완용 넓은 지형도.

**Assistive Systems for Visually Impaired Persons: Challenges and Opportunities** ⚠️likely
- 저자/연도/발표처: 2024 / Sensors (MDPI) 24(11):3572
- 링크: https://www.mdpi.com/1424-8220/24/11/3572 (랜딩 미확인, DOI 일치 — 확인 필요)
- 요약: 센싱/피드백/배포 전반의 과제·기회 리뷰.
- 걸음지기 관련성: 최신 내비 서베이. 과제·기회 프레이밍용.

**Navigation Solutions for Blind and Visually Impaired Persons: A State-of-the-Art Survey** ⚠️unverified
- 저자/연도/발표처: 2026 / Int'l Journal of Human–Computer Interaction (T&F)
- 링크: https://www.tandfonline.com/doi/full/10.1080/10447318.2026.2643358 (미검증, 페이월 추정 — **인용 전 반드시 확인 필요**)
- 요약: BVI 내비 최신 종합 서베이로 검색됨(메타데이터 주의).
- 걸음지기 관련성: HCI 지향 최신 서베이 가능성. 확정 전 URL/서지 확인 필수.

---

### (b) 장애물 · 차량 · 계단 탐지

**WOAD: A wearable obstacle avoidance device with cross-modal learning**
- 저자/연도/발표처: 2025 / Nature Communications
- 링크: https://www.nature.com/articles/s41467-025-58085-x (PMC 미러 PMC11933268)
- 요약: 적외선+깊이 안경 + 스마트폰. 깊이보조 적응형 영상압축으로 지연 감소, 교차모달(영상+깊이) 학습. 야간 고속차량(>10m/s) 대상 **충돌회피 100%**(흰지팡이 ~40%), <320ms, >11h.
- 걸음지기 관련성: **접근차량/충돌경고 요건에 직결**. 야간 고속차 대비 실측 벤치마크는 걸음지기 "접근 vs 주차 차량" 핵심 근거.

**HEADS-UP: Head-Mounted Egocentric Dataset for Trajectory Prediction**
- 저자/연도/발표처: EPFL VITA / 2024 / arXiv
- 링크: https://arxiv.org/abs/2409.20324
- 요약: 회전좌표계 반지역 궤적예측으로 충돌위험 평가, Jetson 실시간 사용자연구 검증.
- 걸음지기 관련성: **TTC/충돌경고 + 1인칭** 정합. 동적 장애물 궤적예측용 최초 헤드마운트 데이터셋. (데이터셋 중복)

**PEDESTRIAN: An Egocentric Vision Dataset for Obstacle Detection on Pavements**
- 저자/연도/발표처: CYENS CoE / 2025 / arXiv
- 링크: https://arxiv.org/abs/2512.19190
- 요약: 모바일 1인칭 영상 340개, 보도 장애물 29종, SOTA 검출기 베이스라인.
- 걸음지기 관련성: **폴대/연석/도로시설물 카테고리** 1인칭 벤치마크. (데이터셋 중복)

**An Embedded Real-time Object Alert System (Monocular Depth based)**
- 저자/연도/발표처: 2025 / arXiv
- 링크: https://arxiv.org/abs/2507.08165
- 요약: 전이학습 객체탐지 + 단안 깊이추정, 임베디드용 양자화. mAP50 0.801, 근접 시 실시간 경보(라즈베리파이).
- 걸음지기 관련성: 단안 깊이 + 탐지 융합 근접 충돌경보 — 걸음지기의 "근접 장애물" 온디바이스 구현 참조.

**Identifying Crucial Objects in Blind and Low-Vision Individuals' Navigation**
- 저자/연도/발표처: 2024 / arXiv
- 링크: https://arxiv.org/abs/2408.13175 (자매 데이터셋 논문 arXiv:2407.16777)
- 요약: 21개 영상 + 포커스그룹으로 내비 핵심 90객체 정리, 31세그먼트 라벨링.
- 걸음지기 관련성: **BLV 위험/장애물 택소노미 정의**(연석·폴대 포함). 기존 CV 데이터셋이 일부만 커버함을 밝힘.

**Saliency-guided stairs detection on wearable RGB-D (Swin-Transformer)** ⚠️likely
- 저자/연도/발표처: 2023 / Pattern Recognition Letters (Elsevier)
- 링크: https://www.sciencedirect.com/science/article/abs/pii/S016786552300332X (페이월, 초록 미검증 — 확인 필요)
- 요약: 웨어러블 RGB-D 살리언시 유도 계단 탐지, RGB-D 계단 ~3,290장 참조.
- 걸음지기 관련성: **계단/낙차 요건 직접 매칭**(웨어러블 깊이 기반).

**Embedded stereo-vision head-level object detection with audio feedback** ⚠️likely
- 저자/연도/발표처: 2025 / Scientific Reports (Nature)
- 링크: https://www.nature.com/articles/s41598-025-01529-7 (IDP 리다이렉트, 초록 미검증 — 확인 필요)
- 요약: 임베디드 스테레오 비전으로 머리 높이 물체 탐지·분류 + 음성 피드백.
- 걸음지기 관련성: 지팡이가 놓치는 머리 높이 위험(돌출 폴대) 스테레오 탐지.

**Seeing Through Touch: A Stereo-Vision Vibrotactile Aid** ⚠️likely
- 저자/연도/발표처: 2026 / Electronics (MDPI) 15(7):1511
- 링크: https://www.mdpi.com/2079-9292/15/7/1511 (오픈액세스, 초록 미완전검증 — 확인 필요)
- 요약: 스테레오 시차/깊이를 진동 패턴으로 변환, 블록기반(저지연)·SGM(고밀도) 매칭.
- 걸음지기 관련성: 스테레오 깊이 → 진동(비음성) 경고. 피드백 모달리티 비교군.

**Cooperative Saliency-based Obstacle Detection and AR Rendering** ⚠️likely
- 저자/연도/발표처: 2023 / arXiv
- 링크: https://arxiv.org/abs/2302.00916 (개별 초록 미검증 — 확인 필요)
- 요약: 살리언시 기반 장애물 탐지 + AR 렌더링.
- 걸음지기 관련성: 상황인지용 장애물 탐지(단 AR 프레이밍 → 저시력 대상, 완전 실명엔 제한).

**A Computer Vision and Depth Sensor-Powered Smart Cane (IoT Cane)**
- 저자/연도/발표처: 2025 / arXiv
- 링크: https://arxiv.org/abs/2508.16698
- 요약: RT-DETRv3-R50 + Intel RealSense 깊이. mAP 53.4%/AP50 71.7%, ~150ms, 진동+음성.
- 걸음지기 관련성: 카메라+깊이 스마트지팡이 최신 트랜스포머 검출 사례.

**A Smart Cane Based on 2D LiDAR and RGB-D Camera**
- 저자/연도/발표처: 2024 / Sensors (MDPI) 24(3):870
- 링크: https://pmc.ncbi.nlm.nih.gov/articles/PMC10856969/
- 요약: 2D LiDAR(Cartographer SLAM) + RGB-D + 개선 YOLOv5. ~1m±7cm, 25–31FPS.
- 걸음지기 관련성: LiDAR+RGB-D+딥러닝 지팡이. 순수 카메라 지팡이 보완.

**Obstacle avoidance using a 3D camera and a haptic feedback sleeve**
- 저자/연도/발표처: 2022 / arXiv
- 링크: https://arxiv.org/abs/2201.04453
- 요약: 3D 카메라 거리→팔착용 슬리브 진동 패턴. 단일패턴 98.6%/복합 70% 인식, 암실 과제 완수.
- 걸음지기 관련성: 깊이→햅틱 감각대체 장애물 회피. 피드백 모달리티 설계 비교군.

**Sight Guide (Cybathlon 2024)** — 시스템/UX 양쪽 해당, 아래 (c)에서 상술
- 링크: https://arxiv.org/abs/2506.02676

**IoT Cane / Smart Cane 계열은 위 참조.**

---

### (c) 음성 / UX · 평가 · 윤리

**Sonification of guidance data during road crossing (VI/blindness)**
- 저자/연도/발표처: 2015 / Int'l Journal of Human-Computer Studies (arXiv 1506.07272)
- 링크: https://arxiv.org/abs/1506.07272
- 요약: 두 소니피케이션 vs 음성 안내 비교. 소니피케이션은 해독에 인지부하 더 크나, 음성이 환경음을 가리므로 2/3+가 소니피케이션 선호.
- 걸음지기 관련성: **음성 vs 비음성 안전경고 트레이드오프 핵심**. 걸음지기가 음성에만 의존하면 환경음 마스킹 위험 — 설계 지침.

**Spearcons (Speech-Based Earcons) Improve Navigation Performance**
- 저자/연도/발표처: 2013 / Human Factors
- 링크: https://pubmed.ncbi.nlm.nih.gov/23516800/
- 요약: 5개 실험으로 스피어콘(가속 음성)이 오디오아이콘·이어콘 대비 내비 효율/정확/학습 우수.
- 걸음지기 관련성: 오디오 큐 설계공간(오디오아이콘/이어콘/스피어콘) 정의. 알림 유형 선택 정당화 시 정석 인용.

**Auditory Icons, Earcons, Spearcons, and Speech: Systematic Review & Meta-Analysis** ⚠️likely
- 저자/연도/발표처: 2023 / Auditory Perception & Cognition 6(3-4)
- 링크: https://www.tandfonline.com/doi/abs/10.1080/25742442.2023.2219201 (403, 서지 확인됨/본문 미검증 — 확인 필요)
- 요약: 음성·스피어콘·하이브리드 > 오디오아이콘 > 이어콘. 단일 최적안에 대한 명확한 휴리스틱은 아직 없음.
- 걸음지기 관련성: 간결 오디오 경고 선택의 최적 근거종합. 과도한 우월성 주장 자제 근거.

**Planning Your Journey in Audio: Auditory Route Overviews** ⚠️likely
- 저자/연도/발표처: 2022 / ACM TACCESS
- 링크: https://spiral.imperial.ac.uk/entities/publication/c4bf0339-022a-435c-b562-478ed35c8bc8 (ACM DOI 403, Imperial 리포지토리로 확인/저자 미완 — 확인 필요)
- 요약: 오디오아이콘+이어콘+음성 혼합 오디오 경로개요. 설문→2단계 설계(8+8)→프로토타입→사용성(22 정안+8 시각장애).
- 걸음지기 관련성: 다중 비음성 오디오 결합 설계·평가 파이프라인 모범.

**A Comparative Study in Real-Time Scene Sonification for VI People**
- 저자/연도/발표처: 2020 / Sensors 20(11):3222
- 링크: https://pmc.ncbi.nlm.nih.gov/articles/PMC7309097/
- 요약: 이미지/장애물/경로 소니피케이션 3수준 vs 흰지팡이, VI 12명 현장. 고수준=학습 쉽지만 정보 적고, 저수준(깊이)=풍부하나 학습 오래. 개인화 필요.
- 걸음지기 관련성: 소니피케이션 학습성 vs 상세도 트레이드오프 실측.

**Haptic Feedback to Assist Blind People Using Vibration Patterns**
- 저자/연도/발표처: 2022 / Sensors 22(1):361
- 링크: https://pmc.ncbi.nlm.nih.gov/articles/PMC8749676/
- 요약: 모스부호식 7개 진동패턴, 시각장애 24명 3개월 앱 테스트. 패턴별 인식률 90/82/75/87/65/70% — 구별성 편차 큼. 소음환경·프라이버시 이점.
- 걸음지기 관련성: 드문 종단(3개월) 햅틱 연구. 어떤 진동이 실제로 구별되는지 정량화 — 걸음지기 진동 보조채널 설계.

**Cognitive/Affective Assessment via EEG and Behavioral Signals**
- 저자/연도/발표처: 2020 / Sensors 20(20):5821
- 링크: https://pmc.ncbi.nlm.nih.gov/articles/PMC7602506/
- 요약: EEG+행동, VI 8명, 흰지팡이 vs Sound of Vision. 햅틱이 오디오보다 덜 직관적, SoV 인지부하 증가, 시각피질 활동과 충돌수 무상관.
- 걸음지기 관련성: 객관적(EEG) 인지부하 근거 + 단일지표=안전 아님 경고.

**Beyond Omakase: Designing Shared Control for Navigation Robots with Blind People**
- 저자/연도/발표처: 2025 / ACM CHI 2025
- 링크: https://arxiv.org/abs/2503.21997
- 요약: 시각장애인은 완전자율("오마카세") 원치 않음. 'boss'(군중 대응)·'monitor'(환경 평가) 모드 선호, 공유제어 필수.
- 걸음지기 관련성: **자동화 윤리/에이전시** — 걸음지기가 하면 안 되는 것(조용히 통제권 탈취)과 권한 배분 근거.

**Large-scale, Longitudinal, Hybrid Participatory Design Program for the Blind**
- 저자/연도/발표처: 2024 / arXiv
- 링크: https://arxiv.org/abs/2410.00192
- 요약: 3년 커뮤니티 중심(온라인 67 + 대면 11 + 코디 4). "우리에 관한 것은 우리 없이 하지 말라"의 대규모 실천.
- 걸음지기 관련성: 시각장애 사용자 참여설계 방법 모델. 대리 평가 비판 반박.

**From abandonment to adoption: advancing AT for blindness/low vision in the AI era**
- 저자/연도/발표처: 2026 / Frontiers in Digital Health (PMC12832816)
- 링크: https://pmc.ncbi.nlm.nih.gov/articles/PMC12832816/
- 요약: 왜 보조기기가 버려지는가 — 혁신뿐 아니라 지속적 일상 사용이 관건. 참여설계·통합생태계·커뮤니티 3원칙.
- 걸음지기 관련성: **과대주장 경계** — 데모 성공 ≠ 실사용 정착. 버려짐 문제 프레이밍.

**Can blindfolded users replace blind ones in product testing?** ⚠️likely
- 저자/연도/발표처: 2023 / Behaviour & Information Technology
- 링크: https://www.tandfonline.com/doi/full/10.1080/0144929X.2023.2226768 (403, 핵심 결론 확인 — 확인 필요)
- 요약: 안대 착용 정안인은 실제 시각장애인보다 과제 품질 유의미하게 높음 → 대리 테스트는 사용성 과대평가.
- 걸음지기 관련성: **"주장하면 안 되는 것"** 근거 — 안대 대리평가는 시각장애인 근거 아님.

**Assistive XR research at ACM ASSETS: A Scoping Review**
- 저자/연도/발표처: 2025 / arXiv (ASSETS 2019-2023 리뷰)
- 링크: https://arxiv.org/abs/2504.13849
- 요약: ASSETS 26편 XR 논문 스코핑. 연구초점·방법론 카탈로그.
- 걸음지기 관련성: 대상 학회(ASSETS)가 기대하는 평가 엄밀성 캘리브레이션.

**All the Way There and Back: Phone-in-Pocket Indoor Wayfinding for Blind Travelers**
- 저자/연도/발표처: Manduchi lab, UC Santa Cruz / 2024 / arXiv
- 링크: https://arxiv.org/abs/2401.08021
- 요약: 인프라 불필요 iOS 앱 2종(관성/자기), 주머니 속 조작 + 스마트워치 + 음성 안내. 시각장애 7명 평가.
- 걸음지기 관련성: 실제 시각장애인 대상 정직한 소규모 음성 UX 평가. 주장 범위 설정 모범.

**Sight Guide: Wearable Assistive Perception and Navigation (Cybathlon 2024)**
- 저자/연도/발표처: ETH Zurich/ZHAW / 2025 / arXiv
- 링크: https://arxiv.org/abs/2506.02676
- 요약: 다중 RGB+깊이 카메라, 진동+음성 안내(장애물회피·객체탐지·OCR). Cybathlon 2024에서 과제성공 95.7%.
- 걸음지기 관련성: **음성+햅틱 결합 최신 설계** + 대회벤치마크 vs 일상사용 주장 경계 사례.

---

## 2. 데이터셋

### (a) 해외 공개

| 이름 | 출처 | 규모 | 걸음지기 용도 | 확인상태 |
|---|---|---|---|---|
| **SANPO** ([GitHub](https://github.com/google-research-datasets/sanpo_dataset) / [arXiv](https://arxiv.org/abs/2309.12172)) | Google Research, WACV 2025 | Real 701 스테레오 영상 ~617K 프레임 + 깊이 + 112K 판옵틱, Synthetic ~113K, ~6TB, CC BY 4.0 | **경로 세그멘테이션 + 깊이(연석/계단/낙차) + 장애물** 통합 학습. 인도-vs-도로 방향, 1인칭. 최우선급 | confirmed |
| **GuideDog + GuideDogQA** ([arXiv](https://arxiv.org/abs/2503.12844)) | Yonsei/SK텔레콤, ACL 2026 | ~22K 이미지-설명쌍(2K 골드) 46개국 + QA 818, 깊이/객체 메타 | VLM 안내 학습/평가, 공간·깊이 지각 벤치마크. **한국 팀 제작(국내 친화)** | confirmed |
| **WalkVLM 벤치마크** ([arXiv](https://arxiv.org/abs/2412.20903)) | WalkVLM 저자 | 12,000 영상-주석쌍 | 스트리밍 **한국어 위험 알림** 생성 학습/평가(중복 억제 포함) | confirmed |
| **mmWalk / mmWalkVQA** ([GitHub](https://github.com/KediYing/mmWalk) / [Dataverse](https://doi.org/10.7910/DVN/KKDXDK)) | Stiefelhagen/Yang, NeurIPS 2025 D&B | 120 궤적, 62K 프레임, 559K+ 파노라마 RGB/깊이/시맨틱, 69K+ QA, CC BY 4.0 | **횡단보도·연석·낙차** + 깊이 안전보행. 다시점 강건성 | confirmed |
| **HEADS-UP** ([arXiv](https://arxiv.org/abs/2409.20324)) | EPFL VITA | 헤드마운트 1인칭 + 이동장애물 궤적 | **TTC/충돌경고**(접근차량·보행자 궤적) | confirmed |
| **PEDESTRIAN** ([arXiv](https://arxiv.org/abs/2512.19190) / [GitHub](https://github.com/CYENS/PEDESTRIAN) / [Zenodo](https://doi.org/10.5281/zenodo.10907945)) | CYENS CoE | 1인칭 영상 340, 보도 장애물 29종, CC BY 4.0 | **폴대/연석/도로시설물** 탐지 학습 | confirmed |
| **BLV 90-객체 택소노미** ([arXiv](https://arxiv.org/abs/2407.16777)) | 2024 | 21영상, 31세그먼트, 90객체 | 위험/장애물 클래스 **택소노미 설계** 근거 | confirmed |
| **GuideTWSI (점자블록)** ([프로젝트](https://guidedogrobot-tactile.github.io/) / [arXiv](https://arxiv.org/abs/2603.07060)) | UMass/UT Austin, ICRA 2026 | ~39.5K(합성 15K + 실제 방향바 22K + 돌출돔 2K), 픽셀마스크, CC BY 4.0 | **점자블록/유도블록** 세그멘테이션(방향바+돌출돔). 지리 균형 최강 | confirmed |
| **ImVisible / PTL + LytNet** ([GitHub](https://github.com/samuelyu2002/ImVisible)) | CAIP/ICCV-W 2019 | 5,059장(3,456/864/739), MIT | **횡단보도 위치 + 보행신호 색** = "건너도 되나". 온디바이스 모델 포함 | confirmed |
| **CDSet-3434 / CDNet** ([Zenodo](https://zenodo.org/records/8289874) / [GitHub](https://github.com/zhangzhengde0225/CDNet)) | 2023 | 3,434(+1,770), 악조건 다양, CC BY 4.0, 1.1GB | 횡단보도 탐지 보조(단 차량시점 → 전이/보조용) | confirmed |
| **FPVCrosswalk2025** ([Mendeley](https://data.mendeley.com/datasets/mcr2jwk5bp/1) / [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12206053/)) | Data in Brief | 3,300장(합성 3,000 + 실제 300) 마스크, CC BY 4.0 | **1인칭 횡단보도 세그멘테이션**(날씨/조명 다양) — 걸음지기 시점에 정확 | confirmed |
| **SideSeeing** ([사이트](https://sites.usp.br/sideseeing/) / [arXiv](https://arxiv.org/abs/2407.06464)) | USP/UIC/MIT 2024 | 12km, 47경로, ~325K 프레임, 4도시, 68요소 택소노미 | 흉부장착 멀티센서(영상+IMU+GPS+오디오) 노면/접근성 평가 | confirmed |
| **Mapillary Vistas** ([데이터셋](https://www.mapillary.com/dataset/vistas) / [연구](https://research.mapillary.com/publication/iccv17a)) | ICCV 2017 | 25K 고해상, 66/124 클래스(sidewalk/crosswalk/curb/curb-cut) | **인도+횡단보도+연석 동시 라벨** 사전학습(등록/라이선스 필요) | confirmed |
| **Cityscapes** ([사이트](https://www.cityscapes-dataset.com/)) | CVPR 2016 | 5K fine + 20K coarse, 50도시, sidewalk 클래스 | **인도-vs-도로 세그멘테이션** 사전학습(차량시점, **비상업 라이선스 주의**) | confirmed |
| **ADE20K** ([사이트](https://ade20k.csail.mit.edu/)) | CVPR 2017 | 20,210/2,000/3,352, 150클래스(sidewalk/stairs/pole/traffic light) | 계단·폴대 포함 범용 장면파싱 사전학습 | confirmed |
| **Flying Guide Dog + PVTL** ([GitHub](https://github.com/EckoTan0804/flying-guide-dog) / [arXiv](https://arxiv.org/abs/2108.07007)) | IEEE ROBIO 2021 | 보행가능경로 파이프라인 + PVTL 신호등 | 보행경로 세그 + 신호등(안전횡단 로직) | confirmed |
| **Roboflow 점자블록 컬렉션** ([검색](https://universe.roboflow.com/search?q=class:braille)) | 커뮤니티 | 소규모 다수(~150–1,324장), 라이선스 상이 | 즉시 학습 가능한 점자블록 탐지 퀵스타트(품질/라이선스 개별 확인) | confirmed |
| **Tenji10K** ([Wiley](https://onlinelibrary.wiley.com/doi/10.1002/tee.24123)) | U. Toyama, IEEJ 2024 | 1인칭 점자블록 10K, 20시퀀스(일본) | 유도블록 시간적 추적(영상형). **다운로드 링크 미확정** | ⚠️likely (확인 필요) |
| **TrackAid / TrackAid-DT** ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1077314226001554)) | CVIU 2026 | 흉부장착 1인칭 픽셀주석 | 보행 레인/경로 세그(운동선수 조건). **릴리스 위치 미확정** | ⚠️likely (확인 필요) |
| **Obstacle Dataset for Blind Sidewalk (OD)** ([Springer](https://link.springer.com/article/10.1007/s10209-021-00837-9)) | UAIS 2021 | 옥외 보도 장애물 다수(논문 참조) | 점자블록 경로 위 장애물 인식. **원본 데이터 링크 미확정** | ⚠️likely (확인 필요) |

### (b) 국내 / AI Hub

| 이름 | 출처 | 규모 | 걸음지기 용도 | 확인상태 |
|---|---|---|---|---|
| **인도보행 영상 (Sidewalk Walking Video) = SideGuide** ([AI Hub #189](https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=189) / [IROS 논문](https://ieeexplore.ieee.org/document/9340734/)) | AI Hub(NIA), KAIST RCV(Kweon 그룹)+Testworks | ~670K(BBox 350K + Polygon 100K + Surface 50K + Depth 170K 스테레오), 29 장애물 클래스 + ~20 노면종류 + 깊이 | **가장 직접적인 국내 데이터** — 인도 세그 + 장애물 + 노면 + 깊이(인도-vs-도로, 근접 장애물, 연석/노면). 프로토타입: [github](https://github.com/ChelseaGH/sidewalk_prototype_AI_Hub) | confirmed (계정+승인 필요, 국내접근·연구용 무료) |
| **보행 안전을 위한 도로 시설물 데이터** ([AI Hub #513](https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=513)) | AI Hub(NIA) | ~1,025K장(정상 34.6%/파손 65.4%), bbox+세그, ~30 시설물종 | **점자블록·턱낮춤·보도·횡단보도** 탐지 + 파손/위험 시설물 경고 | confirmed |
| **차선/횡단보도 인지 영상(수도권 외)** ([AI Hub #196](https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=196)) | AI Hub(NIA) | ~1,997K 이미지, ~12.39M 객체 | 국내 **횡단보도** 주석 보조(차량시점 → #189보다 부적합, 보조용). 수도권판 별도 존재 | confirmed |
| **도로장애물/표면 인지 영상(수도권 외)** ([AI Hub #178](https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=178)) | AI Hub(NIA) | >1,000K장, >300시간(공사장/파손도로) | 노면 손상·장애물 클래스 전이(차량시점 → 보조적) | confirmed |
| **DeepGuider 데이터셋 (Geo-tagged 인도 보행)** ([GitHub](https://github.com/deepguider/DeepGuider)) | ETRI(MSIT/IITP) | 계절별 ~1년 인도 영상 + 고정밀/저가 GPS + IMU | 옥외 **인도 내비게이션/측위**, 한국 거리 특화(카메라+GPS+IMU) | confirmed (ETRI 나눔 호스팅, TLS 인증서 만료 상태 유의) |

---

## 3. 종합 추천

### TOP 논문 3
1. **AI Guide Dog** (https://arxiv.org/abs/2501.07957) — 걸음지기와 가장 동형인 스마트폰 전용 비전 내비. 아키텍처·데이터·평가의 직접 기준점.
2. **WOAD (Nature Communications)** (https://www.nature.com/articles/s41467-025-58085-x) — **접근차량 충돌경고**의 최강 실측 근거(야간 고속차 100%). 걸음지기 "접근 vs 주차 차량" 핵심 요건에 직결.
3. **WalkVLM-LR** (https://arxiv.org/abs/2508.16070) — 위험도 게이팅으로 "언제·얼마나 간결히 말할지"를 푸는 SOTA. 걸음지기의 한국어 짧은 경고 UX 설계에 직접 응용.
   - (보조 필독: 오디오 설계는 **Sonification 2015** https://arxiv.org/abs/1506.07272 — 음성 과의존이 환경음을 가리는 위험을 명시)

### TOP 데이터셋 3
1. **AI Hub 인도보행 영상 #189 / SideGuide** (https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=189) — 국내·1인칭·인도 세그+장애물+깊이 통합. 걸음지기의 대부분 기능을 한 데이터로 커버하는 앵커.
2. **SANPO** (https://github.com/google-research-datasets/sanpo_dataset) — 1인칭 판옵틱 세그 + 깊이의 최강 해외 벤치마크. 연석/계단/낙차·인도-vs-도로에 최적, CC BY 4.0로 상업 활용 여지.
3. **GuideDog + GuideDogQA** (https://arxiv.org/abs/2503.12844) — 한국 팀 제작 1인칭 VLM 안내 데이터셋. 한국어 경고 생성·깊이 지각 평가에 바로 활용.
   - (횡단보도 특화 보강: **FPVCrosswalk2025** 1인칭 https://data.mendeley.com/datasets/mcr2jwk5bp/1, **점자블록**은 국내 **AI Hub #513** + 해외 **GuideTWSI**)

### 부족한 부분 (직접 수집 / 라벨링 필요)
- **한국어 음성 경고 문구·타이밍 셋**: "접근 차량", "앞 기둥", "계단 내려감" 등 상황→한국어 짧은 발화 매핑과 발화 시점(위험도 게이팅) 라벨은 공개 데이터에 없음. WalkVLM/WalkVLM-LR 스키마를 한국어로 재라벨링 필요.
- **접근 vs 주차 차량(ego-motion 기반) 라벨**: WOAD/HEADS-UP은 시스템·궤적 위주라, 걸음지기의 "정지 차량 vs 접근 차량" 이진 분류에 맞는 국내 보행자 시점 영상+ego-motion 주석은 자체 수집 필요.
- **국내 연석/계단/낙차 깊이 이벤트**: #189가 노면·깊이를 주나 "연석 높이·계단 시작점" 같은 낙차 이벤트 라벨은 부족 → SANPO/mmWalk 스키마 참고해 국내 보강 촬영 권장.
- **점자블록 방향·손상 통합**: GuideTWSI(방향바+돌출돔) + AI Hub #513(손상)은 있으나, 걸음지기의 "인도-vs-도로 방향 유도"와 결합한 국내 1인칭 방향 라벨은 재구성 필요.
- **실제 시각장애인 대상 평가 데이터**: 관련 문헌(Blindfolded proxy ⚠️, Participatory Design, Beyond Omakase)이 공통 경고 — 안대 대리평가는 근거로 불충분. 걸음지기는 **실제 사용자 대상 소규모 정직 평가**를 직접 설계·수집해야 함.

---

### 참고 (검증 상태 요약)
- **인용 전 반드시 재확인(⚠️)**: NavCog3 저널판, DeepNAVI, Heliyon 리뷰, MDPI 24(11):3572, **T&F 2026 서베이(unverified)**, Swin 계단, Sci Rep 스테레오, Electronics 2026, arXiv 2302.00916, T&F 메타분석, TACCESS 오디오개요, Blindfolded proxy, 그리고 데이터셋 Tenji10K·TrackAid·OD(Blind Sidewalk) — 링크는 검색근거만 있고 페이지 미검증이므로 **확인 필요**.
- 링크는 모두 원문 findings에 있는 것만 사용했으며, 미검증 항목은 새 링크를 만들지 않고 `⚠️`와 "확인 필요"를 유지했습니다.