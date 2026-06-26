import ctypes
import subprocess
import threading
from pathlib import Path
from typing import Dict, Optional

from src import config
from src.config import _log, PROJECT_ROOT, VOICES_DIR, RVQ_CACHE_DIR, CODEC_PATH, TALKER_PATH, RUNTIME_SPEAKERS_DIR
from src.services.audio import _unpack_rvq_codes


class VoiceCache:
    """Pre-encoded speaker embedding (spk) and RVQ codes for one voice."""

    __slots__ = ("spk_array", "spk_dim", "codes_array", "ref_T", "ref_text")

    def __init__(self, rvq_path: Path, spk_path: Path, txt_path: Path, fallback_ref_text: Optional[str] = None):
        # 1. RVQ codes
        data = rvq_path.read_bytes()
        self.codes_array, self.ref_T = _unpack_rvq_codes(data)

        # 2. Speaker embedding — raw f32 binary.
        spk_data = spk_path.read_bytes()
        self.spk_dim = len(spk_data) // 4
        self.spk_array = (ctypes.c_float * self.spk_dim).from_buffer_copy(spk_data)

        # 3. Reference text.
        self.ref_text = None
        if txt_path.exists():
            self.ref_text = txt_path.read_text(encoding="utf-8").strip().encode("utf-8")
        elif fallback_ref_text:
            self.ref_text = fallback_ref_text.strip().encode("utf-8")


_VOICE_CACHE: Dict[str, VoiceCache] = {}


def _find_codec_exe() -> Path | None:
    """Locate qwen-codec.exe in backend bin directories."""
    # Check unified/common bin folder first
    candidate = PROJECT_ROOT / "bin" / "qwen-codec.exe"
    if candidate.exists():
        return candidate
    for name in ("qwentts_VULKAN", "qwentts_CUDA", "qwentts_CPU"):
        candidate = PROJECT_ROOT / "bin" / name / "qwen-codec.exe"
        if candidate.exists():
            return candidate
    return None


_encode_lock = threading.Lock()


