# QwenTTS Adapter for SkyrimNet

<p align="left">
  <a href="README.md">English</a> •
  <a href="README_RU.md">Русский</a>
</p>

---

This project implements the integration of the local, high-performance **QwenTTS** speech synthesis engine (powered by [qwentts.cpp](https://github.com/ServeurpersoCom/qwentts.cpp)) as a backend for SkyrimNet.

The adapter emulates the standard SkyrimNet API (`/tts_to_audio/`, `/health`, `/create_and_store_latents`), ensuring seamless client operation.

---

## Key Engine Features

* **Local & Fast**: Written in C++17 (GGML), runs entirely on CPU (or GPU via CUDA/Vulkan) without heavy dependencies like PyTorch or Transformers.
* **Voice Cloning (ICL)**: Supports instant voice cloning using a short reference WAV sample (3–7 seconds) and its corresponding transcript.
* **Standalone / Offline**: Requires no internet connection once the models are downloaded.

---

## Installation & Build Modes

You can set up the adapter in two ways depending on whether you want a ready-to-run setup or a custom build:

* **Pre-built Release (Recommended)**: Download the latest archive from the [Releases]() tab. It already contains the pre-compiled `qwen.dll`, computational backend DLLs (`ggml-cuda.dll`, `ggml-vulkan.dll`), and standalone utility executables inside the `bin/` directory.
* **Build from Source (Advanced)**: If you want to compile the core engine manually, this repository includes `qwentts.cpp` as a Git submodule. You can pull the submodule and compile the binaries directly on your machine using CMake and your preferred compiler (MSVC/GCC).

---

## Quick Start

1. **Unpack & Clone**: 
   * If using a pre-built release, simply extract the `QwenTTS` folder into your working directory.
   * If building from source, clone this repository recursively to fetch the submodule:
     ```bash
     git clone --recursive https://github.com/Holastor/Qwentts-SkyrimNet-Backend.git
     ```
2. **Environment Setup**: Run the `Setup_QwenTTS_Adapter.bat` file. It will create a local `.venv` virtual environment and install all required Python dependencies.
   > [!NOTE]
   > The script will complete successfully even if the model files are missing. You can download them later via the dashboard.
3. **Launch the Server**: Run `Start_QwenTTS_Persistent.bat`. The server will boot up and automatically open the settings dashboard in your default browser.
4. **Configure SkyrimNet**: In your SkyrimNet client settings, specify the following TTS server URL:
   ```
   http://127.0.0.1:7861
   ```

---

## Control Panel (Dashboard)

Dashboard URL: **[http://127.0.0.1:7861/settings](http://127.0.0.1:7861/settings)**

### 1. "Settings & Models" Tab
* **Backend**: Select the compute core (`CPU`, `CUDA` for NVIDIA graphics cards, or `Vulkan` for AMD/integrated GPUs).
* **Generation Parameters**: Tweak Temperature (voice expressiveness), Repetition Penalty, Seed (generation seed), and other sampling settings.
* **Model Management**:
* If the `models/qwen/` folder is empty, you can **download models directly from HuggingFace** with a single click in the "Download from HuggingFace" section.
* Select the active language model (`Talker LM`) and audio codec (`Audio Codec`), then click **Apply Models** to reload the backend.

### 2. "Voices Manager" Tab
* **Import from SkyrimNet**: Sync and automatically download reference voice samples from a running SkyrimNet server.
> [!IMPORTANT]
> The import process displays a clear **progress bar, completion percentage, total processed voices, and estimated time remaining**. Before starting the import, make sure the correct language (e.g., `russian`) is selected in the synthesis parameters so the reference files are sorted into the proper directories!
* **Manual Management**: Add, edit, listen to (via the built-in audio player at the bottom), or delete NPC voices from the `voice_refs_<lang>.json` database.

---

## Project Structure

```
QwenTTS/
├── qwentts_adapter_server.py     # Application entry point
├── Start_QwenTTS_Persistent.bat  # Server startup script
├── Setup_QwenTTS_Adapter.bat     # Environment setup script
├── Check_QwenTTS_Adapter.bat     # Diagnostics script
├── requirements_qwentts_adapter.txt # Python dependencies
├── bin/                          # qwen.dll and dependency DLLs (GGML)
├── models/qwen/                  # Directory for GGUF models
├── Voices/                       # Voice asset data
│   ├── qwen_speakers/            # Reference WAV files (split by locale, e.g., ru_RU)
│   ├── runtime_speakers/         # Reference samples uploaded during gameplay
│   ├── cached_voices/            # Pre-encoded RVQ token cache
│   └── voice_refs/               # Voice mapping databases (voice_refs_ru_RU.json, etc.)
├── src/                          # Adapter source code
│   ├── api/                      # Endpoints (FastAPI)
│   ├── core/                     # Ctypes wrapper for qwen.dll and backend management
│   ├── services/                 # Synthesis, caching, and voice import services
│   └── web/                      # Dashboard frontend (settings.html, settings.css, settings.js)
└── output_temp/                  # Temporary generated WAVs and diagnostics logs
```

---

---

## Reference Sample Requirements (ICL Mode)

For high-fidelity voice cloning, QwenTTS requires:
1. **A high-quality reference WAV file** (preferably mono, 24 kHz, **3–7 seconds** in duration).
2. **An exact transcript** (`ref_text` parameter). If the text does not perfectly match the spoken words in the audio sample, synthesis quality will drop drastically.

---

## Diagnostics & Log Files

If you encounter unexpected behavior or errors, check the following log targets:
* Synthesis logs are written directly to the standard console output.
* Temporary generated audio files are saved to `output_temp/qwentts_generated/`.
* Debug info for failed generations is stored in `output_temp/qwentts_debug_failed/`.
* Raw processed text passed to the model is backed up in `output_temp/qwentts_debug_text/`.
