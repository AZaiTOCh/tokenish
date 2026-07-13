# Download tokenish

UX modeled on [Ollama’s download page](https://ollama.com/download): one install path, then you’re chatting.

## pip (ready now)

```bash
pip install tokenish
tokenish
```

Then open **http://127.0.0.1:8741/** if the browser does not auto-open.

```bash
tokenish doctor
```

## Windows exe

Build locally (release assets can be attached to GitHub Releases as `tokenish-windows.zip`):

```powershell
cd packages/engine
.\packaging\build_windows.ps1
```

Run:

```text
dist\tokenish\tokenish.exe
```

Keys persist under `%USERPROFILE%\.tokenish\`.

## macOS / Linux

```bash
pip install tokenish
tokenish
```

(Shell installer `curl | sh` can be added when a hosted install script exists.)

## what you get

1. Local optimizer daemon  
2. Chat UI with TOKEX (before / after / saved)  
3. Automatic instruction thinning, tabular format rewrite, ITS gate, conditional pxpipe  
4. Provider fallback (ChatGPT → Gemini → OpenRouter)
