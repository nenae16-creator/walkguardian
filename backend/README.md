# 걸음지기 AI 백엔드

앱의 **AI 설명 모드**용 서버. **OpenAI 키는 서버에만** 두고 앱엔 주소만 넣습니다(키 노출 방지).
두 가지 방법:

| 방법 | 언제 | 폰에서? |
|---|---|---|
| **A. 로컬(PC)** — `local_server.py` | 지금 바로 PC에서 테스트 (Cloudflare 불필요) | ❌(PC만) |
| **B. Cloudflare Worker** — `worker.js` | 폰에서도 쓰려면 (공개 HTTPS) | ✅ |

---

## A. 로컬(PC)에서 바로 — 가장 빠름 ⚡
앱과 백엔드를 **한 번에** 띄웁니다(같은 localhost라 카메라·CORS 문제 없음). 설치 필요 없음(표준 파이썬).

```powershell
# PowerShell (Windows)
$env:OPENAI_API_KEY="sk-...재발급한_새_키..."
python backend/local_server.py
```
```cmd
:: cmd
set OPENAI_API_KEY=sk-...새_키...
python backend/local_server.py
```
→ 브라우저 **http://localhost:8000** → **⚙ 설정 → AI 백엔드 주소 =** `/analyze` → **AI 설명** 모드 → 시작.
- 키는 **환경변수에서만** 읽습니다(코드/저장소에 없음). 셀 닫으면 사라짐.
- PC 웹캠으로 테스트. 폰에서 쓰려면 아래 B(Worker).

---

## B. Cloudflare Worker (폰에서도)

앱의 **AI 설명 모드**용 서버. **OpenAI 키는 여기(Worker secret)에만** 두고, 앱엔 이 Worker의 **주소만** 넣습니다.
→ 키가 공개 코드/앱에 절대 노출되지 않습니다.

## 왜 백엔드가 필요한가
- 앱은 GitHub Pages(공개 HTTPS)라 키를 넣으면 누구나 봅니다. 봇이 스캔·도용 → 공용 키 소진.
- Worker가 키를 대신 들고 OpenAI를 호출 → 앱은 안전한 중계 주소만 압니다.

## 배포 (한 번만, ~5분)
사전: Node 설치, Cloudflare 무료 계정.

```bash
cd backend
npm create cloudflare@latest wg-ai -- --type=hello-world   # 또는: npm i -g wrangler
# 생성된 폴더의 src/index.js 를 이 폴더의 worker.js 내용으로 교체

# 시크릿 등록(키는 여기에만 저장됨)
npx wrangler secret put OPENAI_API_KEY     # ← 재발급한 OpenAI 키 붙여넣기
npx wrangler secret put WG_TOKEN           # ← 아무 문자열(앱에도 같은 값 입력). 남용 방지용

npx wrangler deploy                        # → https://wg-ai.<계정>.workers.dev 주소 발급
```

간단 대안(wrangler.toml 직접):
```
name = "wg-ai"
main = "worker.js"
compatibility_date = "2024-11-01"
```
그 뒤 `npx wrangler deploy`.

## 앱에 연결
1. 발급된 주소(`https://wg-ai.xxx.workers.dev`)를 앱 **⚙ 설정 → AI 백엔드 주소** 에 입력
2. `WG_TOKEN` 에 넣은 값을 **AI 토큰** 에 입력
3. 모드에서 **AI 설명** 선택 → 시작

## 동작
- 앱이 ~3초마다 전방 사진(작게) 전송 → Worker가 gpt-4o-mini vision 호출
- 모델은 **정해진 안내문 목록 중에서만** 위험을 고름(앞 장애물/앞 계단 주의/… 최대 2개)
- 앱은 그 문구의 **미리 만든 한국어 클립**을 재생 → 폰에 한국어 TTS 없어도 됨

## 비용·주의
- gpt-4o-mini + detail:low = 호출당 매우 저렴(대략 $0.0002~). 3초 간격 1시간 ≈ 수백 원.
- ★노출된 키는 **반드시 재발급**해서 secret 에 넣으세요.
- WG_TOKEN 으로 남의 무단 사용을 1차 차단(완벽하진 않으니 Cloudflare 대시보드에서 사용량 확인 권장).
- 프롬프트에 "옆 차도 차량 무시" 규칙이 들어 있습니다(worker.js SYS).
