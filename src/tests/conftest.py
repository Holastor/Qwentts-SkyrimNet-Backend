"""
Shared fixtures for the QwenTTS SkyrimNet Adapter test suite.

Provides:
- TestClient for the FastAPI app (with localhost check bypassed).
- Temporary directories for settings, models, voices, and output.
- Mocked backend functions so tests never call the real qwen.dll.
- Helpers to build voice databases on the fly.
"""

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path (coverage / IDE runners)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# FastAPI TestClient – import the real app *once* at session scope.
# ---------------------------------------------------------------------------
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app():
    """Return the real FastAPI application (session-scoped)."""
    from src.main import app

    return app


@pytest.fixture
def client(app, monkeypatch) -> TestClient:
    """Return a TestClient with the localhost guard bypassed for settings APIs.

    Patches ``_is_localhost_request`` so that every request appears to come
    from localhost, unlocking the ``/settings/api/*`` and ``/models/api/*``
    family of endpoints.
    """
    monkeypatch.setattr(
        "src.api.endpoints_skyrim._is_localhost_request",
        lambda _request: True,
    )
    monkeypatch.setattr(
        "src.api.endpoints_ui._is_localhost_request",
        lambda _request: True,
    )
    return TestClient(app)


# ---------------------------------------------------------------------------
# Backend mocks — prevent any real qwen.dll / GPU interaction.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _mock_backend(monkeypatch):
    """Automatically mock backend entry-points so tests stay lightweight.

    NOTE: _detect_backends is NOT mocked here — the real function only checks
    file existence, so it is safe to call.  Tests that need specific backends
    can control what files exist under ``config.BIN_DIR``.

    IMPORTANT: endpoints_ui.py imports these names with ``from src.core.backend
    import …``, creating local references that must also be patched.
    """
    # Model reload / switch – always report success.
    _ok = {"success": True}
    _switch = lambda name: {"success": True, "backend": name}

    monkeypatch.setattr("src.core.backend._reload_model", lambda: _ok)
    monkeypatch.setattr("src.core.backend._switch_backend", _switch)

    # Also patch the module-level imported copy in endpoints_ui.py.
    # (_reload_model is NOT imported at module level — it is imported
    #  inside individual handler bodies, so only _switch_backend needs
    #  the extra patch.)
    monkeypatch.setattr("src.api.endpoints_ui._switch_backend", _switch)

    # Persistent backend singleton – reset to None for every test.
    monkeypatch.setattr("src.core.backend.PERSISTENT_BACKEND", None)


