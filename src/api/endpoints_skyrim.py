from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from src import config
from src.config import (
    _log, OUTPUT_DIR, RUNTIME_SPEAKERS_DIR, ALLOW_RUNTIME_UPLOAD_OVERWRITE,
    BACKEND_NAME, _get_lang_code, _resolve_path
)
from src.services.audio import generate_silence_wav
from src.services.text import _prepare_qwentts_gen_text
from src.services.importer import VOICE_REFS, VOICE_DESIGN_REFS

router = APIRouter()


class TtsRequest(BaseModel):
    text: str = ""
    speaker_wav: Optional[str] = None
    language: Optional[str] = "ru"
    accent: Optional[str] = None
    save_path: Optional[str] = None
    override: Optional[bool] = False


def _safe_output_name(save_path: Optional[str]) -> str:
    if save_path:
        name = Path(save_path).name
        if name.lower().endswith(".wav"):
            return name
        return f"{name}.wav"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"qwentts_{timestamp}.wav"


def _write_silence_file(save_path: Optional[str]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / _safe_output_name(save_path)
    output_path.write_bytes(generate_silence_wav())
    return output_path


def _resolve_voice_ref(speaker_wav: Optional[str], gen_text: str) -> Optional[Dict[str, Any]]:
    requested_key = speaker_wav or ""
    
    from src.core import backend
    is_voicedesign_model = False
    if backend.PERSISTENT_BACKEND and backend.PERSISTENT_BACKEND.talker_path:
        is_voicedesign_model = "voicedesign" in str(backend.PERSISTENT_BACKEND.talker_path).lower()

    is_custom = requested_key in VOICE_REFS
    is_design = requested_key in VOICE_DESIGN_REFS

    resolved_key = "default"
    voice_ref = None
    type_mode = "unknown"

    if is_voicedesign_model:
        if is_design:
            resolved_key = requested_key
            voice_ref = VOICE_DESIGN_REFS.get(resolved_key)
            type_mode = "design"
        elif is_custom:
            resolved_key = requested_key
            voice_ref = VOICE_REFS.get(resolved_key)
            type_mode = "custom"
        else:
            if "default" in VOICE_DESIGN_REFS:
                resolved_key = "default"
                voice_ref = VOICE_DESIGN_REFS.get(resolved_key)
                type_mode = "design"
            elif "default" in VOICE_REFS:
                resolved_key = "default"
                voice_ref = VOICE_REFS.get(resolved_key)
                type_mode = "custom"
    else:
        if is_custom:
            resolved_key = requested_key
            voice_ref = VOICE_REFS.get(resolved_key)
            type_mode = "custom"
        elif is_design:
            resolved_key = requested_key
            voice_ref = VOICE_DESIGN_REFS.get(resolved_key)
            type_mode = "design"
        else:
            if "default" in VOICE_REFS:
                resolved_key = "default"
                voice_ref = VOICE_REFS.get(resolved_key)
                type_mode = "custom"
            elif "default" in VOICE_DESIGN_REFS:
                resolved_key = "default"
                voice_ref = VOICE_DESIGN_REFS.get(resolved_key)
                type_mode = "design"

    _log(f"current backend: qwentts-persistent")
    _log(f"current mode: persistent ({type_mode})")
    _log(f"requested speaker_wav: {requested_key}")
    _log(f"resolved speaker key: {resolved_key if voice_ref else None}")

    if not voice_ref:
        _log(f"ERROR: no voice ref for '{requested_key}' and no usable 'default'; returning silence WAV")
        _log(f"gen_text length: {len(gen_text)}")
        return None

    if type_mode == "design":
        instruct = voice_ref.get("instruct", "")
        _log(f"instruct description: {instruct}")
        _log(f"gen_text length: {len(gen_text)}")
        return {
            "speaker_key": resolved_key,
            "instruct": instruct,
        }
    else:
        ref_audio = voice_ref.get("ref_audio", "")
        ref_text = voice_ref.get("ref_text", "")
        ref_audio_path = _resolve_path(ref_audio)
        ref_audio_exists = ref_audio_path.exists()

        _log(f"ref_audio: {ref_audio_path}")
        _log(f"ref_audio exists: {ref_audio_exists}")
        _log(f"ref_text preview: {ref_text[:80]}")
        _log(f"gen_text length: {len(gen_text)}")
        return {
            "speaker_key": resolved_key,
            "ref_audio": str(ref_audio_path),
            "ref_text": ref_text,
        }


def _is_localhost_request(request: Request) -> bool:
    if not request.client:
        return False
    return request.client.host in {"127.0.0.1", "::1", "localhost"}


def _safe_file_name(name: Optional[str], fallback: str) -> str:
    raw_name = Path(name or fallback).name
    safe_chars = []
    for char in raw_name:
        if char.isalnum() or char in ("-", "_", "."):
            safe_chars.append(char)
        else:
            safe_chars.append("_")
    safe_name = "".join(safe_chars).strip("._")
    return safe_name or fallback


async def _extract_fields_and_uploads(request: Request) -> tuple[Dict[str, Any], list[tuple[str, Any]]]:
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            data = await request.json()
            return (data if isinstance(data, dict) else {}), []
        except Exception as exc:
            _log(f"failed to parse JSON body: {exc}")
            return {}, []

    if "multipart/form-data" not in content_type and "application/x-www-form-urlencoded" not in content_type:
        return {}, []

    try:
        form = await request.form()
    except Exception as exc:
        _log(f"failed to parse form body: {exc}")
        return {}, []

    fields: Dict[str, Any] = {}
    uploads = []
    for key, value in form.multi_items():
        if hasattr(value, "filename") and hasattr(value, "read"):
            fields[key] = getattr(value, "filename", None)
            uploads.append((key, value))
        else:
            fields[key] = value

    return fields, uploads


async def _extract_fields_and_save_runtime_uploads(request: Request) -> tuple[Dict[str, Any], list[str]]:
    fields, uploads = await _extract_fields_and_uploads(request)
    saved_files: list[str] = []
    if not uploads:
        return fields, saved_files

    _log(
        "WARNING: Received SkyrimNet voice sample upload. It will not update QwenTTS voice_refs "
        "because QwenTTS ICL also needs matching ref_text."
    )

    speaker = fields.get("speaker") or fields.get("speaker_name") or fields.get("speaker_wav")
    for key, upload in uploads:
        upload_name = getattr(upload, "filename", None)
        if speaker:
            target_name = _safe_file_name(f"{Path(str(speaker)).stem}.wav", f"{key}.wav")
        else:
            target_name = _safe_file_name(upload_name, f"{key}.wav")

        target_dir = RUNTIME_SPEAKERS_DIR
        target_path = target_dir / target_name
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            if target_path.exists() and not ALLOW_RUNTIME_UPLOAD_OVERWRITE:
                _log(f"runtime voice sample already exists, keeping existing file: {target_path}")
                continue
            content = await upload.read()
            target_path.write_bytes(content)
            saved_files.append(str(target_path))
            _log(f"saved uploaded runtime voice sample: {target_path}")
        except Exception as exc:
            _log(f"failed to save uploaded runtime voice sample '{upload_name}': {exc}")

    return fields, saved_files


@router.post("/tts_to_audio")
@router.post("/tts_to_audio/")
async def tts_to_audio(payload: TtsRequest) -> FileResponse:
    from src.core import backend
    _log("endpoint called: /tts_to_audio")
    _log(f"received text: {payload.text}")
    _log(f"speaker_wav: {payload.speaker_wav}")
    _log(f"language: {payload.language}")
    _log(f"save_path: {payload.save_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / _safe_output_name(payload.save_path)

    if payload.text == "ping":
        _log("ping received, returning silence WAV")
        output_path = _write_silence_file(payload.save_path)
    else:
        gen_text, _ending_pause_appended = _prepare_qwentts_gen_text(payload.text)
        voice_ref = _resolve_voice_ref(payload.speaker_wav, gen_text)

        if voice_ref and backend.PERSISTENT_BACKEND:
            generated_path = backend.PERSISTENT_BACKEND.infer(
                voice_ref, gen_text, output_path,
                payload.speaker_wav, payload.language,
            )
            if generated_path:
                output_path = generated_path
            else:
                _log("failure: returning silence WAV fallback")
                output_path = _write_silence_file(payload.save_path)
        elif voice_ref:
            _log("failure: persistent backend is not loaded, returning silence WAV fallback")
            output_path = _write_silence_file(payload.save_path)
        else:
            _log("failure: missing voice ref, returning silence WAV fallback")
            output_path = _write_silence_file(payload.save_path)

    _log(f"output path: {output_path}")

    return FileResponse(
        path=str(output_path),
        media_type="audio/wav",
        filename=output_path.name,
    )


@router.post("/create_and_store_latents")
@router.post("/create_and_store_latents/")
async def create_and_store_latents(request: Request) -> JSONResponse:
    fields, saved_files = await _extract_fields_and_save_runtime_uploads(request)

    _log("endpoint called: /create_and_store_latents")
    _log(f"speaker: {fields.get('speaker') or fields.get('speaker_name')}")
    _log(f"language: {fields.get('language')}")
    _log(f"file: {fields.get('file') or fields.get('wav_file')}")
    _log(f"speaker_wav: {fields.get('speaker_wav')}")
    _log(f"uploaded sample saved: {bool(saved_files)}")
    _log("QwenTTS no-op, no latents are created")

    return JSONResponse(
        {
            "success": True,
            "backend": BACKEND_NAME,
            "message": "QwenTTS no-op: create_and_store_latents accepted.",
            "received": {
                "speaker": fields.get("speaker") or fields.get("speaker_name"),
                "language": fields.get("language"),
                "file": fields.get("file") or fields.get("wav_file"),
                "speaker_wav": fields.get("speaker_wav"),
                "saved_files": saved_files,
            },
        }
    )
