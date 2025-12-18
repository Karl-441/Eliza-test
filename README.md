# Eliza AI Assistant

A powerful, local AI assistant with Girls' Frontline aesthetic.

## Features
- **Local LLM**: Run quantized models (GGUF) locally on CPU.
- **Memory**: Remembers conversation history and user preferences.
- **Search**: Integrated web search (DuckDuckGo).
- **Voice**: ASR (Speech-to-Text) and TTS (Text-to-Speech) support.
- **UI**: Tactical interface built with PyQt5.
- **Modular**: Client-Server architecture (deploy server on NAS, client on PC).

## System Requirements

- **OS**: Windows 10/11 (64-bit)
- **CPU**: AVX2 support recommended for LLM
- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 10GB free space

## Installation

### Server Setup (Python)
1. **Prerequisites**:
   - Python 3.10+ installed.

2. **Installation**:
   ```bash
   cd server
   pip install -r requirements.txt
   ```

3. **Start Server**:
   Double-click `run_server.bat` in the root directory.

### Client Setup (PyQt5)
1. **Prerequisites**:
   - Python 3.10+
   - Visual C++ Redistributable (Windows)

2. **Installation**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Build & Run**:
   ```bash
   # Run directly
   run_client.bat
   
   # Build Executable (Windows Only)
   pyinstaller client.spec
   ```

4. **Deployment**:
   - Copy the `dist/ElizaClient.exe` and `client/assets/` folder to target machine.


## Usage

1. **Start Server**:
   Double-click `run_server.bat`.
   Wait for "Model loaded" message.

2. **Start Client**:
   Double-click `run_client.bat`.
   The tactical interface will launch.

## Configuration
- Edit `config/settings.json` (created after first run) or `server/core/config.py` to change parameters like `n_ctx`, `temperature`, etc.

## Project Structure
- `client/`: PyQt5 Desktop Application.
- `server/`: FastAPI Backend.
- `models/`: Store your GGUF models here.
- `data/`: Stores chat history and user profile.

## Server Dashboard Guide

The server comes with a built-in web dashboard for monitoring and management.

### 1. Start Dashboard
Run the following command in the `server` directory:
```bash
# Using npm
npm run dashboard

# Using yarn
yarn dashboard
```
*Note: This command starts the main server process.*

### 2. Access
Open your browser and visit:
```
http://localhost:8000/dashboard
```
*(Replace `8000` with your configured port if different)*

### 3. Requirements
- **Node.js**: Version 14.x or higher (for running npm scripts).
- **Python**: 3.10+ (Server runtime).
- **Dependencies**: Ensure `npm install` and `pip install -r requirements.txt` are completed.

### 4. Features
- **System Status**: Monitor server uptime and resource usage.
- **Log Viewer**: View real-time server logs and activity.
- **Configuration**: View current server settings.
- **API Status**: Check the health of API endpoints.

### 5. FAQ
- **Q: Dashboard shows 404?**
  - A: Ensure the server is running and you are visiting `/dashboard`.
- **Q: npm command not found?**
  - A: Install Node.js or run `python app.py` directly.

## UI Design System

### Client UI Simplification
The client interface has been streamlined to focus on functionality and usability, adopting a minimalist "Native" design approach.

### 1. Design Philosophy
- **Minimalist**: Removed non-essential visual decorations (effects, animations, shadows).
- **Native**: Uses standard system colors and widget styles.
- **Functional**: High contrast and clear layout for better accessibility.

### 2. Core Styles
- **Background**: Standard Window Background (White/Light Gray).
- **Text**: High contrast Black/Dark Gray.
- **Buttons**: Standard system push buttons with clear states.
- **Layout**: Clean grid-based structure without "Tactical" overlays.
