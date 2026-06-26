"""
Integration tests for ``/voices/api/*`` endpoints.

Covers: list (custom + design), save (add / edit), delete (by key), and play.
"""

import json
from pathlib import Path

import pytest


# ======================================================================
# GET /voices/api/list
# ======================================================================
class TestVoicesApiList:
    """Tests for retrieving the voice databases."""

    def test_returns_custom_and_design_dicts(self, client):
        resp = client.get("/voices/api/list")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "custom" in body
        assert "design" in body
        assert isinstance(body["custom"], dict)
        assert isinstance(body["design"], dict)

    def test_seeded_custom_voices_appear(self, client, voice_refs_db):
        """After seeding voice_refs.json, custom voices show up."""
        resp = client.get("/voices/api/list")
        custom = resp.json()["custom"]
        assert "nord" in custom
        assert custom["nord"]["ref_audio"] == "Voices/qwen_speakers/nord.wav"
        assert custom["nord"]["ref_text"] == "I am a Nord."

    def test_seeded_design_voices_appear(self, client, voice_design_db):
        """After seeding voice_design.json, design voices show up."""
        resp = client.get("/voices/api/list")
        design = resp.json()["design"]
        assert "stormcloak" in design
        assert design["stormcloak"]["instruct"] == "male, angry, nordic accent"


