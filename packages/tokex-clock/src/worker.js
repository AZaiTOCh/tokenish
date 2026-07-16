/**
 * Live World Counter Clock — Cloudflare Worker hive (option B).
 *
 * Endpoints:
 *   GET  /clock       → live collective tally (no secrets)
 *   POST /contribute  → { node_id, saved_tokex, total_tokex, ts }
 *
 * Deploy:
 *   cd packages/tokex-clock && npx wrangler deploy
 *
 * Set TOKENISH_HIVE_URL to the worker URL in tokenish prefs / env.
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: cors() });
    }

    const id = env.TOKEX_CLOCK.idFromName("global");
    const stub = env.TOKEX_CLOCK.get(id);

    if (url.pathname === "/clock" && request.method === "GET") {
      return stub.fetch("https://clock/internal/clock");
    }
    if (url.pathname === "/contribute" && request.method === "POST") {
      return stub.fetch("https://clock/internal/contribute", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: await request.text(),
      });
    }
    if (url.pathname === "/" || url.pathname === "/health") {
      return json({ ok: true, clock: "Live World Counter Clock", agent: "Neoborg" });
    }
    return json({ ok: false, error: "not found" }, 404);
  },
};

export class TokexClock {
  constructor(state, env) {
    this.state = state;
    this.env = env;
  }

  async fetch(request) {
    const url = new URL(request.url);
    const data = (await this.state.storage.get("tally")) || {
      saved_tokex: 0,
      total_tokex: 0,
      contributions: 0,
      nodes: {},
      updated_ts: null,
    };

    if (url.pathname.endsWith("/clock")) {
      const nodes = Object.keys(data.nodes || {}).length;
      const saved = Number(data.saved_tokex || 0);
      const total = Number(data.total_tokex || 0);
      const pct = total > 0 ? Math.round((saved / total) * 10000) / 100 : 0;
      return json({
        clock: "Live World Counter Clock",
        agent: "Neoborg",
        saved_tokex: saved,
        total_tokex: total,
        saved_pct: pct,
        contributions: Number(data.contributions || 0),
        nodes,
        updated_ts: data.updated_ts,
      });
    }

    if (url.pathname.endsWith("/contribute") && request.method === "POST") {
      let body;
      try {
        body = await request.json();
      } catch {
        return json({ ok: false, error: "invalid json" }, 400);
      }
      const saved = Number(body.saved_tokex);
      const total = Number(body.total_tokex);
      const nodeId = String(body.node_id || "").slice(0, 64);
      if (!nodeId || !Number.isFinite(saved) || !Number.isFinite(total)) {
        return json({ ok: false, error: "need node_id, saved_tokex, total_tokex" }, 400);
      }
      if (saved < 0 || total < 0 || (total > 0 && saved > total)) {
        return json({ ok: false, error: "impossible tokex relationship" }, 400);
      }
      // Dedupe rapid identical posts from same node within 2s window is optional;
      // every accepted vetted contribution adds to the permanent tally.
      data.saved_tokex = Number(data.saved_tokex || 0) + Math.floor(saved);
      data.total_tokex = Number(data.total_tokex || 0) + Math.floor(total);
      data.contributions = Number(data.contributions || 0) + 1;
      data.nodes = data.nodes || {};
      data.nodes[nodeId] = {
        last_ts: Date.now() / 1000,
        last_saved: Math.floor(saved),
      };
      data.updated_ts = Date.now() / 1000;
      await this.state.storage.put("tally", data);
      const nodes = Object.keys(data.nodes).length;
      const pct =
        data.total_tokex > 0
          ? Math.round((data.saved_tokex / data.total_tokex) * 10000) / 100
          : 0;
      return json({
        ok: true,
        clock: "Live World Counter Clock",
        saved_tokex: data.saved_tokex,
        total_tokex: data.total_tokex,
        saved_pct: pct,
        contributions: data.contributions,
        nodes,
        updated_ts: data.updated_ts,
      });
    }

    return json({ ok: false, error: "not found" }, 404);
  }
}

function cors() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "access-control-allow-headers": "content-type",
  };
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json", ...cors() },
  });
}
