/* wg_depth.js — 단안 깊이 (Depth Anything V2 small, onnxruntime-web)
 * 일반 카메라 RGB → 상대 깊이맵(클수록 가까움). ARCore/WebXR 불필요 → 어떤 폰에서든 동작.
 * 용도: walk_logic.analyzeDropoff 와 결합해 '내리막 계단/턱(바닥 꺼짐)' 감지.
 * 전처리: 518×518, x/255 후 ImageNet mean/std 정규화 (HF preprocessor_config 기준).
 */
(function (global) {
  "use strict";
  const MEAN = [0.485, 0.456, 0.406], STD = [0.229, 0.224, 0.225];

  class WGDepth {
    /* size: 입력 한 변(14의 배수). 낙차 감지엔 196이면 충분 — 실측상 int8 모델은 wasm이 webgpu보다 빠름 */
    constructor(modelUrl, size) {
      this.url = modelUrl; this.N = size || 196;
      this.session = null; this.provider = "?";
      this.cv = document.createElement("canvas"); this.cv.width = this.N; this.cv.height = this.N;
      this.ctx = this.cv.getContext("2d", { willReadFrequently: true });
      this.input = new Float32Array(3 * this.N * this.N);
    }
    async load() {
      ort.env.wasm.wasmPaths = "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.20.1/dist/";
      this.session = await ort.InferenceSession.create(this.url,
        { executionProviders: ["wasm"], graphOptimizationLevel: "all" });   // int8 → wasm이 최속
      this.provider = "wasm";
      return this.provider;
    }
    /* src(video/canvas) → {data: Float32Array(N*N), W:N, H:N} — 값 클수록 가까움(상대) */
    async estimate(src, srcW, srcH) {
      if (!this.session) return null;
      const N = this.N;
      this.ctx.drawImage(src, 0, 0, srcW, srcH, 0, 0, N, N);   // stretch(낙차 스캔엔 충분)
      const img = this.ctx.getImageData(0, 0, N, N).data, d = this.input, area = N * N;
      for (let i = 0; i < area; i++) {
        d[i]            = (img[i * 4]     / 255 - MEAN[0]) / STD[0];
        d[area + i]     = (img[i * 4 + 1] / 255 - MEAN[1]) / STD[1];
        d[2 * area + i] = (img[i * 4 + 2] / 255 - MEAN[2]) / STD[2];
      }
      const t = new ort.Tensor("float32", d, [1, 3, N, N]);
      const res = await this.session.run({ [this.session.inputNames[0]]: t });
      const out = res[this.session.outputNames[0]];
      // dims [1,H,W] 또는 [1,1,H,W] 대응
      const dims = out.dims, H = dims[dims.length - 2], W = dims[dims.length - 1];
      return { data: out.data, W, H };
    }
  }
  global.WGDepth = WGDepth;
})(window);