# ======================================================================
# POST /voices/api/save
# ======================================================================
class TestVoicesApiSave:
    """Tests for adding / editing voice entries."""

    # -- custom voices --------------------------------------------------
    def test_save_new_custom_voice(self, client, tmp_project_root):
        """A valid custom voice with ref_audio + ref_text is saved."""
        payload = {
            "key": "khajiit",
            "ref_audio": "Voices/qwen_speakers/khajiit.wav",
            "ref_text": "Khajiit has wares if you have coin.",
            "db_type": "custom",
        }
        resp = client.post("/voices/api/save", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["key"] == "khajiit"

        # Verify it appears in /list
        list_resp = client.get("/voices/api/list")
        assert "khajiit" in list_resp.json()["custom"]

    def test_save_custom_voice_missing_ref_audio_is_rejected(self, client):
        """Custom voices MUST include ref_audio."""
        resp = client.post("/voices/api/save", json={
            "key": "bad",
            "ref_text": "some text",
            "db_type": "custom",
        })
        assert resp.status_code == 400, resp.text

    def test_save_custom_voice_missing_ref_text_is_rejected(self, client):
        """Custom voices MUST include ref_text."""
        resp = client.post("/voices/api/save", json={
            "key": "bad",
            "ref_audio": "Voices/qwen_speakers/some.wav",
            "db_type": "custom",
        })
        assert resp.status_code == 400, resp.text

    def test_save_custom_voice_empty_key_is_rejected(self, client):
        resp = client.post("/voices/api/save", json={
            "key": "   ",
            "ref_audio": "a.wav",
            "ref_text": "text",
            "db_type": "custom",
        })
        assert resp.status_code == 400

    # -- design voices --------------------------------------------------
    def test_save_new_design_voice(self, client):
        """A valid design voice with an instruct string is saved."""
        payload = {
            "key": "dragonborn",
            "instruct": "male, heroic, deep, nordic",
            "db_type": "design",
        }
        resp = client.post("/voices/api/save", json=payload)
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True

        list_resp = client.get("/voices/api/list")
        assert "dragonborn" in list_resp.json()["design"]

    def test_save_design_voice_missing_instruct_is_rejected(self, client):
        resp = client.post("/voices/api/save", json={
            "key": "bad_design",
            "db_type": "design",
        })
        assert resp.status_code == 400, resp.text

    # -- auto-detection -------------------------------------------------
    def test_save_auto_detect_design_when_instruct_present(self, client):
        """When db_type is empty but instruct is given, it saves as design."""
        resp = client.post("/voices/api/save", json={
            "key": "auto_design",
            "instruct": "neutral tone",
        })
        assert resp.status_code == 200

        # Should be in design, not custom.
        list_resp = client.get("/voices/api/list")
        assert "auto_design" in list_resp.json()["design"]

    def test_save_edit_existing_voice_overwrites(self, client, voice_refs_db):
        """Saving an existing key overwrites the previous entry."""
        # First save.
        client.post("/voices/api/save", json={
            "key": "nord",
            "ref_audio": "Voices/qwen_speakers/nord_v2.wav",
            "ref_text": "Skyrim belongs to the Nords!",
            "db_type": "custom",
        })
        # Verify overwrite.
        list_resp = client.get("/voices/api/list")
        nord = list_resp.json()["custom"]["nord"]
        assert nord["ref_text"] == "Skyrim belongs to the Nords!"


# ======================================================================
# POST /voices/api/delete
# ======================================================================
class TestVoicesApiDelete:
    """Tests for removing voice entries from the databases."""

    def test_delete_existing_custom_voice(self, client, voice_refs_db):
        """Deleting a known custom key removes it."""
        resp = client.post("/voices/api/delete", json={
            "key": "nord",
            "db_type": "custom",
        })
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True

        # Gone from list.
        list_resp = client.get("/voices/api/list")
        assert "nord" not in list_resp.json()["custom"]

    def test_delete_existing_design_voice(self, client, voice_design_db):
        """Deleting a known design key removes it."""
        resp = client.post("/voices/api/delete", json={
            "key": "stormcloak",
            "db_type": "design",
        })
        assert resp.status_code == 200
        list_resp = client.get("/voices/api/list")
        assert "stormcloak" not in list_resp.json()["design"]

    def test_delete_nonexistent_key_returns_404(self, client):
        resp = client.post("/voices/api/delete", json={
            "key": "nobody",
            "db_type": "custom",
        })
        assert resp.status_code == 404, resp.text

    def test_delete_empty_key_is_rejected(self, client):
        resp = client.post("/voices/api/delete", json={"key": "", "db_type": "custom"})
        assert resp.status_code == 400

    def test_delete_fallback_auto_detect(self, client, voice_refs_db):
        """When db_type is empty, the endpoint auto-detects where the key lives."""
        resp = client.post("/voices/api/delete", json={
            "key": "nord",
            "db_type": "",
        })
        assert resp.status_code == 200
        assert "nord" not in client.get("/voices/api/list").json()["custom"]


# ======================================================================
# Persistence across endpoints
# ======================================================================
class TestVoicesPersistence:
    """End-to-end: save → list → delete → list."""

    def test_full_lifecycle_custom(self, client, tmp_project_root):
        key = "lifecycle_test"

        # Create.
        r = client.post("/voices/api/save", json={
            "key": key,
            "ref_audio": "Voices/qwen_speakers/test.wav",
            "ref_text": "Test transcript.",
            "db_type": "custom",
        })
        assert r.status_code == 200

        # Verify in list.
        assert key in client.get("/voices/api/list").json()["custom"]

        # Delete.
        r = client.post("/voices/api/delete", json={"key": key, "db_type": "custom"})
        assert r.status_code == 200

        # Verify gone.
        assert key not in client.get("/voices/api/list").json()["custom"]


# ======================================================================
# GET /voices/api/play
# ======================================================================
class TestVoicesApiPlay:
    """Tests for the voice preview / playback endpoint."""

    def test_play_nonexistent_file_returns_404(self, client):
        resp = client.get("/voices/api/play?path=no_such_file.wav")
        assert resp.status_code == 404

    def test_play_file_that_resolves_successfully(self, client, tmp_project_root):
        """When a WAV path resolves, it is served as audio/wav."""
        # Create a minimal valid WAV in the voices dir.
        voices_dir = tmp_project_root / "Voices" / "qwen_speakers"
        voices_dir.mkdir(parents=True, exist_ok=True)
        wav_path = voices_dir / "preview.wav"
        wav_path.write_bytes(
            b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
            b"\x01\x00\x01\x00\x80\xbb\x00\x00\x00\xee\x02\x00"
            b"\x02\x00\x10\x00data\x00\x00\x00\x00"
        )

        resp = client.get(f"/voices/api/play?path={wav_path.name}")
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"] == "audio/wav"