def _encode_voice_to_rvq(wav_path: Path, rvq_path: Path, spk_path: Path, txt_path: Path) -> bool:
    """Run qwen-codec.exe to pre-encode a reference WAV into .spk + .rvq."""
    with _encode_lock:
        if rvq_path.exists() and spk_path.exists():
            return True

        codec_exe = _find_codec_exe()
        if codec_exe is None:
            _log("WARNING: qwen-codec.exe not found — voice caching disabled")
            return False

        cmd = [str(codec_exe), "--model", str(CODEC_PATH), "-i", str(wav_path), "--talker", str(TALKER_PATH)]
        _log(f"encoding voice: {wav_path.name}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                _log(f"WARNING: qwen-codec failed for {wav_path.name}: {result.stderr[:200]}")
                return False
        except Exception as exc:
            _log(f"WARNING: qwen-codec exception for {wav_path.name}: {exc}")
            return False

        base_stem = wav_path.with_suffix("")
        gen_rvq = base_stem.with_suffix(".rvq")
        gen_spk  = base_stem.with_suffix(".spk")

        if gen_rvq.exists() and gen_spk.exists():
            rvq_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                gen_rvq.replace(rvq_path)
                gen_spk.replace(spk_path)
                _log(f"  cached -> {rvq_path.name}, {spk_path.name}")
                return True
            except Exception as exc:
                _log(f"WARNING: failed to move generated cache files: {exc}")
                return False

        _log(f"WARNING: qwen-codec did not produce output for {wav_path.name}")
        return False


_CACHE_PROGRESS = {
    "running": False,
    "total": 0,
    "completed": 0,
    "remaining": 0,
    "elapsed_sec": 0,
    "eta_sec": 0,
    "current_file": "",
}

_cache_thread_lock = threading.Lock()


def _ensure_voice_cache(
    ref_audio: str,
    user_lang: Optional[str] = None,
    fallback_ref_text: Optional[str] = None
) -> VoiceCache | None:
    """Return a cached VoiceCache for *ref_audio* if exists, but never encode it on demand."""
    wav_path = _resolve_path(ref_audio)
    key = str(wav_path.resolve())

    if key in _VOICE_CACHE:
        return _VOICE_CACHE[key]

    stem = wav_path.stem
    rvq_path = RVQ_CACHE_DIR / f"{stem}.rvq"
    spk_path = RVQ_CACHE_DIR / f"{stem}.spk"
    txt_path = wav_path.with_suffix(".txt")

    if not rvq_path.exists() or not spk_path.exists() or \
       (wav_path.exists() and wav_path.stat().st_mtime > rvq_path.stat().st_mtime):
        return None

    try:
        cache = VoiceCache(rvq_path, spk_path, txt_path, fallback_ref_text=fallback_ref_text)
        _VOICE_CACHE[key] = cache
        _log(f"voice cached: {stem} ({cache.ref_T} frames, spk_dim={cache.spk_dim})")
        return cache
    except Exception as exc:
        _log(f"WARNING: failed to load voice cache for {stem}: {exc}")
        return None


def _resolve_path(path_text: str) -> Path:
    return config._resolve_path(path_text)


_precache_lock = threading.Lock()


def _precache_all_voices(encode_missing: bool = False) -> None:
    """Load every pre-existing voice cache, and optionally encode missing ones."""
    if not _precache_lock.acquire(blocking=False):
        _log("voice caching already in progress, skipping duplicate thread")
        return
    try:
        RVQ_CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # First load cached voices registered in voice_refs, even if WAV file is not present on disk
        try:
            from src.services.importer import VOICE_REFS
            for key, ref in list(VOICE_REFS.items()):
                ref_audio = ref.get("ref_audio")
                ref_text = ref.get("ref_text")
                if not ref_audio:
                    continue
                wav_path = _resolve_path(ref_audio)
                stem = wav_path.stem
                rvq_path = RVQ_CACHE_DIR / f"{stem}.rvq"
                spk_path = RVQ_CACHE_DIR / f"{stem}.spk"
                if rvq_path.exists() and spk_path.exists():
                    cache_key = str(wav_path.resolve())
                    if cache_key not in _VOICE_CACHE:
                        try:
                            cache = VoiceCache(rvq_path, spk_path, wav_path.with_suffix(".txt"), fallback_ref_text=ref_text)
                            _VOICE_CACHE[cache_key] = cache
                        except Exception:
                            pass
        except Exception as exc:
            _log(f"WARNING: failed preloading cached voice references: {exc}")

        # Then scan directories for actual WAVs to update/encode
        for d in (VOICES_DIR / "qwen_speakers", RUNTIME_SPEAKERS_DIR):
            if not d.exists():
                continue
            for wav in sorted(d.glob("*.wav")):
                stem = wav.stem
                rvq_path = RVQ_CACHE_DIR / f"{stem}.rvq"
                spk_path = RVQ_CACHE_DIR / f"{stem}.spk"
                if not rvq_path.exists() or not spk_path.exists() or \
                   wav.stat().st_mtime > rvq_path.stat().st_mtime:
                    if encode_missing:
                        _encode_voice_to_rvq(wav, rvq_path, spk_path, wav.with_suffix(".txt"))
                    else:
                        if not rvq_path.exists() or not spk_path.exists():
                            continue
                try:
                    cache = VoiceCache(rvq_path, spk_path, wav.with_suffix(".txt"))
                    key = str(wav.resolve())
                    _VOICE_CACHE[key] = cache
                except Exception:
                    pass
        _log(f"voice cache loaded: {len(_VOICE_CACHE)} voices")
    finally:
        _precache_lock.release()


def _start_cache_encoding_thread() -> bool:
    """Start background cache encoding process for all voices."""
    global _cache_thread_lock
    if not _cache_thread_lock.acquire(blocking=False):
        return False

    def run():
        import time
        from src.services.importer import VOICE_REFS
        global _CACHE_PROGRESS

        try:
            # Gather all WAVs
            wav_paths = []

            # 1. WAVs from voice refs
            for key, ref in list(VOICE_REFS.items()):
                ref_audio = ref.get("ref_audio")
                if not ref_audio:
                    continue
                wav_path = _resolve_path(ref_audio)
                if wav_path.exists() and wav_path not in wav_paths:
                    wav_paths.append(wav_path)

            # 2. WAVs from directories
            for d in (VOICES_DIR / "qwen_speakers", RUNTIME_SPEAKERS_DIR):
                if not d.exists():
                    continue
                for wav in d.glob("*.wav"):
                    if wav.exists() and wav not in wav_paths:
                        wav_paths.append(wav)

            # Filter only those that actually need encoding
            to_encode = []
            for wav in wav_paths:
                stem = wav.stem
                rvq_path = RVQ_CACHE_DIR / f"{stem}.rvq"
                spk_path = RVQ_CACHE_DIR / f"{stem}.spk"
                if not rvq_path.exists() or not spk_path.exists() or \
                   wav.stat().st_mtime > rvq_path.stat().st_mtime:
                    to_encode.append(wav)

            total = len(to_encode)
            if total == 0:
                _CACHE_PROGRESS = {
                    "running": False,
                    "total": 0,
                    "completed": 0,
                    "remaining": 0,
                    "elapsed_sec": 0,
                    "eta_sec": 0,
                    "current_file": "",
                }
                # Reload existing
                _precache_all_voices(encode_missing=False)
                return

            _CACHE_PROGRESS = {
                "running": True,
                "total": total,
                "completed": 0,
                "remaining": total,
                "elapsed_sec": 0,
                "eta_sec": 0,
                "current_file": "",
            }

            start_time = time.time()
            for idx, wav in enumerate(to_encode):
                _CACHE_PROGRESS["current_file"] = wav.name
                _CACHE_PROGRESS["remaining"] = total - idx

                stem = wav.stem
                rvq_path = RVQ_CACHE_DIR / f"{stem}.rvq"
                spk_path = RVQ_CACHE_DIR / f"{stem}.spk"
                txt_path = wav.with_suffix(".txt")

                _encode_voice_to_rvq(wav, rvq_path, spk_path, txt_path)

                _CACHE_PROGRESS["completed"] = idx + 1
                elapsed = time.time() - start_time
                _CACHE_PROGRESS["elapsed_sec"] = int(elapsed)

                # Estimate remaining time
                avg_time_per_file = elapsed / (idx + 1)
                remaining_files = total - (idx + 1)
                _CACHE_PROGRESS["eta_sec"] = int(avg_time_per_file * remaining_files)

            _CACHE_PROGRESS["running"] = False
            _CACHE_PROGRESS["remaining"] = 0
            _CACHE_PROGRESS["current_file"] = ""

            # Reload all into memory cache
            _precache_all_voices(encode_missing=False)
        finally:
            _cache_thread_lock.release()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return True
