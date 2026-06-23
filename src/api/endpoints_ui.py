import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from src import config
from src.config import _log, PROJECT_ROOT, _SETTINGS, _save_settings, _apply_settings, _resolve_path, _get_voice_refs_path
from src.api.endpoints_skyrim import _is_localhost_request
from src.core.backend import _detect_backends, _switch_backend
from src.services import importer

router = APIRouter()


class VoiceSaveRequest(BaseModel):
    key: str = ""
    ref_audio: str = ""
    ref_text: str = ""


class VoiceDeleteRequest(BaseModel):
    key: str = ""


class VoiceImportRequest(BaseModel):
    base_url: str = "http://127.0.0.1:8080"
    selection_mode: str = "qwentts-safe"
    force: bool = False
    preserve_existing: bool = True


def _require_settings_api(request: Request) -> None:
    if not _is_localhost_request(request):
        raise HTTPException(status_code=403, detail="Settings API is only available from localhost")


def _get_local_models() -> Dict[str, list[Dict[str, str]]]:
    """Scan models/qwen/ for GGUF files, return {talker: [...], codec: [...]}."""
    models_dir = PROJECT_ROOT / "models" / "qwen"
    result: Dict[str, list[Dict[str, str]]] = {"talker": [], "codec": []}
    if not models_dir.exists():
        return result
    for f in sorted(models_dir.iterdir()):
        if f.suffix.lower() != ".gguf" or not f.is_file():
            continue
        name = f.name
        size_gb = f.stat().st_size / (1024**3)
        entry = {"name": name, "path": str(f), "size_gb": round(size_gb, 2)}
        if "talker" in name.lower():
            result["talker"].append(entry)
        elif "tokenizer" in name.lower() or "codec" in name.lower():
            result["codec"].append(entry)
        else:
            result["codec" if size_gb < 0.3 else "talker"].append(entry)
    return result


async def _fetch_hf_model_list() -> list[Dict[str, Any]]:
    import urllib.request
    api_url = "https://huggingface.co/api/models/Serveurperso/Qwen3-TTS-GGUF"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "qwentts-adapter/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        _log(f"WARNING: HF API fetch failed: {exc}")
        return []

    siblings = data.get("siblings", [])
    gguf_files = []
    for sib in siblings:
        path = sib.get("rfilename", "")
        if path.endswith(".gguf"):
            gguf_files.append({
                "name": path.split("/")[-1],
                "path": path,
                "size_bytes": sib.get("size", 0),
                "download_url": f"https://huggingface.co/Serveurperso/Qwen3-TTS-GGUF/resolve/main/{path}",
            })
    return gguf_files


_DOWNLOAD_PROGRESS: Dict[str, Any] = {"running": False, "name": "", "progress": 0, "error": None}


