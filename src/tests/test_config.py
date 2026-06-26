"""
Unit tests for ``src/config.py`` — settings management, language resolution,
path resolution, and persistence helpers.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src import config


# ======================================================================
# _resolve_lang
# ======================================================================
class TestResolveLang:
    """Tests for the language alias resolver."""

    @pytest.mark.parametrize(
        "user_input, expected",
        [
            ("ru", "russian"),
            ("RU", "russian"),
            ("Ru", "russian"),
            ("en", "english"),
            ("zh", "chinese"),
            ("ja", "japanese"),
            ("ko", "korean"),
        ],
    )
    def test_known_aliases(self, user_input, expected):
        """All known two-letter aliases map to the canonical name."""
        assert config._resolve_lang(user_input) == expected

    @pytest.mark.parametrize(
        "user_input, expected",
        [
            ("russian", "russian"),
            ("english", "english"),
            ("chinese", "chinese"),
            ("japanese", "japanese"),
            ("korean", "korean"),
            ("french", "french"),
            ("german", "german"),
            ("spanish", "spanish"),
            ("italian", "italian"),
            ("portuguese", "portuguese"),
            ("auto", "auto"),
        ],
    )
    def test_known_full_names_pass_through(self, user_input, expected):
        """Full language names are accepted as-is (lowercased)."""
        assert config._resolve_lang(user_input) == expected

    def test_unknown_language_warns_but_returns_normalized(self, monkeypatch):
        """Unknown languages produce a warning log but still return lowercased."""
        warnings = []

        def _fake_log(msg):
            if "WARNING" in msg:
                warnings.append(msg)

        monkeypatch.setattr(config, "_log", _fake_log)
        result = config._resolve_lang("elvish")
        assert result == "elvish"
        assert any("elvish" in w for w in warnings), "should warn about unknown language"

    @pytest.mark.parametrize("empty_value", [None, "", "   "])
    def test_empty_falls_back_to_global_lang(self, empty_value, monkeypatch):
        """Empty / None / whitespace returns the module-level LANG default."""
        monkeypatch.setattr(config, "LANG", "english")
        assert config._resolve_lang(empty_value) == "english"

    def test_whitespace_stripping(self):
        """Leading / trailing whitespace is stripped."""
        assert config._resolve_lang("  russian  ") == "russian"


# ======================================================================
# _get_lang_code
# ======================================================================
class TestGetLangCode:
    """Tests for the language → locale folder mapping."""

    @pytest.mark.parametrize(
        "lang, expected_code",
        [
            ("russian", "ru_RU"),
            ("english", "en_US"),
            ("chinese", "zh_CN"),
            ("japanese", "ja_JP"),
            ("korean", "ko_KR"),
            ("french", "fr_FR"),
            ("german", "de_DE"),
            ("spanish", "es_ES"),
            ("italian", "it_IT"),
            ("portuguese", "pt_BR"),
            ("auto", "en_US"),
        ],
    )
    def test_known_languages(self, lang, expected_code):
        assert config._get_lang_code(lang) == expected_code

    def test_unknown_language_falls_back_to_en_us(self):
        assert config._get_lang_code("klingon") == "en_US"


# ======================================================================
# _load_settings / _save_settings
# ======================================================================
class TestSettingsPersistence:
    """Tests for the settings persistence layer (JSON round-trip)."""

    def test_load_defaults_when_no_file(self, tmp_path, monkeypatch):
        """When the settings file does not exist, defaults are returned."""
        fake_path = tmp_path / "nonexistent_settings.json"
        monkeypatch.setattr(config, "SETTINGS_PATH", fake_path)
        monkeypatch.setattr(config, "_SETTINGS", {"lang": "russian", "seed": -1})

        result = config._load_settings()
        assert result["lang"] == "russian"

    def test_save_and_reload_roundtrip(self, tmp_path, monkeypatch):
        """Settings written by _save_settings can be read back correctly."""
        # Snapshot globals _apply_settings will touch.
        restore = {k: getattr(config, k) for k in (
            "LANG", "SEED", "MAX_NEW_TOKENS", "TEMPERATURE", "USE_FA",
        )}
        settings_path = tmp_path / "qwen_settings.json"
        monkeypatch.setattr(config, "SETTINGS_PATH", settings_path)

        test_settings = {
            "lang": "english",
            "seed": 42,
            "temperature": 0.7,
            "max_new_tokens": 512,
            "use_fa": False,
        }
        monkeypatch.setattr(config, "_SETTINGS", test_settings.copy())

        config._save_settings()
        assert settings_path.exists(), "settings file should be created"

        # Reload into a fresh dict
        monkeypatch.setattr(config, "_SETTINGS", {"lang": "russian", "seed": -1})
        loaded = config._load_settings()
        try:
            assert loaded["lang"] == "english"
            assert loaded["seed"] == 42
            assert loaded["temperature"] == 0.7
            assert loaded["max_new_tokens"] == 512
            assert loaded["use_fa"] is False
        finally:
            # Restore module globals modified by _apply_settings inside _load_settings.
            for k, v in restore.items():
                setattr(config, k, v)

    def test_save_creates_parent_directories(self, tmp_path, monkeypatch):
        """_save_settings creates intermediate directories automatically."""
        deep_path = tmp_path / "deep" / "nested" / "settings.json"
        monkeypatch.setattr(config, "SETTINGS_PATH", deep_path)

        monkeypatch.setattr(config, "_SETTINGS", {"lang": "russian"})
        config._save_settings()
        assert deep_path.exists()

    def test_load_corrupted_json_does_not_crash(self, tmp_path, monkeypatch):
        """A malformed settings file is handled gracefully (falls back to defaults)."""
        bad_path = tmp_path / "bad_settings.json"
        bad_path.write_text("this is not json {{{", encoding="utf-8")
        monkeypatch.setattr(config, "SETTINGS_PATH", bad_path)

        defaults = {"lang": "russian", "seed": -1}
        monkeypatch.setattr(config, "_SETTINGS", defaults.copy())

        result = config._load_settings()
        assert result == defaults

    def test_load_non_dict_json_is_ignored(self, tmp_path, monkeypatch):
        """A JSON array (not object) is ignored; defaults are kept."""
        arr_path = tmp_path / "array_settings.json"
        arr_path.write_text('[{"lang": "english"}]', encoding="utf-8")
        monkeypatch.setattr(config, "SETTINGS_PATH", arr_path)

        defaults = {"lang": "russian"}
        monkeypatch.setattr(config, "_SETTINGS", defaults.copy())
        result = config._load_settings()
        assert result["lang"] == "russian"


# ======================================================================
# _apply_settings
# ======================================================================
class TestApplySettings:
    """Tests for _apply_settings that copies dict values to module globals."""

    def test_apply_updates_module_globals(self, monkeypatch):
        """After _apply_settings, module-level globals reflect _SETTINGS."""
        # Snapshot the globals we're about to change so we can restore them.
        restore = {k: getattr(config, k) for k in (
            "LANG", "TEMPERATURE", "SEED", "USE_FA", "APPEND_ENDING_PAUSE",
        )}

        monkeypatch.setattr(config, "_SETTINGS", {
            "lang": "english",
            "temperature": 0.5,
            "seed": 123,
            "use_fa": False,
            "append_ending_pause": False,
        })
        config._apply_settings()

        try:
            assert config.LANG == "english"
            assert config.TEMPERATURE == 0.5
            assert config.SEED == 123
            assert config.USE_FA is False
            assert config.APPEND_ENDING_PAUSE is False
        finally:
            # Restore globals so other tests see the originals.
            for k, v in restore.items():
                setattr(config, k, v)

    def test_missing_keys_keep_existing_globals(self, monkeypatch):
        """When a key is absent from _SETTINGS the global is left unchanged."""
        restore_lang = config.LANG
        restore_temp = config.TEMPERATURE

        monkeypatch.setattr(config, "TEMPERATURE", 0.99)
        monkeypatch.setattr(config, "_SETTINGS", {"lang": "japanese"})
        config._apply_settings()
        try:
            assert config.LANG == "japanese"
            assert config.TEMPERATURE == 0.99  # untouched
        finally:
            config.LANG = restore_lang
            config.TEMPERATURE = restore_temp


# ======================================================================
# _resolve_path
# ======================================================================
class TestResolvePath:
    """Tests for the multi-strategy path resolver."""

    def test_absolute_existing_path(self, tmp_path, monkeypatch):
        """An absolute path that exists is returned as-is."""
        f = tmp_path / "real.wav"
        f.write_text("audio")
        monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(config, "VOICES_DIR", tmp_path / "Voices")
        assert config._resolve_path(str(f)) == f

    def test_absolute_nonexistent_falls_back_to_basename(self, tmp_path, monkeypatch):
        """An absolute path that doesn't exist triggers basename resolution."""
        root = tmp_path
        (root / "fallback.wav").write_text("audio")
        monkeypatch.setattr(config, "PROJECT_ROOT", root)
        monkeypatch.setattr(config, "VOICES_DIR", root / "Voices")
        # Use a Windows-style absolute path with a drive letter that doesn't exist.
        resolved = config._resolve_path("X:\\nonexistent\\deadbeef\\fallback.wav")
        assert resolved == root / "fallback.wav"

    def test_relative_path_resolved_against_project_root(self, tmp_path, monkeypatch):
        """A relative path is looked up under PROJECT_ROOT first."""
        root = tmp_path
        target = root / "Voices" / "qwen_speakers" / "test.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("audio")
        monkeypatch.setattr(config, "PROJECT_ROOT", root)
        monkeypatch.setattr(config, "VOICES_DIR", root / "Voices")
        resolved = config._resolve_path("qwen_speakers/test.wav")
        assert resolved == target

    def test_basename_only_searches_voice_subdirs(self, tmp_path, monkeypatch):
        """A bare filename is searched in qwen_speakers/ and runtime_speakers/."""
        root = tmp_path
        (root / "Voices" / "qwen_speakers").mkdir(parents=True, exist_ok=True)
        (root / "Voices" / "runtime_speakers").mkdir(parents=True, exist_ok=True)
        target = root / "Voices" / "runtime_speakers" / "found.wav"
        target.write_text("audio")

        monkeypatch.setattr(config, "PROJECT_ROOT", root)
        monkeypatch.setattr(config, "VOICES_DIR", root / "Voices")
        resolved = config._resolve_path("found.wav")
        assert resolved == target


