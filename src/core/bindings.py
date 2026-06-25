import os
import ctypes
from ctypes import (
    CFUNCTYPE, POINTER, Structure, c_bool, c_char_p, c_float, c_int, c_int32, c_int64, c_void_p,
)
from pathlib import Path
from src.config import BIN_DIR

# ---------------------------------------------------------------------------
# ctypes ABI — matches qwen.h (QT_ABI_VERSION = 2) exactly.
# ---------------------------------------------------------------------------

ABI_VERSION = 2

# Callback types
qt_cancel_cb      = CFUNCTYPE(c_bool, c_void_p)                            # bool (*)(void *)
qt_audio_chunk_cb = CFUNCTYPE(c_bool, POINTER(c_float), c_int, c_void_p)   # bool (*)(const float*, int, void *)
qt_log_cb         = CFUNCTYPE(None, c_int, c_char_p, c_void_p)             # void (*)(int, const char*, void*)


class QtInitParams(Structure):
    """Mirrors struct qt_init_params from qwen.h."""
    _fields_ = [
        ("abi_version", c_int),
        ("talker_path", c_char_p),
        ("codec_path",  c_char_p),
        ("use_fa",      c_bool),
        ("clamp_fp16",  c_bool),
    ]


class QtTtsParams(Structure):
    """Mirrors struct qt_tts_params from qwen.h."""
    _fields_ = [
        ("abi_version",             c_int),
        ("text",                    c_char_p),
        ("lang",                    c_char_p),
        ("instruct",                c_char_p),
        ("speaker",                 c_char_p),
        ("ref_audio_24k",           POINTER(c_float)),
        ("ref_n_samples",           c_int),
        ("ref_text",                c_char_p),
        ("seed",                    c_int64),
        ("max_new_tokens",          c_int),
        ("do_sample",               c_bool),
        ("temperature",             c_float),
        ("top_k",                   c_int),
        ("top_p",                   c_float),
        ("repetition_penalty",      c_float),
        ("subtalker_do_sample",     c_bool),
        ("subtalker_temperature",   c_float),
        ("subtalker_top_k",         c_int),
        ("subtalker_top_p",         c_float),
        ("dump_dir",                c_char_p),
        ("cancel",                  qt_cancel_cb),
        ("cancel_user_data",        c_void_p),
        ("on_chunk",                qt_audio_chunk_cb),
        ("on_chunk_user_data",      c_void_p),
        ("codec_chunk_sec",         c_float),
        ("codec_left_context_sec",  c_float),

        # ABI v2 — pre-encoded speaker embedding + RVQ codes.
        ("ref_spk_emb",             POINTER(c_float)),
        ("ref_spk_dim",             c_int),
        ("ref_codes",               POINTER(c_int32)),
        ("ref_T",                   c_int),
    ]


class QtAudio(Structure):
    """Mirrors struct qt_audio from qwen.h."""
    _fields_ = [
        ("samples",     POINTER(c_float)),
        ("n_samples",   c_int),
        ("sample_rate", c_int),
        ("channels",    c_int),
    ]


# Status codes matching enum qt_status.
QT_STATUS_OK              = 0
QT_STATUS_INVALID_PARAMS  = -1
QT_STATUS_MODE_INVALID    = -2
QT_STATUS_GENERATE_FAILED = -3
QT_STATUS_OOM             = -4
QT_STATUS_CANCELLED       = -5

_STATUS_NAMES = {
    0:  "QT_STATUS_OK",
    -1: "QT_STATUS_INVALID_PARAMS",
    -2: "QT_STATUS_MODE_INVALID",
    -3: "QT_STATUS_GENERATE_FAILED",
    -4: "QT_STATUS_OOM",
    -5: "QT_STATUS_CANCELLED",
}


def _find_backend_dir(bin_base: Path) -> Path | None:
    """Check if qwen.dll exists in the common bin directory.

    With the unified build, all backends live in the same qwen.dll.
    The GGML_BACKEND environment variable selects which backend to use.
    """
    dll = bin_base / "qwen.dll"
    if dll.exists():
        print(f"[qwentts-adapter] found qwen.dll in common bin: {bin_base}", flush=True)
        return bin_base
    return None


def _load_qwen_dll(bin_base: Path):
    """Load qwen.dll from the common bin directory.

    Explicitly pre-loads ggml*.dll dependencies before loading qwen.dll
    to work around Windows DLL search-path issues with transitive deps.
    """
    backend_dir = _find_backend_dir(bin_base)
    if backend_dir is None:
        raise RuntimeError(
            f"no qwen.dll found in {bin_base}. "
            f"Expected qwen.dll + ggml*.dll in the same directory."
        )

    abs_dir = str(backend_dir.resolve())

    # Add to both DLL search path and system PATH
    try:
        os.add_dll_directory(abs_dir)
    except (OSError, AttributeError):
        pass
    os.environ["PATH"] = abs_dir + os.pathsep + os.environ.get("PATH", "")

    # Pre-load ggml dependency DLLs in the correct order so that qwen.dll
    # finds them already in memory.  Load order matters: base → backend →
    # ggml umbrella → qwen.
    _GGML_LOAD_ORDER = [
        "ggml-base.dll",
        "ggml-cpu.dll",
        "ggml-cuda.dll",
        "ggml-vulkan.dll",
        "ggml.dll",
    ]
    preloaded = []
    for dep_name in _GGML_LOAD_ORDER:
        dep_path = backend_dir / dep_name
        if dep_path.exists():
            try:
                ctypes.CDLL(str(dep_path), winmode=0)
                preloaded.append(dep_name)
            except Exception as exc:
                print(f"[qwentts-adapter] note: could not pre-load {dep_name}: {exc}", flush=True)
    if preloaded:
        print(f"[qwentts-adapter] pre-loaded dependencies: {', '.join(preloaded)}", flush=True)

    dll_path = str(backend_dir / "qwen.dll")
    print(f"[qwentts-adapter] loading qwen.dll from {dll_path}", flush=True)
    try:
        return ctypes.CDLL(dll_path, winmode=0)
    except Exception:
        old_cwd = Path.cwd()
        os.chdir(abs_dir)
        try:
            return ctypes.CDLL("qwen.dll")
        finally:
            os.chdir(old_cwd)


# DLL loading — done once at module level.
_QWEN = _load_qwen_dll(BIN_DIR)


def _bind(name: str, restype, argtypes):
    """Shortcut to set the result type and argument types on a DLL function."""
    fn = getattr(_QWEN, name, None)
    if fn is None:
        raise RuntimeError(f"qwen.dll does not export '{name}' — version mismatch?")
    fn.restype = restype
    fn.argtypes = argtypes
    return fn


qt_version               = _bind("qt_version",               c_char_p,                [])
qt_last_error            = _bind("qt_last_error",            c_char_p,                [])
qt_init_default_params   = _bind("qt_init_default_params",   None,                    [POINTER(QtInitParams)])
qt_init                  = _bind("qt_init",                  c_void_p,                [POINTER(QtInitParams)])
qt_free                  = _bind("qt_free",                  None,                    [c_void_p])
qt_tts_default_params    = _bind("qt_tts_default_params",    None,                    [POINTER(QtTtsParams)])
qt_synthesize            = _bind("qt_synthesize",            c_int,                   [c_void_p, POINTER(QtTtsParams), POINTER(QtAudio)])
qt_audio_free            = _bind("qt_audio_free",            None,                    [POINTER(QtAudio)])
qt_num_codebooks         = _bind("qt_num_codebooks",         c_int,                   [c_void_p])
