import os
import time
import ctypes
import threading
from pathlib import Path
from ctypes import POINTER, c_float, c_int32
from typing import Any, Dict, Optional

from src import config
from src.config import _log
from src.core.bindings import (
    ABI_VERSION, QtInitParams, QtTtsParams, QtAudio,
    QT_STATUS_OK, _STATUS_NAMES, qt_version, qt_last_error,
    qt_init_default_params, qt_init, qt_free, qt_tts_default_params,
    qt_synthesize, qt_audio_free
)

# Active backend instance singleton
PERSISTENT_BACKEND: Optional['PersistentQwenTTSBackend'] = None


class PersistentQwenTTSBackend:
    """Thin ctypes wrapper around the qwen.dll public ABI."""

    def __init__(self, talker_path: Path, codec_path: Path, *,
                 use_fa: bool = True, clamp_fp16: bool = False) -> None:
        self.lock = threading.Lock()
        self.talker_path = talker_path
        self.codec_path  = codec_path
        self._ctx        = None
        self._ref_buf    = None  # keeps the ctypes ref-audio buffer alive

        _log("qwentts_persistent model load start")
        _log(f"talker path: {talker_path}")
        _log(f"codec path:  {codec_path}")
        _log(f"qt_version:  {qt_version().decode()}")

        if not talker_path.exists():
            raise RuntimeError(f"talker GGUF not found: {talker_path}")
        if not codec_path.exists():
            raise RuntimeError(f"codec GGUF not found: {codec_path}")

        iparams = QtInitParams()
        qt_init_default_params(ctypes.byref(iparams))
        iparams.abi_version  = ABI_VERSION
        iparams.talker_path  = str(talker_path).encode("utf-8")
        iparams.codec_path   = str(codec_path).encode("utf-8")
        iparams.use_fa       = use_fa
        iparams.clamp_fp16   = clamp_fp16

        started = time.perf_counter()
        ctx = qt_init(ctypes.byref(iparams))
        if not ctx:
            err = qt_last_error()
            msg = err.decode() if err else "unknown error"
            raise RuntimeError(f"qt_init failed: {msg}")
        self._ctx = ctx
        elapsed = time.perf_counter() - started
        _log("qwentts_persistent model load end")
        _log(f"model load time: {elapsed:.2f}s")

    def __del__(self):
        if self._ctx is not None:
            try:
                qt_free(self._ctx)
            except Exception:
                pass
            self._ctx = None

    def infer(
        self,
        voice_ref: Dict[str, str],
        gen_text: str,
        output_path: Path,
        speaker_wav: Optional[str],
        lang: Optional[str],
    ) -> Optional[Path]:
        import numpy as np
        from src.services.cache import _ensure_voice_cache
        from src.services.audio import (
            _read_wav_mono_24k, _write_wav_float32_mono,
            _save_debug_text, _diagnose_qwentts_output
        )

        ref_audio_path = Path(voice_ref["ref_audio"])
        ref_text       = voice_ref["ref_text"]

        if not ref_audio_path.exists():
            _log(f"ERROR: ref_audio not found: {ref_audio_path}")
            return None
        if not ref_text.strip():
            _log("ERROR: ref_text is empty")
            return None

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            output_path.unlink(missing_ok=True)

        # Save debug text before synthesis.
        try:
            debug_text_path = _save_debug_text(output_path, gen_text)
            if debug_text_path:
                _log(f"debug QwenTTS gen_text saved: {debug_text_path}")
        except Exception as exc:
            _log(f"WARNING: failed to save QwenTTS gen_text debug file: {exc}")

        # Build synthesis parameters — prefer cached .spk + .rvq (ABI v2).
        params = QtTtsParams()
        qt_tts_default_params(ctypes.byref(params))
        params.abi_version           = ABI_VERSION
        params.text                  = gen_text.encode("utf-8")
        params.lang                  = config._resolve_lang(lang).encode("utf-8")
        params.seed                  = config.SEED
        params.max_new_tokens        = config.MAX_NEW_TOKENS
        params.do_sample             = config.DO_SAMPLE
        params.temperature           = config.TEMPERATURE
        params.top_k                 = config.TOP_K
        params.top_p                 = config.TOP_P
        params.repetition_penalty    = config.REPETITION_PENALTY
        params.subtalker_do_sample   = config.SUB_DO_SAMPLE
        params.subtalker_temperature = config.SUB_TEMPERATURE
        params.subtalker_top_k       = config.SUB_TOP_K
        params.subtalker_top_p       = config.SUB_TOP_P
        params.codec_chunk_sec       = config.CODEC_CHUNK_SEC
        params.codec_left_context_sec = config.CODEC_LEFT_CONTEXT_SEC

        # Try ABI v2 cached path first.
        vc = _ensure_voice_cache(voice_ref["ref_audio"], lang)
        if vc is not None and vc.ref_text is not None:
            _log("using cached voice (spk + rvq, ABI v2)")
            params.ref_spk_emb = ctypes.cast(vc.spk_array, POINTER(c_float))
            params.ref_spk_dim = vc.spk_dim
            params.ref_codes   = ctypes.cast(vc.codes_array, POINTER(c_int32))
            params.ref_T       = vc.ref_T
            params.ref_text    = vc.ref_text
        else:
            # Fall back to raw audio path (ABI v1 compatible).
            _log("using raw audio path (no voice cache)")
            try:
                ref_floats, ref_n = _read_wav_mono_24k(str(ref_audio_path))
            except Exception as exc:
                _log(f"ERROR: ref_audio decode failed: {exc}")
                return None
            self._ref_buf = (c_float * ref_n)(*ref_floats.tolist())
            ref_ptr = ctypes.cast(self._ref_buf, POINTER(c_float))
            params.ref_audio_24k    = ref_ptr
            params.ref_n_samples    = ref_n
            params.ref_text         = ref_text.encode("utf-8")

        if config.DUMP_DIR is not None:
            params.dump_dir = str(config.DUMP_DIR).encode("utf-8")

        _log(f"temperature: {config.TEMPERATURE}")
        _log(f"top_k: {config.TOP_K}")
        _log(f"top_p: {config.TOP_P}")
        _log(f"repetition_penalty: {config.REPETITION_PENALTY}")
        _log(f"max_new_tokens: {config.MAX_NEW_TOKENS}")
        _log(f"seed: {config.SEED}")
        _log(f"lang: {params.lang.decode()}")
        _log(f"use_fa: {config.USE_FA}")
        _log(f"clamp_fp16: {config.CLAMP_FP16}")

        _log("qwentts_persistent inference waiting for lock")
        started = time.perf_counter()

        audio = QtAudio()
        try:
            with self.lock:
                _log("qwentts_persistent lock acquired")
                _log("qwentts_persistent inference start")
                _log(f"output path: {output_path}")
                status = qt_synthesize(self._ctx, ctypes.byref(params), ctypes.byref(audio))
        except Exception as exc:
            elapsed = time.perf_counter() - started
            _log(f"inference time before failure: {elapsed:.2f}s")
            _log(f"ERROR: qwentts_persistent inference raised: {exc}")
            self._ref_buf = None
            return None
        finally:
            _log("qwentts_persistent lock released")

        elapsed = time.perf_counter() - started
        _log("qwentts_persistent inference end")
        _log(f"inference time: {elapsed:.2f}s")

        # Check status.
        if status != QT_STATUS_OK:
            name = _STATUS_NAMES.get(status, str(status))
            err  = qt_last_error()
            msg  = err.decode() if err else ""
            _log(f"ERROR: qt_synthesize returned {name}: {msg}")
            self._ref_buf = None
            return None

        if audio.n_samples <= 0 or not audio.samples:
            _log("ERROR: synthesis returned empty audio")
            qt_audio_free(ctypes.byref(audio))
            self._ref_buf = None
            return None

        sample_rate = audio.sample_rate
        n_samples   = audio.n_samples

        samples = np.ctypeslib.as_array(audio.samples, shape=(n_samples,)).copy()
        qt_audio_free(ctypes.byref(audio))
        self._ref_buf = None

        try:
            _write_wav_float32_mono(output_path, samples, sample_rate)
        except Exception as exc:
            _log(f"ERROR: failed to write output WAV: {exc}")
            return None

        _log("success: qwentts_persistent output WAV created")
        try:
            _diagnose_qwentts_output(
                output_path=output_path,
                text=gen_text,
                speaker_wav=speaker_wav,
                voice_ref=voice_ref,
                inference_time=elapsed,
            )
        except Exception as exc:
            _log(f"WARNING: failed to write QwenTTS output diagnostics: {exc}")

        return output_path


