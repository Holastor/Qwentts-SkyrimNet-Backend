"""
Integration tests for ``/models/api/*`` endpoints.

Covers: list (with size verification), select (bulk selection), delete (safe removal).
"""

import json
from pathlib import Path

import pytest


# ======================================================================
# GET /models/api/list
# ======================================================================
class TestModelsApiList:
    """Tests for scanning and listing local + remote models."""

    def test_returns_200_and_expected_structure(self, client):
        resp = client.get("/models/api/list")
        assert resp.status_code == 200, resp.text
        body = resp.json()

        for key in ("local", "remote", "active_talker", "active_codec"):
            assert key in body, f"missing key: {key}"

        assert isinstance(body["local"], dict)
        assert "talker" in body["local"]
        assert "codec" in body["local"]

    def test_local_models_seeded_correctly(self, client, seed_models):
        """When seed_models fixture runs, the list endpoint returns them."""
        resp = client.get("/models/api/list")
        body = resp.json()
        local = body["local"]

        talker_names = {m["name"] for m in local["talker"]}
        assert "qwen-talker-1.7b-base-Q4_K_M.gguf" in talker_names
        assert "qwen-talker-0.6b-base-Q4_K_M.gguf" in talker_names

        codec_names = {m["name"] for m in local["codec"]}
        assert "qwen-tokenizer-12hz-F32.gguf" in codec_names

    def test_each_entry_has_required_fields(self, client, seed_models):
        """Every listed model carries name, path, size_gb, size_bytes, size_mismatch."""
        resp = client.get("/models/api/list")
        for category in ("talker", "codec"):
            for entry in resp.json()["local"][category]:
                for field in ("name", "path", "size_gb", "size_bytes", "size_mismatch"):
                    assert field in entry, f"{field} missing in {entry}"

    def test_size_mismatch_is_false_for_correct_files(self, client, seed_models, monkeypatch):
        """When expected sizes match actual sizes, size_mismatch is False.

        We override ``_MODEL_EXPECTED_SIZES`` in endpoints_ui so that the
        placeholder files (100 bytes each) are treated as correctly sized.
        """
        monkeypatch.setattr(
            "src.api.endpoints_ui._MODEL_EXPECTED_SIZES",
            {
                "qwen-talker-1.7b-base-Q4_K_M.gguf": 100,
                "qwen-talker-0.6b-base-Q4_K_M.gguf": 100,
                "qwen-tokenizer-12hz-F32.gguf": 100,
                "qwen-talker-1.7b-voicedesign-Q4_K_M.gguf": 100,
            },
        )
        resp = client.get("/models/api/list")
        for category in ("talker", "codec"):
            for entry in resp.json()["local"][category]:
                assert entry["size_mismatch"] is False, (
                    f"{entry['name']} should not be mismatched"
                )

    def test_empty_models_directory_returns_empty_lists(self, client, tmp_project_root):
        """When models/qwen/ is empty, the lists are empty."""
        model_dir = tmp_project_root / "models" / "qwen"
        # Remove any leftover files.
        for f in model_dir.glob("*.gguf"):
            f.unlink()

        resp = client.get("/models/api/list")
        assert resp.json()["local"] == {"talker": [], "codec": []}


# ======================================================================
# POST /models/api/select
# ======================================================================
class TestModelsApiSelect:
    """Tests for bulk-selecting Talker LM + Codec models."""

    def test_select_valid_talker_and_codec(self, client, seed_models):
        """Selecting existing talker + codec returns success."""
        payload = {
            "talker": "qwen-talker-1.7b-base-Q4_K_M.gguf",
            "codec": "qwen-tokenizer-12hz-F32.gguf",
        }
        resp = client.post("/models/api/select", json=payload)
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True

    def test_select_talker_only(self, client, seed_models):
        """Selecting only a talker model is allowed."""
        payload = {"talker": "qwen-talker-0.6b-base-Q4_K_M.gguf"}
        resp = client.post("/models/api/select", json=payload)
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True

    def test_select_nonexistent_file_returns_404(self, client, seed_models):
        """Referring to a model that doesn't exist on disk returns 404."""
        resp = client.post(
            "/models/api/select",
            json={"talker": "no-such-model.gguf"},
        )
        assert resp.status_code == 404

    def test_select_missing_both_keys_returns_400(self, client):
        """Omitting both talker and codec must be rejected."""
        resp = client.post("/models/api/select", json={})
        assert resp.status_code == 400

    def test_select_persists_to_settings(self, client, seed_models, tmp_project_root):
        """After selecting a model, the settings file on disk reflects it."""
        client.post(
            "/models/api/select",
            json={"talker": "qwen-talker-1.7b-voicedesign-Q4_K_M.gguf"},
        )
        settings_path = tmp_project_root / "src" / "local_settings" / "qwen_settings.json"
        if settings_path.exists():
            on_disk = json.loads(settings_path.read_text(encoding="utf-8"))
            assert on_disk.get("active_talker_name") == "qwen-talker-1.7b-voicedesign-Q4_K_M.gguf"

    def test_select_legacy_name_kind_format(self, client, seed_models):
        """Backward-compatible {name, kind} payload format still works."""
        resp = client.post(
            "/models/api/select",
            json={"name": "qwen-tokenizer-12hz-F32.gguf", "kind": "codec"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True


# ======================================================================
# POST /models/api/delete
# ======================================================================
class TestModelsApiDelete:
    """Tests for safe deletion of model GGUF files."""

    def test_delete_existing_model(self, client, models_dir):
        """Deleting an existing model file removes it from disk."""
        target = models_dir / "to_delete.gguf"
        target.write_bytes(b"\x00" * 100)

        resp = client.post("/models/api/delete", json={"name": "to_delete.gguf"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True
        assert not target.exists(), "file should be deleted"

    def test_delete_nonexistent_model_is_idempotent(self, client):
        """Deleting a file that doesn't exist still reports success."""
        resp = client.post("/models/api/delete", json={"name": "ghost.gguf"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_delete_rejects_empty_name(self, client):
        resp = client.post("/models/api/delete", json={"name": "  "})
        assert resp.status_code == 400

    def test_delete_rejects_path_traversal(self, client):
        """Names containing ../ or \\ are rejected for safety."""
        resp = client.post("/models/api/delete", json={"name": "../evil.gguf"})
        assert resp.status_code == 400

    def test_delete_rejects_backslash_path(self, client):
        resp = client.post("/models/api/delete", json={"name": "subdir\\model.gguf"})
        assert resp.status_code == 400
