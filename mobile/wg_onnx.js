/* wg_onnx.js — 국내 학습 YOLOv8 탐지기 (onnxruntime-web)
 * best.onnx (입력 1×3×640×640, 출력 1×25×8400) 를 브라우저에서 추론 →
 * letterbox 역변환 + NMS → [{cls,conf,xyxy}] (원본 프레임 좌표). 걸음지기 엔진에 그대로 투입.
 */
(function (global) {
  "use strict";
  // 학습 클래스 순서(멀티 데이터셋) — data.yaml names 와 동일해야 함
  const CLASSES = ["lamb", "bike", "block", "cars", "chair", "dogs", "person", "sidewalk",
    "stairs", "table", "garbage-bin", "cupboard", "door", "fence", "plant", "pole",
    "rikshaw", "road", "signboard", "tree", "window"];
  const N = 640;

  function iou(a, b) {
    const x1 = Math.max(a[0], b[0]), y1 = Math.max(a[1], b[1]);
    const x2 = Math.min(a[2], b[2]), y2 = Math.min(a[3], b[3]);
    const iw = Math.max(0, x2 - x1), ih = Math.max(0, y2 - y1), inter = iw * ih;
    const ua = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter;
    return ua > 0 ? inter / ua : 0;
  }

  class WGOnnxDetector {
    constructor(modelUrl, conf = 0.35, iouThr = 0.45) {
      this.url = modelUrl; this.conf = conf; this.iouThr = iouThr;
      this.session = null; this.inputName = null; this.provider = "?";
      this.cv = document.createElement("canvas"); this.cv.width = N; this.cv.height = N;
      this.ctx = this.cv.getContext("2d", { willReadFrequently: true });
      this.data = new Float32Array(N * N * 3);
    }
    async load(onProgress) {
      ort.env.wasm.wasmPaths = "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.20.1/dist/";
      // WebGPU 우선(빠름) → 안 되면 wasm 폴백
      try {
        this.session = await ort.InferenceSession.create(this.url,
          { executionProviders: ["webgpu", "wasm"], graphOptimizationLevel: "all" });
        this.provider = "webgpu/wasm";
      } catch (e) {
        this.session = await ort.InferenceSession.create(this.url,
          { executionProviders: ["wasm"], graphOptimizationLevel: "all" });
        this.provider = "wasm";
      }
      this.inputName = this.session.inputNames[0];
      return this.provider;
    }
    _preprocess(src, W, H) {
      const r = Math.min(N / W, N / H);
      const nw = Math.round(W * r), nh = Math.round(H * r);
      const padX = Math.floor((N - nw) / 2), padY = Math.floor((N - nh) / 2);
      this.ctx.fillStyle = "#727272"; this.ctx.fillRect(0, 0, N, N);
      this.ctx.drawImage(src, 0, 0, W, H, padX, padY, nw, nh);
      const img = this.ctx.getImageData(0, 0, N, N).data, d = this.data, area = N * N;
      for (let i = 0; i < area; i++) {           // HWC uint8 → CHW float32 [0,1]
        d[i] = img[i * 4] / 255;
        d[area + i] = img[i * 4 + 1] / 255;
        d[2 * area + i] = img[i * 4 + 2] / 255;
      }
      return { r, padX, padY };
    }
    async detect(src, W, H) {
      if (!this.session) return [];
      const { r, padX, padY } = this._preprocess(src, W, H);
      const t = new ort.Tensor("float32", this.data, [1, 3, N, N]);
      const res = await this.session.run({ [this.inputName]: t });
      const o = res[this.session.outputNames[0]];
      const data = o.data, na = o.dims[2], nc = CLASSES.length;   // dims: [1,25,8400]
      const cand = [];
      for (let a = 0; a < na; a++) {
        let best = 0, bi = 0;
        for (let k = 0; k < nc; k++) { const s = data[(4 + k) * na + a]; if (s > best) { best = s; bi = k; } }
        if (best < this.conf) continue;
        const cx = data[a], cy = data[na + a], w = data[2 * na + a], h = data[3 * na + a];
        cand.push({
          cls: CLASSES[bi], conf: best,
          xyxy: [((cx - w / 2) - padX) / r, ((cy - h / 2) - padY) / r,
                 ((cx + w / 2) - padX) / r, ((cy + h / 2) - padY) / r],
        });
      }
      return this._nms(cand);
    }
    _nms(boxes) {
      boxes.sort((a, b) => b.conf - a.conf);
      const keep = [], used = new Array(boxes.length).fill(false);
      for (let i = 0; i < boxes.length; i++) {
        if (used[i]) continue; keep.push(boxes[i]);
        for (let j = i + 1; j < boxes.length; j++)
          if (!used[j] && boxes[i].cls === boxes[j].cls && iou(boxes[i].xyxy, boxes[j].xyxy) > this.iouThr) used[j] = true;
      }
      return keep;
    }
  }
  global.WGOnnxDetector = WGOnnxDetector;
  global.WG_CLASSES = CLASSES;
})(window);