async def _download_model_async(download_url: str, filename: str, target_dir: Path) -> bool:
    import urllib.request
    global _DOWNLOAD_PROGRESS

    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename
    _DOWNLOAD_PROGRESS = {"running": True, "name": filename, "progress": 0, "error": None}

    try:
        req = urllib.request.Request(download_url, headers={"User-Agent": "qwentts-adapter/1.0"})
        with urllib.request.urlopen(req, timeout=3600) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 1024 * 1024
            with open(str(target_path), "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        _DOWNLOAD_PROGRESS["progress"] = int(downloaded * 100 / total)
                    else:
                        _DOWNLOAD_PROGRESS["progress"] = -1

        _DOWNLOAD_PROGRESS["running"] = False
        _DOWNLOAD_PROGRESS["progress"] = 100
        return True
    except Exception as exc:
        _DOWNLOAD_PROGRESS["running"] = False
        _DOWNLOAD_PROGRESS["error"] = str(exc)
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        return False


# ---------------------------------------------------------------------------
# UI Endpoint Handlers
# ---------------------------------------------------------------------------

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request) -> HTMLResponse:
    backends = _detect_backends()
    current_backend = _SETTINGS.get("backend", "qwentts_CPU")
    s = _SETTINGS

    backend_rows = ""
    for name, status in backends.items():
        short = name.replace("qwentts_", "")
        active = "active" if name == current_backend else ""
        is_checked = "checked" if active else ""
        is_disabled = "" if status == "ready" else "disabled"
        status_text = "Ready" if status == "ready" else "Not built"
        backend_rows += f"""
        <label class="backend-option {active}">
          <input type="radio" name="backend" value="{name}" {is_checked} {is_disabled}>
          <span class="backend-name">{short}</span>
          <span class="backend-status" data-i18n-status="{status}">{status_text}</span>
          <svg class="backend-check" viewBox="0 0 24 24" width="20" height="20"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
        </label>"""

    tooltips = {
        "lang": "Language for synthesis. Supported: russian, english, chinese, japanese, korean, french, german, spanish, italian, portuguese, auto",
        "seed": "Random seed for reproducible output. -1 = random (different every time). Any other value = deterministic.",
        "max_new_tokens": "Maximum audio frames to generate. 2048 ≈ 160 seconds of audio at 12.5 Hz.",
        "temperature": "Sampling temperature. Lower values (0.3–0.7) = more deterministic. Higher (0.9–1.5) = more creative.",
        "top_k": "Top-K sampling: limit next token to top K candidates. 0 = disabled (consider all tokens).",
        "top_p": "Nucleus (top-P) sampling: cumulative probability threshold. 1.0 = disabled.",
        "repetition_penalty": "Penalises repeated tokens. 1.0 = no penalty. 1.05–1.2 = mild. Higher = stronger anti-repetition.",
        "subtalker_temperature": "Temperature for the Code Predictor MTP head (acoustic code sampling).",
        "subtalker_top_k": "Top-K for the code predictor sub-talker.",
        "subtalker_top_p": "Top-P for the code predictor sub-talker.",
        "codec_chunk_sec": "Duration of each codec decode chunk in seconds. Larger chunks use more RAM but reduce boundary artifacts.",
        "codec_left_context_sec": "Left context window (seconds) for chunked decode. Prevents audio artifacts at chunk boundaries.",
        "max_text_chars": "Truncate input text to this many characters before synthesis. 0 = no limit.",
        "do_sample": "Enable stochastic (randomised) sampling. Disable for fully deterministic greedy output.",
        "subtalker_do_sample": "Enable sampling for the Code Predictor. Disable for deterministic acoustic code generation.",
        "use_fa": "Flash attention — fused attention kernel. Requires CUDA or Vulkan backend. Speeds up inference on GPU.",
        "clamp_fp16": "Clamp hidden states and attention V to FP16 range. Only needed on older (pre-Ampere) CUDA GPUs.",
        "append_ending_pause": "Automatically append '...' to the end of text for a more natural trailing pause.",
        "debug_save_text": "Save the processed text sent to the model to disk (under output_temp/qwentts_debug_text/).",
    }

    form_fields = [
        ("lang", "Language", "text", s.get("lang", "russian"), "", "", ""),
        ("seed", "Seed", "number", s.get("seed", -1), "", "", ""),
        ("temperature", "Temperature", "number", s.get("temperature", 0.9), "0.01", "3.0", "0.01"),
        ("top_k", "Top-K", "number", s.get("top_k", 50), "0", "200", "1"),
        ("top_p", "Top-P", "number", s.get("top_p", 1.0), "0.0", "1.0", "0.01"),
        ("repetition_penalty", "Repetition Penalty", "number", s.get("repetition_penalty", 1.05), "1.0", "2.0", "0.01"),
        ("max_new_tokens", "Max New Tokens", "number", s.get("max_new_tokens", 2048), "1", "8192", "1"),
        ("max_text_chars", "Max Text Chars", "number", s.get("max_text_chars", 180), "0", "1000", "1"),
        ("codec_chunk_sec", "Codec Chunk (sec)", "number", s.get("codec_chunk_sec", 24.0), "1", "120", "1"),
        ("codec_left_context_sec", "Codec Left Context (sec)", "number", s.get("codec_left_context_sec", 2.0), "0", "30", "0.5"),
    ]
    form_html = ""
    for row in form_fields:
        fid = row[0]; label = row[1]; ftype = row[2]; fval = row[3]
        attrs = ""
        if row[4]: attrs += f' min="{row[4]}"'
        if row[5]: attrs += f' max="{row[5]}"'
        if row[6]: attrs += f' step="{row[6]}"'
        hint = tooltips.get(fid, "")
        form_html += f"""
        <div class="field">
          <label for="{fid}">
            <span data-i18n="field_label_{fid}">{label}</span>
            <span class="tooltip-icon" data-i18n-tip="field_hint_{fid}" data-tip="{hint}">ⓘ</span>
          </label>
          <div class="field-input-wrap">
            <input type="{ftype}" id="{fid}" name="{fid}" value="{fval}"{attrs}>
          </div>
        </div>"""

    bool_fields = [
        ("do_sample", "Do Sample", s.get("do_sample", True)),
        ("subtalker_do_sample", "Sub Talker Do Sample", s.get("subtalker_do_sample", True)),
        ("use_fa", "Flash Attention", s.get("use_fa", True)),
        ("clamp_fp16", "Clamp FP16", s.get("clamp_fp16", False)),
        ("append_ending_pause", "Append Ending Pause", s.get("append_ending_pause", True)),
        ("debug_save_text", "Debug Save Text", s.get("debug_save_text", True)),
    ]
    bool_html = ""
    for fid, label, fval in bool_fields:
        checked = 'checked' if fval else ''
        hint = tooltips.get(fid, "")
        bool_html += f"""
        <div class="field bool">
          <label for="{fid}">
            <span data-i18n="field_label_{fid}">{label}</span>
            <span class="tooltip-icon" data-i18n-tip="field_hint_{fid}" data-tip="{hint}">ⓘ</span>
          </label>
          <div class="field-input-wrap">
            <input type="checkbox" id="{fid}" name="{fid}" {checked}>
            <span class="toggle-slider"></span>
          </div>
        </div>"""

    sub_fields = [
        ("subtalker_temperature", "Sub Talker Temperature", "number", s.get("subtalker_temperature", 0.9), "0.01", "3.0", "0.01"),
        ("subtalker_top_k", "Sub Talker Top-K", "number", s.get("subtalker_top_k", 50), "0", "200", "1"),
        ("subtalker_top_p", "Sub Talker Top-P", "number", s.get("subtalker_top_p", 1.0), "0.0", "1.0", "0.01"),
    ]
    sub_html = ""
    for row in sub_fields:
        fid = row[0]; label = row[1]; ftype = row[2]; fval = row[3]
        attrs = ""
        if row[4]: attrs += f' min="{row[4]}"'
        if row[5]: attrs += f' max="{row[5]}"'
        if row[6]: attrs += f' step="{row[6]}"'
        hint = tooltips.get(fid, "")
        sub_html += f"""
        <div class="field">
          <label for="{fid}">
            <span data-i18n="field_label_{fid}">{label}</span>
            <span class="tooltip-icon" data-i18n-tip="field_hint_{fid}" data-tip="{hint}">ⓘ</span>
          </label>
          <div class="field-input-wrap">
            <input type="{ftype}" id="{fid}" name="{fid}" value="{fval}"{attrs}>
          </div>
        </div>"""

    local = _get_local_models()
    active_talker = _SETTINGS.get("active_talker_name", "")
    active_codec = _SETTINGS.get("active_codec_name", "")

    talker_html = ""
    for m in local.get("talker", []):
        is_active = m["name"] == active_talker
        checked = "checked" if is_active else ""
        talker_html += f"""
        <label class="model-item">
          <input type="radio" name="talker_model" value="{m['path']}" data-name="{m['name']}" {checked}>
          <span class="model-check">
            <svg viewBox="0 0 24 24" width="18" height="18"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
          </span>
          <span class="model-name">{m['name']}</span>
          <span class="model-size">{m['size_gb']} GB</span>
        </label>"""

    codec_html = ""
    for m in local.get("codec", []):
        is_active = m["name"] == active_codec
        checked = "checked" if is_active else ""
        codec_html += f"""
        <label class="model-item {'active' if is_active else ''}">
          <input type="radio" name="codec_model" value="{m['path']}" data-name="{m['name']}" {checked}>
          <span class="model-check">
            <svg viewBox="0 0 24 24" width="18" height="18"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
          </span>
          <span class="model-name">{m['name']}</span>
          <span class="model-size">{m['size_gb']} GB</span>
        </label>"""

    if not talker_html:
        talker_html = '<p class="empty-message">No talker models found in <code>models/qwen/</code>.</p>'
    if not codec_html:
        codec_html = '<p class="empty-message">No codec models found in <code>models/qwen/</code>.</p>'

    template_path = PROJECT_ROOT / "src" / "web" / "settings.html"
    try:
        template = template_path.read_text(encoding="utf-8")
    except Exception as exc:
        return HTMLResponse(
            f"<h3>ERROR: Failed to load src/web/settings.html: {exc}</h3>", 
            status_code=500
        )

    page = template.replace("{{backend_rows}}", backend_rows) \
                   .replace("{{form_html}}", form_html) \
                   .replace("{{bool_html}}", bool_html) \
                   .replace("{{sub_html}}", sub_html) \
                   .replace("{{talker_html}}", talker_html) \
                   .replace("{{codec_html}}", codec_html)

    return HTMLResponse(page)


