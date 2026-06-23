import os
import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------------
HOST = "0.0.0.0"
PORT = 7861
BACKEND_NAME = "qwentts-adapter"

# Path(__file__) is PROJECT_ROOT / src / config.py -> PROJECT_ROOT is two levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = PROJECT_ROOT / "bin"
OUTPUT_DIR = PROJECT_ROOT / "output_temp" / "qwentts_generated"
VOICES_DIR = PROJECT_ROOT / "Voices"
VOICE_REFS_PATH = VOICES_DIR / "voice_refs" / "voice_refs.json"
RUNTIME_SPEAKERS_DIR = VOICES_DIR / "runtime_speakers"
ALLOW_RUNTIME_UPLOAD_OVERWRITE = False
QWENTTS_DEBUG_FAILED_DIR = PROJECT_ROOT / "output_temp" / "qwentts_debug_failed"
QWENTTS_DEBUG_TEXT_DIR = PROJECT_ROOT / "output_temp" / "qwentts_debug_text"
RVQ_CACHE_DIR = VOICES_DIR / "cached_voices"

# Paths inside PROJECT_ROOT/models/qwen/
TALKER_PATH = PROJECT_ROOT / "models" / "qwen" / "qwen-talker-1.7b-base-Q4_K_M.gguf"
CODEC_PATH  = PROJECT_ROOT / "models" / "qwen" / "qwen-tokenizer-12hz-F32.gguf"

# ---------------------------------------------------------------------------
# QwenTTS Synthesis Defaults
# ---------------------------------------------------------------------------
LANG                    = "russian"
SEED                    = -1
MAX_NEW_TOKENS          = 2048
DO_SAMPLE               = True
TEMPERATURE             = 0.9
TOP_K                   = 50
TOP_P                   = 1.0
REPETITION_PENALTY      = 1.05
SUB_DO_SAMPLE           = True
SUB_TEMPERATURE         = 0.9
SUB_TOP_K               = 50
SUB_TOP_P               = 1.0
USE_FA                  = True
CLAMP_FP16              = False
CODEC_CHUNK_SEC         = 24.0
CODEC_LEFT_CONTEXT_SEC  = 2.0
DUMP_DIR                = None

# Text preprocessing
MAX_TEXT_CHARS          = 0
APPEND_ENDING_PAUSE     = True
ENDING_PAUSE_TEXT       = "..."
MIN_OUTPUT_DURATION     = 0.0
DEBUG_SAVE_TEXT         = True

# Cleanup
CLEANUP_ENABLED          = True
CLEANUP_INTERVAL_MINUTES = 30.0
KEEP_OUTPUT_MINUTES      = 60.0
CLEANUP_STOP_EVENT       = threading.Event()

# Pronunciation overrides
STRESS_MARK                    = "́"
STRESS_VOWELS                  = set("аеёиоуыэюяАЕЁИОУЫЭЮЯ")

# Settings persistence path
SETTINGS_PATH = PROJECT_ROOT / "src" / "local_settings" / "qwen_settings.json"

_SETTINGS: Dict[str, Any] = {
    "lang": "russian",
    "seed": -1,
    "max_new_tokens": 2048,
    "do_sample": True,
    "temperature": 0.9,
    "top_k": 50,
    "top_p": 1.0,
    "repetition_penalty": 1.05,
    "subtalker_do_sample": True,
    "subtalker_temperature": 0.9,
    "subtalker_top_k": 50,
    "subtalker_top_p": 1.0,
    "use_fa": True,
    "clamp_fp16": False,
    "codec_chunk_sec": 24.0,
    "codec_left_context_sec": 2.0,
    "max_text_chars": 180,
    "append_ending_pause": True,
    "ending_pause_text": "...",
    "min_output_duration": 0.0,
    "debug_save_text": True,
    "talker_path": str(TALKER_PATH),
    "codec_path": str(CODEC_PATH),
    "backend": "qwentts_CPU",
    "active_talker_name": "qwen-talker-1.7b-base-Q4_K_M.gguf",
    "active_codec_name":  "qwen-tokenizer-12hz-F32.gguf",
}


