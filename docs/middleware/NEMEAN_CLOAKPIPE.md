# Peer note — CloakPipe × Nemean / vTOPU

**Date:** 2026-07-22  
**Peer:** [CloakPipe](https://github.com/rohansx/cloakpipe) (MIT OSS; Cloud dashboard is proprietary BUSL)  
**Owner class:** [Nemean](NEMEAN.md) Privacy Middleware — **not** a [vTOPU](../cylinders/CYLINDER_REGISTER.md) cylinder  
**Status:** Peer assessed · hold for Nemean full-force runtime · do not induct as OptComp virtual core

## One-line verdict

CloakPipe is a strong **substrate candidate for Nemean** (PII detect → mask → vault → unmask). It is **not** a TOKEX compressor and must **not** be registered as a new virtual core.

## What CloakPipe is

Rust-native local LLM privacy stack:

- Multi-layer PII detection (regex/checksums, financial heuristics, DistilBERT-PII ONNX, fuzzy entity resolution, custom rules)
- Session-consistent pseudonymization + AES-256-GCM vault + response rehydration
- Optional OpenAI-compatible HTTP proxy sidecar
- Policy packs: DPDP / GDPR / HIPAA / PCI-DSS
- Adjacent crates: CloakTree (vectorless retrieve), ADCPE (distance-preserving vector encryption), audit / ledger / verify

## Fit matrix

| Target | Fit | Notes |
|--------|-----|--------|
| **Nemean** | **High** | Same job class: privacy controls, masking, encryption on-device |
| **Mode C (Sovereign)** | Medium–High | Less critical for egress if fully local; still useful for logs, multi-user, audit |
| **Mode A (Azure-direct)** | High *if framed correctly* | On-device mask **before** direct Azure call — not a TOKISH cloud prompt proxy |
| **vTOPU / OptComp cylinders** | **Low / wrong category** | Masks rarely shrink TOKEX; often flat or longer (`PERSON_042`) |
| **New virtual core** | **No** | Belongs under middleware, never cylinder #N |
| **CloakTree** | Secondary | Privacy-first retrieve — peer to Chump / ITS / Memtrove stories, not OptComp |
| **ADCPE** | Secondary | Only if remote embedding / Memtrove path ships |
| **CloakPipe Cloud / BUSL** | **Out of scope** | Use MIT OSS only |

## Product tension (must keep)

Nemean marketing: *zero TOKISH prompt proxy* · Mode A = device → Azure region.

CloakPipe’s default product shape *is* a proxy. For TOKISH:

- Allowed: **local** CloakPipe (or `cloakpipe-core` logic) as **device-side** Nemean stage
- Forbidden: TOKISH SaaS sitting mid-prompt as the privacy hop
- Prefer library / in-process or localhost sidecar; never rebrand their cloud as Nemean

## Recommended build path (when Nemean goes full-force)

1. **Primary:** Optional Nemean stage — local binary *or* Python reimplementation of regex + vault + rehydrate; ONNX NER opt-in
2. **Reuse first:** `cloakpipe-core` ideas (detect / replace / vault / rehydrator) and policy TOMLs — not the whole monorepo by default
3. **Secondary:** Study CloakTree only when revisiting Chump / ITS privacy-preserving retrieve
4. **Never:** Attribute CloakPipe work to SAVED_TOKEX / cylinder scoreboard

## Licensing

- OSS repo: **MIT** — usable with attribution
- Cloud dashboard / enterprise: **BUSL** — do not vendor

## Related

- [Nemean](NEMEAN.md)
- [Middleware index](README.md)
- [vTOPU register](../cylinders/CYLINDER_REGISTER.md) — CloakPipe listed under rejected-as-cylinder / middleware peers
