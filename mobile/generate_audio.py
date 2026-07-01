"""
generate_audio.py — 걸음지기 음성 문구를 미리 WAV 로 생성 (PC 한국어 음성 Heami 사용)
폰에 한국어 TTS 가 없어도 앱이 이 파일을 재생해 '한국어'로 안내한다.
결과: mobile/audio/clipNN.wav + mobile/clips.json (문구→파일 매핑)
"""
import pyttsx3, json, os, sys

SIDES = ["앞", "왼쪽", "오른쪽"]

def texts():
    s = set()
    # 방향 포함 문구
    for tmpl in ["정지, {s} 차량 접근", "정지, {s} 오토바이 접근",
                 "{s} 차량 주의", "{s} 차량 지나감", "{s} 정차 차량", "{s} 오토바이 주의"]:
        for sd in SIDES:
            s.add(tmpl.replace("{s}", sd))
    for sd in ["왼쪽", "오른쪽"]:
        s.add(f"{sd} 점자블록")
    # 고정 문구
    s.update(["정지, 앞 낭떠러지", "앞 장애물", "앞 사람", "앞 계단 주의", "앞 턱 주의",
              "보도 끝 주의", "앞 공사구간", "차도입니다, 인도로", "점자블록 위",
              "앞 횡단보도", "신호 대기", "보행로를 벗어남",
              "직진", "왼쪽으로", "오른쪽으로", "정지, 길 막힘",
              "소리 테스트, 걸음지기입니다", "걸음지기 시작"])
    return sorted(s)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(here, "audio")
    os.makedirs(outdir, exist_ok=True)
    ts = texts()
    manifest = {}
    made = 0
    for i, t in enumerate(ts):
        fn = f"clip{i:02d}.wav"
        path = os.path.join(outdir, fn)
        eng = pyttsx3.init()               # 파일마다 재초기화(SAVE 안정성)
        for v in eng.getProperty("voices"):
            nm = (v.name or "").lower()
            if "korean" in nm or "heami" in nm:
                eng.setProperty("voice", v.id); break
        eng.setProperty("rate", 190)
        eng.save_to_file(t, path)
        eng.runAndWait()
        eng.stop()
        ok = os.path.exists(path) and os.path.getsize(path) > 1000
        if ok:
            made += 1
        manifest[t] = "audio/" + fn
        print(("  ok " if ok else " FAIL ") + f"{fn}  «{t}»")
    with open(os.path.join(here, "clips.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False)
    total = sum(os.path.getsize(os.path.join(outdir, x)) for x in os.listdir(outdir) if x.endswith(".wav"))
    print(f"\n생성 {made}/{len(ts)}개, 합계 {total/1024:.0f} KB → clips.json 저장")
    sys.exit(0 if made == len(ts) else 1)


if __name__ == "__main__":
    main()
