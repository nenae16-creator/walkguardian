/* walk_logic.js — 걸음지기 코어 로직 (모바일)
 * geometry / risk(L1~L4) / scheduler / navigation / phrases
 * v0.3 개선: ①가까운 것 우선 ②정차 vs 이동 차량 구분 ⑥인도/차도 분리(방향안내)
 * window.WalkLogic 로 노출.
 */
(function (global) {
  "use strict";

  // ---------------- geometry ----------------
  const NEAR = "NEAR", MID = "MID", FAR = "FAR";
  const LEFT = "LEFT", CENTER = "CENTER", RIGHT = "RIGHT";
  let BAND_NEAR_RATIO = 0.045;   // 화면의 4.5%↑ = 가까움 (폰 화각 기준, 현장보정)
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
  function sideWord(zone) { return zone === LEFT ? "왼쪽" : zone === RIGHT ? "오른쪽" : "앞"; }

  // 정차 vs 이동 판별기: 박스 면적 증가율(접근)과 중심 이동(횡단)을 함께 추적.
  // ※ 카메라가 걷는 사람 몸에 있어 모든 것이 겉보기로 움직이므로, '빠른 증가'만
  //   실제 이동 차량으로 간주(천천히 커지면 우리가 정차물에 다가가는 것으로 해석).
  const GROW_FAST = 1.6, GROW_SLOW = 1.15, SHRINK = 0.9, LAT_MOVE = 0.10;
  class MotionTracker {
    constructor(history = 6) { this.h = history; this.buf = new Map(); }
    _key(det, zone) { return det.id != null ? "id:" + det.id : det.cls + ":" + zone; }
    update(det, area, cx, zone) {
      const k = this._key(det, zone);
      let b = this.buf.get(k); if (!b) { b = []; this.buf.set(k, b); }
      b.push({ a: area, cx }); if (b.length > this.h) b.shift();
      if (b.length < 3) return { state: "UNKNOWN", growth: 1, lateral: 0 };
      const first = b[0], last = b[b.length - 1];
      const growth = last.a / (first.a > 0 ? first.a : 1e-9);
      const lateral = Math.abs(last.cx - first.cx);
      let state;
      if (growth >= GROW_FAST) state = "APPROACH_FAST";
      else if (lateral >= LAT_MOVE) state = "CROSSING";
      else if (growth >= GROW_SLOW) state = "APPROACH_SLOW";
      else if (growth <= SHRINK) state = "RECEDING";
      else state = "STATIONARY";
      return { state, growth, lateral };
    }
  }

  function iou(a, b) {
    const x1 = Math.max(a[0], b[0]), y1 = Math.max(a[1], b[1]);
    const x2 = Math.min(a[2], b[2]), y2 = Math.min(a[3], b[3]);
    const iw = Math.max(0, x2 - x1), ih = Math.max(0, y2 - y1), inter = iw * ih;
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
        if (bi >= 0) { d.id = this.prev[bi].id; used.add(bi); } else { d.id = this.next++; }
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
    vehicle_moving: "{side} 차량 지나감",
    vehicle_parked: "{side} 정차 차량",
    moto_caution: "{side} 오토바이 주의",
    obstacle_front: "앞 장애물",
    person_front: "앞 사람",
    stairs_front: "앞 계단 주의",
    curb_front: "앞 턱 주의",
    boundary_edge: "보도 끝 주의",
    construction_front: "앞 공사구간",
    on_road: "차도입니다, 인도로",
    braille_guide: "{side} 점자블록",
    braille_on: "점자블록 위",
    crosswalk_front: "앞 횡단보도",
    signal_wait: "신호 대기",
    offpath_warn: "보행로를 벗어남",
    nav_front: "직진",
    nav_left: "왼쪽으로",
    nav_right: "오른쪽으로",
    nav_stop: "정지, 길 막힘",
  };
  function render(kind, side) { return (PHRASES[kind] || kind).replace("{side}", side || "앞"); }

  // '위험요소만' 모드에서 말하는 종류(=실제 위험). 길안내/참고/부정확한 것은 제외.
  const DANGER_KINDS = new Set([
    "vehicle_imminent", "moto_imminent", "drop_imminent",
    "vehicle_caution", "vehicle_moving", "vehicle_parked", "moto_caution",
    "obstacle_front", "person_front", "construction_front", "on_road",
  ]);
  // 제외(위험만 모드): braille_*, crosswalk, signal, boundary, stairs, curb, nav_*

  // ---------------- risk (L1~L4) ----------------
  const L1 = 1, L2 = 2, L3 = 3, L4 = 4;
  const VEHICLE = new Set(["car", "truck", "bus"]);
  const MOTO = new Set(["motorcycle", "bicycle"]);
  const PERSON = new Set(["person"]);
  // 정적 장애물(전봇대/꼬깔콘/화분 등) — 중간거리에서도 잡음(인식률↑)
  const STATIC_OBST = new Set(["fire hydrant", "bench", "chair", "potted plant",
    "parking meter", "stop sign", "suitcase", "backpack", "pole", "cone", "traffic cone"]);

  function Hazard(level, kind, side, conf, prox) {
    return { level, kind, side: side || CENTER, conf: conf == null ? 1 : conf,
             prox: prox == null ? 0.5 : prox, key: kind + ":" + (side || CENTER) };
  }

  class WalkingRiskEngine {
    constructor(confGate = 0.35) { this.confGate = confGate; this.motion = new MotionTracker(); }
    process(dets, env, W, H) {
      const hz = [];
      for (const d of dets) {
        if ((d.conf == null ? 1 : d.conf) < this.confGate) continue;
        const cls = d.cls, xyxy = d.xyxy;
        const zone = horizontalZone(xyxy, W);
        const band = proximityBand(xyxy, W, H);
        const prox = areaRatio(xyxy, W, H);
        const cx = (xyxy[0] + xyxy[2]) / 2 / W;
        const m = this.motion.update(d, prox, cx, zone);
        const conf = d.conf == null ? 1 : d.conf;

        if (VEHICLE.has(cls) || MOTO.has(cls)) {
          const isMoto = MOTO.has(cls);
          if (m.state === "APPROACH_FAST" && (band === NEAR || band === MID)) {
            // 빠르게 다가오는(=움직이는) 차량 → 즉시 위험
            hz.push(Hazard(L1, isMoto ? "moto_imminent" : "vehicle_imminent", zone, conf, prox));
          } else if (m.state === "CROSSING" && (band === NEAR || band === MID)) {
            hz.push(Hazard(L2, isMoto ? "moto_caution" : "vehicle_moving", zone, conf, prox));
          } else if ((m.state === "APPROACH_SLOW" || m.state === "STATIONARY") && band === NEAR) {
            // 안 움직이는 차 = 정차/주차 → 정면 근접 시 장애물성 안내
            if (zone === CENTER) hz.push(Hazard(L2, isMoto ? "moto_caution" : "vehicle_parked", zone, conf, prox));
          } else if (m.state === "UNKNOWN" && band === NEAR && zone === CENTER) {
            hz.push(Hazard(L2, "vehicle_caution", zone, conf, prox));
          }
        } else if (PERSON.has(cls)) {
          if (zone === CENTER && band === NEAR) hz.push(Hazard(L2, "person_front", zone, conf, prox));
        } else {
          // 정적 장애물: NEAR 는 물론, 알려진 정적 클래스는 MID 에서도 잡음(전봇대·꼬깔콘 인식률↑)
          if (zone === CENTER && (band === NEAR || (band === MID && STATIC_OBST.has(cls))))
            hz.push(Hazard(L2, "obstacle_front", zone, conf, prox));
        }
      }

      if (env) {
        if (env.drop === "front") hz.push(Hazard(L1, "drop_imminent", CENTER, 1, 0.95));
        if (env.stairs === "front") hz.push(Hazard(L2, "stairs_front", CENTER, 1, 0.9));
        if (env.curb === "front") hz.push(Hazard(L2, "curb_front", CENTER, 1, 0.9));
        if (env.on_road) hz.push(Hazard(L2, "on_road", CENTER, 1, 0.85));
        if (env.obstacle === "front") hz.push(Hazard(L2, "obstacle_front", CENTER, 1, 0.8));
        if (env.boundary) hz.push(Hazard(L2, "boundary_edge", CENTER, 1, 0.55));
        if (env.construction === "front") hz.push(Hazard(L2, "construction_front", CENTER, 1, 0.7));
        if (env.braille === "left") hz.push(Hazard(L3, "braille_guide", LEFT, 1, 0.5));
        else if (env.braille === "right") hz.push(Hazard(L3, "braille_guide", RIGHT, 1, 0.5));
        else if (env.braille === "on") hz.push(Hazard(L3, "braille_on", CENTER, 1, 0.5));
        if (env.crosswalk) hz.push(Hazard(L4, "crosswalk_front", CENTER, 1, 0.4));
        if (env.signal_wait) hz.push(Hazard(L4, "signal_wait", CENTER, 1, 0.3));
      }
      // 같은 등급이면 '가까운 것(prox 큰 것)' 먼저
      hz.sort((a, b) => a.level - b.level || b.prox - a.prox);
      return hz;
    }
  }

  // ---------------- scheduler ----------------
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
        if (!ex || h.level < ex.level || (h.level === ex.level && h.prox > ex.prox)) byKey.set(h.key, h);
      }
      for (const k of this.persist.keys()) if (!seen.has(k)) this.persist.set(k, 0);

      const active = [];
      for (const [k, h] of byKey) if ((this.persist.get(k) || 0) >= (PERSIST[h.level] || 3)) active.push(h);
      if (!active.length) return [];
      active.sort((a, b) => a.level - b.level || b.prox - a.prox);   // 가까운 것 먼저

      const l1 = active.find(h => h.level === 1);
      if (l1) return this._cooldownOk(l1, t) ? [this._emit(l1, t)] : [];

      for (const h of active) {
        if (h.level >= 4 && !moving) continue;
        if (!this._cooldownOk(h, t)) continue;
        if (h.level >= 3) { this._pruneLow(t); if (this.lowEmits.length >= RATE_MAX_LOW) continue; this.lowEmits.push(t); }
        return [this._emit(h, t)];
      }
      return [];
    }
    _cooldownOk(h, t) { const l = this.last.get(h.key); return l == null || (t - l) >= (COOLDOWN[h.level] || 3); }
    _emit(h, t) { this.last.set(h.key, t); return { level: h.level, kind: h.kind, side: h.side, text: render(h.kind, sideWord(h.side)) }; }
    _pruneLow(t) { while (this.lowEmits.length && (t - this.lowEmits[0]) > RATE_WINDOW) this.lowEmits.shift(); }
  }

  // ---------------- navigation ----------------
  const NAV_PERSIST = 4, NAV_REMIND = 9.0, NAV_COOLDOWN = 2.5;
  class NavigationGuide {
    constructor() { this.stable = null; this.cand = null; this.candCnt = 0; this.lastSpoke = -1e9; }
    update(dir, t, opts) {
      opts = opts || {};
      if (dir == null) return null;
      if (dir === this.cand) this.candCnt++; else { this.cand = dir; this.candCnt = 1; }
      let changed = false;
      if (this.candCnt >= NAV_PERSIST && dir !== this.stable) { this.stable = dir; changed = true; }
      if (this.stable == null) return null;
      if (opts.hazardActive) return null;
      if (!opts.moving && this.stable !== "STOP") return null;
      const due = (t - this.lastSpoke) >= NAV_REMIND;
      if (changed || (due && (t - this.lastSpoke) >= NAV_COOLDOWN)) {
        this.lastSpoke = t;
        const kind = { FRONT: "nav_front", LEFT: "nav_left", RIGHT: "nav_right", STOP: "nav_stop" }[this.stable];
        return { level: this.stable === "STOP" ? 2 : 3, kind, side: "CENTER", text: render(kind, "앞"), nav: true };
      }
      return null;
    }
  }
  // 인도(sidewalk) 비율 + 중심 → 방향. 인도가 거의 없으면 STOP(막힘/차도).
  function walkDirection(pedFrac, cx) {
    if (pedFrac < 0.20) return "STOP";
    if (cx < 0.42) return "LEFT";
    if (cx > 0.58) return "RIGHT";
    return "FRONT";
  }

  // ---------------- self-test ----------------
  function selfTest() {
    const W = 1280, H = 720;
    const box = (cxf, size) => { const cx = cxf*W, cy = 0.6*H, half = size*Math.min(W,H)/2; return [cx-half, cy-half, cx+half, cy+half]; };
    const run = (seq, movingSeq) => {
      const eng = new WalkingRiskEngine(), sch = new AlertScheduler(), out = [];
      seq.forEach(([dets, env], i) => { const t = i/10, moving = movingSeq ? movingSeq[i] : true;
        for (const a of sch.feed(eng.process(dets, env, W, H), t, moving)) out.push([+t.toFixed(2), a.level, a.text]); });
      return out;
    };
    const R = [];
    // ① 접근(커지는) 차량 → L1, 횡단보도 L4 억제
    let seq = []; for (let i = 0; i < 6; i++) seq.push([[{cls:"car",conf:.9,id:1,xyxy:box(0.5,0.30+i*0.06)}], {crosswalk:true}]);
    let o = run(seq);
    R.push(["접근차량 L1 인터럽트", o.some(r=>r[1]===1 && r[2].includes("접근")) && !o.some(r=>r[1]===4), o]);
    // ② 정차(안 커지는) 차량 → '정차 차량'(접근 아님)
    seq = []; for (let i = 0; i < 8; i++) seq.push([[{cls:"car",conf:.9,id:2,xyxy:box(0.5,0.5)}], null]);
    o = run(seq);
    R.push(["정차/이동 구분", o.some(r=>r[2].includes("정차")) && !o.some(r=>r[2].includes("접근")), o]);
    // ① 가까운 것 먼저: 큰 의자(가까움) vs 사람 → 의자 먼저
    seq = []; for (let i = 0; i < 5; i++) seq.push([[{cls:"chair",conf:.9,id:3,xyxy:box(0.5,0.5)},{cls:"person",conf:.9,id:4,xyxy:box(0.5,0.30)}], null]);
    o = run(seq);
    R.push(["가까운 것 먼저", o.length>0 && o[0][2].includes("장애물"), o]);
    // 쿨다운 1회
    seq = []; for (let i = 0; i < 20; i++) seq.push([[{cls:"chair",conf:.9,id:5,xyxy:box(0.5,0.5)}], null]);
    o = run(seq);
    R.push(["쿨다운 1회", o.filter(r=>r[1]===2).length===1, o]);
    // 정지 침묵 L4
    o = run(Array(10).fill([[], {crosswalk:true}]), Array(10).fill(false));
    R.push(["정지 침묵 L4", o.length===0, o]);
    return R;
  }

  function selfTestNav() {
    const runNav = (dirs, opts) => { const g = new NavigationGuide(), out = [];
      dirs.forEach((d, i) => { const a = g.update(d, i/2, opts ? opts[i] : { moving: true }); if (a) out.push([i, a.text]); }); return out; };
    const R = [];
    let o = runNav(["FRONT","FRONT","FRONT","FRONT","RIGHT","RIGHT","RIGHT","RIGHT"]);
    R.push(["변경시 안내", o.length === 2 && o[0][1] === "직진" && o[1][1] === "오른쪽으로", o]);
    o = runNav(["FRONT","RIGHT","FRONT","RIGHT","FRONT","RIGHT","FRONT","RIGHT"]);
    R.push(["히스테리시스 흔들림 억제", o.length === 0, o]);
    o = runNav(Array(8).fill("LEFT"), Array(8).fill({ moving: true, hazardActive: true }));
    R.push(["위험 중 내비 침묵", o.length === 0, o]);
    o = runNav(Array(8).fill("STOP"), Array(8).fill({ moving: false }));
    R.push(["길막힘 정지안내", o.some(x => x[1].includes("막힘")), o]);
    return R;
  }

  global.WalkLogic = {
    geometry: { areaRatio, proximityBand, horizontalZone, sideWord, NEAR, MID, FAR, LEFT, CENTER, RIGHT,
                setBands: (n, m) => { BAND_NEAR_RATIO = n; BAND_MID_RATIO = m; } },
    Tracker, MotionTracker, WalkingRiskEngine, AlertScheduler, NavigationGuide, walkDirection,
    render, selfTest, selfTestNav, STATIC_OBST, VEHICLE, MOTO, PERSON, DANGER_KINDS,
  };
})(typeof window !== "undefined" ? window : globalThis);
