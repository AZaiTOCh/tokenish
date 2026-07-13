from pathlib import Path

ROOT = Path(r"c:\Users\admin\Desktop\TOKISH\tokenish")
STATIC = ROOT / "packages" / "engine" / "tokenish_engine" / "static"
PUBLIC = ROOT / "apps" / "desktop" / "public"
SCRIPTS = ROOT / "scripts"
STATIC.mkdir(parents=True, exist_ok=True)
PUBLIC.mkdir(parents=True, exist_ok=True)

INDEX = """<!DOCTYPE html>
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
        <option value="auto">auto (best available)</option>
        <option value="groq">groq</option>
        <option value="gemini">gemini</option>
        <option value="openrouter">openrouter</option>
        <option value="perplexity">perplexity</option>
        <option value="openai">openai</option>
        <option value="anthropic">anthropic</option>
      </select>
      <div class="section-label">model</div>
      <input id="model" list="models" value="llama-3.3-70b-versatile" placeholder="model id" />
      <datalist id="models"></datalist>
      <div class="section-label">apis — click to set up</div>
      <div class="provider-list" id="providers"></div>
      <div class="setup-box" id="setupBox">
        <div class="hint" id="setupHint"></div>
        <input id="setupKey" type="password" placeholder="paste api key" autocomplete="off" />
        <button class="btn primary" id="setupSave" type="button">save &amp; test</button>
        <div class="hint" id="setupStatus"></div>
      </div>
      <div class="section-label">pdf page range (optional)</div>
      <input id="pageRange" type="text" placeholder="e.g. 12-15" />
    </aside>
    <main class="main">
      <div class="topbar">
        <div class="tokex-panel" id="tokexPanel">
          <div class="tokex-title">tokens saved</div>
          <div class="tokex-big" id="tokexSaved">—</div>
          <div class="tokex-grid">
            <div><span class="k">before</span><span id="tokexTotal">—</span></div>
            <div><span class="k">after</span><span id="tokexRun">—</span></div>
            <div><span class="k">saved</span><span id="tokexPct">—</span></div>
          </div>
          <div class="tokex-stages" id="tokexStages">send a message to see how many tokens were saved</div>
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

APP_JS = r"""
const messagesEl = document.getElementById("messages");
const errorEl = document.getElementById("error");
const promptEl = document.getElementById("prompt");
const fileInput = document.getElementById("fileInput");
const attachmentsEl = document.getElementById("attachments");
const providersEl = document.getElementById("providers");
const modelsList = document.getElementById("models");
const setupBox = document.getElementById("setupBox");
const setupHint = document.getElementById("setupHint");
const setupKey = document.getElementById("setupKey");
const setupStatus = document.getElementById("setupStatus");

let history = [];
let files = [];
let setupProvider = null;

const SETUP_HELP = {
  groq: { env: "GROQ_API_KEY", url: "https://console.groq.com/keys", blurb: "Create a free Groq key, paste it here, then save & test." },
  gemini: { env: "GEMINI_API_KEY", url: "https://aistudio.google.com/apikey", blurb: "Create a Gemini API key, paste it here, then save & test." },
  openrouter: { env: "OPENROUTER_API_KEY", url: "https://openrouter.ai/keys", blurb: "Create an OpenRouter key (free models available), paste it here, then save & test." },
  perplexity: { env: "PERPLEXITY_API_KEY", url: "https://www.perplexity.ai/settings/api", blurb: "Create a Perplexity API key, paste it here, then save & test." },
  openai: { env: "OPENAI_API_KEY", url: "https://platform.openai.com/api-keys", blurb: "Create an OpenAI API key, paste it here, then save & test." },
  anthropic: { env: "ANTHROPIC_API_KEY", url: "https://console.anthropic.com/settings/keys", blurb: "Create an Anthropic API key, paste it here, then save & test." },
};

function showError(msg) {
  errorEl.hidden = !msg;
  errorEl.textContent = msg || "";
}

