"""
Integration tests for ``/settings/api/*`` endpoints.

Covers: status, update, set-backend, backends, and logs.
All tests use ``TestClient`` with the localhost guard bypassed (see conftest.py).
"""

import json

import pytest


# ======================================================================
# GET /settings/api/status
# ======================================================================
class TestSettingsApiStatus:
    """Tests for the settings status endpoint."""

    def test_returns_200_and_expected_keys(self, client):
        """Status endpoint returns a well-formed JSON structure."""
        resp = client.get("/settings/api/status")
        assert resp.status_code == 200, resp.text
        body = resp.json()

        # Required top-level keys.
        for key in ("settings", "backends", "current_backend", "local_models",
                     "talker_path", "codec_path"):
            assert key in body, f"missing key: {key}"

        # settings is a dict with at least the core keys.
        assert isinstance(body["settings"], dict)
        assert "lang" in body["settings"]

        # backends is a dict, current_backend is a string.
        assert isinstance(body["backends"], dict)
        assert isinstance(body["current_backend"], str)

        # local_models contains talker and codec lists.
        assert "talker" in body["local_models"]
        assert "codec" in body["local_models"]

    def test_current_backend_matches_settings(self, client, reset_settings):
        """The reported backend matches what is stored in _SETTINGS."""
        reset_settings["backend"] = "qwentts_CUDA"
        resp = client.get("/settings/api/status")
        assert resp.status_code == 200
        assert resp.json()["current_backend"] == "qwentts_CUDA"

    def test_local_models_detect_files(self, client, tmp_project_root, seed_models):
        """When model files exist on disk they appear in local_models."""
        resp = client.get("/settings/api/status")
        assert resp.status_code == 200
        models = resp.json()["local_models"]
        assert len(models["talker"]) >= 2, "should find at least 2 talker GGUF files"
        assert len(models["codec"]) >= 1, "should find at least 1 codec GGUF file"

    def test_size_mismatch_flag_on_truncated_file(self, client, tmp_project_root):
        """A GGUF file smaller than expected gets size_mismatch=True."""
        model_dir = tmp_project_root / "models" / "qwen"
        model_dir.mkdir(parents=True, exist_ok=True)
        bad = model_dir / "qwen-talker-1.7b-base-Q4_K_M.gguf"
        # Write a tiny file — way smaller than the expected 1.2 GB.
        bad.write_bytes(b"\x00" * 100)

        resp = client.get("/settings/api/status")
        assert resp.status_code == 200
        talkers = resp.json()["local_models"]["talker"]
        bad_entry = next((m for m in talkers if m["name"] == bad.name), None)
        assert bad_entry is not None, "truncated file must be listed"
        assert bad_entry["size_mismatch"] is True, "truncated file should flag mismatch"


# ======================================================================
# POST /settings/api/update
# ======================================================================
class TestSettingsApiUpdate:
    """Tests for updating synthesis settings at runtime."""

    def test_update_valid_field(self, client, reset_settings):
        """POSTing a valid setting updates the backend and persists."""
        payload = {"temperature": 0.55, "top_k": 30}
        resp = client.post("/settings/api/update", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["settings"]["temperature"] == 0.55
        assert body["settings"]["top_k"] == 30

    def test_update_empty_body_is_accepted(self, client):
        """An empty JSON object is a valid update (no-op)."""
        resp = client.post("/settings/api/update", json={})
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True

    def test_update_rejects_non_dict_body(self, client):
        """Passing a JSON array instead of an object must return 400."""
        resp = client.post("/settings/api/update", json=[1, 2, 3])
        assert resp.status_code == 400

    def test_update_rejects_invalid_json(self, client):
        """Malformed request body must return 400."""
        resp = client.post(
            "/settings/api/update",
            content="this is not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    def test_update_persists_to_disk(self, client, tmp_project_root):
        """After an update the settings file is written."""
        settings_path = tmp_project_root / "src" / "local_settings" / "qwen_settings.json"

        payload = {"lang": "english", "seed": 99}
        resp = client.post("/settings/api/update", json=payload)
        assert resp.status_code == 200

        assert settings_path.exists(), "settings file must exist after update"
        on_disk = json.loads(settings_path.read_text(encoding="utf-8"))
        assert on_disk.get("lang") == "english"
        assert on_disk.get("seed") == 99

    def test_update_then_status_reflects_change(self, client, reset_settings):
        """After an update the /status endpoint returns the new values."""
        client.post("/settings/api/update", json={"max_new_tokens": 777})
        resp = client.get("/settings/api/status")
        assert resp.json()["settings"]["max_new_tokens"] == 777


# ======================================================================
# POST /settings/api/set-backend
# ======================================================================
class TestSettingsApiSetBackend:
    """Tests for switching the active GGML backend at runtime."""

    def test_switch_to_cpu_succeeds(self, client):
        """Switching to qwentts_CPU is always reported as ready by the mock."""
        resp = client.post("/settings/api/set-backend", json={"backend": "qwentts_CPU"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["backend"] == "qwentts_CPU"

    def test_switch_rejects_empty_body(self, client):
        resp = client.post("/settings/api/set-backend", json={})
        assert resp.status_code == 400

    def test_switch_rejects_missing_backend_key(self, client):
        resp = client.post("/settings/api/set-backend", json={"other": "value"})
        assert resp.status_code == 400


# ======================================================================
# GET /settings/api/logs
# ======================================================================
class TestSettingsApiLogs:
    """Tests for the in-memory log buffer endpoint."""

    def test_returns_200_and_logs_list(self, client):
        resp = client.get("/settings/api/logs")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["logs"], list)

    def test_logs_are_not_empty_after_startup(self, client):
        """The log buffer contains entries written during app construction."""
        resp = client.get("/settings/api/logs")
        logs = resp.json()["logs"]
        assert len(logs) > 0, "log buffer should contain startup messages"


# ======================================================================
# GET /settings/api/backends
# ======================================================================
class TestSettingsApiBackends:
    """Tests for the backends listing endpoint."""

    def test_returns_backend_dict(self, client):
        resp = client.get("/settings/api/backends")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert isinstance(body["backends"], dict)
        assert "current_backend" in body


# ======================================================================
# Localhost guard (403 when bypass is NOT active)
# ======================================================================
class TestLocalhostGuard:
    """Verify that the localhost check actually rejects non-local requests."""

    def test_status_rejects_when_guard_is_active(self, app):
        """Without the monkeypatch, the localhost check must return 403."""
        from fastapi.testclient import TestClient

        raw_client = TestClient(app)
        resp = raw_client.get("/settings/api/status")
        assert resp.status_code == 403, (
            "should be forbidden when _is_localhost_request returns False"
        )
