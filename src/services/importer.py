import io
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src import config
from src.config import _log, PROJECT_ROOT, VOICES_DIR

# Voice refs database in-memory cache
VOICE_REFS: Dict[str, Dict[str, str]] = {}
VOICE_DESIGN_REFS: Dict[str, Dict[str, str]] = {}


def load_voice_refs() -> Dict[str, Dict[str, str]]:
    """Load QwenTTS speaker references from voice_refs_<lang>.json in the project root."""
    path = config._get_voice_refs_path()
    if not path.exists():
        _log(f"WARNING: {path} not found, using empty voice refs")
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as exc:
        _log(f"WARNING: failed to load {path}: {exc}")
        return {}

    if not isinstance(data, dict):
        _log(f"WARNING: {path} must contain a JSON object, using empty voice refs")
        return {}

    valid_refs: Dict[str, Dict[str, str]] = {}
    for key, value in data.items():
        if not isinstance(value, dict):
            _log(f"WARNING: voice ref '{key}' is not an object, skipping")
            continue

        ref_audio = value.get("ref_audio")
        ref_text = value.get("ref_text")

        if not isinstance(ref_text, str) or not isinstance(ref_audio, str):
            _log(f"WARNING: voice ref '{key}' must contain ref_audio and ref_text strings, skipping")
            continue

        valid_refs[key] = {"ref_audio": ref_audio, "ref_text": ref_text}

    _log(f"loaded voice refs: {len(valid_refs)} entries from {path}")
    if "default" not in valid_refs:
        _log(f"WARNING: {path} has no 'default' fallback entry")
    return valid_refs


def load_voice_design_refs() -> Dict[str, Dict[str, str]]:
    """Load QwenTTS design voice references from voice_design_<lang>.json in the project root."""
    path = config._get_voice_design_path()
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as exc:
        _log(f"WARNING: failed to load {path}: {exc}")
        return {}

    if not isinstance(data, dict):
        _log(f"WARNING: {path} must contain a JSON object, using empty voice design refs")
        return {}

    valid_refs: Dict[str, Dict[str, str]] = {}
    for key, value in data.items():
        if not isinstance(value, dict):
            _log(f"WARNING: voice design ref '{key}' is not an object, skipping")
            continue

        instruct = value.get("instruct")
        if not isinstance(instruct, str):
            _log(f"WARNING: voice design ref '{key}' must contain instruct string, skipping")
            continue

        valid_refs[key] = {"instruct": instruct}

    _log(f"loaded voice design refs: {len(valid_refs)} entries from {path}")
    return valid_refs


def reload_voice_refs() -> Dict[str, Dict[str, str]]:
    """Reload voice reference files from disk and update the global VOICE_REFS and VOICE_DESIGN_REFS dicts."""
    global VOICE_REFS, VOICE_DESIGN_REFS
    VOICE_REFS.clear()
    VOICE_REFS.update(load_voice_refs())
    VOICE_DESIGN_REFS.clear()
    VOICE_DESIGN_REFS.update(load_voice_design_refs())
    _log(f"voice_refs reloaded: {len(VOICE_REFS)} custom refs, {len(VOICE_DESIGN_REFS)} design refs")
    return VOICE_REFS


# Initial load
VOICE_REFS.update(load_voice_refs())
VOICE_DESIGN_REFS.update(load_voice_design_refs())

# ---------------------------------------------------------------------------
# Background Import Status
# ---------------------------------------------------------------------------
_IMPORT_THREAD_LOCK = threading.Lock()
_IMPORT_STATUS = {
    "running": False,
    "log": "",
    "completed": False,
    "total": 0,
    "processed": 0,
}
_IMPORT_LOGGER: Optional['RealTimeLogger'] = None


class RealTimeLogger(io.StringIO):
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.content = ""

    def write(self, s):
        with self.lock:
            self.content += s
        return super().write(s)

    def get_realtime_log(self):
        with self.lock:
            return self.content


# Selection logic parameters
MIN_DURATION_SEC = 3.0
MAX_DURATION_SEC = 5.0
MIN_TEXT_LEN = 20
MAX_TEXT_LEN = 120


