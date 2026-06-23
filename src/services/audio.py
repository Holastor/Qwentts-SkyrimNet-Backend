import io
import json
import wave
import ctypes
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np

from src import config
from src.config import _log


def generate_silence_wav(duration_seconds: float = 1.0, sample_rate: int = 24000) -> bytes:
    """Create a valid mono 16-bit PCM silence WAV in memory."""
    frame_count = max(1, int(duration_seconds * sample_rate))
    silence_frames = b"\x00\x00" * frame_count

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(silence_frames)

    return buffer.getvalue()


def _read_wav_mono_24k(path: str) -> tuple[np.ndarray, int]:
    """Decode a WAV file to 24 kHz mono PCM float32."""
    with wave.open(path, "rb") as w:
        n_channels   = w.getnchannels()
        sample_rate  = w.getframerate()
        sample_width = w.getsampwidth()
        n_frames     = w.getnframes()
        raw          = w.readframes(n_frames)

    if sample_width == 2:
        samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    elif sample_width == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        i32 = (b[:, 0].astype(np.int32)
               | (b[:, 1].astype(np.int32) << 8)
               | (b[:, 2].astype(np.int32) << 16))
        i32[i32 & 0x800000 != 0] -= 0x1000000
        samples = i32.astype(np.float32) / 8388608.0
    elif sample_width == 4:
        try:
            samples = np.frombuffer(raw, dtype="<f4").astype(np.float32)
        except Exception:
            samples = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise RuntimeError(f"unsupported sample width: {sample_width}")

    if n_channels == 1:
        mono = samples
    elif n_channels == 2:
        left  = samples[0::2]
        right = samples[1::2]
        mono  = 0.5 * (left + right)
    else:
        frames = samples.reshape(-1, n_channels)
        mono   = frames.mean(axis=1).astype(np.float32)

    if sample_rate != 24000:
        target_len = int(round(len(mono) * 24000 / sample_rate))
        xp    = np.arange(len(mono), dtype=np.float64)
        x_new = np.linspace(0, len(mono) - 1, target_len, dtype=np.float64)
        mono  = np.interp(x_new, xp, mono.astype(np.float64)).astype(np.float32)

    return mono, len(mono)


def _write_wav_float32_mono(out_path: Path, samples: np.ndarray, sample_rate: int = 24000) -> None:
    """Write mono float32 (-1 .. 1) samples as a 16-bit PCM WAV file."""
    pcm = np.clip(samples, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())


def _unpack_rvq_codes(data: bytes, K: int = 16, code_bits: int = 11) -> tuple[ctypes.Array, int]:
    """Unpack binary RVQ file into a c_int32 array."""
    mask = (1 << code_bits) - 1
    total_bits = len(data) * 8
    n_codes = total_bits // code_bits
    out = (ctypes.c_int32 * n_codes)()

    acc = 0
    bits_in_acc = 0
    in_pos = 0
    for i in range(n_codes):
        while bits_in_acc < code_bits and in_pos < len(data):
            acc |= (data[in_pos] << bits_in_acc)
            in_pos += 1
            bits_in_acc += 8
        out[i] = acc & mask
        acc >>= code_bits
        bits_in_acc -= code_bits
    return out, n_codes // K


def _read_wav_duration_info(output_path: Path) -> tuple[Optional[float], Optional[int]]:
    try:
        with wave.open(str(output_path), "rb") as wav_file:
            frame_count = wav_file.getnframes()
            frame_rate = wav_file.getframerate()
            if frame_rate <= 0:
                return None, frame_rate
            return frame_count / float(frame_rate), frame_rate
    except Exception as exc:
        _log(f"WARNING: failed to read WAV duration for {output_path}: {exc}")
        return None, None


def _is_sane_wav_duration(duration: Optional[float], sample_rate: Optional[int]) -> bool:
    if sample_rate is None or duration is None:
        return False
    return 8000 <= sample_rate <= 96000 and 0.1 < duration < 60.0


def _wav_duration_seconds(output_path: Path) -> Optional[float]:
    duration, sample_rate = _read_wav_duration_info(output_path)
    if not _is_sane_wav_duration(duration, sample_rate):
        _log(f"WARNING: invalid WAV duration for {output_path}: "
             f"duration={duration}, sample_rate={sample_rate}")
        return None
    return duration


def _write_qwentts_failed_debug_json(
    output_path: Path,
    text: str,
    speaker_wav: Optional[str],
    voice_ref: Dict[str, str],
    output_duration: Optional[float],
    file_size: int,
    inference_time: float,
) -> Path:
    config.QWENTTS_DEBUG_FAILED_DIR.mkdir(parents=True, exist_ok=True)
    debug_path = config.QWENTTS_DEBUG_FAILED_DIR / f"{output_path.stem}.json"
    payload = {
        "text": text,
        "speaker_wav": speaker_wav,
        "resolved_speaker_key": voice_ref.get("speaker_key"),
        "ref_audio": voice_ref.get("ref_audio"),
        "ref_text": voice_ref.get("ref_text"),
        "output_path": str(output_path),
        "output_duration": output_duration,
        "file_size": file_size,
        "inference_time": inference_time,
    }
    with debug_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return debug_path


def _save_debug_text(output_path: Path, gen_text: str) -> Optional[Path]:
    if not config.DEBUG_SAVE_TEXT:
        return None

    config.QWENTTS_DEBUG_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    text_path = config.QWENTTS_DEBUG_TEXT_DIR / f"{output_path.stem}.txt"
    with text_path.open("w", encoding="utf-8") as file:
        file.write(gen_text)
        file.write("\n")
    return text_path


def _diagnose_qwentts_output(
    output_path: Path,
    text: str,
    speaker_wav: Optional[str],
    voice_ref: Dict[str, str],
    inference_time: float,
) -> None:
    file_size = output_path.stat().st_size
    output_duration = _wav_duration_seconds(output_path)
    text_length = len(text)
    chars_per_second = text_length / output_duration if output_duration and output_duration > 0 else None

    _log(f"output file size bytes: {file_size}")
    if output_duration is None:
        _log("output duration seconds: unknown")
        _log(f"generated text length: {text_length}")
        _log("estimated chars per second: unknown")
        return

    _log(f"output duration seconds: {output_duration:.3f}")
    _log(f"generated text length: {text_length}")
    _log(f"estimated chars per second: {chars_per_second:.2f}")

    if config.MIN_OUTPUT_DURATION > 0 and output_duration < config.MIN_OUTPUT_DURATION:
        _log(
            f"WARNING: output WAV duration {output_duration:.3f}s is shorter than "
            f"--min-output-duration={config.MIN_OUTPUT_DURATION:.3f}s"
        )

    warnings = []
    if output_duration < 1.0 and text_length > 20:
        warnings.append("Suspiciously short output WAV")

    expected_min_duration = max(1.0, text_length / 25.0)
    if output_duration < expected_min_duration * 0.45:
        warnings.append("Possible truncated generation")

    for warning in warnings:
        _log(f"WARNING: {warning}")

    if warnings:
        debug_path = _write_qwentts_failed_debug_json(
            output_path=output_path,
            text=text,
            speaker_wav=speaker_wav,
            voice_ref=voice_ref,
            output_duration=output_duration,
            file_size=file_size,
            inference_time=inference_time,
        )
        _log(f"debug JSON saved: {debug_path}")
