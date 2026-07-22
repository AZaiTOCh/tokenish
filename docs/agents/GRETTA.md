# Gretta

**Role:** Onboarding host + LLM **protoprompter / qualifier / router** via curated capability map among **linked** APIs (not scrape-as-truth). Also **material suitability gate**: after API setup, nudge upload; after upload (or need text), say yes/no if Tokenish would risk fidelity loss.

**Code:** `packages/engine/tokenish_engine/agents/gretta.py`  
**API:** `POST /gretta/recommend`  
**UI:** post-API thank-you → upload CTA; sidebar ask; upload inspect heuristics in `static/app.js`

**Owns:** splash/API explainer/need modal + sidebar ask recommend + fidelity suitability notes.  
**Must not:** invent “best model” from live web scrapes; silently run lossy cylinders on legal/scientific/mission-critical corpora.

**Incepted:** v0.4.1 · Chatbox follow-ups parked (light/medium/heavy phases) · Suitability gate v0.4.5
