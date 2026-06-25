// Supabase Edge Function: kb-agent
// 對話框後台：串接 Anthropic Claude API 與 GitHub（medical-kb- repo）。
//
// 部署：supabase functions deploy kb-agent
// 需設定密鑰（supabase secrets set ...，或 Dashboard → Edge Functions → Secrets）：
//   ANTHROPIC_API_KEY   Anthropic API 金鑰
//   GITHUB_TOKEN        fine-grained PAT，限 drmichelletang-cyber/medical-kb- 之 Contents: Read+Write
//   GITHUB_REPO         drmichelletang-cyber/medical-kb-
//   GITHUB_BRANCH       claude/sweet-hopper-ckn6il（或 main）
//   KB_NOTES_URL        https://drmichelletang-cyber.github.io/medical-kb-/notes.json
//   KB_SYSTEM_URL       https://raw.githubusercontent.com/drmichelletang-cyber/medical-kb-/<branch>/agent/系統提示.md
//   SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY  （驗證呼叫者身分用，已由平台預設注入）
//
// 兩種請求：
//   { action: "chat", messages: [...], attachments?: [{media_type, data(base64)}] }
//   { action: "commit", path, content, message, pdf?: {path, data(base64)} }   ← 使用者核可後才送

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const MODEL = "claude-opus-4-8";
const ANTHROPIC_URL = "https://api.anthropic.com/v1/messages";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (b: unknown, status = 200) =>
  new Response(JSON.stringify(b), { status, headers: { ...cors, "Content-Type": "application/json" } });

// ── 只允許已登入且具 admin 角色者使用（沿用既有 user_roles 表）──
async function requireAdmin(req: Request): Promise<{ ok: boolean; msg?: string }> {
  const authHeader = req.headers.get("Authorization") ?? "";
  if (!authHeader) return { ok: false, msg: "缺少授權" };
  const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const { data: u } = await admin.auth.getUser(authHeader.replace("Bearer ", ""));
  if (!u?.user) return { ok: false, msg: "未登入" };
  const { data: roles } = await admin.from("user_roles").select("role").eq("user_id", u.user.id);
  const isAdmin = (roles ?? []).some((r: { role: string }) => r.role === "admin");
  return isAdmin ? { ok: true } : { ok: false, msg: "需要 admin 權限" };
}

// ── 載入 KB 快照與 system prompt（公開 URL，可快取）──
let _notesCache: { at: number; notes: any[] } | null = null;
async function loadNotes(): Promise<any[]> {
  if (_notesCache && Date.now() - _notesCache.at < 60_000) return _notesCache.notes;
  const r = await fetch(Deno.env.get("KB_NOTES_URL")!);
  const notes = await r.json();
  _notesCache = { at: Date.now(), notes };
  return notes;
}
async function loadSystemPrompt(): Promise<string> {
  try {
    const r = await fetch(Deno.env.get("KB_SYSTEM_URL")!);
    if (r.ok) return await r.text();
  } catch (_) { /* fall through */ }
  return "你是「叮噹長壽知識庫」的維護助手。只動 .md；引用前一律查核；先查再寫；提案→核可。繁體中文回覆。";
}

// ── 工具定義（提供給 Claude）──
const TOOLS = [
  {
    name: "search_kb",
    description: "在知識庫快照中搜尋相關筆記，回傳標題、路徑與摘要。寫入前務必先查避免重複。",
    input_schema: { type: "object", properties: { query: { type: "string" } }, required: ["query"] },
  },
  {
    name: "propose_note",
    description: "產生一篇新筆記草稿（不落檔）。path 例：02 老年醫學證據庫/作者 年份 主題.md。",
    input_schema: {
      type: "object",
      properties: { path: { type: "string" }, content: { type: "string", description: "完整 .md（含 frontmatter）" } },
      required: ["path", "content"],
    },
  },
  {
    name: "propose_edit",
    description: "產生既有筆記的修改草稿（不落檔）。",
    input_schema: {
      type: "object",
      properties: { path: { type: "string" }, content: { type: "string" }, rationale: { type: "string" } },
      required: ["path", "content"],
    },
  },
];

// search_kb 的本地實作（在 notes.json 上做簡單比對）
function runSearch(notes: any[], query: string) {
  const q = String(query).toLowerCase();
  return notes
    .map((n) => {
      const hay = `${n.title} ${n.file} ${(n.fm?.aliases ?? []).join(" ")} ${n.body ?? ""}`.toLowerCase();
      const score = hay.includes(q) ? (n.title.toLowerCase().includes(q) ? 2 : 1) : 0;
      return { n, score };
    })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 8)
    .map((x) => ({ title: x.n.title, path: `${x.n.folder}/${x.n.file}.md`, excerpt: (x.n.body ?? "").slice(0, 300) }));
}

