from pathlib import Path

ROOT = Path(r"c:\Users\admin\Desktop\TOKISH\tokenish")
STATIC = ROOT / "packages" / "engine" / "tokenish_engine" / "static"
PUBLIC = ROOT / "apps" / "desktop" / "public"
STATIC.mkdir(parents=True, exist_ok=True)
PUBLIC.mkdir(parents=True, exist_ok=True)

INDEX = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>tokenish</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/ui/styles.css" />
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <h1>tokenish</h1>
        <span>token use optimizer</span>
      </div>
      <div class="section-label">provider</div>
      <select id="provider">
        <option value="auto">auto</option>
        <option value="ollama">local</option>
        <option value="openai">openai</option>
        <option value="anthropic">anthropic</option>
        <option value="groq">groq</option>
      </select>
      <div class="section-label">model</div>
      <input id="model" list="models" value="gpt-4o" placeholder="model id" />
      <datalist id="models"></datalist>
      <div class="section-label">status</div>
      <div class="provider-list" id="providers"></div>
      <div class="section-label">pdf page range</div>
      <input id="pageRange" type="text" placeholder="e.g. 12-15" />
    </aside>
    <main class="main">
      <div class="topbar">
        <div class="tokex-panel" id="tokexPanel">
          <div class="tokex-title">saved tokex</div>
          <div class="tokex-big" id="tokexSaved">—</div>
          <div class="tokex-grid">
            <div><span class="k">total tokex</span><span id="tokexTotal">—</span></div>
            <div><span class="k">this run</span><span id="tokexRun">—</span></div>
            <div><span class="k">saved %</span><span id="tokexPct">—</span></div>
          </div>
          <div class="tokex-stages" id="tokexStages">send a prompt to measure token expenditure</div>
        </div>
        <button class="btn" id="newChat">new chat</button>
      </div>
      <div class="messages" id="messages"></div>
      <div class="composer">
        <div class="attachments" id="attachments"></div>
        <div class="error" id="error" hidden></div>
        <div class="row">
          <button class="btn" id="attachBtn">attach</button>
          <input id="fileInput" type="file" multiple hidden accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt,.md,.json,.png,.jpg,.jpeg,.webp" />
          <textarea id="prompt" placeholder="message tokenish…"></textarea>
          <button class="btn primary" id="sendBtn">send</button>
        </div>
      </div>
    </main>
  </div>
  <script src="/ui/app.js"></script>