@router.get("/settings.css")
async def settings_css():
    css_path = PROJECT_ROOT / "src" / "web" / "settings.css"
    if not css_path.exists():
        raise HTTPException(status_code=404, detail="CSS file not found")
    return FileResponse(str(css_path), media_type="text/css")


@router.get("/settings.js")
async def settings_js():
    js_path = PROJECT_ROOT / "src" / "web" / "settings.js"
    if not js_path.exists():
        raise HTTPException(status_code=404, detail="JS file not found")
    return FileResponse(str(js_path), media_type="application/javascript")


@router.get("/settings/api/status")
async def settings_api_status(request: Request) -> Dict[str, Any]:
    _require_settings_api(request)
    backends = _detect_backends()
    local_models = _get_local_models()
    return {
        "settings": dict(_SETTINGS),
        "backends": backends,
        "current_backend": _SETTINGS.get("backend", "qwentts_CPU"),
        "local_models": local_models,
        "talker_path": str(config.TALKER_PATH),
        "codec_path": str(config.CODEC_PATH),
    }


@router.post("/settings/api/update")
async def settings_api_update(request: Request) -> Dict[str, Any]:
    _require_settings_api(request)
    try:
        data = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid JSON: {exc}")

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="body must be a JSON object")

    _SETTINGS.update(data)
    _save_settings()
    _apply_settings()
    return {"success": True, "settings": dict(_SETTINGS)}


