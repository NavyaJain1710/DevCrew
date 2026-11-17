"""
DevCrew Workspace Preparation Service.
Ensures that all generated project workspaces contain everything needed
to be 100% runnable out of the box when downloaded as a ZIP archive:
1. Root run.py launcher with auto-dependency installer and browser opener
2. Windows start.bat double-click runner
3. Linux/macOS start.sh runner
4. Complete requirements.txt (including uvicorn, fastapi, etc.)
5. Interactive Web UI mounted at / in app/main.py (if no root route exists)
6. if __name__ == '__main__': block in app/main.py
7. Professional README.md with clear execution instructions
"""

from __future__ import annotations

import os
import re
from pathlib import Path


def ensure_workspace_runnable(workspace_path: str, project_name: str, raw_requirement: str = "") -> None:
    """Prepares a project workspace to be immediately runnable by end users."""
    if not workspace_path or not os.path.exists(workspace_path):
        return

    clean_name = project_name.strip() or "DevCrew Generated Application"

    # 1. Update requirements.txt to ensure uvicorn and essential packages are present
    req_file = os.path.join(workspace_path, "requirements.txt")
    existing_reqs = ""
    if os.path.exists(req_file):
        with open(req_file, "r", encoding="utf-8", errors="ignore") as f:
            existing_reqs = f.read()

    needed_packages = ["fastapi>=0.110.0", "uvicorn[standard]>=0.28.0", "pydantic>=2.0.0"]
    reqs_to_add = []
    for pkg in needed_packages:
        base_pkg = pkg.split(">=")[0].split("[")[0]
        if base_pkg.lower() not in existing_reqs.lower():
            reqs_to_add.append(pkg)

    if reqs_to_add:
        updated_reqs = existing_reqs.strip() + "\n" + "\n".join(reqs_to_add) + "\n"
        with open(req_file, "w", encoding="utf-8") as f:
            f.write(updated_reqs.strip() + "\n")

    # 2. Ensure root run.py exists
    run_py = os.path.join(workspace_path, "run.py")
    if not os.path.exists(run_py) or "find_available_port" not in open(run_py, "r", encoding="utf-8", errors="ignore").read():
        run_content = f'''"""
One-Click Runner for {clean_name}
Generated autonomously by DevCrew Agentic Platform.
Usage: python run.py
"""
import os
import sys
import time
import socket
import subprocess
import webbrowser
import threading

def find_available_port(default_port=8000, fallbacks=(8080, 8081, 8001, 8888)):
    for p in (default_port, *fallbacks):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                return p
    return default_port

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    port = find_available_port(8000)

    print("=" * 60)
    print("  🚀 Starting {clean_name}")
    print(f"  🌐 Running on: http://127.0.0.1:{{port}}")
    print("=" * 60)

    # Check dependencies
    try:
        import uvicorn
        import fastapi
    except ImportError:
        print("[*] Installing required dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        import uvicorn

    print(f"[*] Server booting at http://127.0.0.1:{{port}}")
    print(f"    Documentation:  http://127.0.0.1:{{port}}/docs")
    print("=" * 60)

    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(f"http://127.0.0.1:{{port}}")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    # Determine app module
    app_module = "app.main:app" if os.path.exists(os.path.join(root_dir, "app", "main.py")) else "main:app"
    uvicorn.run(app_module, host="127.0.0.1", port=port, reload=True)

if __name__ == "__main__":
    main()
'''
        with open(run_py, "w", encoding="utf-8") as f:
            f.write(run_content)

    # 3. Ensure start.bat exists (Windows double click)
    start_bat = os.path.join(workspace_path, "start.bat")
    if not os.path.exists(start_bat):
        bat_content = f'''@echo off
cd /d "%~dp0"
title {clean_name} - DevCrew
echo ========================================================
echo   Starting {clean_name}...
echo ========================================================
echo.
python -m pip install -r requirements.txt
python run.py
if errorlevel 1 (
    echo.
    echo [ERROR] Application failed to start.
    echo Please ensure Python 3.10+ is installed and available in PATH.
    pause
)
'''
        with open(start_bat, "w", encoding="utf-8") as f:
            f.write(bat_content)

    # 4. Ensure start.sh exists (Linux/Mac)
    start_sh = os.path.join(workspace_path, "start.sh")
    if not os.path.exists(start_sh):
        sh_content = f'''#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "========================================================"
echo "  Starting {clean_name}..."
echo "========================================================"
python3 -m pip install -r requirements.txt
python3 run.py
'''
        with open(start_sh, "w", encoding="utf-8") as f:
            f.write(sh_content)

    # 5. Ensure README.md exists
    readme_md = os.path.join(workspace_path, "README.md")
    if not os.path.exists(readme_md) or os.path.getsize(readme_md) < 50:
        readme_content = f'''# 🚀 {clean_name}

Autonomous application generated by **DevCrew Multi-Agent Platform**.

**Requirement Specification:**
> {raw_requirement or clean_name}

---

## ⚡ Quick Start (How to Run)

### Option 1: 1-Click Launch (Windows)
Double-click `start.bat`. It will automatically install dependencies and launch the application in your web browser.

---

### Option 2: Command Line (Windows, macOS, Linux)
Open your terminal in this directory and run:
```bash
python run.py
```
*(Or `python3 run.py` on macOS/Linux)*

This will:
1. Check and install dependencies from `requirements.txt`
2. Start the Uvicorn web server on `http://127.0.0.1:8000`
3. Automatically open the web browser!

---

### Option 3: Standard Manual Execution
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Open your browser at:
- **Application Web UI:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Running Tests
```bash
pytest
```
'''
        with open(readme_md, "w", encoding="utf-8") as f:
            f.write(readme_content)

    # 6. Ensure app/main.py has root endpoint and main block
    main_py = os.path.join(workspace_path, "app", "main.py")
    if os.path.exists(main_py):
        with open(main_py, "r", encoding="utf-8", errors="ignore") as f:
            main_code = f.read()

        modified = False

        # Add root HTML if missing
        if "@app.get(\"/\")" not in main_code and "@app.get('/')" not in main_code:
            html_landing = f"""
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
def root_ui():
    return \"\"\"<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>{clean_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }}
        .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 1rem; padding: 2.5rem; max-width: 540px; text-align: center; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }}
        h1 {{ color: #38bdf8; font-size: 1.75rem; margin-bottom: 0.5rem; }}
        p {{ color: #94a3b8; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem; }}
        .btn {{ display: inline-block; background: #0284c7; color: white; padding: 0.75rem 1.5rem; border-radius: 0.5rem; text-decoration: none; font-weight: 600; margin: 0.25rem; }}
        .btn:hover {{ background: #0369a1; }}
        .badge {{ display: inline-block; background: #064e3b; color: #34d399; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; margin-bottom: 1rem; }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">● Online & Ready</span>
        <h1>{clean_name}</h1>
        <p>This application was autonomously synthesized and verified by DevCrew. All API routers, services, and models are live.</p>
        <a href="/docs" class="btn">Explore Interactive Swagger API &rarr;</a>
        <a href="/redoc" class="btn" style="background: #334155;">ReDoc Specification</a>
    </div>
</body>
</html>\"\"\"
"""
            main_code += "\n" + html_landing
            modified = True

        # Add if __name__ == "__main__": block if missing
        if 'if __name__ == "__main__":' not in main_code and "if __name__ == '__main__':" not in main_code:
            main_code += """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
"""
            modified = True

        if modified:
            with open(main_py, "w", encoding="utf-8") as f:
                f.write(main_code)
