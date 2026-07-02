"""
걸음지기 로컬 AI 백엔드 (PC 테스트용, Cloudflare 불필요)
- mobile/ 앱을 정적 서빙 + POST /analyze 로 OpenAI 비전 호출
- ★키는 환경변수 OPENAI_API_KEY 에서만 읽음(코드/저장소에 없음)
- 같은 오리진(localhost)이라 카메라도 되고 mixed-content 문제도 없음

실행:
  Windows PowerShell:  $env:OPENAI_API_KEY="sk-..."; python backend/local_server.py
  Windows cmd:         set OPENAI_API_KEY=sk-... && python backend/local_server.py
  mac/Linux:           OPENAI_API_KEY=sk-... python backend/local_server.py
그 뒤 브라우저: http://localhost:8000  → ⚙설정 → 'AI 백엔드 주소' 에  /analyze  입력 → 'AI 설명' 모드
"""
import os, sys, json, http.server, urllib.request, urllib.error
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows cp949 콘솔 대비
except Exception: pass

import base64
KEY = os.environ.get("OPENAI_API_KEY", "").strip().strip('"').strip("'")   # 공백·따옴표 제거
MOBILE = str(Path(__file__).resolve().parent.parent / "mobile")
PORT = int(os.environ.get("PORT", "8000"))
VOICE = os.environ.get("WG_VOICE", "nova")   # OpenAI tts 목소리

VSYS = ("너는 시각장애인 보행 보조다. 사진은 걷는 사람의 바로 앞 시야다. "
        "앞에 있는 사물·장애물·계단·턱을 아주 짧은 한국어로 알려줘. "
        "예: '앞에 의자', '왼쪽 테이블', '앞 계단 조심', '앞 전봇대', '앞에 문'. "
        "가장 가깝고 중요한 것 1~2개만, 전체 15자 이내로 짧게. "
        "★계단·단차가 보이면 꼭 '계단'을 말해(특히 내려가는 계단). 옆 차도의 차량은 무시. "
        "위험/사물이 없으면 정확히 '없음' 이라고만 답해. 문장부호·설명 금지.")


def _openai(url, payload, timeout=30, raw=False):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read() if raw else json.loads(r.read().decode())


def vision(image):
    j = _openai("https://api.openai.com/v1/chat/completions", {
        "model": "gpt-4o-mini", "temperature": 0.2, "max_tokens": 30,
        "messages": [
            {"role": "system", "content": VSYS},
            {"role": "user", "content": [
                {"type": "text", "text": "앞에 뭐가 있어?"},
                {"type": "image_url", "image_url": {"url": image, "detail": "high"}},
            ]},
        ],
    })
    return (j["choices"][0]["message"]["content"] or "").strip().replace('"', "").replace(".", "")


def tts(text):
    audio = _openai("https://api.openai.com/v1/audio/speech", {
        "model": "gpt-4o-mini-tts", "voice": VOICE, "input": text, "response_format": "mp3",
    }, raw=True)
    return base64.b64encode(audio).decode()


def analyze(image):
    if not KEY or not image:
        return {"text": "", "audio": ""}
    try:
        text = vision(image)
    except urllib.error.HTTPError as e:
        body = ""
        try: body = e.read().decode(errors="replace")
        except Exception: pass
        print(f"[OpenAI {e.code}] {body[:400]}")
        return {"text": "", "audio": "", "error": f"OpenAI {e.code}: {body[:180]}"}
    except Exception as e:
        print("[vision error]", e)
        return {"text": "", "audio": "", "error": str(e)}
    if not text or text in ("없음", "없습니다", "없어요", "[]", "none", "None"):
        return {"text": "", "audio": ""}
    try:
        return {"text": text, "audio": tts(text)}
    except Exception as e:
        print("[tts error]", e)
        return {"text": text, "audio": ""}   # 음성 실패해도 텍스트는 반환


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=MOBILE, **k)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type,x-wg-token")

    def do_OPTIONS(self):
        self.send_response(204); self._cors()
        self.send_header("Access-Control-Allow-Methods", "POST,OPTIONS"); self.end_headers()

    def do_POST(self):
        if self.path.rstrip("/") != "/analyze":
            self.send_error(404); return
        try:
            n = int(self.headers.get("content-length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            result = analyze(body.get("image", ""))
        except Exception as e:
            print("[analyze error]", e); result = {"text": "", "audio": "", "error": str(e)}
        out = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors(); self.end_headers(); self.wfile.write(out)

    def log_message(self, fmt, *args):
        a0 = args[0] if args else ""
        if isinstance(a0, str) and "/analyze" in a0:
            print("[AI]", *args)


if __name__ == "__main__":
    print("=" * 56)
    print("걸음지기 로컬 백엔드")
    print("  OpenAI 키:", "설정됨" if KEY else "없음 (OPENAI_API_KEY 환경변수 설정 필요)")
    print(f"  앱:  http://localhost:{PORT}")
    print("  설정 -> AI 백엔드 주소 =  /analyze   -> 'AI 설명' 모드")
    print("=" * 56)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