@router.post("/settings/api/set-backend")
async def settings_api_set_backend(request: Request) -> Dict[str, Any]:
    _require_settings_api(request)
    try:
        data = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid JSON: {exc}")

    backend = (data or {}).get("backend", "")
    if not backend:
        raise HTTPException(status_code=400, detail="backend name required")

    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _switch_backend, backend)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "unknown error"))
    return result


@router.get("/settings/api/backends")
async def settings_api_backends(request: Request) -> Dict[str, Any]:
    _require_settings_api(request)
    return {
        "backends": _detect_backends(),
        "current_backend": _SETTINGS.get("backend", "qwentts_CPU"),
    }


@router.get("/models")
async def models_page(request: Request) -> RedirectResponse:
    return RedirectResponse(url="/settings")


@router.get("/models/api/list")
async def models_api_list(request: Request) -> Dict[str, Any]:
    _require_settings_api(request)
    local = _get_local_models()
    remote = await _fetch_hf_model_list()
    return {
        "local": local,
        "remote": remote,
        "active_talker": _SETTINGS.get("active_talker_name", ""),
        "active_codec":  _SETTINGS.get("active_codec_name", ""),
    }


@router.post("/models/api/download")
async def models_api_download(request: Request) -> Dict[str, Any]:
    _require_settings_api(request)
    try:
        data = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid JSON: {exc}")
    url = (data or {}).get("url", "")
    name = (data or {}).get("name", "")
    if not url or not name:
        raise HTTPException(status_code=400, detail="url and name required")

    target_dir = PROJECT_ROOT / "models" / "qwen"
    success = await _download_model_async(url, name, target_dir)
    if success:
        return {"success": True, "name": name}
    err = _DOWNLOAD_PROGRESS.get("error", "download failed")
    return {"success": False, "error": err}


@router.get("/models/api/progress")
async def models_api_progress(request: Request) -> Dict[str, Any]:
    return dict(_DOWNLOAD_PROGRESS)