# ---------------------------------------------------------------------------
# Temporary project root – isolates ALL filesystem side-effects.
# ---------------------------------------------------------------------------
@pytest.fixture
def tmp_project_root(app, tmp_path, monkeypatch) -> Path:
    """Replace ``config.PROJECT_ROOT`` with a clean temp directory.

    Creates the expected sub-directory skeleton underneath so that
    path-construction inside endpoint handlers does not raise.

    Also patches the *imported* copies of PROJECT_ROOT / VOICES_DIR in
    other modules so that ``_get_local_models`` and voice-path helpers
    resolve inside the temp tree.
    """
    root = tmp_path / "qwentts_test_project"
    root.mkdir()

    # Expected sub-dirs (many endpoint handlers call mkdir on these).
    for sub in (
        "models/qwen",
        "Voices/voice_refs",
        "Voices/qwen_speakers",
        "Voices/runtime_speakers",
        "Voices/cached_voices",
        "output_temp/qwentts_generated",
        "output_temp/qwentts_debug_failed",
        "output_temp/qwentts_debug_text",
        "src/local_settings",
        "bin",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)

    # Create a dummy qwen.dll so _detect_backends reports CPU=ready.
    (root / "bin" / "qwen.dll").touch()

    # --- config module globals ---
    monkeypatch.setattr("src.config.PROJECT_ROOT", root)
    monkeypatch.setattr("src.config.OUTPUT_DIR", root / "output_temp" / "qwentts_generated")
    monkeypatch.setattr("src.config.VOICES_DIR", root / "Voices")
    monkeypatch.setattr("src.config.VOICE_REFS_PATH", root / "Voices" / "voice_refs" / "voice_refs.json")
    monkeypatch.setattr("src.config.RUNTIME_SPEAKERS_DIR", root / "Voices" / "runtime_speakers")
    monkeypatch.setattr("src.config.RVQ_CACHE_DIR", root / "Voices" / "cached_voices")
    monkeypatch.setattr("src.config.SETTINGS_PATH", root / "src" / "local_settings" / "qwen_settings.json")
    monkeypatch.setattr("src.config.BIN_DIR", root / "bin")
    monkeypatch.setattr("src.config.QWENTTS_DEBUG_FAILED_DIR", root / "output_temp" / "qwentts_debug_failed")
    monkeypatch.setattr("src.config.QWENTTS_DEBUG_TEXT_DIR", root / "output_temp" / "qwentts_debug_text")

    # --- imported copies in other modules ---
    # endpoints_ui.py imports: PROJECT_ROOT, _SETTINGS, _save_settings, _apply_settings, ...
    monkeypatch.setattr("src.api.endpoints_ui.PROJECT_ROOT", root)

    # endpoints_skyrim.py imports: OUTPUT_DIR, RUNTIME_SPEAKERS_DIR, ...
    monkeypatch.setattr("src.api.endpoints_skyrim.OUTPUT_DIR", root / "output_temp" / "qwentts_generated")
    monkeypatch.setattr("src.api.endpoints_skyrim.RUNTIME_SPEAKERS_DIR", root / "Voices" / "runtime_speakers")

    # Re-point the importer globals so voice operations land inside tmp.
    monkeypatch.setattr("src.services.importer.VOICE_REFS", {})
    monkeypatch.setattr("src.services.importer.VOICE_DESIGN_REFS", {})

    return root


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------
@pytest.fixture
def reset_settings(monkeypatch) -> Dict[str, Any]:
    """Return a clean copy of the default _SETTINGS dict and patch it in.

    Patches both ``src.config._SETTINGS`` and the imported copy in
    ``src.api.endpoints_ui`` so endpoint handlers see the fresh dict.
    """
    defaults = {
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
        "talker_path": "",
        "codec_path": "",
        "backend": "qwentts_CPU",
        "active_talker_name": "",
        "active_codec_name": "",
    }
    monkeypatch.setattr("src.config._SETTINGS", defaults)
    monkeypatch.setattr("src.api.endpoints_ui._SETTINGS", defaults)
    return defaults


# ---------------------------------------------------------------------------
# Voice database helpers
# ---------------------------------------------------------------------------
@pytest.fixture
def _voice_db_paths(tmp_project_root) -> tuple[Path, Path]:
    """Return (voice_refs_path, voice_design_path) inside the temp project."""
    refs_dir = tmp_project_root / "Voices" / "voice_refs"
    return refs_dir / "voice_refs.json", refs_dir / "voice_design.json"