def _log(message: str) -> None:
    print(f"[{BACKEND_NAME}] {message}", flush=True)


# ---------------------------------------------------------------------------
# Language Mappings
# ---------------------------------------------------------------------------
KNOWN_LANGS = {
    "auto", "english", "chinese", "russian", "japanese", "korean",
    "french", "german", "spanish", "italian", "portuguese",
}

_LANG_ALIASES = {
    "ru": "russian", "en": "english", "zh": "chinese",
    "ja": "japanese", "ko": "korean",
}


def _resolve_lang(user_lang: Optional[str]) -> str:
    """Normalize a user-supplied language string.

    Returns the alias or the lowercased input, falling back to the
    global LANG default when *user_lang* is empty.
    """
    if not user_lang or not user_lang.strip():
        return LANG
    norm = user_lang.strip().lower()
    resolved = _LANG_ALIASES.get(norm, norm)
    if resolved not in KNOWN_LANGS:
        _log(f"WARNING: unknown language '{user_lang}' (resolved to '{resolved}'); "
             "the model may reject it with QT_STATUS_INVALID_PARAMS")
    return resolved


def _get_lang_code(user_lang: Optional[str] = None) -> str:
    """Map the synthesis language setting to a locale-tagged folder name."""
    lang = _resolve_lang(user_lang)
    mapping = {
        "russian": "ru_RU",
        "english": "en_US",
        "chinese": "zh_CN",
        "japanese": "ja_JP",
        "korean": "ko_KR",
        "french": "fr_FR",
        "german": "de_DE",
        "spanish": "es_ES",
        "italian": "it_IT",
        "portuguese": "pt_BR",
        "auto": "en_US"
    }
    return mapping.get(lang, "en_US")


def _get_voice_refs_path() -> Path:
    """Get the dynamic path to voice_refs_<lang_code>.json, migrating global database if necessary."""
    lang_code = _get_lang_code()
    refs_dir = VOICES_DIR / "voice_refs"
    refs_dir.mkdir(parents=True, exist_ok=True)
    path = refs_dir / f"voice_refs_{lang_code}.json"
    if not path.exists():
        global_path = refs_dir / "voice_refs.json"
        if global_path.exists():
            import shutil
            try:
                shutil.copy(global_path, path)
                _log(f"Migrated global voice_refs.json to language-specific database: {path}")
            except Exception as exc:
                _log(f"WARNING: failed to copy template voice_refs.json to {path}: {exc}")
        else:
            example_path = refs_dir / "voice_refs.json.example"
            if example_path.exists():
                import shutil
                try:
                    shutil.copy(example_path, path)
                    _log(f"Initialized language-specific database from example: {path}")
                except Exception as exc:
                    _log(f"WARNING: failed to copy example to {path}: {exc}")
    return path


# ---------------------------------------------------------------------------
# Settings Management
# ---------------------------------------------------------------------------
def _load_settings() -> Dict[str, Any]:
    if SETTINGS_PATH.exists():
        try:
            with SETTINGS_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                _SETTINGS.update(data)
                _log(f"settings loaded from {SETTINGS_PATH}")
        except Exception as exc:
            _log(f"WARNING: failed to load settings: {exc}")
    _apply_settings()
    return _SETTINGS


def _save_settings() -> None:
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with SETTINGS_PATH.open("w", encoding="utf-8") as f:
            json.dump(_SETTINGS, f, ensure_ascii=False, indent=2)
            f.write("\n")
        _log(f"settings saved to {SETTINGS_PATH}")
    except Exception as exc:
        _log(f"WARNING: failed to save settings: {exc}")


