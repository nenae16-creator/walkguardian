# 팀 개발 가이드 (CONTRIBUTING)

## 1. 시작
```bash
git clone https://github.com/nenae16-creator/walkguardian.git
cd walkguardian
python -m http.server 8777 --directory mobile   # http://localhost:8777 로 열기
```
- 대부분의 작업은 **`mobile/`** 에서 이뤄집니다 (웹앱).
- 카메라는 `localhost` 또는 HTTPS 에서만 동작. PC에선 `⚙ → 동영상`으로 영상 파일 테스트 가능.

## 2. 어디를 고치나
| 하고 싶은 것 | 파일 |
|---|---|
| 위험 판단·문안·차량/장애물 로직·스케줄러 | `mobile/walk_logic.js` |
| UI·모드·카메라·GPS·설정 | `mobile/index.html` |
| 국내모델 추론(YOLO onnx) | `mobile/wg_onnx.js` |
| 음성 문구 추가 | `walk_logic.js` PHRASES + `mobile/generate_audio.py` 로 클립 재생성 |
| AI 백엔드 프롬프트 | `backend/worker.js` |
| 모델 재학습 | `training/*.ipynb` (Colab) |

## 3. 브랜치 / PR
- `master` = 배포(자동으로 GitHub Pages 라이브). **직접 push 지양**, 기능은 브랜치로.
```bash
git checkout -b feat/<기능>
# ...작업...
git commit -m "..."; git push -u origin feat/<기능>
# GitHub 에서 Pull Request 생성 → 리뷰 후 master 병합
```
- master 에 병합되면 몇 분 뒤 라이브(https://nenae16-creator.github.io/walkguardian/mobile/) 반영.

## 4. 커밋 전 체크
1. **자가검사 통과** — 브라우저 콘솔 `window.__selfTest().every(x=>x[1])` 또는
   `node -e "require('./mobile/walk_logic.js'); const r=WalkLogic.selfTest(); console.log(r.every(x=>x[1]))"`
2. 콘솔 에러 없는지 확인.
3. 로직을 바꿨으면 `walk_logic.js` 의 `selfTest*` 에 **테스트 케이스 추가**.

## 5. 🔐 보안 (중요)
- **API 키·비밀번호·토큰을 저장소나 앱 코드에 절대 커밋하지 말 것.**
- OpenAI 키는 `backend/` 의 Cloudflare Worker **secret** 에만. 앱엔 백엔드 **주소만** 입력(로컬 저장).
- 실수로 키를 커밋/노출했다면 **즉시 재발급**.

## 6. 팀원 추가 (소유자)
GitHub 저장소 → **Settings → Collaborators → Add people** → 팀원 GitHub 아이디 입력.
(공개 저장소라 누구나 클론·PR 가능하지만, push 권한은 collaborator 에게만.)

## 7. 원칙
- 과장 금지: "안전합니다/사고 예방" 같은 표현 쓰지 않기(보조 도구).
- 짧은 음성 우선, 알림 최소화(피로 방지).
- 바꾸기 전 `docs/references.md` 의 근거 참고.
