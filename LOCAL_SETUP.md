# Running Friday Locally - Complete Setup Guide

This guide walks you through setting up and running Friday on your local machine, including Ollama integration for local LLM inference.

---

## Prerequisites

- **Python 3.12+**
- **Linux, macOS, or Windows**
- **~4GB RAM** (minimum)
- **~2GB disk space** for dependencies and Ollama models

---

## Step 1: Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/utkarshjain1338-hub/Friday.git
cd Friday

# Create virtual environment
python3 -m venv venv

# Activate environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

---

## Step 2: Install Friday Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Optional but recommended: Install rich for better HUD display
pip install rich
```

**Installed packages:**
- `loguru` — Structured logging
- `numpy`, `sounddevice` — Audio processing
- `psutil` — System monitoring
- `pyautogui`, `keyboard` — Automation
- `pyyaml`, `requests` — Configuration and HTTP

---

## Step 3: Install Ollama (Local LLM)

### 3a. Install Ollama Binary

#### On Linux:
```bash
# Download and install
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

#### On macOS:
```bash
# Download from: https://ollama.ai/download/Ollama-darwin.zip
# Or use Homebrew:
brew install ollama

# Verify
ollama --version
```

#### On Windows:
```powershell
# Download installer from: https://ollama.ai/download/OllamaSetup.exe
# Run the installer, then verify:
ollama --version
```

### 3b. Start Ollama Server

Ollama runs as a server. Start it in a **separate terminal**:

```bash
# Start Ollama server (listens on http://localhost:11434)
ollama serve
```

**Output should show:**
```
time=2024-01-15T10:00:00.000Z level=INFO source=main.go:104 msg="Listening on 127.0.0.1:11434"
```

Keep this terminal open while using Friday.

### 3c. Download a Model

In **another terminal**, download a model:

```bash
# Activate venv if needed
source venv/bin/activate

# Download a small, fast model (recommended for local use)
ollama pull mistral        # 4.1GB, fast, good quality
# OR
ollama pull neural-chat    # 5.8GB, optimized for chat
# OR (smallest)
ollama pull tinyllama      # 1.1GB, very fast but lower quality

# List available models
ollama list
```

**Recommended models for local use:**
- `tinyllama` — Smallest, fastest (1.1GB)
- `mistral` — Good balance (4.1GB)
- `neural-chat` — Better conversation (5.8GB)

---

## Step 4: Configure Friday for Ollama

### 4a. Check Current Configuration

```bash
cat config/friday_config.yaml
```

### 4b. Update Configuration (if needed)

Edit `config/friday_config.yaml`:

```yaml
# ... existing config ...

ollama:
  enabled: true
  binary: "ollama"           # Use system ollama
  model: "mistral"           # Or your chosen model
  base_url: "http://localhost:11434"  # Ollama server URL
  timeout: 30
```

Or set environment variables:

```bash
export OLLAMA_MODEL=mistral
export OLLAMA_URL=http://localhost:11434
```

---

## Step 5: Run Friday Locally

### 5a. Quick Test (Recommended First)

```bash
# Activate venv
source venv/bin/activate

# Run the example showing all components
python examples/quickstart.py
```

**Expected output:**
```
2024-01-15 10:05:32 | INFO     | Starting Friday Assistant Example
2024-01-15 10:05:32 | INFO     | All components initialized
2024-01-15 10:05:32 | INFO     | === Iteration 1 ===
2024-01-15 10:05:32 | INFO     | Waiting for wake word or user input...
2024-01-15 10:05:33 | INFO     | Transcribed: 'hello'
2024-01-15 10:05:34 | INFO     | Processing request...
...
```

### 5b. Run Full Assistant (CLI Mode)

```bash
# Activate venv
source venv/bin/activate

# Run interactive CLI
python main.py
```

**Use commands:**
```
> help                    # Show all commands
> tell me a joke          # Get response from Ollama
> what time is it         # System info
> remember my favorite food is pizza    # Save to memory
> show memory             # Retrieve memories
> exit                    # Quit
```

