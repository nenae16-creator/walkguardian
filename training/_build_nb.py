"""걸음지기 AI Hub #189 학습 Colab 노트북(.ipynb) 생성기."""
import json, os

C = []
def md(s): C.append({"cell_type": "markdown", "metadata": {}, "source": s})
def code(s): C.append({"cell_type": "code", "metadata": {}, "outputs": [], "execution_count": None, "source": s})

md("""# 걸음지기 × AI Hub #189 (인도보행 영상 / SideGuide) — 보도 장애물 탐지 학습

로컬 GPU가 없어 **Colab GPU** 기준. 목표: 국내 보도 장애물 **29종 YOLOv8** 파인튜닝 → **TF.js export** → 걸음지기 웹앱('빠름' 모드)에 꽂기.

> ⚠️ AI Hub #189는 **로그인+이용신청 승인** 후 다운로드(연구용 무료, 수십 GB). 아래 다운로드 셀은 승인된 계정 기준.
> ⚠️ 주석 스키마는 실제 파일을 봐야 확정 → **[STEP 3] 변환 셀의 표시 지점만 조정**하면 됩니다.
> 런타임 → 유형 변경 → **GPU** 먼저 설정하세요.""")

code("""# [STEP 0] 환경
import torch, subprocess
print("CUDA:", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
!pip -q install ultralytics
from ultralytics import YOLO
print("ultralytics OK")""")

md("""## [STEP 1] AI Hub #189 다운로드
AI Hub 공식 `aihubshell` CLI 사용 (dataSetSn=189). 계정 승인 필요.
- 데이터 페이지: https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=189
- 다운로드 매뉴얼(aihubshell): AI Hub 사이트 '이용안내 > AI데이터 다운로드' 참고
- 처음엔 **BBox 파트 일부만** 받아 소규모로 검증 권장.""")

code("""# [STEP 1] aihubshell 내려받기 + 로그인 정보
# ※ 아이디/비밀번호는 노트북에 하드코딩하지 말고 실행 시 입력 권장
import getpass, os
AIHUB_ID = input("AI Hub ID: ")
AIHUB_PW = getpass.getpass("AI Hub PW: ")

!curl -s -o aihubshell https://api.aihub.or.kr/api/aihubshell.do && chmod +x aihubshell
# 파일키 목록 확인(어떤 파트가 있는지) — 실제 filekey는 여기서 확인해 아래에 채움
!./aihubshell -mode l -datasetkey 189 -aihubid "$AIHUB_ID" -aihubpw "$AIHUB_PW" | head -50
# TODO: 위 목록에서 BBox 세트 filekey 를 골라 아래 FILEKEY 에 입력
FILEKEY = ""   # 예: "1,2,3" (BBox 관련 파트)
assert FILEKEY, "위 목록을 보고 BBox 파트 filekey 를 채우세요"
!./aihubshell -mode d -datasetkey 189 -filekey "$FILEKEY" -aihubid "$AIHUB_ID" -aihubpw "$AIHUB_PW"
# 압축해제
!mkdir -p /content/sideguide && find . -name "*.zip" -exec unzip -oq {} -d /content/sideguide \\;
!ls -R /content/sideguide | head -40""")

md("""## [STEP 2] 데이터 확인
이미지 폴더 / 주석 폴더 위치를 확인하고, 클래스 목록(29종)을 파악합니다.
AI Hub #189 주석은 이미지별 JSON(또는 통합 JSON)로 제공되며 bbox + 클래스가 들어있습니다.""")

code("""# [STEP 2] 경로/샘플 주석 살펴보기 (실제 구조 파악)
import glob, json, os, collections
ROOT = "/content/sideguide"
imgs = glob.glob(ROOT + "/**/*.jpg", recursive=True) + glob.glob(ROOT + "/**/*.png", recursive=True)
anns = glob.glob(ROOT + "/**/*.json", recursive=True) + glob.glob(ROOT + "/**/*.xml", recursive=True)
print("images:", len(imgs), "| annotation files:", len(anns))
if anns:
    print("샘플 주석:", anns[0])
    print(open(anns[0], encoding="utf-8").read()[:1200])""")

md("""## [STEP 3] 주석 → YOLO 포맷 변환  ★조정 지점★
YOLO는 이미지당 `.txt`(각 줄: `cls_id cx cy w h`, 0~1 정규화)를 원합니다.
아래 `parse_ann()` 의 **필드명/구조만** AI Hub #189 실제 스키마에 맞게 바꾸면 됩니다.""")

