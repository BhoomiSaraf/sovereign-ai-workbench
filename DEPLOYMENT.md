# Sovereign AI Workbench — Deployment Guide

**Project:** SIH 2026 — Problem Statement SIH26117  
**Classification:** Internal / Demo  
**Architecture:** Single-machine, fully air-gapped, no cloud dependencies

---

## Section 1 — Prerequisites

Install every dependency listed below on the demo machine **while it still has internet access**. After this section is complete the machine can be taken offline permanently.

### 1.1 Python 3.13

Download the official installer from [python.org](https://www.python.org/downloads/).

```bash
python --version   # must print 3.13.x
```

Ensure `pip` and `venv` are available:

```bash
pip --version
python -m venv --help
```

### 1.2 Node.js 20 LTS (for the React frontend)

Download from [nodejs.org](https://nodejs.org/en/download).

```bash
node --version    # must print v20.x.x
npm --version
```

### 1.3 Docker Desktop

Download from [docker.com](https://www.docker.com/products/docker-desktop/).  
Start Docker Desktop and confirm the daemon is running:

```bash
docker info
```

Pull the sandbox image while online — it is needed for isolated Python execution:

```bash
docker pull python:3.13-slim
```

### 1.4 Ollama

Download from [ollama.com](https://ollama.com/download).  
After install, verify the daemon starts automatically:

```bash
ollama --version
curl http://127.0.0.1:11434/api/tags
```

### 1.5 Tesseract OCR

**Windows:**
Download the installer from the [UB Mannheim builds](https://github.com/UB-Mannheim/tesseract/wiki) and add the install directory to `PATH`.

**Linux/macOS:**

```bash
# Ubuntu / Debian
sudo apt-get install -y tesseract-ocr

# macOS
brew install tesseract
```

Verify:

```bash
tesseract --version   # must print 5.x.x
```

---

## Section 2 — Network Enforcement (Air-Gap Procedure)

The application's `NetworkMonitor` tracks sovereignty metrics and blocks
non-loopback connections **at the application level**. For a fully certified
air-gap, OS-level enforcement is mandatory in addition to the software guard.

### 2.1 Physical isolation (preferred for demo)

1. **Disconnect the ethernet cable** from the machine.
2. **Disable all Wi-Fi adapters** in the OS network settings.
3. **Disable Bluetooth** if the machine has a BT network adapter.

Verify no external route exists:

```bash
# Windows PowerShell
Test-NetConnection -ComputerName 8.8.8.8 -Port 80   # must time out

# Linux / macOS
curl --max-time 3 https://google.com   # must fail
```

### 2.2 Docker network isolation

The `PythonSandbox` already passes `--network none` to every container it
launches. Confirm this default is active:

```bash
grep SANDBOX_NETWORK_MODE .env   # should print: SANDBOX_NETWORK_MODE=none
```

Never change this to `bridge` or `host` on a demo machine.

### 2.3 Windows Firewall (defence-in-depth)

Create outbound block rules for the `python.exe` and `uvicorn.exe` processes
in Windows Defender Firewall with Advanced Security to prevent any library
from opening an outbound socket, even if the application guard is somehow
bypassed.

### 2.4 Sovereignty verification at runtime

After startup, call the health endpoint to confirm the live sovereignty proof:

```bash
curl http://127.0.0.1:8000/system/health
```

The response must show:

```json
{
  "components": {
    "network": {
      "internet_access": "BLOCKED",
      "status": "AIR-GAPPED",
      "sovereignty_verified": true,
      "external_calls": 0
    }
  }
}
```

---

## Section 3 — Model Provisioning

Run all `ollama pull` commands **before** going offline. Ollama stores models
in `~/.ollama/models`; no internet access is required once they are cached.

### 3.1 Pull all required models

```bash
# Primary reasoning model (~2.6 GB)
ollama pull qwen3:4b

# Code generation model (~4.7 GB)
ollama pull qwen2.5-coder:7b

# Vision / multimodal model (~2.1 GB)
ollama pull qwen2.5vl:3b
```

> **Note on deepseek-r1:1.5b** — if the demo machine has less than 8 GB
> VRAM, substitute the smaller DeepSeek model for reasoning tasks:
>
> ```bash
> ollama pull deepseek-r1:1.5b   # ~1.1 GB, fits on 4 GB VRAM
> ```
>
> Update `MAIN_MODEL=deepseek-r1:1.5b` in `.env` accordingly.

### 3.2 Verify models are locally cached

```bash
ollama list
```

Expected output (sizes approximate):

```
NAME                    ID              SIZE    MODIFIED
qwen3:4b                ...             2.6 GB  ...
qwen2.5-coder:7b        ...             4.7 GB  ...
qwen2.5vl:3b            ...             2.1 GB  ...
```

### 3.3 BGE-M3 embedding model

The RAG pipeline uses `BAAI/bge-m3` via `sentence-transformers`.
It is downloaded automatically by the HuggingFace hub the first time the
application runs. Pre-cache it explicitly while online:

```python
# Run once before going offline
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
```

After the download completes, set the offline guards (already defaults in
`.env.example`):

```bash
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

---

## Section 4 — Startup Sequence

Follow these steps in order on every fresh boot of the demo machine.

### 4.1 Clone / copy the project

```bash
git clone <repo-url> sovereign-ai-workbench
cd sovereign-ai-workbench
```

Or copy the folder from a USB drive if the machine is already offline.

### 4.2 Configure environment

```bash
cp .env.example .env
# Edit .env only if you need to override a default (e.g., a different model name)
```

### 4.3 Build the React frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

The compiled assets land in `frontend/dist/`. The FastAPI server serves them
statically — no separate Node.js process is needed at runtime.

### 4.4 Create and activate a Python virtual environment

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

### 4.5 Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4.6 Seed the knowledge base (first run only)

```bash
python scripts/seed_kb.py
```

Expected output:

```
Seeding local organizational knowledge base...
Wrote data/knowledge_base/MRPL_Maintenance_SOP.md
Wrote data/knowledge_base/Delegation_of_Power_2026.md
Wrote data/knowledge_base/Safety_Protocol_Hazardous_Leaks.md
Wrote data/knowledge_base/Past_Inspection_Report_Valve_A4.md
Ingesting MRPL_Maintenance_SOP.md ...  N chunks
...
Seed complete.
```

### 4.7 Start Ollama

```bash
ollama serve
```

Leave this running in a separate terminal. Confirm it is ready:

```bash
curl http://127.0.0.1:11434/api/tags
```

### 4.8 Start the backend server

```bash
uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

For production-grade stability (multiple worker processes), use:

```bash
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --workers 2
```

> **Do not** bind to `0.0.0.0` on a demo machine unless the Wi-Fi adapter
> is physically removed or the firewall blocks port 8000 externally.

### 4.9 Verify full system health

```bash
curl http://127.0.0.1:8000/system/health
```

All `"ok": true` entries confirm the system is ready. The UI is accessible
at **http://127.0.0.1:8000**.

---

## Quick-Reference Checklist

| Step | Command | Expected result |
|---|---|---|
| Python version | `python --version` | `3.13.x` |
| Node version | `node --version` | `v20.x.x` |
| Docker daemon | `docker info` | no error |
| Ollama daemon | `curl localhost:11434/api/tags` | JSON with model list |
| Tesseract | `tesseract --version` | `5.x.x` |
| No internet | `curl --max-time 3 https://google.com` | timeout / fail |
| Backend health | `curl localhost:8000/system/health` | `"healthy": true` |
| Sovereignty proof | (same response) | `"sovereignty_verified": true` |

---

## Troubleshooting

**`curl: (7) Failed to connect to 127.0.0.1 port 11434`**  
Ollama is not running. Execute `ollama serve` in a separate terminal.

**`FileNotFoundError: Local embedding model not found: BAAI/bge-m3`**  
The HuggingFace cache is missing. Run the pre-cache command in Section 3.3
while temporarily online, then re-enable `HF_HUB_OFFLINE=1`.

**`docker: command not found`**  
Docker Desktop is not installed or not added to `PATH`. Re-run the Docker
Desktop installer and restart the terminal.

**`tesseract: command not found`**  
Tesseract install directory is not in `PATH`. Add it via System Properties →
Environment Variables on Windows, or re-run the package manager install on
Linux/macOS.

**Frontend shows blank page**  
The `frontend/dist` directory is missing. Run `npm install && npm run build`
inside the `frontend/` directory and restart the backend server.