def _score_sample(text: str, duration: float) -> tuple[float, str]:
    """Score a voice sample for QwenTTS ICL suitability.

    Returns ``(score, reason)`` where lower scores are better.
    """
    import re
    reasons = []

    # Prefer target duration range.
    if duration < MIN_DURATION_SEC:
        return (100.0, f"too short: {duration:.1f}s < {MIN_DURATION_SEC}s")
    if duration > MAX_DURATION_SEC:
        return (50.0, f"long duration: {duration:.1f}s")

    reasons.append(f"duration {duration:.1f}s in [{MIN_DURATION_SEC}, {MAX_DURATION_SEC}]")

    if not text or not text.strip():
        return (99.0, "empty text")

    text_len = len(text.strip())
    if text_len < MIN_TEXT_LEN:
        return (90.0, f"text too short: {text_len} chars")
    if text_len > MAX_TEXT_LEN:
        return (45.0, f"text too long: {text_len} chars")

    reasons.append(f"text length {text_len} in [{MIN_TEXT_LEN}, {MAX_TEXT_LEN}]")

    # Penalise multiple sentences (ICL prefers short neutral phrases).
    sentence_count = max(1, text.count(".") + text.count("!") + text.count("?"))
    if sentence_count > 2:
        return (30.0, f"many sentences: {sentence_count}")

    reasons.append(f"sentences: {sentence_count}")

    # Penalise ALL CAPS / shouting.
    upper_ratio = sum(1 for c in text if c.isupper()) / max(1, len(text))
    if upper_ratio > 0.5:
        return (40.0, "high uppercase ratio (shouting)")

    # Penalise ragged ellipses.
    if re.search(r"\.{4,}", text):
        return (35.0, "contains ragged ellipsis")

    score = max(1.0, 10.0 - text_len / 10.0 + sentence_count * 2.0)
    reasons.append(f"composite score: {score:.1f}")
    return (score, "; ".join(reasons))


def _fetch_json(url: str) -> Any:
    import json
    from urllib.request import urlopen
    try:
        with urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        _log(f"WARNING: failed to fetch {url}: {exc}")
        return None


def _fetch_wav(url: str) -> Optional[bytes]:
    from urllib.request import urlopen
    try:
        with urlopen(url, timeout=120) as resp:
            return resp.read()
    except Exception as exc:
        _log(f"WARNING: failed to download {url}: {exc}")
        return None