@router.post("/models/api/select")
async def models_api_select(request: Request) -> Dict[str, Any]:
    _require_settings_api(request)
    try:
        data = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid JSON: {exc}")
    name = (data or {}).get("name", "")
    kind = (data or {}).get("kind", "")
    if not name or kind not in ("talker", "codec"):
        raise HTTPException(status_code=400, detail="name and kind (talker/codec) required")

    model_path = str(PROJECT_ROOT / "models" / "qwen" / name)
    if not Path(model_path).exists():
        raise HTTPException(status_code=404, detail=f"model file not found: {model_path}")

    if kind == "talker":
        _SETTINGS["talker_path"] = model_path
        _SETTINGS["active_talker_name"] = name
    else:
        _SETTINGS["codec_path"] = model_path
        _SETTINGS["active_codec_name"] = name

    _save_settings()
    _apply_settings()
    return {"success": True, "kind": kind, "name": name, "path": model_path}


@router.get("/voices/api/list")
async def voices_api_list(request: Request) -> Dict[str, Any]:
    _require_settings_api(request)
    return importer.VOICE_REFS


@router.post("/voices/api/save")
async def voices_api_save(request: Request, payload: VoiceSaveRequest) -> Dict[str, Any]:
    _require_settings_api(request)
    key = payload.key.strip()
    ref_audio = payload.ref_audio.strip()
    ref_text = payload.ref_text.strip()

    if not key:
        raise HTTPException(status_code=400, detail="Key must not be empty")
    if not ref_audio:
        raise HTTPException(status_code=400, detail="Reference audio path must not be empty")
    if not ref_text:
        raise HTTPException(status_code=400, detail="Reference transcript must not be empty")

    importer.VOICE_REFS[key] = {
        "ref_audio": ref_audio,
        "ref_text": ref_text
    }

    path = _get_voice_refs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(importer.VOICE_REFS, f, ensure_ascii=False, indent=2)
        f.write("\n")

    importer.reload_voice_refs()
    return {"success": True, "key": key}


@router.post("/voices/api/delete")
async def voices_api_delete(request: Request, payload: VoiceDeleteRequest) -> Dict[str, Any]:
    _require_settings_api(request)
    key = payload.key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="Key must not be empty")

    if key in importer.VOICE_REFS:
        del importer.VOICE_REFS[key]

        path = _get_voice_refs_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(importer.VOICE_REFS, f, ensure_ascii=False, indent=2)
            f.write("\n")

        importer.reload_voice_refs()
        return {"success": True, "key": key}
    else:
        raise HTTPException(status_code=404, detail=f"Voice key '{key}' not found")


@router.get("/voices/api/play")
async def voices_api_play(path: str, request: Request):
    _require_settings_api(request)
    resolved = _resolve_path(path)
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(str(resolved), media_type="audio/wav")


@router.post("/voices/api/import")
async def voices_api_import(request: Request, payload: VoiceImportRequest) -> Dict[str, Any]:
    _require_settings_api(request)

    with importer._IMPORT_THREAD_LOCK:
        if importer._IMPORT_STATUS["running"]:
            raise HTTPException(status_code=400, detail="Import is already running")

        importer._IMPORT_STATUS["running"] = True
        importer._IMPORT_STATUS["completed"] = False
        importer._IMPORT_STATUS["log"] = "Starting background import thread...\n"
        importer._IMPORT_STATUS["total"] = 0
        importer._IMPORT_STATUS["processed"] = 0

        t = threading.Thread(
            target=importer._background_import_task,
            args=(
                payload.base_url,
                payload.selection_mode,
                payload.force,
                payload.preserve_existing
            ),
            daemon=True
        )
        t.start()

    return {"success": True, "message": "Import thread spawned."}


@router.get("/voices/api/import/status")
async def voices_api_import_status(request: Request) -> Dict[str, Any]:
    _require_settings_api(request)
    status = dict(importer._IMPORT_STATUS)
    if importer._IMPORT_STATUS.get("running") and importer._IMPORT_LOGGER:
        status["log"] = importer._IMPORT_LOGGER.get_realtime_log()
    return status


@router.post("/reload-voice-refs")
async def reload_voice_refs_endpoint() -> Dict[str, Any]:
    refs = importer.reload_voice_refs()
    _log("/reload-voice-refs called")
    return {"success": True, "entries": len(refs)}