def _resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        if path.exists():
            return path
        path = Path(path.name)
    resolved = PROJECT_ROOT / path
    if resolved.exists():
        return resolved
    # Try under Voices/ directory
    voices_resolved = VOICES_DIR / path
    if voices_resolved.exists():
        return voices_resolved
    if len(path.parts) >= 2 and path.parts[0] in ("qwen_speakers", "runtime_speakers"):
        lang_code = _get_lang_code()
        lang_resolved = VOICES_DIR / path.parts[0] / lang_code / Path(*path.parts[1:])
        if lang_resolved.exists():
            return lang_resolved
    # Try basename only under Voices/qwen_speakers/<lang>
    if len(path.parts) == 1:
        lang_code = _get_lang_code()
        for subdir in ("qwen_speakers", "runtime_speakers"):
            lang_resolved = VOICES_DIR / subdir / lang_code / path
            if lang_resolved.exists():
                return lang_resolved
    return resolved


def _apply_settings() -> None:
    """Copy _SETTINGS dict into the module-level globals used by synthesis."""
    s = _SETTINGS
    global LANG, SEED, MAX_NEW_TOKENS, DO_SAMPLE, TEMPERATURE, TOP_K, TOP_P
    global REPETITION_PENALTY, SUB_DO_SAMPLE, SUB_TEMPERATURE, SUB_TOP_K, SUB_TOP_P
    global USE_FA, CLAMP_FP16, CODEC_CHUNK_SEC, CODEC_LEFT_CONTEXT_SEC
    global MAX_TEXT_CHARS, APPEND_ENDING_PAUSE, ENDING_PAUSE_TEXT
    global MIN_OUTPUT_DURATION, DEBUG_SAVE_TEXT, TALKER_PATH, CODEC_PATH

    LANG                = str(s.get("lang", LANG))
    SEED                = int(s.get("seed", SEED))
    MAX_NEW_TOKENS      = int(s.get("max_new_tokens", MAX_NEW_TOKENS))
    DO_SAMPLE           = bool(s.get("do_sample", DO_SAMPLE))
    TEMPERATURE         = float(s.get("temperature", TEMPERATURE))
    TOP_K               = int(s.get("top_k", TOP_K))
    TOP_P               = float(s.get("top_p", TOP_P))
    REPETITION_PENALTY  = float(s.get("repetition_penalty", REPETITION_PENALTY))
    SUB_DO_SAMPLE       = bool(s.get("subtalker_do_sample", SUB_DO_SAMPLE))
    SUB_TEMPERATURE     = float(s.get("subtalker_temperature", SUB_TEMPERATURE))
    SUB_TOP_K           = int(s.get("subtalker_top_k", SUB_TOP_K))
    SUB_TOP_P           = float(s.get("subtalker_top_p", SUB_TOP_P))
    USE_FA              = bool(s.get("use_fa", USE_FA))
    CLAMP_FP16          = bool(s.get("clamp_fp16", CLAMP_FP16))
    CODEC_CHUNK_SEC     = float(s.get("codec_chunk_sec", CODEC_CHUNK_SEC))
    CODEC_LEFT_CONTEXT_SEC = float(s.get("codec_left_context_sec", CODEC_LEFT_CONTEXT_SEC))
    MAX_TEXT_CHARS      = int(s.get("max_text_chars", MAX_TEXT_CHARS))
    APPEND_ENDING_PAUSE = bool(s.get("append_ending_pause", APPEND_ENDING_PAUSE))
    ENDING_PAUSE_TEXT   = str(s.get("ending_pause_text", ENDING_PAUSE_TEXT))
    MIN_OUTPUT_DURATION = float(s.get("min_output_duration", MIN_OUTPUT_DURATION))
    DEBUG_SAVE_TEXT     = bool(s.get("debug_save_text", DEBUG_SAVE_TEXT))
    TALKER_PATH         = _resolve_path(str(s.get("talker_path", str(TALKER_PATH))))
    CODEC_PATH          = _resolve_path(str(s.get("codec_path", str(CODEC_PATH))))

    # Reload voice refs database and start background caching for the active language
    try:
        from src.services.importer import reload_voice_refs
        from src.services.cache import _precache_all_voices
        reload_voice_refs()
        import threading as _thr
        _thr.Thread(target=_precache_all_voices, daemon=True).start()
    except Exception as exc:
        _log(f"WARNING: failed to reload voice refs/precache on settings update: {exc}")
