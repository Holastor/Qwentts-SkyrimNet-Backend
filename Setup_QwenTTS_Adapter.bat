 @echo off
    cd /d "%~dp0"
    set PYTHONUTF8=1
    set PYTHONIOENCODING=utf-8

    echo ============================================================
    echo   SkyrimNet QwenTTS Adapter — Setup
    echo ============================================================
    echo.

    :: -----------------------------------------------------------------
    :: 1. Find Python
    :: -----------------------------------------------------------------
    echo [1/7] Searching for Python...

    set "PYTHON_EXE="
    py -3.11 --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=py -3.11"

    if not defined PYTHON_EXE (
        python --version >nul 2>&1
        if not errorlevel 1 set "PYTHON_EXE=python"
    )

    if not defined PYTHON_EXE (
        echo ERROR: Python 3.10+ is required.
        echo        Install Python and run this setup again.
        goto fail
    )

    echo        Found: & %PYTHON_EXE% --version
    echo.

    :: -----------------------------------------------------------------
    :: 2. Create / verify virtual environment
    :: -----------------------------------------------------------------
    echo [2/7] Virtual environment...

    if not exist ".venv\Scripts\python.exe" (
        echo        Creating .venv...
        %PYTHON_EXE% -m venv .venv
        if errorlevel 1 goto fail
        echo        OK — created.
    ) else (
        echo        OK — already exists.
    )

    call .venv\Scripts\activate.bat
    if errorlevel 1 goto fail
    echo.

    :: -----------------------------------------------------------------
    :: 3. Install / update dependencies
    :: -----------------------------------------------------------------
    echo [3/7] Installing dependencies...

    python -m pip install --upgrade pip setuptools wheel >nul 2>&1
    if errorlevel 1 (
        echo        ERROR: pip upgrade failed.
        goto fail
    )

    python -m pip install -r requirements_qwentts_adapter.txt
    if errorlevel 1 (
        echo        ERROR: pip install failed.
        goto fail
    )
    echo        OK.
    echo.

    :: -----------------------------------------------------------------
    :: 4. Verify Python imports
    :: -----------------------------------------------------------------
    echo [4/7] Verifying Python imports...

    python -c "import ctypes; print('        ctypes ........... OK')"
    if errorlevel 1 goto fail
    python -c "import numpy; print('        numpy ' + numpy.__version__ + ' ... OK')"
    if errorlevel 1 goto fail
    python -c "import fastapi, uvicorn; print('        fastapi/uvicorn .. OK')"
    if errorlevel 1 goto fail
    echo.

    :: -----------------------------------------------------------------
    :: 5. Locate and test qwen.dll
    :: -----------------------------------------------------------------
    echo [5/7] Checking QwenTTS native backend (bin\)...

    :: Check if bin\qwen.dll exists. If not, trigger automated download.
    if not exist "bin\qwen.dll" (
        echo        Native binaries ^(bin\^) missing.
        echo        Downloading latest stable bin.zip from GitHub...
        
        :: Attempt 1: Using built-in Windows curl
        curl -L -o bin_temp.zip "https://github.com/Holastor/Qwentts-SkyrimNet-Backend/releases/download/binaries-latest/bin.zip"
        
        :: Attempt 2: PowerShell fallback if curl is missing or fails
        if errorlevel 1 (
            echo        curl failed or missing. Trying fallback via PowerShell...
            powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/Holastor/Qwentts-SkyrimNet-Backend/releases/download/binaries-latest/bin.zip' -OutFile 'bin_temp.zip'" >nul 2>&1
        )
        
        :: Final check if both download vectors failed
        if errorlevel 1 (
            echo.
            echo        ERROR: Failed to download native binaries automatically.
            echo               Please download it manually from:
            echo               https://github.com/Holastor/Qwentts-SkyrimNet-Backend/releases/tag/binaries-latest
            echo               and unpack the 'bin' folder to the project root.
            goto fail
        )
        
        echo        Unpacking binaries...
        :: Extracting the zip file natively via tar
        tar -xf bin_temp.zip
        if errorlevel 1 (
            echo        ERROR: Failed to unpack bin.zip. Make sure you have tar installed.
            del bin_temp.zip >nul 2>&1
            goto fail
        )
        
        :: Cleanup the temporary downloaded archive
        del bin_temp.zip >nul 2>&1
        echo        Binaries successfully installed!
        echo.
    )

    set "BACKEND_DIR="
    if exist "bin\qwen.dll"               set "BACKEND_DIR=bin"
    if exist "bin\qwentts_CPU\qwen.dll"   set "BACKEND_DIR=bin\qwentts_CPU"
    if exist "bin\qwentts_VULKAN\qwen.dll" set "BACKEND_DIR=bin\qwentts_VULKAN"
    if exist "bin\qwentts_CUDA\qwen.dll"  set "BACKEND_DIR=bin\qwentts_CUDA"

    if not defined BACKEND_DIR (
        echo        ERROR: qwen.dll not found in any bin\ subdirectory.
        echo        Place qwen.dll + ggml*.dll into bin\, bin\qwentts_CPU\,
        echo        bin\qwentts_VULKAN\, or bin\qwentts_CUDA\.
        goto fail
    )

    echo        Found backend: %BACKEND_DIR%
    python -c "from src.core import bindings; print('        qwen.dll loaded, version:', bindings.qt_version().decode())"
    if errorlevel 1 (
        echo        ERROR: qwen.dll found but failed to load via ctypes.
        echo        Check that all ggml*.dll dependencies are present.
        goto fail
    )

    if exist "%BACKEND_DIR%\qwen-codec.exe" (
        echo        qwen-codec.exe .. OK  (voice caching enabled^)
    ) else (
        echo        qwen-codec.exe .. NOT FOUND  (voice caching will be disabled^)
    )
    echo.

    :: -----------------------------------------------------------------
    :: 6. Check model files
    :: -----------------------------------------------------------------
    echo [6/7] Checking GGUF model files (models\qwen\)...

    set "MODELS_OK=1"
    if exist "models\qwen\qwen-talker-1.7b-base-Q4_K_M.gguf" (
        echo        talker GGUF ...... OK
    ) else (
        echo        talker GGUF ...... MISSING
        set "MODELS_OK=0"
    )
    if exist "models\qwen\qwen-tokenizer-12hz-F32.gguf" (
        echo        codec  GGUF ...... OK
    ) else (
        echo        codec  GGUF ...... MISSING
        set "MODELS_OK=0"
    )
    if "%MODELS_OK%"=="0" (
        echo.
        echo        WARNING: Required GGUF model files are missing.
        echo                 You will be able to download them via the settings web dashboard
        echo                 at http://127.0.0.1:7861/settings after starting the server.
    ) else (
        echo        All model files present.
    )
    echo.

    :: -----------------------------------------------------------------
    :: 7. Create directory structure
    :: -----------------------------------------------------------------
    echo [7/7] Setting up directory structure...

    :: --- Voices ---
    if not exist "Voices\" mkdir "Voices"

    if not exist "Voices\qwen_speakers\" (
        mkdir "Voices\qwen_speakers"
        echo        Created Voices\qwen_speakers\
    ) else (
        echo        Voices\qwen_speakers\ ... OK
    )

    if not exist "Voices\runtime_speakers\" (
        mkdir "Voices\runtime_speakers"
        echo        Created Voices\runtime_speakers\
    ) else (
        echo        Voices\runtime_speakers\ ... OK
    )

    if not exist "Voices\cached_voices\" (
        mkdir "Voices\cached_voices"
        echo        Created Voices\cached_voices\
    ) else (
        echo        Voices\cached_voices\ ... OK
    )

    if not exist "Voices\voice_refs\" (
        mkdir "Voices\voice_refs"
        echo        Created Voices\voice_refs\
    ) else (
        echo        Voices\voice_refs\ ... OK
    )

    :: Copy voice_refs.json.example if no voice_refs exist yet
    if not exist "Voices\voice_refs\voice_refs.json" (
        if exist "Voices\voice_refs\voice_refs.json.example" (
            copy "Voices\voice_refs\voice_refs.json.example" "Voices\voice_refs\voice_refs.json" >nul
            echo        Initialized voice_refs.json from example.
        ) else (
            echo        WARNING: Voices\voice_refs\voice_refs.json not found.
            echo                 It will be created automatically on first run
            echo                 or when you import voices from SkyrimNet.
        )
    )

    :: --- Output ---
    if not exist "output_temp\" mkdir "output_temp"
    if not exist "output_temp\qwentts_generated\"    mkdir "output_temp\qwentts_generated"
    if not exist "output_temp\qwentts_debug_failed\" mkdir "output_temp\qwentts_debug_failed"
    if not exist "output_temp\qwentts_debug_text\"   mkdir "output_temp\qwentts_debug_text"
    echo        output_temp\ ............. OK

    :: --- Settings ---
    if not exist "src\local_settings\" mkdir "src\local_settings"
    echo        src\local_settings\ ...... OK
    echo.

    :: -----------------------------------------------------------------
    :: Done
    :: -----------------------------------------------------------------
    echo ============================================================
    echo   Setup completed successfully!
    echo ============================================================
    echo.
    echo   To start the server, run:
    echo     Start_QwenTTS_Persistent.bat
    echo.
    echo   Server URL:    http://127.0.0.1:7861
    echo   Settings UI:   http://127.0.0.1:7861/settings
    echo.
    echo   NOTE: First start loads ~1.9 GB of GGUF model files
    echo         into memory (5-30 seconds).
    echo         Subsequent TTS requests are fast.
    echo.
    echo   Project layout:
    echo     bin\                  QwenTTS native DLLs
    echo     models\qwen\          GGUF model files
    echo     src\                  Python source code
    echo       api\                API endpoints
    echo       core\               DLL bindings ^& backend
    echo       services\           TTS, cache, importer
    echo       web\                Settings UI template
    echo       local_settings\     Runtime settings (JSON)
    echo     Voices\               All voice data
    echo       qwen_speakers\      Reference speaker WAVs
    echo       runtime_speakers\   Runtime-uploaded WAVs
    echo       cached_voices\      Pre-encoded RVQ cache
    echo       voice_refs\         Voice reference database
    echo.
    pause
    exit /b 0

    :fail
    echo.
    echo ============================================================
    echo   Setup FAILED — see errors above.
    echo ============================================================
    echo.
    pause
    exit /b 1