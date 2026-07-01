"""
run_video.py — 영상 파일로 걸음지기 데모 (라이브 YOLOv8)

사용:
  pip install ultralytics pyttsx3
  python run_video.py --video "샘플.mp4" --out demo_out.mp4 --max-sec 20

--out 지정 시 GUARDIAN 처럼 박스 + 마지막 음성 자막을 얹은 데모 영상을 만든다.
음성은 콘솔 로그로도 남으므로 GPU/스피커 없이도 결과 확인 가능.
"""
import argparse, sys, os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from walkguardian.detection import YOLOv8Detector
from walkguardian.pipeline import WalkGuardian
from walkguardian.voice import Voice
from walkguardian import geometry as G

LEVEL_BGR = {1: (50, 50, 255), 2: (30, 140, 255), 3: (0, 200, 255), 4: (200, 200, 200)}


def _font(size):
    for p in [r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\malgunbd.ttf",
              "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def draw_caption(frame_bgr, text, level):
    """PIL 로 한국어 자막(하단 배너) 렌더."""
    if not text:
        return frame_bgr
    img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(img, "RGBA")
    f = _font(34)
    w, h = img.size
    bb = d.textbbox((0, 0), text, font=f)
    tw = bb[2] - bb[0]
    col = {1: (220, 30, 30), 2: (230, 120, 20), 3: (210, 180, 0), 4: (120, 120, 120)}.get(level, (60, 60, 60))
    d.rectangle([w // 2 - tw // 2 - 20, h - 74, w // 2 + tw // 2 + 20, h - 20], fill=col + (220,))
    d.text((w // 2 - tw // 2, h - 70), text, font=f, fill=(255, 255, 255))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--weights", default="yolov8n.pt")
    ap.add_argument("--out", default=None, help="주석 데모 영상 출력 경로(mp4)")
    ap.add_argument("--max-sec", type=float, default=0, help="처리 최대 초(0=전체)")
    ap.add_argument("--no-tts", action="store_true", help="스피커 음성 끄고 로그만")
    ap.add_argument("--resize-w", type=int, default=960)
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"영상 열기 실패: {args.video}"); sys.exit(1)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ow = args.resize_w
    oh = int(src_h * ow / src_w)

    det = YOLOv8Detector(weights=args.weights)
    voice = Voice(use_tts=not args.no_tts)
    wg = WalkGuardian(detector=det, voice=voice)

    writer = None
    if args.out:
        writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (ow, oh))

    last_text, last_level = "", 0
    i, n_alerts = 0, 0
    max_frames = int(args.max_sec * fps) if args.max_sec > 0 else 10 ** 9
    print(f"▶ 처리 시작: {os.path.basename(args.video)}  ({ow}x{oh}, {fps:.0f}fps)")
    while i < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (ow, oh))
        t = i / fps
        alerts, dets, env = wg.step(frame, t, (ow, oh), moving=True)
        for a in alerts:
            last_text, last_level = a.text, a.level
            n_alerts += 1
        if writer is not None:
            for dobj in dets:
                x1, y1, x2, y2 = [int(v) for v in dobj["xyxy"]]
                band = G.proximity_band(dobj["xyxy"], ow, oh)
                c = (0, 200, 80) if band == G.FAR else (0, 165, 255) if band == G.MID else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), c, 2)
            frame = draw_caption(frame, last_text, last_level)
            writer.write(frame)
        i += 1

    cap.release()
    if writer is not None:
        writer.release()
        print(f"💾 데모 영상 저장: {args.out}")
    voice.close()
    print(f"✅ 완료 — {i}프레임, 음성안내 {n_alerts}건")


if __name__ == "__main__":
    main()
