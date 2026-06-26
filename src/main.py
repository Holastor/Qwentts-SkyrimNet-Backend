import os
import time
import threading
import argparse
from pathlib import Path
from fastapi import FastAPI

from src import config
from src.config import _log
from src.core.bindings import qt_version
from src.core.backend import _detect_backends
from src.api.endpoints_skyrim import router as skyrim_router
from src.api.endpoints_ui import router as ui_router

app = FastAPI(
    title="SkyrimNet QwenTTS Adapter",
    description="QwenTTS adapter that preserves SkyrimNet-compatible endpoints. Uses qwentts.cpp via ctypes.",
    version="0.1.0",
)

app.include_router(skyrim_router)
app.include_router(ui_router)


# ---------------------------------------------------------------------------
# Cleanup Thread Logic
# ---------------------------------------------------------------------------
def _cleanup_old_output_wavs_once() -> None:
    output_dir = config.OUTPUT_DIR.resolve()
    keep_seconds = max(0.0, config.KEEP_OUTPUT_MINUTES) * 60.0
    cutoff_time = time.time() - keep_seconds
    deleted_count = 0
    deleted_bytes = 0
    errors_count = 0

    _log("cleanup started")
    _log(f"cleanup output_dir: {output_dir}")
    _log(f"cleanup keep_output_minutes: {config.KEEP_OUTPUT_MINUTES}")

    if not output_dir.exists():
        _log("cleanup output_dir does not exist yet")
        _log("cleanup deleted files count: 0")
        _log("cleanup deleted bytes: 0")
        _log("cleanup errors count: 0")
        return

    if not output_dir.is_dir():
        _log("WARNING: cleanup output_dir is not a directory; skipping cleanup")
        _log("cleanup deleted files count: 0")
        _log("cleanup deleted bytes: 0")
        _log("cleanup errors count: 1")
        return

    for path in output_dir.rglob("*.wav"):
        try:
            resolved_path = path.resolve()
            if not path.is_file():
                continue
            stat = path.stat()
            if stat.st_mtime > cutoff_time:
                continue
            size = stat.st_size
            path.unlink()
            deleted_count += 1
            deleted_bytes += size
        except Exception as exc:
            errors_count += 1
            _log(f"WARNING: cleanup failed for {path}: {exc}")

    _log(f"cleanup deleted files count: {deleted_count}")
    _log(f"cleanup deleted bytes: {deleted_bytes}")
    _log(f"cleanup errors count: {errors_count}")


def _cleanup_loop() -> None:
    _cleanup_old_output_wavs_once()
    interval_seconds = max(0.1, config.CLEANUP_INTERVAL_MINUTES) * 60.0
    while not config.CLEANUP_STOP_EVENT.wait(interval_seconds):
        _cleanup_old_output_wavs_once()


def _start_cleanup_thread() -> threading.Thread:
    thread = threading.Thread(target=_cleanup_loop, name="qwentts-output-cleanup", daemon=True)
    thread.start()
    return thread