# ======================================================================
# Default constants
# ======================================================================
class TestDefaultConstants:
    """Verify the module-level defaults match expectations."""

    def test_host_default(self):
        assert config.HOST == "0.0.0.0"

    def test_port_default(self):
        assert config.PORT == 7861

    def test_synthesis_defaults(self):
        assert config.LANG == "russian"
        assert config.SEED == -1
        assert config.MAX_NEW_TOKENS == 2048
        assert config.TEMPERATURE == 0.9
        assert config.TOP_K == 50
        assert config.TOP_P == 1.0
        assert config.REPETITION_PENALTY == 1.05

    def test_cleanup_defaults(self):
        assert config.CLEANUP_ENABLED is True
        assert config.CLEANUP_INTERVAL_MINUTES == 30.0
        assert config.KEEP_OUTPUT_MINUTES == 60.0

    def test_known_langs_set(self):
        """The KNOWN_LANGS set contains all expected languages."""
        assert "russian" in config.KNOWN_LANGS
        assert "english" in config.KNOWN_LANGS
        assert "chinese" in config.KNOWN_LANGS
        assert "auto" in config.KNOWN_LANGS
        assert len(config.KNOWN_LANGS) >= 10


# ======================================================================
# Log buffer
# ======================================================================
class TestLogBuffer:
    """The in-memory log buffer is accessible for the /settings/api/logs endpoint."""

    def test_log_appends_to_buffer(self, monkeypatch):
        from collections import deque

        buf = deque(maxlen=100)
        monkeypatch.setattr(config, "_LOG_BUFFER", buf)
        config._log("test message 1")
        config._log("test message 2")
        assert "test message 1" in list(buf)
        assert "test message 2" in list(buf)

    def test_log_buffer_respects_maxlen(self, monkeypatch):
        import threading
        from collections import deque

        buf = deque(maxlen=5)
        monkeypatch.setattr(config, "_LOG_BUFFER", buf)
        monkeypatch.setattr(config, "_log_lock", threading.Lock())
        for i in range(10):
            config._log(f"msg {i}")
        assert len(buf) == 5