### 5c. Run with Voice (if available)

```bash
# Requires: sounddevice, whisper.cpp (optional but recommended)
python main.py --voice
```

**Voice mode features (if binaries available):**
- Say "Friday" to activate
- Automatic speech-to-text with whisper.cpp
- Voice responses with piper TTS
- Real-time listening

---

## Step 6: Monitor with Dashboard

In a **third terminal**, watch the real-time dashboard:

```bash
# Activate venv
source venv/bin/activate

# Run the dashboard (updates every 1 second)
python -c "
import asyncio
from core.assistant_state import get_state_manager
from core.diagnostics import get_diagnostics
from ui.hud import SimpleDashboard

async def main():
    state = await get_state_manager()
    diag = await get_diagnostics()
    hud = SimpleDashboard()
    await hud.start(state, diag)

asyncio.run(main())
"
```

---

## Local Setup Architecture

```
Terminal 1: Ollama Server       Terminal 2: Friday CLI         Terminal 3: Dashboard
┌──────────────────────┐       ┌──────────────────────┐       ┌─────────────────────┐
│ $ ollama serve       │       │ $ python main.py     │       │ $ python -c "..."   │
│                      │       │                      │       │                     │
│ Listening on:11434   │───→   │ > tell me a joke     │───→   │ Mode: PROCESSING    │
│                      │       │                      │       │ Listening: ✓        │
│ Model: mistral       │       │ (waiting for response)│       │ Uptime: 2m 15s     │
│ Ready...             │       │                      │       │ Errors: 0          │
└──────────────────────┘       └──────────────────────┘       └─────────────────────┘
         ↑                             ↓
         │                      Uses context_manager
         │                      + ollama_client to fetch
         │                      responses
         └──────────────────────────────┘
         
         All communication via HTTP on localhost:11434
```

---

## Complete Local Workflow Example

**Terminal 1 - Start Ollama:**
```bash
ollama serve
# Output: Listening on 127.0.0.1:11434
```

**Terminal 2 - Download Model (one-time):**
```bash
source venv/bin/activate
ollama pull mistral
# Takes 2-5 minutes depending on internet speed
```

**Terminal 3 - Start Friday:**
```bash
cd /workspaces/Friday
source venv/bin/activate
python main.py
```

**Terminal 3 - Interact:**
```
> tell me a joke
[Friday fetches from Ollama, shows response]

> what is the capital of france
[Gets response from local mistral model]

> remember i like python programming
[Saved to local database]

> show memory
[Lists all remembered items]
```

**Terminal 4 (Optional) - Monitor:**
```bash
source venv/bin/activate
python -c "
import asyncio
from core.assistant_state import get_state_manager
from core.diagnostics import get_diagnostics
from ui.hud import SimpleDashboard

async def main():
    state = await get_state_manager()
    diag = await get_diagnostics()
    hud = SimpleDashboard()
    await hud.start(state, diag)

asyncio.run(main())
"
```

---

## Troubleshooting

### Issue: "ollama: command not found"

**Solution:** Ollama not on PATH.

```bash
# Verify installation
which ollama

# If not found, add to PATH:
export PATH="/Applications/Ollama.app/Contents/Bin:$PATH"  # macOS
# Or check your Ollama installation directory
```

### Issue: "Connection refused" when Friday tries to contact Ollama

**Solution:** Ollama server not running.

```bash
# In Terminal 1, start Ollama:
ollama serve

# Verify it's listening:
curl http://localhost:11434/api/tags
```

### Issue: Model loading is slow

**Solution:** First model load takes time.

```bash
# First time: be patient (2-10 minutes depending on model size)
ollama pull mistral

# Second time: cached, instant
ollama pull mistral
```

### Issue: Out of memory error

**Solution:** Use a smaller model.

