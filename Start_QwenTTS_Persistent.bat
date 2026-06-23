@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo SkyrimNet QwenTTS Persistent TTS Adapter
echo Server URL: http://127.0.0.1:7861
echo SkyrimNet TTS Server URL: http://127.0.0.1:7861
echo Settings UI: http://127.0.0.1:7861/settings
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Local .venv not found. Run Setup_QwenTTS_Adapter.bat first.
    pause
    exit /b 1
)

echo.
echo NOTE: First start may be slow (5-30 s) because the QwenTTS talker GGUF
echo file (~1.2 GB) and the tokenizer GGUF (~647 MB) must be loaded into
echo memory.  After the server is ready, subsequent TTS requests are fast.
echo.

echo.
echo Opening settings page in browser after server starts...

start "" http://127.0.0.1:7861/settings

".venv\Scripts\python.exe" qwentts_adapter_server.py --max-text-chars 180 --cleanup-interval-minutes 30 --keep-output-minutes 60
pause
