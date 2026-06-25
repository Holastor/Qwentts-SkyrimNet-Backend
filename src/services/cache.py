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


def _ensure_voice_cache(
    ref_audio: str,
    user_lang: Optional[str] = None,
    fallback_ref_text: Optional[str] = None
) -> VoiceCache | None:
    """Return a cached VoiceCache for *ref_audio*, encoding it first if needed."""
    wav_path = _resolve_path(ref_audio)
    key = str(wav_path.resolve())

    if key in _VOICE_CACHE:
        return _VOICE_CACHE[key]

    stem = wav_path.stem
    rvq_path = RVQ_CACHE_DIR / f"{stem}.rvq"
    spk_path = RVQ_CACHE_DIR / f"{stem}.spk"
    txt_path = wav_path.with_suffix(".txt")

    if not wav_path.exists():
        if rvq_path.exists() and spk_path.exists():
            _log(f"ref_audio WAV not found: {wav_path}. But cache files exist, loading from cache.")
        else:
            _log(f"WARNING: ref_audio not found for caching: {wav_path}")
            return None
    else:
        if not rvq_path.exists() or not spk_path.exists() or \
           wav_path.stat().st_mtime > rvq_path.stat().st_mtime:
            if not _encode_voice_to_rvq(wav_path, rvq_path, spk_path, txt_path):
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


def _precache_all_voices() -> None:
    """Encode every voice WAV in qwen_speakers/ and runtime_speakers/."""
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
                if not rvq_path.exists() or not spk_path.exists():
                    _encode_voice_to_rvq(wav, rvq_path, spk_path, wav.with_suffix(".txt"))
                try:
                    cache = VoiceCache(rvq_path, spk_path, wav.with_suffix(".txt"))
                    key = str(wav.resolve())
                    _VOICE_CACHE[key] = cache
                except Exception:
                    pass
        _log(f"voice cache loaded: {len(_VOICE_CACHE)} voices")
    finally:
        _precache_lock.release()