code("""# [STEP 3] 변환 — parse_ann 만 실제 스키마에 맞게 수정
import json, os, glob, shutil, collections
OUT = "/content/yolo";
for d in ["images/train","images/val","labels/train","labels/val"]:
    os.makedirs(f"{OUT}/{d}", exist_ok=True)

CLASSES = []   # 비우면 자동 수집. 특정 서브셋만 쓰려면 여기에 클래스명 리스트를 넣으세요.
cls_idx = {}

def get_id(name):
    if CLASSES:
        return CLASSES.index(name) if name in CLASSES else None
    if name not in cls_idx: cls_idx[name] = len(cls_idx)
    return cls_idx[name]

def parse_ann(path):
    \"\"\"→ (image_filename, W, H, [ (class_name, x1,y1,x2,y2), ... ])
       ★ AI Hub #189 실제 JSON 키에 맞게 아래를 조정하세요.\"\"\"
    j = json.load(open(path, encoding="utf-8"))
    # --- 예시(일반적 구조). 실제 키(예: 'annotations','bbox','category')로 교체 ---
    img_name = j.get("image", {}).get("filename") or os.path.basename(path).replace(".json", ".jpg")
    W = j.get("image", {}).get("width", 1920); H = j.get("image", {}).get("height", 1080)
    boxes = []
    for a in j.get("annotations", []):
        name = a.get("class") or a.get("category") or a.get("label")
        b = a.get("bbox") or a.get("box")          # [x,y,w,h] 또는 [x1,y1,x2,y2]
        if not (name and b): continue
        if len(b) == 4 and (b[2] < W and b[3] < H) and a.get("bbox"):
            x1,y1,x2,y2 = b[0], b[1], b[0]+b[2], b[1]+b[3]   # xywh 가정
        else:
            x1,y1,x2,y2 = b[:4]
        boxes.append((name, x1, y1, x2, y2))
    return img_name, W, H, boxes

# 이미지 파일 인덱스(이름→경로)
img_index = {os.path.basename(p): p for p in
             glob.glob(ROOT+"/**/*.jpg", recursive=True)+glob.glob(ROOT+"/**/*.png", recursive=True)}

n=0; skipped=0
for i, ap in enumerate(sorted(glob.glob(ROOT+"/**/*.json", recursive=True))):
    try:
        img_name, W, H, boxes = parse_ann(ap)
    except Exception as e:
        skipped+=1; continue
    ip = img_index.get(img_name)
    if not ip or not boxes: skipped+=1; continue
    split = "val" if i % 10 == 0 else "train"      # 10% val
    shutil.copy(ip, f"{OUT}/images/{split}/{img_name}")
    lines=[]
    for name,x1,y1,x2,y2 in boxes:
        cid = get_id(name)
        if cid is None: continue
        cx=((x1+x2)/2)/W; cy=((y1+y2)/2)/H; w=abs(x2-x1)/W; h=abs(y2-y1)/H
        if w<=0 or h<=0: continue
        lines.append(f"{cid} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
    open(f"{OUT}/labels/{split}/{os.path.splitext(img_name)[0]}.txt","w").write("\\n".join(lines))
    n+=1
names = CLASSES if CLASSES else [k for k,_ in sorted(cls_idx.items(), key=lambda kv: kv[1])]
print("변환 이미지:", n, "| skip:", skipped, "| classes:", len(names))
print(names)""")

code("""# [STEP 3b] data.yaml
yaml = f\"\"\"path: {OUT}
train: images/train
val: images/val
names: {{{', '.join(f'{i}: {repr(n)}' for i,n in enumerate(names))}}}
\"\"\"
open("/content/data.yaml","w").write(yaml); print(yaml)""")

md("""## [STEP 4] YOLOv8 파인튜닝
GUARDIAN에서 쓰던 `yolov8s`를 시작 가중치로 재사용. 소규모부터(epochs 작게) 돌려보고 늘리세요.""")

code("""# [STEP 4] 학습
model = YOLO("yolov8s.pt")   # GUARDIAN과 동일 계열
model.train(data="/content/data.yaml", epochs=30, imgsz=640, batch=16,
            project="walkguardian", name="sideguide_yolo", patience=10)""")

code("""# [STEP 5] 검증 + 샘플 추론
metrics = model.val()
print("mAP50-95:", metrics.box.map, "| mAP50:", metrics.box.map50)
import glob
sample = glob.glob(OUT+"/images/val/*")[:3]
if sample: model.predict(sample, save=True, conf=0.3)""")

md("""## [STEP 6] Export → 웹앱용
- **ONNX/TFLite**: 온디바이스/서버용.
- **TF.js**: 걸음지기 웹앱에 직접. (YOLO 후처리(NMS)를 JS에서 해야 하므로 글루 코드 필요 — 1차엔 정확도 벤치마크·제안서 근거로 먼저 활용 권장.)""")

code("""# [STEP 6] export
model.export(format="onnx")                 # → best.onnx
model.export(format="tflite")               # → best_saved_model/ , best.tflite
# TF.js:
!pip -q install tensorflowjs
# tflite/saved_model → tfjs (saved_model 경로는 export 로그 참고)
# !tensorflowjs_converter --input_format=tf_saved_model /content/.../best_saved_model /content/tfjs_model
print("export 완료 — runs/walkguardian/sideguide_yolo/weights/ 확인")""")

md("""## [STEP 7] 걸음지기 웹앱에 연결
1. TF.js 모델을 `mobile/models/sideguide/` 에 넣고 정적 호스팅(같은 GitHub Pages).
2. `index.html` 에서 COCO-SSD 대신 이 모델 로드(또는 '국내모델' 토글 추가). YOLO 출력 → `{cls,conf,xyxy}` 스키마로 변환(NMS 포함) 후 기존 `engine.process()` 에 그대로 투입.
3. 클래스명 → 걸음지기 문안 매핑: bollard/pole/입간판/화분 → `STATIC_OBST`("앞 장애물"), car/bus/truck → 에고보정 차량, stairs → "앞 계단 주의".

> 즉, **탐지기만 국내 특화로 바꾸고** 위험판단·음성·스케줄러(walk_logic.js)는 그대로 재사용됩니다.""")

nb = {"cells": C, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"},
      "accelerator": "GPU", "colab": {"provenance": []}},
      "nbformat": 4, "nbformat_minor": 5}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sideguide_walkguardian_colab.ipynb")
json.dump(nb, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out, "cells:", len(C))