// ── 寫入 GitHub（核可後）──
async function ghPut(path: string, contentB64: string, message: string) {
  const repo = Deno.env.get("GITHUB_REPO")!, branch = Deno.env.get("GITHUB_BRANCH")!;
  const token = Deno.env.get("GITHUB_TOKEN")!;
  const api = `https://api.github.com/repos/${repo}/contents/${encodeURIComponent(path).replace(/%2F/g, "/")}`;
  const headers = { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "User-Agent": "kb-agent" };
  // 取既有 sha（更新時必要）
  let sha: string | undefined;
  const cur = await fetch(`${api}?ref=${branch}`, { headers });
  if (cur.ok) sha = (await cur.json()).sha;
  const r = await fetch(api, {
    method: "PUT",
    headers: { ...headers, "Content-Type": "application/json" },
    body: JSON.stringify({ message, content: contentB64, branch, sha }),
  });
  if (!r.ok) throw new Error(`GitHub ${r.status}: ${await r.text()}`);
  return (await r.json()).commit?.html_url;
}
const utf8ToB64 = (s: string) => btoa(String.fromCharCode(...new TextEncoder().encode(s)));

// ── 呼叫 Anthropic（含 tool loop 與 prompt caching）──
async function callClaude(system: string, notes: any[], messages: any[]) {
  const apiKey = Deno.env.get("ANTHROPIC_API_KEY")!;
  // system + KB 快照加 cache_control，重用時大幅降成本
  const systemBlocks = [
    { type: "text", text: system },
    {
      type: "text",
      text: "## 目前知識庫快照（notes.json，唯讀參考）\n" + JSON.stringify(notes).slice(0, 180_000),
      cache_control: { type: "ephemeral" },
    },
  ];
  const drafts: any[] = [];
  const convo = [...messages];

  for (let hop = 0; hop < 6; hop++) {
    const resp = await fetch(ANTHROPIC_URL, {
      method: "POST",
      headers: { "x-api-key": apiKey, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model: MODEL, max_tokens: 4096, system: systemBlocks, tools: TOOLS, messages: convo }),
    });
    if (!resp.ok) throw new Error(`Anthropic ${resp.status}: ${await resp.text()}`);
    const msg = await resp.json();
    convo.push({ role: "assistant", content: msg.content });

    const toolUses = (msg.content ?? []).filter((b: any) => b.type === "tool_use");
    if (toolUses.length === 0) {
      const text = (msg.content ?? []).filter((b: any) => b.type === "text").map((b: any) => b.text).join("\n");
      return { text, drafts };
    }
    const results = [];
    for (const tu of toolUses) {
      if (tu.name === "search_kb") {
        results.push({ type: "tool_result", tool_use_id: tu.id, content: JSON.stringify(runSearch(notes, tu.input.query)) });
      } else if (tu.name === "propose_note" || tu.name === "propose_edit") {
        drafts.push({ kind: tu.name, ...tu.input });
        results.push({ type: "tool_result", tool_use_id: tu.id, content: "草稿已收，等待使用者核可。" });
      } else {
        results.push({ type: "tool_result", tool_use_id: tu.id, content: "未知工具", is_error: true });
      }
    }
    convo.push({ role: "user", content: results });
  }
  return { text: "（已達工具回合上限）", drafts };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  try {
    const auth = await requireAdmin(req);
    if (!auth.ok) return json({ error: auth.msg }, 403);
    const body = await req.json();

    if (body.action === "commit") {
      // 使用者已核可：落檔 .md（與可選的 PDF）
      const url = await ghPut(body.path, utf8ToB64(body.content), body.message ?? `對話框新增：${body.path}`);
      if (body.pdf?.data) await ghPut(body.pdf.path, body.pdf.data, `對話框附件：${body.pdf.path}`);
      return json({ ok: true, commit: url, note: "GitHub Action 會自動重生 HTML，稍候站上即更新。" });
    }

    // 預設 action: chat
    const notes = await loadNotes();
    const system = await loadSystemPrompt();
    const messages = [...body.messages];
    // 把附件接到最後一則使用者訊息
    if (body.attachments?.length) {
      const last = messages[messages.length - 1];
      const blocks = Array.isArray(last.content) ? last.content : [{ type: "text", text: String(last.content) }];
      for (const a of body.attachments) {
        if (a.media_type === "application/pdf")
          blocks.unshift({ type: "document", source: { type: "base64", media_type: a.media_type, data: a.data } });
        else if (String(a.media_type).startsWith("image/"))
          blocks.unshift({ type: "image", source: { type: "base64", media_type: a.media_type, data: a.data } });
      }
      last.content = blocks;
    }
    const out = await callClaude(system, notes, messages);
    return json(out);
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
