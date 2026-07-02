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
import os, sys, json, http.server, urllib.request
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows cp949 콘솔 대비
except Exception: pass

KEY = os.environ.get("OPENAI_API_KEY", "")
MOBILE = str(Path(__file__).resolve().parent.parent / "mobile")
PORT = int(os.environ.get("PORT", "8000"))
ALLOWED = ["앞 장애물", "앞 계단 주의", "앞 턱 주의", "앞 사람", "앞 공사구간",
           "보도 끝 주의", "앞 정차 차량", "정지, 앞 차량 접근", "앞 횡단보도", "차도입니다, 인도로"]
SYS = ("너는 시각장애인 보행 보조다. 사진은 인도를 걷는 사람의 바로 앞 시야다. "
       "경로 위에서 위험하거나 부딪힐 수 있는 것을 골라, 아래 '허용 문구' 중에서만 최대 2개를 JSON 배열로 답하라. "
       "★계단·층계·단차가 조금이라도 보이면 반드시 '앞 계단 주의'를 넣어라(올라가는·내려가는 계단, 한 칸 턱, 지하철 계단 모두 포함). "
       "내려가는 계단(바닥이 갑자기 낮아지거나 아래로 이어지는 단)은 특히 위험하니 반드시 잡아라. "
       "전봇대·볼라드·입간판·기둥·문·화분·공사·기타 튀어나온 장애물은 '앞 장애물'. 턱(낮은 단차)은 '앞 턱 주의'. "
       "앞을 막는 사람은 '앞 사람'. 인도가 끊기면 '보도 끝 주의'. "
       "옆 차도의 차량은 무시(내 앞을 가로지르거나 인도로 올라오는 차만 '정지, 앞 차량 접근'). "
       "위험 없으면 []. 설명 금지, 오직 JSON 배열. 허용 문구: " + json.dumps(ALLOWED, ensure_ascii=False))


def analyze(image):
    if not KEY or not image:
        return []
    payload = {
        "model": "gpt-4o-mini", "temperature": 0, "max_tokens": 60,
        "messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content": [
                {"type": "text", "text": "이 장면의 위험을 허용 문구로만 답해."},
                {"type": "image_url", "image_url": {"url": image, "detail": "high"}},
            ]},
        ],
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.loads(r.read().decode())
    txt = j["choices"][0]["message"]["content"].replace("```json", "").replace("```", "").strip()
    arr = json.loads(txt)
    return [h for h in arr if h in ALLOWED][:2] if isinstance(arr, list) else []


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
            hazards = analyze(body.get("image", ""))
        except Exception as e:
            print("[analyze error]", e); hazards = []
        out = json.dumps({"hazards": hazards}, ensure_ascii=False).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors(); self.end_headers(); self.wfile.write(out)

    def log_message(self, fmt, *args):
        if "/analyze" in (args[0] if args else ""):
            print("[AI]", *args)


if __name__ == "__main__":
    print("=" * 56)
    print("걸음지기 로컬 백엔드")
    print("  OpenAI 키:", "설정됨" if KEY else "없음 (OPENAI_API_KEY 환경변수 설정 필요)")
    print(f"  앱:  http://localhost:{PORT}")
    print("  설정 -> AI 백엔드 주소 =  /analyze   -> 'AI 설명' 모드")
    print("=" * 56)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