```bash
ollama pull tinyllama  # 1.1GB, much faster

# Or limit Ollama memory in config
OLLAMA_NUM_GPU=0  # Disable GPU, use CPU only (slower but safer)
```

### Issue: Friday hangs when calling Ollama

**Solution:** Increase timeout in config or check Ollama server:

```bash
# Check if Ollama is still running:
curl -s http://localhost:11434/api/tags | python -m json.tool

# If no response, restart Ollama:
pkill ollama
ollama serve
```

---

## Advanced: Using Different Models

### Switch Models Dynamically

```python
# In Python/main.py:
from brain.ollama_client import OllamaClient

client = OllamaClient(model="neural-chat")  # Switch to neural-chat

response = await client.generate("Hello, how are you?")
```

### Model Comparison (Local Performance)

| Model | Size | Speed | Quality | RAM Needed |
|-------|------|-------|---------|-----------|
| tinyllama | 1.1GB | Very Fast | Lower | 2GB |
| mistral | 4.1GB | Fast | Good | 6GB |
| neural-chat | 5.8GB | Medium | Very Good | 8GB |
| llama2 | 3.8GB | Medium | Good | 6GB |

**Recommendation:** Start with `mistral` for best balance.

---

## Performance Tuning

### Enable GPU Acceleration (if available)

```bash
# For NVIDIA GPUs:
export CUDA_VISIBLE_DEVICES=0
ollama serve

# For Metal (macOS):
# Automatic on Apple Silicon Macs
```

### Adjust Response Timeout

```bash
# In config/friday_config.yaml:
ollama:
  timeout: 60  # Increase for slower systems
```

### Reduce Model Size for Speed

```bash
# Use tinyllama instead of mistral
ollama pull tinyllama
export OLLAMA_MODEL=tinyllama
```

---

## Running Tests

```bash
# Test the audio pipeline
python -m pytest tests/test_plugins.py -v

# Test the main router
python -m pytest tests/test_router_async.py -v

# Run all tests
python -m pytest tests/ -v
```

---

## File Structure for Local Setup

```
Friday/
├── main.py                    ← Start here
├── requirements.txt           ← Dependencies
├── config/
│   └── friday_config.yaml     ← Ollama config
├── brain/
│   ├── ollama_client.py       ← Ollama integration
│   ├── context_manager.py     ← Context for LLM
│   └── ...
├── voice/
│   ├── streaming_transcriber.py
│   ├── speech_queue.py
│   └── ...
├── skills/
│   ├── skill_executor.py
│   └── plugins/
├── examples/
│   └── quickstart.py          ← Complete example
├── logs/                      ← Auto-created
│   ├── friday.log             ← All activity
│   └── errors.log             ← Errors only
└── memory.db                  ← Local SQLite DB
```

---

## Next Steps

1. **Complete Setup:**
   ```bash
   source venv/bin/activate && python examples/quickstart.py
   ```

2. **Test with CLI:**
   ```bash
   python main.py
   ```

3. **Create Custom Skills:**
   - Add plugins to `skills/plugins/`
   - See `skills/plugins/vscode_skill.py` for template

4. **Add Voice (Optional):**
   ```bash
   # Install whisper.cpp for STT
   # Install piper for TTS
   python main.py --voice
   ```

5. **Deploy as Service (Optional):**
   ```bash
   sudo systemctl start friday  # Requires systemd config
   ```

---

## Useful Commands

```bash
# Check Ollama models
ollama list

# Pull a model
ollama pull mistral

# Remove a model to save space
ollama rm mistral

# Run Friday in debug mode
RUST_LOG=debug python main.py

# Monitor Ollama performance
watch -n 1 curl -s http://localhost:11434/api/ps | python -m json.tool

# View Friday logs
tail -f logs/friday.log

# Clear memory database
rm memory.db  # Will be recreated on next run
```

---

**You're ready to run Friday locally!** 🚀

Start with Step 1 above and you'll have a fully functional local assistant with Ollama in ~10 minutes.
