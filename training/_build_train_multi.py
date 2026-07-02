"""걸음지기 — 여러 Roboflow 데이터셋 합쳐서 학습(YOLOv8) Colab 노트북 생성기."""
import json, os
C = []
def md(s): C.append({"cell_type": "markdown", "metadata": {}, "source": s})
def code(s): C.append({"cell_type": "code", "metadata": {}, "outputs": [], "execution_count": None, "source": s})

md("""# 걸음지기 — 여러 데이터셋 합쳐서 학습 (Object Detection)

여러 Roboflow 데이터셋을 **클래스 이름 기준으로 통합**해 하나의 YOLOv8 탐지기로 학습합니다.
미리 채워둔 데이터셋: **Deneme**(1905장) + **Fyp-Videos**(3100장) — 둘 다 Object Detection.

> ⚠️ 앞서 학습한 **Sidewalk-Detection은 Instance Segmentation**이라 여기 섞지 않습니다(별도 모델).
> 데이터셋마다 클래스명이 달라서, 같은 이름(car/Automobile 등)은 자동 병합, 다른 건 새 클래스로 추가됩니다.
> 런타임 → GPU 먼저!""")

code("""# [1] 환경 + Roboflow API
import torch; print("GPU:", torch.cuda.is_available())
!pip -q install ultralytics roboflow pyyaml
from ultralytics import YOLO
from roboflow import Roboflow
rf = Roboflow(api_key="여기에_새_API_KEY")      # ← 재발급한 새 키""")

md("""## [2] 합칠 데이터셋 목록 (workspace, project, version)
`(workspace, project, version)` 튜플만 추가하면 몇 개든 합쳐집니다. URL에서 세 값을 그대로 뽑으면 됩니다.""")

code('''# [2] 데이터셋 목록 — 원하는 만큼 추가
DATASETS = [
    ("proje-a38aj", "deneme-jrfup", 10),                 # Deneme 1905장
    ("fypdataset-pw40c", "fyp-videos-annotations", 29),  # Fyp-Videos 3100장
    # ("workspace", "project", version),                 # 더 추가 가능
]
locations = []
for ws, pj, ver in DATASETS:
    ds = rf.workspace(ws).project(pj).version(ver).download("yolov8")   # 탐지 포맷
    locations.append(ds.location); print("받음:", ds.location)''')

md("""## [3] 병합 — 클래스 이름 기준 통합 (로컬 검증 완료 로직)
같은 뜻의 클래스는 `ALIAS`로 합칩니다(automobile→car 등). 필요하면 ALIAS를 늘리세요.""")

code('''# [3] 병합
import os, glob, shutil, yaml
ALIAS = {"automobile":"car","vehicle":"car","auto":"car",
         "pedestrian":"person","human":"person",
         "light-pole":"pole","lightpole":"pole","electric-pole":"pole","electricpole":"pole",
         "trashcan":"garbage-bin","garbage":"garbage-bin","dustbin":"garbage-bin","trash":"garbage-bin",
         "stair":"stairs","staircase":"stairs"}
def _norm(n): return ALIAS.get(n.strip().lower(), n.strip().lower())
def _load_names(loc):
    y=yaml.safe_load(open(os.path.join(loc,"data.yaml"),encoding="utf-8")); n=y["names"]
    return n if isinstance(n,list) else [n[k] for k in sorted(n, key=lambda x:int(x))]
def merge_yolo(locations, out):
    for s in ["train/images","train/labels","valid/images","valid/labels"]:
        os.makedirs(os.path.join(out,s), exist_ok=True)
    gnames, name2id = [], {}
    def gid(nm):
        k=_norm(nm)
        if k not in name2id: name2id[k]=len(gnames); gnames.append(k)
        return name2id[k]
    imgs=0
    for loc in locations:
        remap={i:gid(nm) for i,nm in enumerate(_load_names(loc))}
        prefix=os.path.basename(os.path.normpath(loc))+"_"
        for split in ["train","valid"]:
            ldir,idir=os.path.join(loc,split,"labels"),os.path.join(loc,split,"images")
            if not os.path.isdir(ldir): continue
            for lbl in glob.glob(os.path.join(ldir,"*.txt")):
                stem=os.path.splitext(os.path.basename(lbl))[0]
                img=next((os.path.join(idir,stem+e) for e in (".jpg",".png",".jpeg",".JPG")
                          if os.path.exists(os.path.join(idir,stem+e))), None)
                if not img: continue
                shutil.copy(img, os.path.join(out,split,"images",prefix+os.path.basename(img)))
                lines=[]
                for ln in open(lbl):
                    p=ln.split()
                    if p: p[0]=str(remap[int(float(p[0]))]); lines.append(" ".join(p))
                open(os.path.join(out,split,"labels",prefix+os.path.basename(lbl)),"w").write("\\n".join(lines))
                imgs+=1
    yaml.safe_dump({"path":out,"train":"train/images","val":"valid/images",
                    "names":{i:n for i,n in enumerate(gnames)}},
                   open(os.path.join(out,"data.yaml"),"w",encoding="utf-8"), allow_unicode=True)
    return gnames, imgs
OUT="/content/combined"
names, imgs = merge_yolo(locations, OUT)
DATA_YAML = OUT+"/data.yaml"
print("통합 클래스:", names)
print("총 이미지:", imgs)''')

md("""## [4] 학습 (YOLOv8 탐지)""")

code("""# [4] 학습
model = YOLO("yolov8s.pt")
model.train(data=DATA_YAML, epochs=60, imgsz=640, batch=16,
            project="walkguardian", name="multi", patience=15)""")

code("""# [5] best.pt 자동 탐색 → 클래스/지표/export/다운로드
import glob, os
best = max(glob.glob("**/weights/best.pt", recursive=True), key=os.path.getmtime)
print("best.pt:", best)
m = YOLO(best); print("클래스:", m.names)      # ← 이 목록을 개발자에게 전달
try: print("mAP50:", m.val(data=DATA_YAML).box.map50)
except Exception as e: print("val skip:", e)
m.export(format="onnx")
from google.colab import files; files.download(best)""")

md("""## [6] 걸음지기 연결
- `[5]`의 **클래스 목록 + mAP** 를 개발자에게 전달 → `walk_logic.js`의 `STATIC_OBST`에 obstacle/pole/curb 등 연결.
- 모델을 웹앱에 넣으려면 TF.js 변환(`model.export(format='tfjs')`) + 브라우저 YOLO 추론 글루(개발자가 처리).
- 위험판단·에고보정·한국어음성·스케줄러는 그대로 재사용.""")

nb = {"cells": C, "metadata": {"kernelspec": {"name":"python3","display_name":"Python 3"},
      "accelerator":"GPU","colab":{"provenance":[]}}, "nbformat":4, "nbformat_minor":5}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "train_multi_roboflow_colab.ipynb")
json.dump(nb, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out, "cells:", len(C))