</body>
</html>
"""

STYLES = r"""
:root {
  --bg: #0f1419;
  --panel: #161d27;
  --panel-2: #1c2533;
  --border: #2a3545;
  --text: #e7eef8;
  --muted: #8b9bb0;
  --accent: #3ecf8e;
  --accent-dim: #1f8f5f;
  --danger: #e06c75;
  --user: #243044;
  --assistant: #1a222e;
  --radius: 10px;
  font-family: "IBM Plex Sans", system-ui, sans-serif;
  color: var(--text);
  background: var(--bg);
}
* { box-sizing: border-box; }
html, body { height: 100%; margin: 0; }
button, input, select, textarea { font: inherit; color: inherit; }
.app {
  display: grid;
  grid-template-columns: 280px 1fr;
  height: 100%;
  background:
    radial-gradient(1200px 600px at 10% -10%, #1a3d32 0%, transparent 55%),
    radial-gradient(900px 500px at 100% 0%, #1a2740 0%, transparent 50%),
    var(--bg);
}
.sidebar {
  border-right: 1px solid var(--border);
  background: color-mix(in srgb, var(--panel) 88%, transparent);
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: auto;
}
.brand h1 { margin: 0; font-size: 1.35rem; letter-spacing: 0.04em; text-transform: lowercase; }
.brand span { color: var(--muted); font-size: 0.78rem; }
.section-label {
  color: var(--muted);
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  margin: 8px 6px 4px;
}
select, input[type="text"] {
  width: 100%;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
}
.provider-list { display: flex; flex-direction: column; gap: 6px; }
.provider {
  display: flex; justify-content: space-between; gap: 8px;
  padding: 8px 10px; border-radius: 8px;
  background: var(--panel-2); border: 1px solid var(--border); font-size: 0.85rem;
}
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
.dot.ok { background: var(--accent); }
.dot.bad { background: var(--danger); }
.main { display: grid; grid-template-rows: auto 1fr auto; min-width: 0; }
.topbar {
  display: flex; align-items: stretch; justify-content: space-between; gap: 12px;
  padding: 14px 20px; border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--panel) 70%, transparent);
}
.tokex-panel {
  flex: 1;
  background: linear-gradient(180deg, #13241c, #101820);
  border: 1px solid #2a5a44;
  border-radius: 12px;
  padding: 12px 16px;
  font-family: "IBM Plex Mono", monospace;
}
.tokex-title { color: var(--accent); font-size: 0.72rem; letter-spacing: 0.12em; font-weight: 600; }
.tokex-big { font-size: 1.85rem; font-weight: 600; color: var(--accent); margin: 4px 0 8px; }
.tokex-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; font-size: 0.82rem; }
.tokex-grid .k { display: block; color: var(--muted); font-size: 0.68rem; letter-spacing: 0.06em; margin-bottom: 2px; }
.tokex-stages { margin-top: 8px; color: var(--muted); font-size: 0.72rem; }
.messages { overflow: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.bubble {
  max-width: min(780px, 92%); padding: 12px 14px; border-radius: var(--radius);
  border: 1px solid var(--border); white-space: pre-wrap; line-height: 1.45; font-size: 0.95rem;
}
.bubble.user { align-self: flex-end; background: var(--user); }
.bubble.assistant { align-self: flex-start; background: var(--assistant); }
.bubble .meta { color: var(--muted); font-size: 0.75rem; margin-bottom: 6px; font-family: "IBM Plex Mono", monospace; }
.composer {
  border-top: 1px solid var(--border); padding: 14px 18px 18px;
  background: color-mix(in srgb, var(--panel) 85%, transparent);
  display: flex; flex-direction: column; gap: 10px;
}
.attachments { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  font-size: 0.78rem; background: var(--panel-2); border: 1px solid var(--border);
  border-radius: 999px; padding: 4px 10px; color: var(--muted);
}
.row { display: flex; gap: 10px; align-items: flex-end; }
textarea {
  flex: 1; min-height: 72px; max-height: 180px; resize: vertical;
  background: var(--panel-2); border: 1px solid var(--border); border-radius: 10px; padding: 12px;
}
.btn {
  border: 1px solid var(--border); background: var(--panel-2);
  border-radius: 10px; padding: 10px 14px; cursor: pointer;
}
.btn.primary {
  background: linear-gradient(180deg, var(--accent), var(--accent-dim));
  border-color: transparent; color: #04140c; font-weight: 600;
}
.error { color: var(--danger); font-size: 0.85rem; }
@media (max-width: 860px) {
  .app { grid-template-columns: 1fr; }
  .sidebar { display: none; }
  .tokex-grid { grid-template-columns: 1fr; }
}
"""

APP_JS = r"""
const messagesEl = document.getElementById("messages");
const errorEl = document.getElementById("error");
const promptEl = document.getElementById("prompt");
const fileInput = document.getElementById("fileInput");
const attachmentsEl = document.getElementById("attachments");
const providersEl = document.getElementById("providers");
const modelsList = document.getElementById("models");

let history = [];
let files = [];

function showError(msg) {
  errorEl.hidden = !msg;
  errorEl.textContent = msg || "";
}

function renderAttachments() {
  attachmentsEl.innerHTML = files.map((f) => `<span class="chip">${f.name}</span>`).join("");
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderTokex(t) {
  if (!t) return;
  const saved = t.saved_tokex ?? t.saved_tokens ?? 0;
  const total = t.total_tokex ?? t.original_tokens ?? 0;
  const run = t.tokex_this_run ?? t.optimized_tokens ?? 0;
  const pct = t.saved_pct ?? 0;
  document.getElementById("tokexSaved").textContent = `${saved.toLocaleString()} tokens (${pct}%)`;
  document.getElementById("tokexTotal").textContent = total.toLocaleString();
  document.getElementById("tokexRun").textContent = run.toLocaleString();
  document.getElementById("tokexPct").textContent = `${pct}%`;
  document.getElementById("tokexStages").textContent = (t.fact_notes || []).slice(0, 2).join(" · ") || "";
}

function addBubble(role, content, meta = {}) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  const bits = [role];
  if (meta.provider) bits.push(`${meta.provider}/${meta.model || ""}`);
  const t = meta.tokex || meta.meter;
  if (t) bits.push(`saved ${t.saved_tokex ?? t.saved_tokens} tokex (${t.saved_pct}%)`);
  div.innerHTML = `<div class="meta">${bits.join(" · ")}</div>${escapeHtml(content)}`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

async function loadProviders() {
  try {
    const res = await fetch("/providers");
    const data = await res.json();
    providersEl.innerHTML = "";
    const modelSet = new Set();
    for (const p of data.providers || []) {
      const row = document.createElement("div");
      row.className = "provider";
      row.innerHTML = `<span><span class="dot ${p.available ? "ok" : "bad"}"></span>${p.name}</span><span style="color:var(--muted);font-size:0.75rem">${p.detail}</span>`;
      providersEl.appendChild(row);
      (p.models || []).forEach((m) => modelSet.add(m));
      if (p.name === "ollama" && p.available && p.models?.length) {
        document.getElementById("provider").value = "ollama";
        document.getElementById("model").value = p.models[0];
      }
    }
    modelsList.innerHTML = [...modelSet].map((m) => `<option value="${m}"></option>`).join("");
  } catch {
    showError("engine offline");
  }
}

async function send() {
  const prompt = promptEl.value.trim() || (files.length ? "(attachment only)" : "");
  if (!prompt && !files.length) return;
  showError("");
  addBubble("user", prompt);
  history.push({ role: "user", content: prompt });
  promptEl.value = "";

  const fd = new FormData();
  fd.append("prompt", prompt);
  const model = document.getElementById("model").value;
  const provider = document.getElementById("provider").value;
  fd.append("target_engine", model);
  fd.append("model", model);
  fd.append("provider", provider);
  fd.append("history", JSON.stringify(history.slice(0, -1)));
  fd.append("stream", "true");
  fd.append("show_envelope", "false");
  const pageRange = document.getElementById("pageRange").value.trim();
  if (pageRange) fd.append("page_range", pageRange);
  for (const f of files) fd.append("files", f);

  const bubble = addBubble("assistant", "");
  let assistant = "";
  let meta = {};

  try {
    const res = await fetch("/chat", { method: "POST", body: fd });
    if (!res.ok || !res.body) throw new Error(await res.text());
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop() || "";
      for (const line of lines) {
        if (!line.trim()) continue;
        let evt;
        try { evt = JSON.parse(line); } catch { continue; }
        if (evt.type === "meta") {
          meta = evt;
          renderTokex(evt.tokex || evt.meter);
        } else if (evt.type === "delta") {
          assistant += evt.text || "";
          const t = meta.tokex || meta.meter;
          bubble.innerHTML = `<div class="meta">assistant${meta.provider ? ` · ${meta.provider}/${meta.model}` : ""}${
            t ? ` · saved ${t.saved_tokex ?? t.saved_tokens} tokex (${t.saved_pct}%)` : ""
          }</div>${escapeHtml(assistant)}`;
          messagesEl.scrollTop = messagesEl.scrollHeight;
        } else if (evt.type === "error") {
          throw new Error(evt.error || "chat failed");
        }
      }
    }
    history.push({ role: "assistant", content: assistant });
    files = [];
    fileInput.value = "";
    renderAttachments();
  } catch (e) {
    showError(e.message || String(e));
    bubble.innerHTML = `<div class="meta">assistant</div>${escapeHtml("error: " + (e.message || e))}`;
  }
}

document.getElementById("attachBtn").onclick = () => fileInput.click();
fileInput.onchange = () => {
  files = Array.from(fileInput.files || []);
  renderAttachments();
};
document.getElementById("sendBtn").onclick = () => send();
document.getElementById("newChat").onclick = () => {
  history = [];
  messagesEl.innerHTML = "";
  addBubble("assistant", "attach a pdf, docx, xlsx, csv, or image. tokenish optimizes every send automatically.");
};
promptEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

addBubble("assistant", "attach a pdf, docx, xlsx, csv, or image. tokenish optimizes every send automatically.");
loadProviders();
"""

for dest in (STATIC, PUBLIC):
    (dest / "index.html").write_text(INDEX, encoding="utf-8")
    (dest / "styles.css").write_text(STYLES, encoding="utf-8")
    (dest / "app.js").write_text(APP_JS, encoding="utf-8")
    print("wrote", dest)
