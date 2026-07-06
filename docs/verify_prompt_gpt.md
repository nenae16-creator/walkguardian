# GPT 검증용 프롬프트 (아래 전체를 복사해서 붙여넣기)

당신은 컴퓨터비전·모바일 온디바이스 AI·접근성(시각장애 보조) 분야 20년차 시니어 엔지니어다.
아래는 시각장애인 보행 보조 웹앱에 방금 구현된 **"내리막 계단/턱 낙차(drop-off) 감지"** 기능이다.
칭찬은 필요 없다. **적대적으로 검증**해라: 논리 오류, 실외 환경에서의 오탐/미탐 시나리오, 파라미터의 근거 부족, 안전상 위험한 설계를 구체적으로 지적하고, 각 지적마다 "어떻게 고칠지"를 제시해라.

## 시스템 맥락
- 대상: 시각장애인. 스마트폰(가슴 높이, 세로)을 들고 인도를 걷는 1인칭 시점.
- 앱: 모바일 웹앱(GitHub Pages). 위험을 짧은 한국어 음성으로 안내 ("앞 계단 주의", "정지, 앞 낭떠러지").
- 문제: 내리막 계단은 접근 중엔 "평평한 바닥의 끝선"으로만 보여 객체탐지(YOLO)로는 못 잡음.
- 해법: 단안 깊이(Depth Anything V2 small, int8 onnx 27MB, onnxruntime-web/wasm)로 깊이맵을 만들고,
  "바닥이 갑자기 꺼지는 깊이 불연속"을 기하적으로 감지.
- 전제: Depth Anything V2 출력은 **relative depth이며 값이 클수록 가까움**(disparity 성격). metric 아님.

## 구현 A — 낙차 감지 알고리즘 (JavaScript, 실코드)
```js
// 입력: 깊이맵(Float32Array, W×H row-major, 값 클수록 가까움, 스케일 임의)
const DROPOFF = { cols: 24, x0: 0.30, x1: 0.70, yTop: 0.45, drop: 0.35, nearMin: 0.25,
                  minCols: 0.40, band: 0.08 };
function analyzeDropoff(data, W, H, cfg) {
  const P = Object.assign({}, DROPOFF, cfg || {});
  let mx = 0;
  for (let i = 0; i < data.length; i += 7) { const v = data[i]; if (v > mx) mx = v; }
  if (mx <= 0) return null;
  const yStart = H - 2, yEnd = Math.floor(H * P.yTop);
  const step = Math.max(1, Math.floor(H / 128));
  const edges = [];
  for (let c = 0; c < P.cols; c++) {
    const x = Math.floor((P.x0 + (P.x1 - P.x0) * (c / (P.cols - 1))) * W);
    let prev = null, edge = -1;
    for (let y = yStart; y >= yEnd; y -= step) {
      const i = y * W + x;
      const v = (data[i] + (data[i - 1] || data[i]) + (data[i + 1] || data[i])) / 3 / mx;
      if (!(v > 0)) continue;
      // 급락 판정: 완만한 바닥 기울기는 EMA(0.7/0.3)로 흡수, 35% 이상 급락 = 끝선
      if (prev != null && prev > P.nearMin && v < prev * (1 - P.drop)) { edge = y; break; }
      prev = prev == null ? v : prev * 0.7 + v * 0.3;
    }
    if (edge >= 0) edges.push(edge);
  }
  if (edges.length < Math.max(6, Math.floor(P.cols * P.minCols))) return null;
  edges.sort((a, b) => a - b);
  const med = edges[edges.length >> 1];
  const coherent = edges.filter(e => Math.abs(e - med) <= H * P.band).length;
  if (coherent < edges.length * 0.6) return null;   // 수평 끝선(코히런트)이 아니면 무시
  const prox = (med - yEnd) / (yStart - yEnd);      // 1=발밑, 0=스캔존 상단
  return { edgeRow: med, prox: Math.max(0, Math.min(1, prox)), cols: edges.length };
}
```

