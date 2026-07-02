"""걸음지기 '오늘 바로 학습' Colab 노트북 — Roboflow 공개 데이터셋(YOLO 즉시)."""
import json, os
C = []
def md(s): C.append({"cell_type": "markdown", "metadata": {}, "source": s})
def code(s): C.append({"cell_type": "code", "metadata": {}, "outputs": [], "execution_count": None, "source": s})

md("""# 걸음지기 — 오늘 바로 학습 (Roboflow 공개 데이터셋 → YOLOv8)

AI Hub #189 승인을 기다리지 않고 **오늘 Colab에서 바로** 보도 장애물 탐지기를 학습합니다.
Roboflow Universe에는 **Bollard(볼라드)·Curb(연석)·Light-pole(전봇대)·Garbage-bin(쓰레기통)·Crosswalk·Construction-barrier** 등
걸음지기에 딱 맞는 공개 데이터셋이 YOLO 포맷으로 준비돼 있습니다.

> 목표: 국내 보도 특화 탐지기 → **TF.js export → 웹앱 '빠름' 모드 교체**. 위험판단·에고보정·한국어음성·스케줄러는 그대로 재사용.
> 런타임 → 유형 변경 → **GPU** 먼저!""")

code("""# [1] 환경
import torch
print("GPU:", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU만 — 런타임 GPU로!")
!pip -q install ultralytics roboflow
from ultralytics import YOLO""")

md("""## [2] 데이터셋 받기 (Roboflow, 무료)
1. https://universe.roboflow.com 접속 → 검색창에 **`sidewalk obstacle`** 또는 **`bollard curb`** 검색
   - 추천: 클래스에 Bollard/Curb/Light-pole/Garbage-bin/Crosswalk 가 있는 것 (예: "sidewalk obstacle avoidance" 계열)
2. 데이터셋 페이지 → **Download Dataset → Format: YOLOv8 → "show download code"**
3. 뜨는 3~4줄 스니펫을 아래 셀에 **그대로 붙여넣기** (무료 가입하면 `api_key` 자동 포함)
4. 여러 데이터셋을 합치고 싶으면 이 셀을 복제해 여러 개 받은 뒤 data.yaml 을 합쳐도 됩니다.""")

code('''# [2] ↓↓↓ Roboflow "show download code" 스니펫을 여기 붙여넣기 (아래는 형식 예시) ↓↓↓
from roboflow import Roboflow
rf = Roboflow(api_key="YOUR_API_KEY")                 # ← 본인 키
project = rf.workspace("WORKSPACE").project("PROJECT") # ← 데이터셋 스니펫 값
dataset = project.version(1).download("yolov8")        # ← 버전 번호
DATA_YAML = dataset.location + "/data.yaml"
print("DATA_YAML =", DATA_YAML)
print(open(DATA_YAML).read())                          # 클래스 목록 확인''')

md("""## [3] 학습 (YOLOv8)
GUARDIAN과 동일한 `yolov8s`로 파인튜닝. 데이터가 작으면 epochs를 늘리고, 크면 줄여서 먼저 감을 잡으세요.""")

code("""# [3] 학습
model = YOLO("yolov8s.pt")
model.train(data=DATA_YAML, epochs=60, imgsz=640, batch=16,
            project="walkguardian", name="train_now", patience=15)""")

code("""# [4] 검증 + 샘플 추론
m = model.val()
print("mAP50:", m.box.map50, "| mAP50-95:", m.box.map)
import glob, os
val_imgs = glob.glob(os.path.join(os.path.dirname(DATA_YAML), "valid", "images", "*"))[:3]
if val_imgs: model.predict(val_imgs, save=True, conf=0.3)
print("예측 결과: runs/.../predict 확인")""")

md("""## [5] Export → 웹앱용
- **best.pt**: 이후 재학습/추론용.
- **TF.js**: 걸음지기 웹앱에 직접(브라우저에서 YOLO NMS 글루 필요 → 1차는 정확도 벤치마크로 먼저 활용 권장).""")

code("""# [5] export
best = "walkguardian/train_now/weights/best.pt"
YOLO(best).export(format="onnx")
YOLO(best).export(format="tflite")
!pip -q install tensorflowjs
# saved_model → tfjs (export 로그의 best_saved_model 경로 사용)
# !tensorflowjs_converter --input_format=tf_saved_model .../best_saved_model /content/tfjs_model
from google.colab import files
# files.download("walkguardian/train_now/weights/best.pt")   # 필요시 다운로드
print("완료 — weights/best.pt / best.onnx / best.tflite")""")

md("""## [6] 걸음지기 웹앱에 연결
1. 학습된 클래스명을 확인(예: Bollard, Curb, Light-pole, Garbage-bin ...).
2. `mobile/walk_logic.js` 의 `STATIC_OBST` 에 이 클래스명들을 추가하면 → 전방 근접 시 **"앞 장애물"** 로 안내됩니다.
   ```js
   const STATIC_OBST = new Set(["...", "bollard","curb","light-pole","garbage-bin","construction-barrier","pole","cone"]);
   ```
3. 탐지기를 이 모델(TF.js)로 교체하거나, 우선은 **정확도 벤치마크·제안서 근거**로 사용.
   → 위험판단/에고보정/음성/스케줄러는 **수정 불필요**(탐지 스키마 `{cls,conf,xyxy}` 만 맞추면 됨).

> 즉 이 노트북의 산출물은 "국내 보도 장애물을 더 잘 보는 눈". 걸음지기의 뇌(walk_logic)는 그대로.""")

nb = {"cells": C, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"},
      "accelerator": "GPU", "colab": {"provenance": []}}, "nbformat": 4, "nbformat_minor": 5}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "train_now_roboflow_colab.ipynb")
json.dump(nb, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out, "cells:", len(C))