@pytest.fixture
def voice_refs_db(_voice_db_paths, monkeypatch) -> Path:
    """Seed voice_refs.json with a minimal valid database and reload globals."""
    path, _ = _voice_db_paths
    data = {
        "default": {"ref_audio": "Voices/qwen_speakers/default.wav", "ref_text": "Hello, world."},
        "nord": {"ref_audio": "Voices/qwen_speakers/nord.wav", "ref_text": "I am a Nord."},
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Reload importer globals from disk.
    from src.services import importer

    importer.reload_voice_refs()
    return path


@pytest.fixture
def voice_design_db(_voice_db_paths, monkeypatch) -> Path:
    """Seed voice_design.json with a minimal valid database."""
    _, path = _voice_db_paths
    data = {
        "default": {"instruct": "neutral, adult, moderate pitch"},
        "stormcloak": {"instruct": "male, angry, nordic accent"},
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    from src.services import importer

    importer.reload_voice_refs()
    return path


# ---------------------------------------------------------------------------
# Model file helpers
# ---------------------------------------------------------------------------
@pytest.fixture
def models_dir(tmp_project_root) -> Path:
    """Return the temp ``models/qwen/`` directory."""
    return tmp_project_root / "models" / "qwen"


@pytest.fixture
def seed_models(models_dir) -> Path:
    """Create dummy GGUF model files with the correct names (tiny placeholders).

    Creates small placeholder files so the model scanner has something to find.
    Files WILL report ``size_mismatch=True`` since they're not the real model
    size — use ``seed_models_correct_size`` if you need exact-size files.
    """
    models = [
        "qwen-talker-1.7b-base-Q4_K_M.gguf",
        "qwen-talker-0.6b-base-Q4_K_M.gguf",
        "qwen-tokenizer-12hz-F32.gguf",
        "qwen-talker-1.7b-voicedesign-Q4_K_M.gguf",
    ]
    for name in models:
        p = models_dir / name
        p.write_bytes(b"\x00" * 100)  # tiny placeholder

    # Update the talker/codec paths in config settings.
    import src.config as cfg

    cfg._SETTINGS["talker_path"] = str(models_dir / "qwen-talker-1.7b-base-Q4_K_M.gguf")
    cfg._SETTINGS["codec_path"] = str(models_dir / "qwen-tokenizer-12hz-F32.gguf")
    cfg._SETTINGS["active_talker_name"] = "qwen-talker-1.7b-base-Q4_K_M.gguf"
    cfg._SETTINGS["active_codec_name"] = "qwen-tokenizer-12hz-F32.gguf"
    cfg.TALKER_PATH = models_dir / "qwen-talker-1.7b-base-Q4_K_M.gguf"
    cfg.CODEC_PATH = models_dir / "qwen-tokenizer-12hz-F32.gguf"

    return models_dir


@pytest.fixture
def seed_models_correct_size(models_dir) -> Path:
    """Create GGUF model files with correct expected sizes (sparse).

    These files report ``size_mismatch=False``.  Only use when testing the
    size-verification logic specifically, as this creates large sparse files.
    """
    models = [
        ("qwen-talker-1.7b-base-Q4_K_M.gguf", 1_219_245_248),
        ("qwen-tokenizer-12hz-F32.gguf", 647_263_104),
    ]
    for name, size in models:
        p = models_dir / name
        with open(str(p), "wb") as f:
            f.seek(size - 1)
            f.write(b"\x00")

    import src.config as cfg

    cfg._SETTINGS["talker_path"] = str(models_dir / "qwen-talker-1.7b-base-Q4_K_M.gguf")
    cfg._SETTINGS["codec_path"] = str(models_dir / "qwen-tokenizer-12hz-F32.gguf")
    cfg._SETTINGS["active_talker_name"] = "qwen-talker-1.7b-base-Q4_K_M.gguf"
    cfg._SETTINGS["active_codec_name"] = "qwen-tokenizer-12hz-F32.gguf"
    cfg.TALKER_PATH = models_dir / "qwen-talker-1.7b-base-Q4_K_M.gguf"
    cfg.CODEC_PATH = models_dir / "qwen-tokenizer-12hz-F32.gguf"

    return models_dir


# ---------------------------------------------------------------------------
# Skip markers for environments where the real qwen.dll is unavailable.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def has_qwen_dll() -> bool:
    """True when the real qwen.dll exists in the project bin/ directory."""
    dll = _PROJECT_ROOT / "bin" / "qwen.dll"
    return dll.exists()


# ---------------------------------------------------------------------------
# conftest-level cleanup (session-scoped temp dirs etc.)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _session_cleanup():
    """Ensure sys.path is restored after the session."""
    yield