## 구현 B — 깊이 추론 러너 (요약)
- 모델: onnx-community/depth-anything-v2-small `model_quantized.onnx`(int8, 27MB)
- 실행: onnxruntime-web, **wasm EP** (실측: int8 모델은 이 기기에서 wasm 1.8s < webgpu 3.2s @196px; 518px는 9.2s로 불가)
- 전처리: 카메라 프레임을 **196×196으로 stretch 리사이즈**(비율 무시), x/255 후 ImageNet mean/std 정규화
  (원 모델 config는 518×518, keep_aspect_ratio=true, ensure_multiple_of=14 — 우리는 속도 때문에 196 stretch 사용)
- 출력: [1,196,196] relative depth

## 구현 C — 앱 통합 (요약)
- 카메라 모드에서 2.5초 간격(적응형: 추론시간×2, 최대 6초)으로 비동기 실행, 메인 탐지 루프는 계속 돎
- 결과 TTL 4.5초 동안 유효, 위험 판정기로 전달:
  - `prox >= 0.8` → L1 "정지, 앞 낭떠러지" (즉시, 하위 알림 인터럽트)
  - 그 외 감지 → L2 "앞 계단 주의"
- 알림단엔 별도 디바운스(연속 프레임 요구)·쿨다운(동일 안내 재발화 제한) 존재

## 자가검사 결과 (64×64 합성 깊이맵)
- 평지(아래로 갈수록 가까움) → 미탐지 ✓
- 내리막(하단 25% 가까운 바닥, 그 위 갑자기 먼 바닥) → 탐지, prox 0.59 ✓
- 오르막(위쪽이 바닥 연장보다 가까움) → 미탐지 ✓
- 노이즈 ±0.05 평지 → 미탐지 ✓
- 전방 장애물(위쪽이 더 가까움) → 미탐지 ✓

## 검증 요청 (각 항목에 대해 구체적 시나리오와 수정안을 제시할 것)
1. **알고리즘 논리**: EMA(0.7/0.3)로 prev를 갱신하며 35% 급락을 찾는 방식의 허점은?
   특히 (a) 완만하지만 긴 내리막 경사로를 낙차로 오인할 가능성, (b) EMA가 이미 급락을 일부 흡수해
   실제 계단 끝선에서 임계 미달로 미탐지될 가능성.
2. **실외 오탐 시나리오**: 그림자 경계, 아스팔트↔검은 대리석 재질 변화, 젖은 바닥 반사, 횡단보도 흰줄,
   맨홀, 배수구, 유리문/유리바닥 — Depth Anything V2가 이런 데서 깊이를 어떻게 잘못 추정하고,
   그 오차가 이 낙차 판정을 어떻게 통과/오작동시키는가?
3. **미탐 시나리오**: 계단 끝선이 화면 하단 55% 밖(yTop=0.45 컷) 시점에 이미 지나쳤을 가능성,
   야간/역광, 폰이 아래로 기울었을 때(바닥만 보임), 계단 폭이 좁아 코리도(x 0.30–0.70) 밖일 때.
4. **196px stretch 전처리**: config(518, keep-aspect, /14배수)를 어긴 것이 DPT/DINOv2 계열 출력 품질에
   주는 실제 영향은? 특히 stretch로 인한 종횡비 왜곡이 "수평 끝선" 검출에 유리/불리한가?
   14의 배수(196=14×14)는 지켰다.
5. **"값 클수록 가까움" 전제**: Depth Anything V2 ONNX(onnx-community 변환본)의 출력이 정말
   disparity 방향인지, 모델/변환본에 따라 뒤집힐 가능성은? 뒤집혔을 때 이 코드는 어떤 증상을 보이는가?
6. **안전 설계**: 2.5~6초 주기 + TTL 4.5초는 보행속도 0.7~1.4m/s에서 낙차를 제때 알리기에 충분한가?
   최악 지연(방금 주기 시작 직후 계단 등장) 계산과, L1 임계 prox 0.8의 적절성.
7. **정량 평가 제안**: 이 기능의 미탐율/오탐율을 실측할 최소 실험 설계(통제환경, 필요 샘플 수, 지표).
8. 종합: 이대로 시각장애인 보조 '참고 정보'로 배포해도 되는 수준인가, 아니면 반드시 먼저 고칠 것 1~3개.

출력 형식: 문제점을 심각도 순으로 번호 매겨 나열하고, 각각 [시나리오 → 코드/설계의 어느 부분이 왜 실패 → 구체적 수정안(파라미터 값 또는 코드 스케치)] 구조로. 마지막에 "배포 가능/조건부 가능/불가" 판정과 근거.
