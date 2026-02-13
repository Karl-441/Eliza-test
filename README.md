# Eliza AI Assistant

[中文](README.md) | [English](#english-version)

<div align="center">
  <img src="client/assets/griffin_logo.png" alt="Eliza Logo" width="200" />
  <h3>Tactical Local AI Assistant / 战术风格本地 AI 助手</h3>
  <p>Inspired by <i>Girls' Frontline</i> | 基于本地 LLM 与 GPT-SoVITS 构建</p>
</div>

---

## 📖 项目简介 (Introduction)

**Eliza** 是一个运行在本地的高级 AI 助手系统。

Eliza is a sophisticated, locally-hosted AI assistant.

## ✨ 核心特性 (Key Features)

### 🧠 智能核心 (Core Intelligence)
*   **本地大模型 (Local LLM)**: 基于 `llama-cpp-python` 运行量化 GGUF 模型 (如 Qwen, Llama 3)，数据完全私有化。
*   **三层记忆系统 (Three-Tier Memory)**: 
    *   **本能 (Instinct)**: 核心指令与人设。
    *   **潜意识 (Subconscious)**: 长期背景知识库。
    *   **主动回忆 (Active Recall)**: 基于向量检索的对话上下文记忆。
*   **记忆管理 (Memory Management)**: 可视化的记忆矩阵管理界面，支持查看和删除记忆片段。

### 🗣️ 语音交互 (Voice Interaction)
*   **TTS (语音合成)**: 集成 **GPT-SoVITS**，提供高质量、富有情感的语音输出。
*   **ASR (语音识别)**: 使用 **Faster-Whisper** 实现快速精准的语音指令输入。

### 🖥️ 交互体验 (User Experience)
*   **战术 UI (Tactical UI)**: 沉浸式赛博朋克风格界面，支持动态音效与视觉反馈。
*   **多智能体看板 (Multi-Agent Dashboard)**: 可视化 DAG 任务流，监控多 Agent 协作状态。
*   **实时监控 (Real-time Monitoring)**: 仪表盘实时显示系统资源与后台状态。

## 💻 系统要求 (System Requirements)

*   **OS**: Windows 10/11 (64-bit)
*   **Python**: 3.10+
*   **GPU**: 推荐 NVIDIA 显卡 (支持 CUDA) 以获得最佳 LLM 和 TTS 性能。
    *   *仅 CPU 模式下运行速度会受限。*
*   **RAM**: 推荐 16GB+ (取决于所选模型大小)。
*   **Disk**: 预留 10GB+ 空间用于存放模型文件。

## 🚀 快速开始 (Quick Start)

### 1. 安装 (Installation)

确保已安装 Python 3.10+，然后运行根目录下的安装脚本：

```batch
install.bat
```

此脚本会自动创建虚拟环境 (`venv`) 并安装所有必要的依赖项。

### 2. 模型准备 (Model Setup)

Eliza 需要外部模型文件才能运行：
1.  **LLM**: 下载 GGUF 格式模型 (例如 [Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF)) 并放入 `models/llm/` 目录。
2.  **Config**: 修改 `server/core/config.py` 中的 `model_path` 指向你的模型文件。

### 3. 启动 (Launch)

**步骤 1: 启动服务端**
运行以下脚本启动后端 API 和 TTS 服务：
```batch
start_server.bat
```
*等待控制台出现 "Application startup complete" 提示。*

**步骤 2: 启动客户端**
运行以下脚本打开战术终端界面：
```batch
start_client.bat
```

## 📂 项目结构 (Project Structure)

```text
Eliza-test/
├── client/                 # 客户端源码 (PyQt5)
│   ├── assets/             # 资源文件 (图标, 音效)
│   ├── ui/                 # UI 组件与窗口定义
│   │   ├── main_window.py      # 主界面
│   │   ├── memory_dialog.py    # 记忆管理界面
│   │   └── multi_agent_ui.py   # 多智能体看板
│   └── client.spec         # PyInstaller 打包配置
├── server/                 # 服务端源码 (FastAPI)
│   ├── core/               # 核心逻辑 (LLM, 记忆, 配置)
│   ├── data/               # 持久化数据 (用户配置, 记忆库)
│   ├── routers/            # API 路由
│   └── Models/             # 模型集成 (TTS, Vision)
├── models/                 # 模型文件存放目录 (需手动下载)
├── install.bat             # 一键安装脚本
├── start_server.bat        # 服务端启动脚本
└── start_client.bat        # 客户端启动脚本
```

---

<a name="english-version"></a>
## English Version

### 1. Installation
Ensure Python 3.10+ is installed, then run:
```batch
install.bat
```

### 2. Launching
**Step 1: Start Server**
```batch
start_server.bat
```
**Step 2: Start Client**
```batch
start_client.bat
```

### 3. Configuration
*   **Settings**: Accessible via the UI Settings menu.
*   **Advanced Config**: Edit `server/core/config.py` for model paths, ports, and API keys.

---
*Project Eliza - Tactical AI Assistant*
