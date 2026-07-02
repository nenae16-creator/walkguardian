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

md("""## [2] 데이터셋 받기 (Roboflow) — 새 API 키만 넣으면 됨
아래 셀은 **Viz 'Sidewalk Detection'** (`viz-kxwrm/sidewalk-detection-d54fs` v11, 318장, Instance Segmentation)로 미리 채워져 있습니다.
- **API 키:** https://roboflow.com 로그인 → 우상단 프로필 → **Settings → Roboflow API → Private API Key** 복사
  (★스크린샷 등으로 노출된 키는 **Regenerate(재발급)** 후 사용)
- 더 큰 세트를 원하면 `version(11)` → `version(7)`(증강 1489장) 등으로 숫자만 바꾸세요.
- 완전히 다른 데이터셋: 그 페이지 URL의 `workspace/project/version` 세 값으로 교체.""")

code('''# [2] Viz "Sidewalk Detection" (Instance Segmentation) — 새 API 키만 채우면 됨
from roboflow import Roboflow
rf = Roboflow(api_key="여기에_새_API_KEY")              # ← 재발급한 새 키
project = rf.workspace("viz-kxwrm").project("sidewalk-detection-d54fs")
dataset = project.version(11).download("yolov8")        # 더 많게: 7(증강 1489장)
DATA_YAML = dataset.location + "/data.yaml"
print("DATA_YAML =", DATA_YAML)
print(open(DATA_YAML).read())                          # 클래스 목록 확인''')

md("""## [3] 학습 (YOLOv8)
GUARDIAN과 동일한 `yolov8s`로 파인튜닝. 데이터가 작으면 epochs를 늘리고, 크면 줄여서 먼저 감을 잡으세요.""")

code("""# [3] 학습 — 라벨이 세그(폴리곤)인지 탐지(박스)인지 자동 판별해 맞는 모델 선택
import glob
lbls = glob.glob(dataset.location + "/train/labels/*.txt")
seg = False
for f in lbls[:30]:
    for ln in open(f):
        if len(ln.split()) > 6: seg = True; break
    if seg: break
base = "yolov8s-seg.pt" if seg else "yolov8s.pt"
print("라벨 형식:", "세그멘테이션" if seg else "탐지", "→ base:", base)
model = YOLO(base)
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

code("""# [5] best.pt 자동 탐색(폴더명 train_now2 등 무관) → 클래스/지표/export/다운로드
import glob, os
best = max(glob.glob("**/weights/best.pt", recursive=True), key=os.path.getmtime)
print("찾은 best.pt:", best)
m = YOLO(best)
print("클래스:", m.names)                 # ← 이 목록을 개발자에게 전달
try:
    metrics = m.val(data=DATA_YAML); print("mAP50:", metrics.box.map50)
except Exception as e:
    print("val skip:", e)
m.export(format="onnx")
from google.colab import files
files.download(best)""")

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