# ---------------------------------------------------------------------------
# CLI Arguments Parser
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone SkyrimNet QwenTTS adapter server")

    # General
    parser.add_argument("--host", default=config.HOST, help=f"Host to bind. Default: {config.HOST}")
    parser.add_argument("--port", type=int, default=config.PORT, help=f"Port to bind. Default: {config.PORT}")
    parser.add_argument(
        "--output-dir",
        default=str(config.OUTPUT_DIR),
        help=f"Directory for temporary generated WAV files. Default: {config.OUTPUT_DIR}",
    )
    parser.add_argument(
        "--cleanup-enabled",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable periodic cleanup of old generated WAV files. Default: true",
    )
    parser.add_argument(
        "--cleanup-interval-minutes",
        type=float,
        default=30.0,
        help="Minutes between generated WAV cleanup passes. Default: 30",
    )
    parser.add_argument(
        "--keep-output-minutes",
        type=float,
        default=60.0,
        help="Keep generated WAV files at least this many minutes. Default: 60",
    )

    # Model paths
    parser.add_argument(
        "--talker-path",
        default=str(config.TALKER_PATH),
        help=f"Qwen talker LM GGUF path. Default: {config.TALKER_PATH}",
    )
    parser.add_argument(
        "--codec-path",
        default=str(config.CODEC_PATH),
        help=f"Qwen tokenizer / codec GGUF path. Default: {config.CODEC_PATH}",
    )

    # Text preprocessing
    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=0,
        help="Maximum text length for generation. 0 means no limit. Default: 0",
    )
    parser.add_argument(
        "--append-ending-pause",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Append ending pause text before generation. Default: true",
    )
    parser.add_argument(
        "--ending-pause-text",
        default="...",
        help='Text appended when --append-ending-pause is enabled. Default: "..."',
    )
    parser.add_argument(
        "--min-output-duration",
        type=float,
        default=0.0,
        help="Warn when generated WAV is shorter than this many seconds. 0 disables. Default: 0",
    )
    parser.add_argument(
        "--debug-save-text",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Save text sent under output_temp/qwentts_debug_text. Default: true",
    )

    # Runtime speakers
    parser.add_argument(
        "--runtime-speakers-dir",
        default=str(config.RUNTIME_SPEAKERS_DIR),
        help=f"Directory for SkyrimNet Select/runtime uploaded speaker WAV files. Default: {config.RUNTIME_SPEAKERS_DIR}",
    )
    parser.add_argument(
        "--allow-runtime-upload-overwrite",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Allow /create_and_store_latents uploads to overwrite files in runtime-speakers-dir. Default: false",
    )

    # QwenTTS synthesis knobs
    parser.add_argument("--lang", default="russian", help="Language for synthesis. Default: russian")
    parser.add_argument("--seed", type=int, default=-1, help="Random seed (-1 = random). Default: -1")
    parser.add_argument("--max-new-tokens", type=int, default=2048, help="Max new audio frames. Default: 2048")
    parser.add_argument("--temperature", type=float, default=0.9, help="Talker temperature. Default: 0.9")
    parser.add_argument("--top-k", type=int, default=50, help="Talker top-k. Default: 50")
    parser.add_argument("--top-p", type=float, default=1.0, help="Talker top-p. Default: 1.0")
    parser.add_argument("--repetition-penalty", type=float, default=1.05, help="Talker repetition penalty. Default: 1.05")
    parser.add_argument("--subtalker-temperature", type=float, default=0.9, help="Sub-talker temperature. Default: 0.9")
    parser.add_argument("--subtalker-top-k", type=int, default=50, help="Sub-talker top-k. Default: 50")
    parser.add_argument("--subtalker-top-p", type=float, default=1.0, help="Sub-talker top-p. Default: 1.0")
    parser.add_argument(
        "--use-fa", "--no-fa",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="use_fa",
        help="Enable flash attention. Default: true",
    )
    parser.add_argument(
        "--clamp-fp16",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Clamp hidden states + V to FP16 range. Default: false",
    )
    parser.add_argument(
        "--codec-chunk-sec",
        type=float,
        default=24.0,
        help="Codec decode chunk duration in seconds. Default: 24.0",
    )
    parser.add_argument(
        "--codec-left-context-sec",
        type=float,
        default=2.0,
        help="Codec decode left context duration in seconds. Default: 2.0",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Server Starter Function
# ---------------------------------------------------------------------------
def main():
    args = parse_args()

    # Re-map command line arguments to module properties
    config.HOST = args.host
    config.PORT = args.port
    config.OUTPUT_DIR = Path(args.output_dir)
    config.TALKER_PATH = config._resolve_path(args.talker_path)
    config.CODEC_PATH  = config._resolve_path(args.codec_path)
    config.CLEANUP_ENABLED = args.cleanup_enabled
    config.CLEANUP_INTERVAL_MINUTES = max(0.1, args.cleanup_interval_minutes)
    config.KEEP_OUTPUT_MINUTES = max(0.0, args.keep_output_minutes)
    config.MAX_TEXT_CHARS = max(0, args.max_text_chars)
    config.APPEND_ENDING_PAUSE = args.append_ending_pause
    config.ENDING_PAUSE_TEXT = args.ending_pause_text
    config.MIN_OUTPUT_DURATION = max(0.0, args.min_output_duration)
    config.DEBUG_SAVE_TEXT = args.debug_save_text

    config.RUNTIME_SPEAKERS_DIR = Path(args.runtime_speakers_dir)
    config.ALLOW_RUNTIME_UPLOAD_OVERWRITE = args.allow_runtime_upload_overwrite
    config.LANG                   = args.lang
    config.SEED                   = args.seed
    config.MAX_NEW_TOKENS         = args.max_new_tokens
    config.TEMPERATURE            = args.temperature
    config.TOP_K                  = args.top_k
    config.TOP_P                  = args.top_p
    config.REPETITION_PENALTY     = args.repetition_penalty
    config.SUB_TEMPERATURE        = args.subtalker_temperature
    config.SUB_TOP_K              = args.subtalker_top_k
    config.SUB_TOP_P              = args.subtalker_top_p
    config.USE_FA                 = args.use_fa
    config.CLAMP_FP16             = args.clamp_fp16
    config.CODEC_CHUNK_SEC        = args.codec_chunk_sec
    config.CODEC_LEFT_CONTEXT_SEC = args.codec_left_context_sec

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.QWENTTS_DEBUG_FAILED_DIR.mkdir(parents=True, exist_ok=True)
    config.QWENTTS_DEBUG_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    config.RVQ_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    _log("server started")
    _log(f"qt_version: {qt_version().decode()}")
    _log(f"output_dir: {config.OUTPUT_DIR.resolve()}")
    _log(f"cleanup_enabled: {str(config.CLEANUP_ENABLED).lower()}")
    _log(f"cleanup_interval_minutes: {config.CLEANUP_INTERVAL_MINUTES}")
    _log(f"keep_output_minutes: {config.KEEP_OUTPUT_MINUTES}")
    _log(f"max text chars: {config.MAX_TEXT_CHARS or 'unlimited'}")
    _log(f"append ending pause: {str(config.APPEND_ENDING_PAUSE).lower()}")
    _log(f"ending pause text: {config.ENDING_PAUSE_TEXT}")
    _log(f"min output duration: {config.MIN_OUTPUT_DURATION or 'disabled'}")
    _log(f"debug save text: {str(config.DEBUG_SAVE_TEXT).lower()}")
    _log(f"runtime speakers dir: {config.RUNTIME_SPEAKERS_DIR}")
    _log(f"allow runtime upload overwrite: {str(config.ALLOW_RUNTIME_UPLOAD_OVERWRITE).lower()}")
    _log(f"talker path: {config.TALKER_PATH}")
    _log(f"codec path: {config.CODEC_PATH}")
    _log(f"lang: {config.LANG}")
    _log(f"seed: {config.SEED}")
    _log(f"max_new_tokens: {config.MAX_NEW_TOKENS}")
    _log(f"temperature: {config.TEMPERATURE}")
    _log(f"top_k: {config.TOP_K}")
    _log(f"top_p: {config.TOP_P}")
    _log(f"repetition_penalty: {config.REPETITION_PENALTY}")
    _log(f"subtalker temperature: {config.SUB_TEMPERATURE}")
    _log(f"subtalker top_k: {config.SUB_TOP_K}")
    _log(f"subtalker top_p: {config.SUB_TOP_P}")
    _log(f"use_fa: {str(config.USE_FA).lower()}")
    _log(f"clamp_fp16: {str(config.CLAMP_FP16).lower()}")
    _log(f"codec_chunk_sec: {config.CODEC_CHUNK_SEC}")
    _log(f"codec_left_context_sec: {config.CODEC_LEFT_CONTEXT_SEC}")
    _log("listening on http://{}:{}".format(config.HOST, config.PORT))
    _log("QwenTTS adapter server starting (persistent mode)")

    config._load_settings()

    backends = _detect_backends()
    _log(f"detected backends: {backends}")
    requested = config._SETTINGS.get("backend", "qwentts_CPU")
    if backends.get(requested) != "ready":
        _log(f"WARNING: requested backend '{requested}' not ready, falling back to CPU")
        config._SETTINGS["backend"] = "qwentts_CPU"
        config._save_settings()
        requested = "qwentts_CPU"

    _backend_to_ggml_env = {
        "qwentts_CPU":    "CPU",
        "qwentts_CUDA":   "CUDA0",
        "qwentts_VULKAN": "Vulkan0",
    }
    ggml_backend = _backend_to_ggml_env.get(requested, "CPU")
    os.environ["GGML_BACKEND"] = ggml_backend
    _log(f"GGML_BACKEND={ggml_backend}")

    _log("initializing QwenTTS persistent backend")
    try:
        from src.core import backend
        backend.PERSISTENT_BACKEND = backend.PersistentQwenTTSBackend(
            config.TALKER_PATH, config.CODEC_PATH,
            use_fa=config.USE_FA, clamp_fp16=config.CLAMP_FP16,
        )
    except Exception as exc:
        _log(f"WARNING: failed to initialize QwenTTS persistent backend (model files might be missing): {exc}")

    if config.USE_VOICE_CACHE:
        from src.services.cache import _precache_all_voices
        import threading as _thr
        _thr.Thread(target=lambda: _precache_all_voices(encode_missing=False), daemon=True).start()

    cleanup_thread = _start_cleanup_thread() if config.CLEANUP_ENABLED else None
    try:
        import uvicorn
        uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
    finally:
        if cleanup_thread is not None:
            config.CLEANUP_STOP_EVENT.set()
            cleanup_thread.join(timeout=5)


if __name__ == "__main__":
    main()