function renderAttachments() {
  attachmentsEl.innerHTML = files.map((f) => `<span class="chip">${escapeHtml(f.name)}</span>`).join("");
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderTokex(t) {
  if (!t) return;
  const before = Number(t.total_tokex ?? t.original_tokens ?? 0);
  const after = Number(t.tokex_this_run ?? t.optimized_tokens ?? 0);
  const saved = Number(t.saved_tokex ?? t.saved_tokens ?? Math.max(0, before - after));
  const pct = Number(t.saved_pct ?? (before ? (100 * saved) / before : 0));
  document.getElementById("tokexSaved").textContent =
    saved > 0 ? `${saved.toLocaleString()} tokens (${pct.toFixed(1)}%)` : `0 tokens (0%)`;
  document.getElementById("tokexTotal").textContent = before.toLocaleString();
  document.getElementById("tokexRun").textContent = after.toLocaleString();
  document.getElementById("tokexPct").textContent = `${pct.toFixed(1)}%`;
  document.getElementById("tokexStages").textContent =
    before === 0
      ? "no tokens measured yet"
      : `before optimization → after optimization · ${pct.toFixed(1)}% fewer tokens sent`;
}

function addBubble(role, content) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  const label = role === "user" ? "you" : "tokenish";
  div.innerHTML = `<div class="meta">${label}</div>${escapeHtml(content || "")}`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

function updateBubble(bubble, text, meta = {}) {
  const t = meta.tokex || meta.meter;
  const bits = ["tokenish"];
  if (meta.provider) bits.push(`${meta.provider}${meta.model ? " / " + meta.model : ""}`);
  if (t && (t.saved_tokex ?? t.saved_tokens) != null) {
    bits.push(`saved ${(t.saved_tokex ?? t.saved_tokens).toLocaleString()} tokens (${Number(t.saved_pct || 0).toFixed(1)}%)`);
  }
  const body = (text && String(text).trim()) ? String(text) : "…";
  bubble.innerHTML = `<div class="meta">${bits.join(" · ")}</div>${escapeHtml(body)}`;
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function loadProviders() {
  try {
    const res = await fetch("/providers");
    const data = await res.json();
    providersEl.innerHTML = "";
    const modelSet = new Set();
    for (const p of data.providers || []) {
      if (!SETUP_HELP[p.name]) continue;
      const row = document.createElement("div");
      row.className = "provider" + (setupProvider === p.name ? " active" : "");
      row.innerHTML = `<span><span class="dot ${p.available ? "ok" : "bad"}"></span>${p.name}</span><span style="color:var(--muted);font-size:0.75rem">${p.available ? "ready" : "click to set up"}</span>`;
      row.onclick = () => openSetup(p.name);
      providersEl.appendChild(row);
      (p.models || []).forEach((m) => modelSet.add(m));
      if (p.available && document.getElementById("provider").value === "auto" && !modelSet.has(document.getElementById("model").value)) {
        // leave model as-is unless empty
      }
    }
    modelsList.innerHTML = [...modelSet].map((m) => `<option value="${m}"></option>`).join("");
  } catch {
    showError("engine offline — run start_tokenish.bat");
  }
}

function openSetup(name) {
  setupProvider = name;
  const help = SETUP_HELP[name];
  setupBox.classList.add("open");
  setupHint.innerHTML = `${help.blurb}<br/><a href="${help.url}" target="_blank" rel="noopener">open ${name} key page</a>`;
  setupKey.value = "";
  setupStatus.textContent = "";
  loadProviders();
}

document.getElementById("setupSave").onclick = async () => {
  if (!setupProvider) return;
  const key = setupKey.value.trim();
  if (!key) {
    setupStatus.textContent = "paste a key first";
    return;
  }
  setupStatus.textContent = "testing…";
  try {
    const res = await fetch("/settings/key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: setupProvider, api_key: key }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "save failed");
    setupStatus.textContent = data.detail || "saved";
    document.getElementById("provider").value = setupProvider;
    if (data.model) document.getElementById("model").value = data.model;
    await loadProviders();
  } catch (e) {
    setupStatus.textContent = e.message || String(e);
  }
};

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
  const pageRange = document.getElementById("pageRange").value.trim();
  if (pageRange) fd.append("page_range", pageRange);
  for (const f of files) fd.append("files", f);

  const bubble = addBubble("assistant", "thinking…");
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
          updateBubble(bubble, assistant || "thinking…", meta);
        } else if (evt.type === "delta") {
          assistant += evt.text || "";
          updateBubble(bubble, assistant, meta);
        } else if (evt.type === "error") {
          throw new Error(evt.error || "chat failed");
        }
      }
    }
    if (!assistant.trim()) {
      throw new Error("no reply — set up a provider api key (click a provider on the left)");
    }
    history.push({ role: "assistant", content: assistant });
    files = [];
    fileInput.value = "";
    renderAttachments();
  } catch (e) {
    const msg = e.message || String(e);
    showError(msg);
    updateBubble(bubble, msg, meta);
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
  addBubble("assistant", "attach a file or type a message. click a provider on the left to add an api key.");
};
promptEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

addBubble("assistant", "attach a file or type a message. click a provider on the left to add an api key.");
loadProviders();
"""

STYLES = (STATIC / "styles.css").read_text(encoding="utf-8") if (STATIC / "styles.css").exists() else ""

for dest in (STATIC, PUBLIC):
    (dest / "index.html").write_text(INDEX, encoding="utf-8")
    (dest / "app.js").write_text(APP_JS, encoding="utf-8")
    if STYLES:
        (dest / "styles.css").write_text(STYLES, encoding="utf-8")
print("ui written")