def _detect_backends() -> Dict[str, str]:
    """Return {backend_name: status} checking which ggml backend DLLs exist."""
    backends: Dict[str, str] = {}
    bin_dir = config.BIN_DIR
    qwen = bin_dir / "qwen.dll"
    if not qwen.exists():
        return {"qwentts_CPU": "not_built", "qwentts_CUDA": "not_built", "qwentts_VULKAN": "not_built"}

    backends["qwentts_CPU"] = "ready"
    backends["qwentts_CUDA"]   = "ready" if (bin_dir / "ggml-cuda.dll").exists() else "not_built"
    backends["qwentts_VULKAN"] = "ready" if (bin_dir / "ggml-vulkan.dll").exists() else "not_built"
    return backends


def _switch_backend(backend_name: str) -> Dict[str, Any]:
    """Free current model context, set GGML_BACKEND, and re-init."""
    global PERSISTENT_BACKEND

    backend_env_map = {
        "qwentts_CPU":    "CPU",
        "qwentts_CUDA":   "CUDA0",
        "qwentts_VULKAN": "Vulkan0",
    }
    ggml_backend = backend_env_map.get(backend_name)
    if ggml_backend is None:
        return {"success": False, "error": f"Unknown backend '{backend_name}'"}

    old_backend = PERSISTENT_BACKEND
    PERSISTENT_BACKEND = None
    if old_backend is not None:
        try:
            ctx = old_backend._ctx
            if ctx is not None:
                old_backend._ctx = None
                qt_free(ctx)
                _log("previous model context freed via qt_free")
        except Exception as exc:
            _log(f"WARNING: cleanup of previous backend failed: {exc}")
    del old_backend

    os.environ["GGML_BACKEND"] = ggml_backend
    _log(f"GGML_BACKEND={ggml_backend}")

    try:
        new_backend = PersistentQwenTTSBackend(
            config.TALKER_PATH, config.CODEC_PATH,
            use_fa=config.USE_FA, clamp_fp16=config.CLAMP_FP16,
        )
    except Exception as exc:
        return {"success": False, "error": f"model re-init failed: {exc}"}

    PERSISTENT_BACKEND = new_backend
    config._SETTINGS["backend"] = backend_name
    config._save_settings()
    return {"success": True, "backend": backend_name}
