/* 걸음지기 AI 백엔드 (Cloudflare Worker)
 * 앱이 보낸 전방 사진 → OpenAI gpt-4o-mini vision(장면 설명) + TTS(음성 합성) → {text, audio}
 * ★OpenAI 키는 이 Worker 의 secret(OPENAI_API_KEY)에만 저장. 앱/공개코드엔 절대 안 들어감.
 * 배포: backend/README.md 참고.
 */
const VOICE = "nova";
const VSYS = `너는 시각장애인 보행 보조다. 사진은 걷는 사람의 바로 앞 시야다.
앞에 있는 사물·장애물·계단·턱을 아주 짧은 한국어로 알려줘.
예: '앞에 의자', '왼쪽 테이블', '앞 계단 조심', '앞 전봇대', '앞에 문'.
가장 가깝고 중요한 것 1~2개만, 전체 15자 이내로 짧게.
★계단·단차가 보이면 꼭 '계단'을 말해(특히 내려가는 계단). 옆 차도의 차량은 무시.
위험/사물이 없으면 정확히 '없음' 이라고만 답해. 문장부호·설명 금지.`;

function b64(buf) {
  const b = new Uint8Array(buf); let s = "";
  for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000));
  return btoa(s);
}

export default {
  async fetch(req, env) {
    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "content-type,x-wg-token",
      "Access-Control-Allow-Methods": "POST,OPTIONS",
    };
    const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { ...cors, "content-type": "application/json" } });
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST") return json({ error: "POST only" }, 405);
    if (env.WG_TOKEN && req.headers.get("x-wg-token") !== env.WG_TOKEN) return json({ error: "unauthorized" }, 401);

    let body; try { body = await req.json(); } catch { return json({ error: "bad json" }, 400); }
    const image = body && body.image;
    if (!image) return json({ text: "", audio: "" });
    const auth = { authorization: "Bearer " + env.OPENAI_API_KEY, "content-type": "application/json" };

    try {
      // 1) 장면 설명(짧은 한국어)
      const vr = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST", headers: auth, body: JSON.stringify({
          model: "gpt-4o-mini", temperature: 0.2, max_tokens: 30,
          messages: [
            { role: "system", content: VSYS },
            { role: "user", content: [
              { type: "text", text: "앞에 뭐가 있어?" },
              { type: "image_url", image_url: { url: image, detail: "high" } },
            ] },
          ],
        }),
      });
      const vj = await vr.json();
      let text = ((vj.choices && vj.choices[0] && vj.choices[0].message && vj.choices[0].message.content) || "").trim().replace(/["'.]/g, "");
      if (!text || ["없음", "없습니다", "없어요", "none", "None", "[]"].includes(text)) return json({ text: "", audio: "" });

      // 2) 한국어 음성 합성
      let audio = "";
      try {
        const tr = await fetch("https://api.openai.com/v1/audio/speech", {
          method: "POST", headers: auth,
          body: JSON.stringify({ model: "gpt-4o-mini-tts", voice: VOICE, input: text, response_format: "mp3" }),
        });
        audio = b64(await tr.arrayBuffer());
      } catch (e) { /* 음성 실패해도 text 는 반환 */ }
      return json({ text, audio });
    } catch (e) {
      return json({ text: "", audio: "", error: String(e) });
    }
  },
};
