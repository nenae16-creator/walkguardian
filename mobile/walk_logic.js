/* walk_logic.js — 걸음지기 코어 로직 (Python walkguardian 의 JS 포팅)
 * geometry / risk(L1~L4) / scheduler(디바운스·쿨다운·인터럽트·레이트리밋·정지침묵) / phrases
 * 폰 브라우저에서 파이썬과 '동일한' 판단을 하도록 상수까지 미러링.
 * window.WalkLogic 로 노출.
 */
(function (global) {
  "use strict";

  // ---------------- geometry ----------------
  const NEAR = "NEAR", MID = "MID", FAR = "FAR";
  const LEFT = "LEFT", CENTER = "CENTER", RIGHT = "RIGHT";
  // 폰 후면카메라는 장애물에 더 가깝게 잡히므로 파이썬(0.06)보다 밴드 임계값을 낮게.
  let BAND_NEAR_RATIO = 0.045;
  let BAND_MID_RATIO = 0.012;
  const ZONE_LEFT_MAX = 0.38, ZONE_RIGHT_MIN = 0.62;

  function areaRatio(xyxy, W, H) {
    const [x1, y1, x2, y2] = xyxy;
    const a = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
    const fa = W * H;
    return fa > 0 ? a / fa : 0;
  }
  function proximityBand(xyxy, W, H) {
    const r = areaRatio(xyxy, W, H);
    if (r >= BAND_NEAR_RATIO) return NEAR;
    if (r >= BAND_MID_RATIO) return MID;
    return FAR;
  }
  function horizontalZone(xyxy, W) {
    const cx = (xyxy[0] + xyxy[2]) / 2 / Math.max(1, W);
    if (cx < ZONE_LEFT_MAX) return LEFT;
    if (cx > ZONE_RIGHT_MIN) return RIGHT;
    return CENTER;
  }
  function sideWord(zone) {
    return zone === LEFT ? "왼쪽" : zone === RIGHT ? "오른쪽" : "앞";
  }

  // 박스 면적의 시간적 증가율 → '접근 중'
  class ApproachTracker {
    constructor(history = 6, grow = 1.18) { this.h = history; this.g = grow; this.buf = new Map(); }
    _key(det, zone) { return det.id != null ? "id:" + det.id : det.cls + ":" + zone; }
    update(det, area, zone) {
      const k = this._key(det, zone);
      let b = this.buf.get(k); if (!b) { b = []; this.buf.set(k, b); }
      b.push(area); if (b.length > this.h) b.shift();
      if (b.length < Math.max(3, this.h >> 1)) return false;
      const first = b[0] > 0 ? b[0] : 1e-9;
      return (b[b.length - 1] / first) >= this.g;
    }
  }

  // 간이 IoU 트래커 → COCO-SSD 는 id 를 안 주므로 프레임간 매칭으로 id 부여(접근판정 안정화)
  function iou(a, b) {
    const x1 = Math.max(a[0], b[0]), y1 = Math.max(a[1], b[1]);
    const x2 = Math.min(a[2], b[2]), y2 = Math.min(a[3], b[3]);
    const iw = Math.max(0, x2 - x1), ih = Math.max(0, y2 - y1);
    const inter = iw * ih;
    const ua = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter;
    return ua > 0 ? inter / ua : 0;
  }
  class Tracker {
    constructor() { this.prev = []; this.next = 1; }
    update(dets) {
      const used = new Set();
      for (const d of dets) {
        let best = 0.3, bi = -1;
        for (let i = 0; i < this.prev.length; i++) {
          if (used.has(i)) continue;
          const s = iou(d.xyxy, this.prev[i].xyxy);
          if (s >= best) { best = s; bi = i; }
        }
        if (bi >= 0) { d.id = this.prev[bi].id; used.add(bi); }
        else { d.id = this.next++; }
      }
      this.prev = dets.map(d => ({ xyxy: d.xyxy, id: d.id }));
      return dets;
    }
  }

  // ---------------- phrases ----------------
  const PHRASES = {
    vehicle_imminent: "정지, {side} 차량 접근",
    moto_imminent: "정지, {side} 오토바이 접근",
    drop_imminent: "정지, 앞 낭떠러지",
    vehicle_caution: "{side} 차량 주의",
    moto_caution: "{side} 오토바이 주의",
    obstacle_front: "앞 장애물",
    person_front: "앞 사람",
    stairs_front: "앞 계단 주의",
    curb_front: "앞 턱 주의",
    boundary_edge: "보도 끝 주의",
    construction_front: "앞 공사구간",
    braille_guide: "{side} 점자블록",
    braille_on: "점자블록 위",
    crosswalk_front: "앞 횡단보도",
    signal_wait: "신호 대기",
    offpath_warn: "보행로를 벗어남",
    // 내비게이션(방향 안내) — AI Guide Dog 논문의 전/좌/우 예측을 보행가능영역에서 유도
    nav_front: "직진",
    nav_left: "왼쪽으로",
    nav_right: "오른쪽으로",
    nav_stop: "정지, 길 막힘",
  };
  function render(kind, side) { return (PHRASES[kind] || kind).replace("{side}", side || "앞"); }

  // ---------------- risk (L1~L4) ----------------
  const L1 = 1, L2 = 2, L3 = 3, L4 = 4;
  const VEHICLE = new Set(["car", "truck", "bus"]);
  const MOTO = new Set(["motorcycle", "bicycle"]);
  const PERSON = new Set(["person"]);
  // COCO 정적 객체 중 보행 장애물로 취급할 것들(+ Cityscapes 'pole')
  const STATIC_OBST = new Set(["fire hydrant", "bench", "chair", "potted plant",
    "parking meter", "stop sign", "suitcase", "backpack", "pole", "traffic light"]);

  function Hazard(level, kind, side, conf) {
    return { level, kind, side: side || CENTER, conf: conf == null ? 1 : conf,
             key: kind + ":" + (side || CENTER) };
  }

  class WalkingRiskEngine {
    constructor(confGate = 0.35) { this.confGate = confGate; this.tracker = new ApproachTracker(); }
    process(dets, env, W, H) {
      const hz = [];
      for (const d of dets) {
        if ((d.conf == null ? 1 : d.conf) < this.confGate) continue;
        const cls = d.cls, xyxy = d.xyxy;
        const zone = horizontalZone(xyxy, W);
        const band = proximityBand(xyxy, W, H);
        const area = areaRatio(xyxy, W, H);
        const approaching = this.tracker.update(d, area, zone);
        const conf = d.conf == null ? 1 : d.conf;

        if (VEHICLE.has(cls) || MOTO.has(cls)) {
          const isMoto = MOTO.has(cls);
          if (band === NEAR && (approaching || zone === CENTER)) {
            hz.push(Hazard(L1, isMoto ? "moto_imminent" : "vehicle_imminent", zone, conf));
          } else if (approaching || (band === MID && zone === CENTER)) {
            hz.push(Hazard(L2, isMoto ? "moto_caution" : "vehicle_caution", zone, conf));
          }
        } else if (PERSON.has(cls)) {
          if (zone === CENTER && band === NEAR) hz.push(Hazard(L2, "person_front", zone, conf));
        } else {
          // 전방 근접한 정적 장애물(전봇대/벤치/화분/쓰레기통 등) → '앞 장애물'
          if (zone === CENTER && (band === NEAR || (band === MID && STATIC_OBST.has(cls))))
            hz.push(Hazard(L2, "obstacle_front", zone, conf));
        }
      }

      if (env) {
        if (env.drop === "front") hz.push(Hazard(L1, "drop_imminent", CENTER));
        if (env.offpath) hz.push(Hazard(L2, "offpath_warn", CENTER));   // 보행로 벗어남
        if (env.stairs === "front") hz.push(Hazard(L2, "stairs_front", CENTER));
        if (env.curb === "front") hz.push(Hazard(L2, "curb_front", CENTER));
        if (env.boundary) hz.push(Hazard(L2, "boundary_edge", CENTER));
        if (env.construction === "front") hz.push(Hazard(L2, "construction_front", CENTER));
        if (env.obstacle === "front") hz.push(Hazard(L2, "obstacle_front", CENTER)); // seg 장애물
        if (env.braille === "left") hz.push(Hazard(L3, "braille_guide", LEFT));
        else if (env.braille === "right") hz.push(Hazard(L3, "braille_guide", RIGHT));
        else if (env.braille === "on") hz.push(Hazard(L3, "braille_on", CENTER));
        if (env.crosswalk) hz.push(Hazard(L4, "crosswalk_front", CENTER));
        if (env.signal_wait) hz.push(Hazard(L4, "signal_wait", CENTER));
      }
      hz.sort((a, b) => a.level - b.level || b.conf - a.conf);
      return hz;
    }
  }

  // ---------------- scheduler (피로 방지) ----------------
  const PERSIST = { 1: 1, 2: 3, 3: 4, 4: 5 };
  const COOLDOWN = { 1: 1.2, 2: 3.0, 3: 6.0, 4: 8.0 };
  const RATE_WINDOW = 4.0, RATE_MAX_LOW = 2;

  class AlertScheduler {
    constructor() { this.persist = new Map(); this.last = new Map(); this.lowEmits = []; }
    feed(hazards, t, moving = true) {
      const seen = new Set(), byKey = new Map();
      for (const h of hazards) {
        seen.add(h.key);
        this.persist.set(h.key, (this.persist.get(h.key) || 0) + 1);
        const ex = byKey.get(h.key);
        if (!ex || h.level < ex.level) byKey.set(h.key, h);
      }
      for (const k of this.persist.keys()) if (!seen.has(k)) this.persist.set(k, 0);

      const active = [];
      for (const [k, h] of byKey) if ((this.persist.get(k) || 0) >= (PERSIST[h.level] || 3)) active.push(h);
      if (!active.length) return [];
      active.sort((a, b) => a.level - b.level || b.conf - a.conf);

      // 인터럽트: L1 활성이면 하위 완전 억제
      const l1 = active.find(h => h.level === 1);
      if (l1) return this._cooldownOk(l1, t) ? [this._emit(l1, t)] : [];

      for (const h of active) {
        if (h.level >= 4 && !moving) continue;            // 정지 중 참고정보 침묵
        if (!this._cooldownOk(h, t)) continue;            // 중복 방지
        if (h.level >= 3) {                                // L3/L4 레이트리밋
          this._pruneLow(t);
          if (this.lowEmits.length >= RATE_MAX_LOW) continue;
          this.lowEmits.push(t);
        }
        return [this._emit(h, t)];                         // 한 tick 한 마디
      }
      return [];
    }
    _cooldownOk(h, t) { const l = this.last.get(h.key); return l == null || (t - l) >= (COOLDOWN[h.level] || 3); }
    _emit(h, t) { this.last.set(h.key, t); return { level: h.level, kind: h.kind, side: h.side, text: render(h.kind, sideWord(h.side)) }; }
    _pruneLow(t) { while (this.lowEmits.length && (t - this.lowEmits[0]) > RATE_WINDOW) this.lowEmits.shift(); }
  }

  // ---------------- navigation (방향 안내) ----------------
  // AI Guide Dog(2501.07957)의 전/좌/우 경로 예측을 '보행가능영역 방향'에서 유도.
  // 안내 규칙: ①방향이 바뀔 때만 말함(연속 잔소리 금지) ②히스테리시스로 흔들림 억제
  //           ③위험 경고(L1/L2)가 있으면 침묵(안전 우선) ④정지 중엔 STOP 외 침묵
  const NAV_PERSIST = 4;      // 방향 확정에 필요한 연속 프레임 (~2s @ 2fps)
  const NAV_REMIND = 9.0;     // 같은 방향 유지 시 재안내 간격(초)
  const NAV_COOLDOWN = 2.5;   // 최소 발화 간격(초)

  class NavigationGuide {
    constructor() { this.stable = null; this.cand = null; this.candCnt = 0; this.lastSpoke = -1e9; }
    // dir: "FRONT"|"LEFT"|"RIGHT"|"STOP"|null,  opts:{moving, hazardActive}
    update(dir, t, opts) {
      opts = opts || {};
      if (dir == null) return null;
      if (dir === this.cand) this.candCnt++; else { this.cand = dir; this.candCnt = 1; }
      let changed = false;
      if (this.candCnt >= NAV_PERSIST && dir !== this.stable) { this.stable = dir; changed = true; }
      if (this.stable == null) return null;
      if (opts.hazardActive) return null;                        // 위험 우선 → 내비 침묵
      if (!opts.moving && this.stable !== "STOP") return null;    // 정지 중 방향안내 억제
      // 방향 전환(changed)은 히스테리시스가 이미 걸러주므로 즉시 안내(쿨다운 우회).
      // 같은 방향 유지 재안내(due)만 쿨다운/재안내 간격 적용.
      const due = (t - this.lastSpoke) >= NAV_REMIND;
      if (changed || (due && (t - this.lastSpoke) >= NAV_COOLDOWN)) {
        this.lastSpoke = t;
        const kind = { FRONT: "nav_front", LEFT: "nav_left", RIGHT: "nav_right", STOP: "nav_stop" }[this.stable];
        return { level: this.stable === "STOP" ? 2 : 3, kind, side: "CENTER", text: render(kind, "앞"), nav: true };
      }
      return null;
    }
  }

  // 보행가능영역 요약(walkFrac, 중심 cx) → 방향(FRONT/LEFT/RIGHT/STOP)
  function walkDirection(walkFrac, cx) {
    if (walkFrac < 0.22) return "STOP";        // 전방 경로 대부분 막힘/끝
    if (cx < 0.42) return "LEFT";
    if (cx > 0.58) return "RIGHT";
    return "FRONT";
  }

  // ---------------- self-test (파이썬 테스트 미러) ----------------
  function selfTest() {
    const W = 1280, H = 720;
    const box = (cxf, size) => { const cx = cxf*W, cy = 0.6*H, half = size*Math.min(W,H)/2; return [cx-half, cy-half, cx+half, cy+half]; };
    const run = (seq, movingSeq) => {
      const eng = new WalkingRiskEngine(), sch = new AlertScheduler(), out = [];
      seq.forEach(([dets, env], i) => {
        const t = i/10, moving = movingSeq ? movingSeq[i] : true;
        for (const a of sch.feed(eng.process(dets, env, W, H), t, moving)) out.push([+t.toFixed(2), a.level, a.text]);
      });
      return out;
    };
    const results = [];
    // L1 인터럽트 — L4 억제
    let o = run(Array(6).fill([[{cls:"car",conf:.9,id:1,xyxy:box(0.5,0.45)}], {crosswalk:true}]));
    results.push(["L1 인터럽트", o.some(r=>r[1]===1) && !o.some(r=>r[1]===4), o]);
    // 정지 침묵
    o = run(Array(10).fill([[], {crosswalk:true}]), Array(10).fill(false));
    results.push(["정지 침묵 L4", o.length===0, o]);
    // 쿨다운 1회
    o = run(Array(20).fill([[{cls:"chair",conf:.9,id:3,xyxy:box(0.5,0.45)}], null]));
    results.push(["쿨다운 1회", o.filter(r=>r[1]===2).length===1, o]);
    return results;
  }

  function selfTestNav() {
    const runNav = (dirs, opts) => {
      const g = new NavigationGuide(), out = [];
      dirs.forEach((d, i) => { const a = g.update(d, i / 2, opts ? opts[i] : { moving: true }); if (a) out.push([i, a.text]); });
      return out;
    };
    const R = [];
    // 방향 변경 시에만 안내: FRONT 확정 → RIGHT 확정 → 두 번만
    let o = runNav(["FRONT","FRONT","FRONT","FRONT","RIGHT","RIGHT","RIGHT","RIGHT"]);
    R.push(["변경시 안내", o.length === 2 && o[0][1] === "직진" && o[1][1] === "오른쪽으로", o]);
    // 흔들림(FRONT/RIGHT 교대) → 확정 안 됨 → 발화 0
    o = runNav(["FRONT","RIGHT","FRONT","RIGHT","FRONT","RIGHT","FRONT","RIGHT"]);
    R.push(["히스테리시스 흔들림 억제", o.length === 0, o]);
    // 위험 중이면 내비 침묵
    o = runNav(Array(8).fill("LEFT"), Array(8).fill({ moving: true, hazardActive: true }));
    R.push(["위험 중 내비 침묵", o.length === 0, o]);
    // STOP 은 정지 중에도 안내
    o = runNav(Array(8).fill("STOP"), Array(8).fill({ moving: false }));
    R.push(["길막힘 정지안내", o.some(x => x[1].includes("막힘")), o]);
    return R;
  }

  global.WalkLogic = {
    geometry: { areaRatio, proximityBand, horizontalZone, sideWord, NEAR, MID, FAR, LEFT, CENTER, RIGHT,
                setBands: (n, m) => { BAND_NEAR_RATIO = n; BAND_MID_RATIO = m; } },
    Tracker, WalkingRiskEngine, AlertScheduler, NavigationGuide, walkDirection,
    render, selfTest, selfTestNav,
    STATIC_OBST, VEHICLE, MOTO, PERSON,
  };
})(typeof window !== "undefined" ? window : globalThis);
