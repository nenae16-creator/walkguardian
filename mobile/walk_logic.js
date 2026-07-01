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

  // 정차 vs 이동 판별기 (에고 움직임 보정).
  // 손에 든 폰이라 정차 차도 걸어가면 커짐 → 여러 물체의 '공통 증가율(median)'을
  // 카메라(에고) 움직임으로 보고, 그보다 더 빨리 커지는 것만 '진짜 접근'으로 판정.
  const GROW_FAST = 1.6, SHRINK = 0.9, LAT_MOVE = 0.10;
  const RESID_APPROACH = 1.35, RESID_RECEDE = 0.7;
  function median(a) { if (!a.length) return null; const s = a.slice().sort((x, y) => x - y); return s[s.length >> 1]; }
  class MotionTracker {
    constructor(history = 6) { this.h = history; this.buf = new Map(); }
    _key(det, zone) { return det.id != null ? "id:" + det.id : det.cls + ":" + zone; }
    update(det, area, cx, zone) {   // 원시 관측만 반환(분류는 에고 보정 후 별도)
      const k = this._key(det, zone);
      let b = this.buf.get(k); if (!b) { b = []; this.buf.set(k, b); }
      b.push({ a: area, cx }); if (b.length > this.h) b.shift();
      if (b.length < 3) return { valid: false, growth: 1, dx: 0 };
      const first = b[0], last = b[b.length - 1];
      return { valid: true, growth: last.a / (first.a > 0 ? first.a : 1e-9), dx: last.cx - first.cx };
    }
  }
  // 에고 보정 분류: ego={growth,dx,n}(주변 물체 median). moving=사용자 보행 여부.
  function classifyMotion(m, moving, ego) {
    if (!m.valid) return "UNKNOWN";
    if (moving && ego.n >= 2) {                         // 걷는 중 + 기준물 충분 → 잔여(residual)로 판정
      const rg = m.growth / (ego.growth > 0.3 ? ego.growth : 1);   // 에고 대비 얼마나 더 커지나
      const rdx = m.dx - ego.dx;                        // 에고(팬) 보정한 좌우 이동
      if (rg >= RESID_APPROACH) return "APPROACH_FAST"; // 배경보다 빨리 커짐 = 나에게 접근
      if (Math.abs(rdx) >= LAT_MOVE) return "CROSSING";
      if (rg <= RESID_RECEDE) return "RECEDING";
      return "STATIONARY";                              // 배경과 같은 비율 = 정차/주차
    }
    // 폴백(정지 중 또는 기준물 부족): 절대 증가율 — 안전 우선(빠르면 접근 경고)
    if (m.growth >= GROW_FAST) return "APPROACH_FAST";
    if (Math.abs(m.dx) >= LAT_MOVE) return "CROSSING";
    if (m.growth <= SHRINK) return "RECEDING";
    return "STATIONARY";
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
    acoustic_signal: "{side} 음향신호기",
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
    process(dets, env, W, H, moving) {
      moving = moving !== false;
      const hz = [];
      // pass 1: 원시 관측 수집
      const obs = [];
      for (const d of dets) {
        if ((d.conf == null ? 1 : d.conf) < this.confGate) continue;
        const xyxy = d.xyxy;
        const zone = horizontalZone(xyxy, W), band = proximityBand(xyxy, W, H);
        const prox = areaRatio(xyxy, W, H), cx = (xyxy[0] + xyxy[2]) / 2 / W;
        const m = this.motion.update(d, prox, cx, zone);
        obs.push({ cls: d.cls, zone, band, prox, conf: d.conf == null ? 1 : d.conf, m });
      }
      // 에고(카메라) 움직임 = 유효 관측들의 median 증가율/좌우이동
      const gs = obs.filter(o => o.m.valid).map(o => o.m.growth);
      const ds = obs.filter(o => o.m.valid).map(o => o.m.dx);
      const ego = { growth: median(gs) == null ? 1 : median(gs), dx: median(ds) == null ? 0 : median(ds), n: gs.length };

      // pass 2: 에고 보정 분류 + 위험 생성
      for (const o of obs) {
        const { cls, zone, band, prox, conf, m } = o;
        if (VEHICLE.has(cls) || MOTO.has(cls)) {
          const isMoto = MOTO.has(cls);
          const st = classifyMotion(m, moving, ego);
          if (st === "APPROACH_FAST" && (band === NEAR || band === MID)) {
            hz.push(Hazard(L1, isMoto ? "moto_imminent" : "vehicle_imminent", zone, conf, prox));
          } else if (st === "CROSSING" && (band === NEAR || band === MID)) {
            hz.push(Hazard(L2, isMoto ? "moto_caution" : "vehicle_moving", zone, conf, prox));
          } else if (st === "STATIONARY" && band === NEAR) {
            if (zone === CENTER) hz.push(Hazard(L2, isMoto ? "moto_caution" : "vehicle_parked", zone, conf, prox));
          } else if (st === "UNKNOWN" && band === NEAR && zone === CENTER) {
            hz.push(Hazard(L2, "vehicle_caution", zone, conf, prox));
          }
        } else if (PERSON.has(cls)) {
          if (zone === CENTER && band === NEAR) hz.push(Hazard(L2, "person_front", zone, conf, prox));
        } else {
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

  // ---------------- depth (WebXR/ARCore, 안드로이드) ----------------
  // 깊이 그리드(미터, rows×cols, 무효=null) → 위험. 클래스 몰라도 '가까운 물체/바닥 꺼짐'을 실측으로.
  const DEPTH_NEAR_M = 0.6, DEPTH_MID_M = 1.2, DROP_JUMP_M = 0.5;
  function analyzeDepth(grid, cfg) {
    cfg = cfg || {};
    const nearM = cfg.nearM || DEPTH_NEAR_M, midM = cfg.midM || DEPTH_MID_M, dropM = cfg.dropM || DROP_JUMP_M;
    const R = grid.length; if (!R) return [];
    const C = grid[0].length;
    const c0 = Math.floor(C / 3), c1 = Math.ceil(C * 2 / 3);   // 중앙 컬럼
    const val = v => (v != null && isFinite(v) && v > 0) ? v : null;
    const mk = (level, kind, prox) => ({ level, kind, side: "CENTER", conf: 1, prox, key: kind + ":CENTER" });
    const hz = [];
    // 1) 전방 장애물: 상단~중단(바닥행 제외) 중앙의 최소 깊이 = 가장 가까운 물체
    let obst = null;
    for (let r = 0; r < Math.max(1, R - 2); r++) for (let c = c0; c < c1; c++) {
      const d = val(grid[r][c]); if (d != null && (obst == null || d < obst)) obst = d;
    }
    if (obst != null) {
      if (obst < nearM) hz.push(mk(2, "obstacle_front", 0.95));
      else if (obst < midM) hz.push(mk(2, "obstacle_front", 0.6));
    }
    // 2) 바닥 꺼짐(내려가는 턱/계단): 발 앞 바닥이 그 위 행보다 더 멀면 = 바닥이 꺼짐
    const cc = Math.floor((c0 + c1) / 2);
    const fB = val(grid[R - 1] && grid[R - 1][cc]);
    const fU = val(grid[R - 2] && grid[R - 2][cc]);
    if (fB != null && fU != null && (fB - fU) > dropM) hz.push(mk(2, "curb_front", 0.85));
    hz.sort((a, b) => a.level - b.level || b.prox - a.prox);
    return hz;
  }

  // ---------------- self-test ----------------
  function selfTest() {
    const W = 1280, H = 720;
    const box = (cxf, size) => { const cx = cxf*W, cy = 0.6*H, half = size*Math.min(W,H)/2; return [cx-half, cy-half, cx+half, cy+half]; };
    const run = (seq, movingSeq) => {
      const eng = new WalkingRiskEngine(), sch = new AlertScheduler(), out = [];
      seq.forEach(([dets, env], i) => { const t = i/10, moving = movingSeq ? movingSeq[i] : true;
        for (const a of sch.feed(eng.process(dets, env, W, H, moving), t, moving)) out.push([+t.toFixed(2), a.level, a.text]); });
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
    // ②b 에고 보정: 걸어가며 지나치는 '주차차 여러 대'가 함께 커져도 접근 아님(정차)
    seq = []; for (let i = 0; i < 7; i++) { const s = 0.30 + i*0.02;
      seq.push([[{cls:"car",conf:.9,id:11,xyxy:box(0.50,s)},{cls:"car",conf:.9,id:12,xyxy:box(0.44,s)},{cls:"car",conf:.9,id:13,xyxy:box(0.56,s)}], null]); }
    o = run(seq);
    R.push(["에고보정 정차 구분", o.some(r=>r[2].includes("정차")) && !o.some(r=>r[2].includes("접근")), o]);
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

  function selfTestDepth() {
    const clear = Array.from({ length: 5 }, () => Array(5).fill(3.0));
    const obst = clear.map(r => r.slice()); obst[1][2] = 0.5;   // 전방 중앙 0.5m 물체
    const drop = clear.map(r => r.slice()); drop[4][2] = 3.2; drop[3][2] = 0.9;  // 발앞 바닥이 더 멂
    return [
      ["깊이 장애물 감지", analyzeDepth(obst).some(h => h.kind === "obstacle_front"), analyzeDepth(obst)],
      ["깊이 빈길 무경고", analyzeDepth(clear).length === 0, analyzeDepth(clear)],
      ["깊이 바닥꺼짐(턱)", analyzeDepth(drop).some(h => h.kind === "curb_front"), analyzeDepth(drop)],
    ];
  }

  // ---------------- geofence (공공데이터 POI: 음향신호기·횡단보도) ----------------
  // GPS 위치로 근처 POI를 감지해 방향과 함께 안내. 카메라 없이 GPS만으로 동작.
  const R_EARTH = 6371000, DEG = Math.PI / 180;
  function haversine(a1, o1, a2, o2) {
    const dLat = (a2 - a1) * DEG, dLon = (o2 - o1) * DEG;
    const s = Math.sin(dLat / 2) ** 2 + Math.cos(a1 * DEG) * Math.cos(a2 * DEG) * Math.sin(dLon / 2) ** 2;
    return 2 * R_EARTH * Math.asin(Math.min(1, Math.sqrt(s)));
  }
  function bearing(a1, o1, a2, o2) {
    const y = Math.sin((o2 - o1) * DEG) * Math.cos(a2 * DEG);
    const x = Math.cos(a1 * DEG) * Math.sin(a2 * DEG) - Math.sin(a1 * DEG) * Math.cos(a2 * DEG) * Math.cos((o2 - o1) * DEG);
    return (Math.atan2(y, x) / DEG + 360) % 360;
  }
  function relSide(heading, brg) {                 // 사용자 진행방향 대비 POI 상대 방향
    if (heading == null) return CENTER;            // 방향 모르면 '앞'으로 통일
    const d = ((brg - heading + 540) % 360) - 180; // [-180,180]
    if (Math.abs(d) > 135) return "BEHIND";
    if (Math.abs(d) < 25) return CENTER;
    return d < 0 ? LEFT : RIGHT;
  }
  // user={lat,lon,heading}, pois=[{id,kind,lat,lon}] → 반경 내 POI(뒤쪽 제외), 가까운 순
  function checkPOIs(user, pois, radius) {
    radius = radius || 30; const out = [];
    for (const p of pois) {
      const dist = haversine(user.lat, user.lon, p.lat, p.lon);
      if (dist > radius) continue;
      const side = relSide(user.heading, bearing(user.lat, user.lon, p.lat, p.lon));
      if (side === "BEHIND") continue;
      out.push({ id: p.id, kind: p.kind, dist, side });
    }
    out.sort((a, b) => a.dist - b.dist);
    return out;
  }
  // 진입(edge)에서 1회만 안내 + POI별 쿨다운. GPS 갱신율(~1Hz)에 맞춤.
  class POIAnnouncer {
    constructor(cooldown = 20) { this.cd = cooldown; this.last = new Map(); this.inside = new Set(); }
    update(nearby, t) {
      const now = new Set(nearby.map(n => n.id)), out = [];
      for (const n of nearby) {
        const was = this.inside.has(n.id), last = this.last.get(n.id);
        if (!was && (last == null || (t - last) >= this.cd)) { out.push(n); this.last.set(n.id, t); }
      }
      this.inside = now;
      return out;
    }
  }

  function selfTestGeo() {
    const R = [];
    const near111 = haversine(37.5000, 127.0000, 37.5010, 127.0000); // 0.001° 위도 ≈ 111m
    R.push(["거리(haversine)", near111 > 105 && near111 < 118, Math.round(near111)]);
    // 북쪽 20m 앞 음향신호기 + 남쪽(뒤) 횡단보도, heading=북(0)
    const user = { lat: 37.5, lon: 127.0, heading: 0 };
    const pois = [
      { id: "a", kind: "acoustic_signal", lat: 37.5 + 0.00018, lon: 127.0 }, // 북 ~20m
      { id: "b", kind: "crosswalk_front", lat: 37.5 - 0.00030, lon: 127.0 }, // 남(뒤) ~33m
    ];
    const near = checkPOIs(user, pois, 30);
    R.push(["앞 POI 감지·뒤 제외", near.length === 1 && near[0].id === "a" && near[0].side === CENTER, near]);
    // 진입 1회만 안내
    const an = new POIAnnouncer(20);
    const a1 = an.update(near, 0), a2 = an.update(near, 1), a3 = an.update([], 2), a4 = an.update(near, 25);
    R.push(["진입 1회+쿨다운", a1.length === 1 && a2.length === 0 && a4.length === 1, [a1.length, a2.length, a4.length]]);
    return R;
  }

  global.WalkLogic = {
    geometry: { areaRatio, proximityBand, horizontalZone, sideWord, NEAR, MID, FAR, LEFT, CENTER, RIGHT,
                setBands: (n, m) => { BAND_NEAR_RATIO = n; BAND_MID_RATIO = m; } },
    geo: { haversine, bearing, relSide, checkPOIs, sideWord },
    Tracker, MotionTracker, WalkingRiskEngine, AlertScheduler, NavigationGuide, walkDirection, analyzeDepth, POIAnnouncer,
    render, selfTest, selfTestNav, selfTestDepth, selfTestGeo, STATIC_OBST, VEHICLE, MOTO, PERSON, DANGER_KINDS,
  };
})(typeof window !== "undefined" ? window : globalThis);
