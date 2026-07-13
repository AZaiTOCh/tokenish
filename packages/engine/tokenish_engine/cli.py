from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
import webbrowser

import uvicorn

from tokenish_engine import __version__
from tokenish_engine.settings_store import apply_saved_keys_to_environ, tokenish_home

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8741


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tokenish", description="tokenish local optimizer daemon")
    sub = parser.add_subparsers(dest="cmd")
    serve = sub.add_parser("serve", help="start the local daemon")
    serve.add_argument("--no-browser", action="store_true")
    serve.add_argument("--host", default=DEFAULT_HOST)
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    sub.add_parser("doctor", help="check keys, home, and port")
    sub.add_parser("version", help="print version")
    sub.add_parser("stop", help="how to stop the daemon")
    return parser


def port_open(host: str, port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


def cmd_doctor() -> int:
    apply_saved_keys_to_environ()
    print(f"tokenish {__version__}")
    print(f"home: {tokenish_home()}")
    print(f"openai key: {'yes' if os.getenv('GPT_TOKENISH') or os.getenv('OPENAI_API_KEY') else 'no'}")
    print(f"gemini key: {'yes' if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') else 'no'}")
    print(f"openrouter key: {'yes' if os.getenv('OPENROUTER_API_KEY') else 'no'}")
    print(f"port {DEFAULT_PORT}: {'in use' if port_open(DEFAULT_HOST, DEFAULT_PORT) else 'free'}")
    return 0


def cmd_serve(*, open_browser: bool = True, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> int:
    apply_saved_keys_to_environ()
    if open_browser:
        def _open() -> None:
            for _ in range(50):
                if port_open(host, port):
                    webbrowser.open(f"http://{host}:{port}/")
                    return
                time.sleep(0.1)

        threading.Thread(target=_open, daemon=True).start()
    print(f"tokenish listening on http://{host}:{port}/")
    uvicorn.run("tokenish_engine.app:app", host=host, port=port, reload=False)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return cmd_serve(open_browser=True)

    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = args.cmd or "serve"

    if cmd == "version":
        print(__version__)
        return 0
    if cmd == "doctor":
        return cmd_doctor()
    if cmd == "stop":
        print("Stop the process from the terminal (Ctrl+C) or Task Manager.")
        return 0
    return cmd_serve(
        open_browser=not getattr(args, "no_browser", False),
        host=getattr(args, "host", DEFAULT_HOST),
        port=getattr(args, "port", DEFAULT_PORT),
    )


if __name__ == "__main__":
    raise SystemExit(main())
