# vToPU Register (OptComp)

**vToPU** = [Virtual](https://www.ibm.com/docs/en/power8/9080-MHE?topic=processors-virtual) [Token Optimization](https://developer.ibm.com/articles/awb-token-optimization-backbone-of-effective-prompt-engineering/) [Processing Unit](https://medium.com/@ramu.mangalarapu1622/the-story-of-processing-units-understanding-the-brains-behind-modern-machines-39ebbdc83578).

A **tokopt cylinder** is one working stage (virtual core) inside **OptComp** / **vToPU**.

| # | Cylinders ([virtual cores](https://blog.coolicehost.com/what-is-virtual-core-and-how-does-it-differ-from-physical-core/)) | Type | Status | Since |
|---|----------|------|--------|-------|
| 1 | [ingest](INGEST.md) | *Ingestly* | ON w/ files | v0.1 |
| 2 | [LCS](LCS.md) | *Luxy* | ON | v0.1 |
| 3 | [split-exec / envelope](SPLIT_EXEC.md) | *Volpe* | ON w/ material | v0.1 |
| 4 | [Hi0](HI0.md) | *Highzero* | ON when JSON-ish | v0.2 |
| 5 | [dedupe](DEDUPE.md) | *Slimz* | ON when doc text | v0.2 |
| 6 | [format_csv](FORMAT_CSV.md) | *Forciv* | situational | v0.2 |
| 7 | [headroom](https://github.com/headroomlabs-ai/headroom) ([profile](HEADROOM.md)) | *Max* | ON (gated) | v0.2 |
| 8 | [ITS](ITS.md) | *Chunkdrop* | OFF (consent) | v0.2 |
| 9 | [FAISS / MIB](FAISS_MIB.md) | *Chump* | standby w/ ITS | v0.2 |
| 10 | [pxpipe](PXPIPE.md) | *Pixish* | OFF | v0.1–v0.2 |
| 11 | [tokenizer gate](TOKENIZER_GATE.md) | *Tokegater* | ON | v0.2 |
| 12 | [vision (Pillow)](VISION.md) | *Previsioner* | ON w/ images | v0.1 |
| 13 | [passthrough](PASSTHROUGH.md) | *Passopter* | ON when triggered | v0.1 |
| 14 | [ffmpeg / Clop media](FFMPEG.md) | *Fidelvid* | **ON** (disable with `enable_ffmpeg=false`) | v0.4.3 / ON v0.4.4 |
| 15 | [Memtrove](MEMTROVE.md) ([Moorcheh](https://github.com/moorcheh-ai)) | *Memtrove* | not in optimize path | probe v0.2 |

## Rejected / parked

| # | Item | Status |
|---|------|--------|
| 1 | [Alcubierre](REJECTED_ALCUBIERRE.md) | rejected |
| 2 | [Latents](PARKED_LATENTS.md) | parked |
| 3 | MicrOpt / UltraOpt / AtoOpt (whitespace·font atomism) | assess only — see peer notes |
| 4 | OKF (Google Open Knowledge Format) | park — knowledge catalog, not TOKEX compressor |