def import_voice_samples(
    base_url: str,
    speakers_dir: Path,
    force: bool = False,
    dry_run: bool = False,
    selection_mode: str = "qwentts-safe",
    preserve_existing: bool = True,
    audit_only: bool = False,
    voice_refs_path: Path = None,
    design_mode: bool = False,
) -> list[dict]:
    import urllib.parse
    from datetime import datetime, timezone
    
    global VOICE_REFS
    refs_path = voice_refs_path or config._get_voice_refs_path()
    
    # Reload voice refs database
    reload_voice_refs()
    
    report: list[dict] = []
    
    _log(f"Starting import from base_url: {base_url}")
    _log(f"speakers_dir: {speakers_dir}")
    _log(f"selection_mode: {selection_mode}")
    _log(f"force: {force}")
    _log(f"dry_run: {dry_run}")
    _log(f"preserve_existing: {preserve_existing}")
    
    voice_data = _fetch_json(f"{base_url.rstrip('/')}/voice-samples?api=voice-types")
    if not voice_data:
        _log("ERROR: could not fetch voice types")
        return report

    if isinstance(voice_data, dict):
        voice_types = voice_data.get("voice_types", [])
    else:
        voice_types = voice_data

    if not isinstance(voice_types, list):
        _log(f"WARNING: expected list of voice types, got {type(voice_types)}")
        return report

    _log(f"Found {len(voice_types)} voice types on SkyrimNet")
    with _IMPORT_THREAD_LOCK:
        _IMPORT_STATUS["total"] = len(voice_types)
        _IMPORT_STATUS["processed"] = 0

    for idx, voice_type in enumerate(voice_types):
        with _IMPORT_THREAD_LOCK:
            _IMPORT_STATUS["processed"] = idx
        if isinstance(voice_type, dict):
            voice_name = voice_type.get("voice_type_id", voice_type.get("name", str(voice_type)))
            selected_path = voice_type.get("selected_sample_path", "")
            if not design_mode and (not selected_path or not str(selected_path).strip()):
                _log(f"[{idx + 1}/{len(voice_types)}] Skipping voice: {voice_name} (no selected sample path on SkyrimNet)")
                continue
        else:
            voice_name = str(voice_type)

        _log(f"[{idx + 1}/{len(voice_types)}] Processing voice: {voice_name}")
        entry = {"voice": voice_name, "status": "pending"}

        if design_mode:
            if voice_name in VOICE_DESIGN_REFS and VOICE_DESIGN_REFS[voice_name].get("instruct"):
                _log(f"  Existing voice design ref and instruction preserved for {voice_name}")
                entry["status"] = "preserved_existing"
                report.append(entry)
                continue

            gender = "female" if "female" in voice_name.lower() else "male"
            default_instruct = f"{gender}, adult, moderate pitch"

            VOICE_DESIGN_REFS[voice_name] = {
                "instruct": default_instruct
            }

            design_path = config._get_voice_design_path()
            design_path.parent.mkdir(parents=True, exist_ok=True)
            with design_path.open("w", encoding="utf-8") as f:
                json.dump(VOICE_DESIGN_REFS, f, ensure_ascii=False, indent=2)
                f.write("\n")

            _log(f"  Successfully registered design voice: {voice_name} with default instruct '{default_instruct}'")
            entry["status"] = "imported"
            report.append(entry)
            continue

        target_wav = speakers_dir / f"{voice_name}.wav"
        if target_wav.exists() and not force:
            # If already fully registered in database and file exists, preserve it and skip completely
            if voice_name in VOICE_REFS and VOICE_REFS[voice_name].get("ref_audio") and VOICE_REFS[voice_name].get("ref_text"):
                _log(f"  Existing voice ref and WAV file preserved for {voice_name}")
                entry["status"] = "preserved_existing"
                report.append(entry)
                continue
            
            # If WAV exists but is not registered in the database, fetch metadata to register it without downloading
            _log(f"  WAV file exists on disk for {voice_name}, but needs registration. Fetching metadata...")
            endpoint = f"{base_url.rstrip('/')}/voice-samples?api=samples&voice_type_id={urllib.parse.quote(voice_name)}"
            samples_data = _fetch_json(endpoint)
            if not samples_data:
                _log(f"  No samples metadata found for {voice_name} to register existing WAV")
                entry["status"] = "no_samples_data"
                report.append(entry)
                continue
            
            samples = samples_data if isinstance(samples_data, list) else samples_data.get("samples", [])
            if not samples:
                _log(f"  No usable samples found for {voice_name} to register existing WAV")
                entry["status"] = "no_usable_samples"
                report.append(entry)
                continue

            scored = []
            for s in samples:
                text = s.get("text_content", s.get("text", "")) or ""
                dur = float(s.get("duration", s.get("duration_seconds", 10)))
                score, reason = _score_sample(text, dur)
                scored.append((score, reason, s))

            scored.sort(key=lambda x: x[0])
            best_score, best_reason, best_sample = scored[0]

            sample_path = best_sample.get("file_path", best_sample.get("sample_path", best_sample.get("path", "")))
            sample_text = best_sample.get("text_content", best_sample.get("text", "")) or ""
            sample_dur = float(best_sample.get("duration", best_sample.get("duration_seconds", 0)))

            VOICE_REFS[voice_name] = {
                "ref_audio": str(target_wav.relative_to(PROJECT_ROOT) if target_wav.is_relative_to(PROJECT_ROOT) else target_wav),
                "ref_text": sample_text,
            }

            # Save DB directly
            refs_path.parent.mkdir(parents=True, exist_ok=True)
            with refs_path.open("w", encoding="utf-8") as f:
                json.dump(VOICE_REFS, f, ensure_ascii=False, indent=2)
                f.write("\n")

            _log(f"  Successfully registered existing WAV in voice refs database: {target_wav}")
            entry["status"] = "imported"
            report.append(entry)
            continue

        # Fetch samples
        endpoint = f"{base_url.rstrip('/')}/voice-samples?api=samples&voice_type_id={urllib.parse.quote(voice_name)}"
        samples_data = _fetch_json(endpoint)
        if not samples_data:
            _log(f"  No samples metadata found for {voice_name}")
            entry["status"] = "no_samples_data"
            report.append(entry)
            continue

        samples = samples_data if isinstance(samples_data, list) else samples_data.get("samples", [])
        if not samples:
            _log(f"  No usable samples found for {voice_name}")
            entry["status"] = "no_usable_samples"
            report.append(entry)
            continue

        scored = []
        for s in samples:
            text = s.get("text_content", s.get("text", "")) or ""
            dur = float(s.get("duration", s.get("duration_seconds", 10)))
            score, reason = _score_sample(text, dur)
            scored.append((score, reason, s))

        scored.sort(key=lambda x: x[0])
        best_score, best_reason, best_sample = scored[0]

        sample_path = best_sample.get("file_path", best_sample.get("sample_path", best_sample.get("path", "")))
        sample_text = best_sample.get("text_content", best_sample.get("text", "")) or ""
        sample_dur = float(best_sample.get("duration", best_sample.get("duration_seconds", 0)))

        _log(f"  Selected best sample: score={best_score:.1f}, duration={sample_dur:.1f}s, text length={len(sample_text)}")

        if audit_only:
            ref_entry = VOICE_REFS.get(voice_name, {})
            ref_audio = ref_entry.get("ref_audio", "")
            ref_text = ref_entry.get("ref_text", "")
            wav_exists = Path(ref_audio).exists() if ref_audio else False
            has_metadata = True

            entry["ref_audio_exists"] = wav_exists
            entry["ref_text_present"] = bool(ref_text)
            entry["has_metadata"] = has_metadata
            entry["status"] = "ok" if wav_exists and ref_text and has_metadata else "issues_found"
            report.append(entry)
            continue

        download_url = f"{base_url.rstrip('/')}/voice-samples?api=play&sample_path={urllib.parse.quote(sample_path)}"
        wav_data = _fetch_wav(download_url) if not dry_run else None

        if not dry_run and wav_data is None:
            _log(f"  ERROR: Download failed for {voice_name}")
            entry["status"] = "download_failed"
            report.append(entry)
            continue

        if not dry_run:
            try:
                speakers_dir.mkdir(parents=True, exist_ok=True)
                target_wav.write_bytes(wav_data)
                
                # Update VOICE_REFS
                VOICE_REFS[voice_name] = {
                    "ref_audio": str(target_wav.relative_to(PROJECT_ROOT) if target_wav.is_relative_to(PROJECT_ROOT) else target_wav),
                    "ref_text": sample_text,
                }
                
                # Save DB directly
                refs_path.parent.mkdir(parents=True, exist_ok=True)
                with refs_path.open("w", encoding="utf-8") as f:
                    json.dump(VOICE_REFS, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                
                _log(f"  Successfully imported: {target_wav}")
                entry["status"] = "imported"
            except Exception as exc:
                _log(f"  ERROR: failed to save voice sample {voice_name}: {exc}")
                entry["status"] = "save_failed"
        else:
            entry["status"] = "dry_run_ok"

        report.append(entry)

    # Save backup refs file
    if not audit_only and not dry_run and report:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = refs_path.with_name(f"{refs_path.stem}.backup.{timestamp}.json")
            import shutil
            shutil.copy(refs_path, backup_path)
            _log(f"Backup saved to: {backup_path}")
        except Exception as exc:
            _log(f"WARNING: failed to write voice_refs backup: {exc}")

    # Final reload to sync variables
    reload_voice_refs()
    with _IMPORT_THREAD_LOCK:
        _IMPORT_STATUS["processed"] = len(voice_types)
    return report


def _run_voice_import(base_url: str, selection_mode: str, force: bool, preserve_existing: bool, design_mode: bool = False) -> list[dict]:
    speakers_dir = VOICES_DIR / "qwen_speakers"
    speakers_dir.mkdir(parents=True, exist_ok=True)
    refs_path = config._get_voice_refs_path()

    return import_voice_samples(
        base_url=base_url,
        speakers_dir=speakers_dir,
        force=force,
        dry_run=False,
        selection_mode=selection_mode,
        preserve_existing=preserve_existing,
        audit_only=False,
        voice_refs_path=refs_path,
        design_mode=design_mode
    )


def _background_import_task(base_url: str, selection_mode: str, force: bool, preserve_existing: bool, design_mode: bool = False):
    global _IMPORT_STATUS, _IMPORT_LOGGER
    import contextlib

    _IMPORT_LOGGER = RealTimeLogger()
    with contextlib.redirect_stdout(_IMPORT_LOGGER):
        try:
            print(f"--- Import started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
            report = _run_voice_import(base_url, selection_mode, force, preserve_existing, design_mode)
            reload_voice_refs()
            print(f"\n--- Import finished successfully! ---")
            print(f"Total voice types processed: {len(report)}")
            imported_count = len([r for r in report if r.get('status') == 'imported'])
            print(f"Successfully imported: {imported_count} new voices")
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print(f"\nERROR: Import failed: {exc}")

    with _IMPORT_THREAD_LOCK:
        _IMPORT_STATUS["running"] = False
        _IMPORT_STATUS["completed"] = True
        _IMPORT_STATUS["log"] = _IMPORT_LOGGER.get_realtime_log()
