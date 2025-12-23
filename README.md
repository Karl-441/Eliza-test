# Eliza AI Assistant

A powerful, local AI assistant with a tactical interface, inspired by *Girls' Frontline*. Designed for privacy and modularity, Eliza runs entirely on your local machine (or distributed across a local network).

## ✨ Key Features

### 🧠 Core Intelligence
- **Local LLM**: Runs quantized GGUF models (e.g., Llama 3, Qwen) locally using `llama-cpp-python`.
- **Memory System**: Context-aware conversation history with short-term memory management.
- **Smart Search**: Analyzes user intent and performs DuckDuckGo web searches when necessary to provide up-to-date information.

### 🗣️ Voice & Audio
- **TTS (Text-to-Speech)**: Integrated **GPT-SoVITS** for high-quality, emotive voice synthesis.
- **ASR (Speech-to-Text)**: Uses **Faster-Whisper** for fast and accurate voice input.

### 👁️ Vision
- **Computer Vision**: Integrated **YOLO** for real-time object detection and scene analysis.
- **Image Analysis**: Capable of analyzing uploaded images or screen content.

### 🖥️ Architecture & UI
- **Client-Server**:
  - **Server**: FastAPI-based backend handling LLM inference, TTS generation, and search.
  - **Client**: PyQt5-based desktop application with a futuristic, tactical UI.
- **Dashboard**: Web-based dashboard for server monitoring and configuration.

---

## 💻 System Requirements

- **OS**: Windows 10/11 (64-bit) recommended.
- **Python**: Version 3.10 or higher.
- **GPU**: NVIDIA GPU with CUDA support recommended for optimal performance (LLM & TTS).
  - *Can run on CPU, but inference will be slower.*
- **RAM**: 16GB recommended (8GB minimum).
- **Disk**: ~10GB+ free space (depending on models downloaded).

---

## 🚀 Installation

### 1. Prerequisites
Ensure you have Python 3.10+ installed and added to your PATH.

### 2. Automatic Setup
Run the installation script to create a virtual environment and install dependencies:
```batch
install.bat
```

### 3. Model Setup
Eliza requires external models to function.
1.  **LLM**: Download a GGUF model (e.g., [Qwen1.5-7B-Chat-GGUF](https://huggingface.co/Qwen/Qwen1.5-7B-Chat-GGUF)) and place it in `models/llm/`.
2.  **Update Config**: Edit `server/core/config.py` or the generated `config/settings.json` to match your model filename.

---

## 🎮 Usage

### 1. Start the Server
Launch the backend services:
```batch
run_server.bat
```
- This starts the Main API (FastAPI) and the TTS Module.
- Wait for the "Application startup complete" message.

### 2. Start the Client
Launch the desktop interface:
```batch
run_client.bat
```
- The tactical interface will appear.
- Connects to `localhost` by default.

### 3. Web Dashboard
Monitor the server status and configure settings via the browser:
- URL: `http://localhost:8000/dashboard`

---

## 📂 Project Structure

```
Eliza-test/
├── client/             # PyQt5 Desktop Application
│   ├── assets/         # Images and UI resources
│   └── ui/             # UI Components
├── server/             # FastAPI Backend
│   ├── core/           # LLM, Memory, Search logic
│   ├── routers/        # API Endpoints (Chat, Audio, Vision)
│   └── Models/
│       └── TTS/        # GPT-SoVITS Integration
├── data/               # User profiles and persistent data
├── models/             # Directory for GGUF and ASR models
└── run_*.bat           # Launcher scripts
```

## 🛠️ Configuration

- **Client Settings**: Accessible via the "Settings" button in the client UI.
- **Server Settings**:
  - `server/core/config.py`: Default configurations.
  - `config/settings.json`: Runtime overrides.
