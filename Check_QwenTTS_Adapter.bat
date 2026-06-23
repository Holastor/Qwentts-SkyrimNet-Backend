@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo SkyrimNet QwenTTS Adapter — Diagnostic Check
echo.

set "PYTHON_EXE="
py -3.11 --version >nul 2>&1
if not errorlevel 1 set "PYTHON_EXE=py -3.11"

if not defined PYTHON_EXE (
    python --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=python"
)

if not defined PYTHON_EXE (
    echo Python 3.10 or compatible Python is required.
    pause
    exit /b 1
)

echo Using Python:
%PYTHON_EXE% --version
echo.

if exist ".venv\Scripts\python.exe" (
    call .venv\Scripts\activate.bat
    echo Using .venv environment.
) else (
    echo WARNING: .venv not found. Run Setup_QwenTTS_Adapter.bat first.
)

echo.
echo === Pip packages ===
%PYTHON_EXE% -c "import ctypes; print('ctyles ok')"
%PYTHON_EXE% -c "import numpy; print('numpy', numpy.__version__)"
%PYTHON_EXE% -c "import fastapi; print('fastapi ok')"
%PYTHON_EXE% -c "import uvicorn; print('uvicorn ok')"

echo.
echo === DLL files in bin\ backends ===
set "BACKEND_DIR="
if exist "bin\qwen.dll" set "BACKEND_DIR=bin"
if exist "bin\qwentts_CPU\qwen.dll" set "BACKEND_DIR=bin\qwentts_CPU"
if exist "bin\qwentts_VULKAN\qwen.dll" set "BACKEND_DIR=bin\qwentts_VULKAN"
if exist "bin\qwentts_CUDA\qwen.dll" set "BACKEND_DIR=bin\qwentts_CUDA"
if defined BACKEND_DIR (
    echo Found DLL directory: %BACKEND_DIR%
    dir "%BACKEND_DIR%\*.dll" /b
) else (
    echo No qwen.dll found in any bin/ subdirectory!
)

echo.
echo === qwen.dll load test ===
%PYTHON_EXE% -c "import os; d=os.path.abspath('%BACKEND_DIR%'); os.add_dll_directory(d); os.environ['PATH']=d+os.pathsep+os.environ.get('PATH',''); import ctypes; q=ctypes.CDLL(os.path.join(d,'qwen.dll'), winmode=0); q.qt_version.restype=ctypes.c_char_p; q.qt_version.argtypes=[]; print('Loaded:', q.qt_version().decode())"
if errorlevel 1 (
    echo FAILED: qwen.dll could not be loaded by Python ctypes.
)

echo.
echo === Model files ===
if exist "models\qwen\qwen-talker-1.7b-base-Q4_K_M.gguf" (
    echo talker GGUF: OK
) else (
    echo talker GGUF: MISSING
)
if exist "models\qwen\qwen-tokenizer-12hz-F32.gguf" (
    echo codec GGUF: OK
) else (
    echo codec GGUF: MISSING
)

echo.
echo === Voice references ===
if exist "Voices\voice_refs\" ( echo Voices\voice_refs\: OK ) else ( echo Voices\voice_refs\: MISSING )
if exist "Voices\qwen_speakers\" ( echo Voices\qwen_speakers\: OK ) else ( echo Voices\qwen_speakers\: MISSING )
if exist "Voices\runtime_speakers\" ( echo Voices\runtime_speakers\: OK ) else ( echo Voices\runtime_speakers\: MISSING )
if exist "Voices\cached_voices\" ( echo Voices\cached_voices\: OK ) else ( echo Voices\cached_voices\: MISSING )

echo.
echo === Output directories ===
if exist "output_temp\" ( echo output_temp\: OK ) else ( mkdir output_temp && echo output_temp\: created )
if exist "output_temp\qwentts_generated" ( echo   qwentts_generated: OK ) else ( mkdir output_temp\qwentts_generated && echo   qwentts_generated: created )
if exist "output_temp\qwentts_debug_failed" ( echo   qwentts_debug_failed: OK ) else ( mkdir output_temp\qwentts_debug_failed && echo   qwentts_debug_failed: created )
if exist "output_temp\qwentts_debug_text" ( echo   qwentts_debug_text: OK ) else ( mkdir output_temp\qwentts_debug_text && echo   qwentts_debug_text: created )

echo.
echo === Summary ===
echo If all items above show OK, the adapter is ready to start.
echo Otherwise fix the reported issues before running.
echo.
pause
