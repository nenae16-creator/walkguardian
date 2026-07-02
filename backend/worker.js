/* 걸음지기 AI 백엔드 (Cloudflare Worker)
 * 앱이 보낸 전방 사진 → OpenAI gpt-4o-mini vision → '허용 안내문' 중에서만 위험 반환.
 * ★OpenAI 키는 이 Worker 의 secret(OPENAI_API_KEY)에만 저장. 앱/공개코드엔 절대 안 들어감.
 * 배포: backend/README.md 참고.
 */
const ALLOWED = [
  "앞 장애물", "앞 계단 주의", "앞 턱 주의", "앞 사람", "앞 공사구간",
  "보도 끝 주의", "앞 정차 차량", "정지, 앞 차량 접근", "앞 횡단보도", "차도입니다, 인도로",
];

const SYS = `너는 시각장애인 보행 보조다. 사진은 인도를 걷는 사람의 바로 앞 시야다.
경로 위에서 위험하거나 부딪힐 수 있는 것을 골라, 아래 '허용 문구' 중에서만 최대 2개를 JSON 배열로 답하라.
규칙:
- ★계단·층계·단차가 조금이라도 보이면 반드시 "앞 계단 주의"를 넣어라(올라가는·내려가는 계단, 한 칸 턱, 지하철 계단 모두). 내려가는 계단(바닥이 갑자기 낮아지는 단)은 특히 위험하니 반드시 잡아라.
- 전봇대·볼라드·입간판·기둥·문·화분·공사·튀어나온 장애물은 "앞 장애물". 낮은 단차는 "앞 턱 주의".
- 앞을 막는 사람은 "앞 사람". 인도가 끊기면 "보도 끝 주의". 차도로 나가면 "차도입니다, 인도로".
- 옆 차도의 차량은 무시. (내 앞을 가로지르거나 인도로 올라오는 차만 "정지, 앞 차량 접근")
- 위험이 없으면 빈 배열 []. 설명·다른 문장 금지, 오직 JSON 배열만.
허용 문구: ${JSON.stringify(ALLOWED)}`;

export default {
  async fetch(req, env) {
    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "content-type,x-wg-token",
      "Access-Control-Allow-Methods": "POST,OPTIONS",
    };
    const json = (obj, status = 200) =>
      new Response(JSON.stringify(obj), { status, headers: { ...cors, "content-type": "application/json" } });

    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST") return json({ error: "POST only" }, 405);
    // 남용 방지용 토큰(선택). WG_TOKEN secret 을 설정하면 앱도 같은 값을 보내야 함.
    if (env.WG_TOKEN && req.headers.get("x-wg-token") !== env.WG_TOKEN) return json({ error: "unauthorized" }, 401);

    let body;
    try { body = await req.json(); } catch { return json({ error: "bad json" }, 400); }
    const image = body && body.image;                 // data:image/jpeg;base64,....
    if (!image) return json({ hazards: [] });

    const payload = {
      model: "gpt-4o-mini",
      temperature: 0,
      max_tokens: 60,
      messages: [
        { role: "system", content: SYS },
        { role: "user", content: [
          { type: "text", text: "이 장면의 위험을 허용 문구로만 답해." },
          { type: "image_url", image_url: { url: image, detail: "high" } },
        ] },
      ],
    };

    let hazards = [];
    try {
      const r = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: { authorization: "Bearer " + env.OPENAI_API_KEY, "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const j = await r.json();
      let txt = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || "[]";
      txt = txt.replace(/```json|```/g, "").trim();
      const arr = JSON.parse(txt);
      hazards = Array.isArray(arr) ? arr.filter(h => ALLOWED.includes(h)).slice(0, 2) : [];
    } catch (e) {
      return json({ hazards: [], error: String(e) });
    }
    return json({ hazards });
  },
};
