"""
Integration tests for TTS synthesis and SkyrimNet-compatible endpoints.

Covers:
- ``/tts_to_audio/`` — core speech synthesis.
- ``/create_and_store_latents/`` — SkyrimNet no-op endpoint.
- Backend protective mechanisms (subtalker_do_sample force, use_fa
  disable for CPU / 0.6B-Vulkan).
- Error handling: missing ref audio, empty text, missing backend.
"""

import io
import json
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ======================================================================
# /tts_to_audio/ — successful responses
# ======================================================================
class TestTtsToAudio:
    """Core speech synthesis endpoint tests."""

    # ------------------------------------------------------------------
    # Ping (silence) path
    # ------------------------------------------------------------------
    def test_ping_returns_silence_wav(self, client):
        """Sending text='ping' returns a valid WAV (silence)."""
        resp = client.post("/tts_to_audio/", json={
            "text": "ping",
            "speaker_wav": "does_not_matter",
            "language": "ru",
        })
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"] == "audio/wav"
        data = resp.read()
        assert len(data) > 44, "must be larger than a minimal WAV header"

    def test_ping_returns_valid_wav_format(self, client):
        """The silence WAV returned for ping has correct RIFF structure."""
        resp = client.post("/tts_to_audio/", json={"text": "ping"})
        data = resp.read()
        with wave.open(io.BytesIO(data), "rb") as w:
            assert w.getnchannels() == 1
            assert w.getsampwidth() == 2  # 16-bit PCM
            assert w.getframerate() == 24000

    # ------------------------------------------------------------------
    # No backend — falls back to silence
    # ------------------------------------------------------------------
    def test_no_backend_returns_silence_fallback(self, client, monkeypatch):
        """When PERSISTENT_BACKEND is None, the endpoint returns silence."""
        # Both the backend module and the endpoints_skyrim module access
        # the same singleton via ``from src.core import backend; backend.PERSISTENT_BACKEND``.
        monkeypatch.setattr("src.core.backend.PERSISTENT_BACKEND", None)

        resp = client.post("/tts_to_audio/", json={
            "text": "Hello, world.",
            "speaker_wav": "default",
            "language": "en",
        })
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"

    # ------------------------------------------------------------------
    # Mocked backend — successful synthesis
    # ------------------------------------------------------------------
    def test_mocked_backend_returns_wav(self, client, monkeypatch, tmp_project_root):
        """With a mocked PERSISTENT_BACKEND that returns a path, we get a WAV."""
        output_dir = tmp_project_root / "output_temp" / "qwentts_generated"
        output_dir.mkdir(parents=True, exist_ok=True)
        fake_wav = output_dir / "mock_output.wav"
        fake_wav.write_bytes(
            b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
            b"\x01\x00\x01\x00\x80\xbb\x00\x00\x00\xee\x02\x00"
            b"\x02\x00\x10\x00data\x00\x00\x00\x00"
        )

        mock_backend = MagicMock()
        mock_backend.infer.return_value = fake_wav
        mock_backend.talker_path = Path("/fake/talker.gguf")

        # Both endpoints_skyrim.py and backend.py access the same singleton via
        # ``from src.core import backend; backend.PERSISTENT_BACKEND``, so
        # patching src.core.backend covers both.
        monkeypatch.setattr("src.core.backend.PERSISTENT_BACKEND", mock_backend)

        resp = client.post("/tts_to_audio/", json={
            "text": "Test synthesis.",
            "speaker_wav": "default",
            "language": "ru",
        })
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"

    # ------------------------------------------------------------------
    # Error: empty text (falls back to silence)
    # ------------------------------------------------------------------
    def test_empty_text_returns_silence(self, client):
        """An empty text string should not crash; silence is returned."""
        resp = client.post("/tts_to_audio/", json={
            "text": "",
            "speaker_wav": "default",
            "language": "ru",
        })
        # Should succeed (silence fallback).
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"

    # ------------------------------------------------------------------
    # Request with save_path
    # ------------------------------------------------------------------
    def test_with_save_path_returns_wav(self, client):
        """Providing a save_path still produces a valid audio response."""
        resp = client.post("/tts_to_audio/", json={
            "text": "ping",
            "save_path": "custom_name.wav",
        })
        assert resp.status_code == 200


# ======================================================================
# /create_and_store_latents/ — SkyrimNet compatibility
# ======================================================================
class TestCreateAndStoreLatents:
    """Tests for the SkyrimNet no-op latents endpoint."""

    def test_returns_success_with_expected_structure(self, client):
        resp = client.post("/create_and_store_latents/", json={
            "speaker": "test_speaker",
            "language": "ru",
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["backend"] == "qwentts-adapter"
        assert "received" in body

    def test_multipart_form_data_is_accepted(self, client):
        """The endpoint also accepts multipart/form-data (SkyrimNet convention)."""
        resp = client.post(
            "/create_and_store_latents/",
            data={"speaker": "ulfric", "language": "ru"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["received"]["speaker"] == "ulfric"

    def test_no_fields_still_succeeds(self, client):
        resp = client.post("/create_and_store_latents/")
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# ======================================================================
# Backend protective mechanisms (unit-level, backend.py logic)
# ======================================================================
class TestBackendProtections:
    """Verify the protective logic inside PersistentQwenTTSBackend.__init__."""

    def _make_mock_bindings(self, monkeypatch):
        """Set up mock bindings so PersistentQwenTTSBackend can init WITHOUT the real DLL.

        IMPORTANT: backend.py imports these names with ``from src.core.bindings import …``,
        so we must monkeypatch them in ``src.core.backend``, not ``src.core.bindings``.

        The ``*_default_params`` mocks are no-ops — the calling code overwrites every
        field after calling them, and they receive ``ctypes.byref()`` objects (which
        lack ``.contents``).
        """
        import ctypes

        def _mock_init_defaults(_params_ptr):
            pass  # all fields set explicitly by caller

        def _mock_init(_params_ptr):
            return ctypes.c_void_p(0xDEADBEEF)

        def _mock_free(_ctx):
            pass

        def _mock_tts_defaults(_params_ptr):
            pass  # all fields set explicitly by caller

        def _mock_version():
            return b"0.1.0-mock"

        def _mock_last_error():
            return None

        # Patch the *imported* names in backend.py.
        monkeypatch.setattr("src.core.backend.qt_init_default_params", _mock_init_defaults)
        monkeypatch.setattr("src.core.backend.qt_init", _mock_init)
        monkeypatch.setattr("src.core.backend.qt_free", _mock_free)
        monkeypatch.setattr("src.core.backend.qt_tts_default_params", _mock_tts_defaults)
        monkeypatch.setattr("src.core.backend.qt_version", _mock_version)
        monkeypatch.setattr("src.core.backend.qt_last_error", _mock_last_error)
        # Default: synthesizer returns error so no test accidentally calls the real DLL.
        monkeypatch.setattr("src.core.backend.qt_synthesize", lambda *a: -1)
        monkeypatch.setattr("src.core.backend.qt_audio_free", lambda x: None)

    def test_use_fa_forced_off_for_cpu_backend(self, monkeypatch, tmp_path):
        """On CPU, use_fa is automatically forced to False."""
        monkeypatch.setattr("src.core.backend.os.environ", {"GGML_BACKEND": "CPU"})

        talker = tmp_path / "talker.gguf"
        codec = tmp_path / "codec.gguf"
        talker.write_bytes(b"\x00" * 100)
        codec.write_bytes(b"\x00" * 100)

        self._make_mock_bindings(monkeypatch)

        from src.core.backend import PersistentQwenTTSBackend

        backend = PersistentQwenTTSBackend(talker, codec, use_fa=True)
        assert backend.use_fa is False, "use_fa must be forced off on CPU"

    def test_use_fa_forced_off_for_0_6b_on_vulkan(self, monkeypatch, tmp_path):
        """On Vulkan with a 0.6B model, use_fa is forced to False."""
        monkeypatch.setattr("src.core.backend.os.environ", {"GGML_BACKEND": "Vulkan0"})

        # Name must contain "0.6b" to trigger the guard.
        talker = tmp_path / "qwen-talker-0.6b-base-Q4_K_M.gguf"
        codec = tmp_path / "codec.gguf"
        # Make talker file small enough (< 800 MB) so the 0.6b check passes.
        talker.write_bytes(b"\x00" * 100)
        codec.write_bytes(b"\x00" * 100)

        self._make_mock_bindings(monkeypatch)

        from src.core.backend import PersistentQwenTTSBackend

        backend = PersistentQwenTTSBackend(talker, codec, use_fa=True)
        assert backend.use_fa is False, (
            "use_fa must be forced off for 0.6B model on Vulkan"
        )

    def test_use_fa_remains_on_for_1_7b_on_vulkan(self, monkeypatch, tmp_path):
        """On Vulkan with a 1.7B model, use_fa stays True."""
        monkeypatch.setattr("src.core.backend.os.environ", {"GGML_BACKEND": "Vulkan0"})

        talker = tmp_path / "qwen-talker-1.7b-base-Q4_K_M.gguf"
        codec = tmp_path / "codec.gguf"
        # Make it large enough so the 0.6b path doesn't match.
        # The 0.6b check is: "0.6b" in name.lower() OR size < 800 MB
        # We name it 1.7b AND make it big enough.
        talker.write_bytes(b"\x00" * 100)
        codec.write_bytes(b"\x00" * 100)

        self._make_mock_bindings(monkeypatch)
        # Need to mock stat().st_size to be > 800 MB to avoid the size-based check.
        # Actually the check is:
        #   is_0_6b = "0.6b" in talker_path.name.lower() or talker_path.stat().st_size < 800 * 1024 * 1024
        # With 100 bytes, it's < 800 MB, so is_0_6b would be True from the size check.
        # We need to mock the stat result.
        from unittest.mock import patch as mock_patch

        class FakeStat:
            st_size = 900 * 1024 * 1024  # 900 MB

        with mock_patch.object(Path, "stat", return_value=FakeStat):
            from src.core.backend import PersistentQwenTTSBackend
            backend = PersistentQwenTTSBackend(talker, codec, use_fa=True, clamp_fp16=False)
            assert backend.use_fa is True, (
                "use_fa should remain True for 1.7B model on Vulkan"
            )

    def test_no_use_fa_force_on_cuda(self, monkeypatch, tmp_path):
        """On CUDA, use_fa is NOT forced off (no guard for CUDA)."""
        monkeypatch.setattr("src.core.backend.os.environ", {"GGML_BACKEND": "CUDA0"})

        talker = tmp_path / "talker.gguf"
        codec = tmp_path / "codec.gguf"
        talker.write_bytes(b"\x00" * 100)
        codec.write_bytes(b"\x00" * 100)

        self._make_mock_bindings(monkeypatch)

        from src.core.backend import PersistentQwenTTSBackend

        backend = PersistentQwenTTSBackend(talker, codec, use_fa=True)
        assert backend.use_fa is True, "use_fa should not be forced off on CUDA"

    def test_subtalker_do_sample_forced_true(self, monkeypatch, tmp_path):
        """The subtalker_do_sample=False guard forces it back to True.

        Because mock qt_synthesize receives ``ctypes.byref()`` arguments (CArgObject)
        that cannot be dereferenced from Python, ``infer()`` will fail at the
        synthesizer call.  However, the guard runs *before* that call and emits a
        warning log — we verify that the warning is present in the log buffer.
        """
        monkeypatch.setattr("src.core.backend.os.environ", {"GGML_BACKEND": "CPU"})
        monkeypatch.setattr("src.config.SUB_DO_SAMPLE", False)

        talker = tmp_path / "qwen-talker-1.7b-voicedesign-Q4_K_M.gguf"
        codec = tmp_path / "codec.gguf"
        talker.write_bytes(b"\x00" * 100)
        codec.write_bytes(b"\x00" * 100)

        self._make_mock_bindings(monkeypatch)

        from src.core.backend import PersistentQwenTTSBackend

        backend = PersistentQwenTTSBackend(talker, codec, use_fa=False)

        # Call infer() — it will fail at qt_synthesize (CArgObject), but
        # the subtalker_do_sample guard runs BEFORE the synthesizer call.
        voice_ref = {"instruct": "neutral tone"}
        out = tmp_path / "out.wav"
        backend.infer(voice_ref, "Hello", out, None, "en")

        # Verify the guard warning was emitted.
        from src.config import _LOG_BUFFER, _log_lock
        with _log_lock:
            logs = list(_LOG_BUFFER)
        guard_warning = any(
            "subtalker_do_sample is False" in msg and "Forcing to True" in msg
            for msg in logs
        )
        assert guard_warning, (
            "subtalker_do_sample must be forced to True when SUB_DO_SAMPLE=False; "
            "expected warning in log buffer"
        )


# ======================================================================
# Error handling inside infer()
# ======================================================================
class TestBackendInferErrors:
    """Test error paths in PersistentQwenTTSBackend.infer()."""

    def _make_backend(self, monkeypatch, tmp_path):
        """Create a minimal working backend (no real DLL calls)."""
        monkeypatch.setattr("src.core.backend.os.environ", {"GGML_BACKEND": "CPU"})

        import ctypes

        def _init_defaults(_params_ptr):
            pass  # all fields set explicitly by caller

        def _init(_params_ptr):
            return ctypes.c_void_p(0xBEEF)

        def _free(_ctx):
            pass

        def _tts_defaults(_params_ptr):
            pass  # all fields set explicitly by caller

        def _mock_version():
            return b"0.1.0-mock"

        def _mock_last_error():
            return None

        # Patch the *imported* names in backend.py.
        monkeypatch.setattr("src.core.backend.qt_init_default_params", _init_defaults)
        monkeypatch.setattr("src.core.backend.qt_init", _init)
        monkeypatch.setattr("src.core.backend.qt_free", _free)
        monkeypatch.setattr("src.core.backend.qt_tts_default_params", _tts_defaults)
        monkeypatch.setattr("src.core.backend.qt_version", _mock_version)
        monkeypatch.setattr("src.core.backend.qt_last_error", _mock_last_error)
        monkeypatch.setattr("src.core.backend.qt_audio_free", lambda x: None)

        talker = tmp_path / "talker.gguf"
        codec = tmp_path / "codec.gguf"
        talker.write_bytes(b"\x00" * 100)
        codec.write_bytes(b"\x00" * 100)

        from src.core.backend import PersistentQwenTTSBackend
        return PersistentQwenTTSBackend(talker, codec, use_fa=False)

    def test_infer_with_missing_ref_audio_returns_none(self, monkeypatch, tmp_path):
        """When ref_audio path doesn't exist on disk, infer returns None."""
        backend = self._make_backend(monkeypatch, tmp_path)
        voice_ref = {
            "ref_audio": str(tmp_path / "nonexistent" / "ghost.wav"),
            "ref_text": "Hello.",
        }
        out = tmp_path / "out.wav"
        result = backend.infer(voice_ref, "Hello test", out, None, "en")
        assert result is None, "missing ref_audio should cause None return"

    def test_infer_with_voicedesign_model_and_custom_ref_fails(self, monkeypatch, tmp_path):
        """A design model rejects custom voice refs (and vice versa)."""
        monkeypatch.setattr("src.core.backend.os.environ", {"GGML_BACKEND": "CPU"})
        import ctypes

        def _init_defaults(_p): pass
        def _init(_p): return ctypes.c_void_p(0xBEEF)
        def _free(_ctx): pass

        monkeypatch.setattr("src.core.backend.qt_init_default_params", _init_defaults)
        monkeypatch.setattr("src.core.backend.qt_init", _init)
        monkeypatch.setattr("src.core.backend.qt_free", _free)
        monkeypatch.setattr("src.core.backend.qt_version", lambda: b"mock")
        monkeypatch.setattr("src.core.backend.qt_last_error", lambda: None)

        talker = tmp_path / "qwen-talker-voicedesign-model.gguf"
        codec = tmp_path / "codec.gguf"
        talker.write_bytes(b"\x00" * 100)
        codec.write_bytes(b"\x00" * 100)

        from src.core.backend import PersistentQwenTTSBackend
        backend = PersistentQwenTTSBackend(talker, codec, use_fa=False)

        # Custom voice (no instruct) → should fail with design model.
        voice_ref = {
            "ref_audio": str(tmp_path / "some.wav"),
            "ref_text": "Hello.",
        }
        out = tmp_path / "out.wav"
        result = backend.infer(voice_ref, "Hello test", out, None, "en")
        assert result is None, (
            "custom voice ref must be rejected when using a voicedesign model"
        )

    def test_qt_synthesize_nonzero_status_returns_none(self, monkeypatch, tmp_path):
        """When qt_synthesize returns a non-zero status, infer returns None."""
        backend = self._make_backend(monkeypatch, tmp_path)

        def _fail_synthesize(ctx, params_ptr, audio_ptr):
            return -1  # QT_STATUS_INVALID_PARAMS

        monkeypatch.setattr("src.core.backend.qt_synthesize", _fail_synthesize)

        voice_ref = {"instruct": "neutral"}
        out = tmp_path / "out.wav"
        result = backend.infer(voice_ref, "Hello", out, None, "en")
        assert result is None, "non-zero status should cause None return"


# ======================================================================
# Backend detection
# ======================================================================
class TestDetectBackends:
    """Tests for _detect_backends and related logic."""

    def test_all_not_built_when_dll_missing(self, monkeypatch, tmp_path):
        """When qwen.dll doesn't exist, all backends report 'not_built'."""
        empty_bin = tmp_path / "empty_bin"
        empty_bin.mkdir()
        monkeypatch.setattr("src.config.BIN_DIR", empty_bin)

        from src.core.backend import _detect_backends
        result = _detect_backends()
        for name in ("qwentts_CPU", "qwentts_CUDA", "qwentts_VULKAN"):
            assert result[name] == "not_built", f"{name} should be not_built"

    def test_cpu_ready_when_qwen_dll_exists(self, monkeypatch, tmp_path):
        """When qwen.dll exists (and no GPU DLLs), CPU is ready."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        (bin_dir / "qwen.dll").touch()
        monkeypatch.setattr("src.config.BIN_DIR", bin_dir)

        from src.core.backend import _detect_backends
        result = _detect_backends()
        assert result["qwentts_CPU"] == "ready"
        assert result["qwentts_CUDA"] == "not_built"
        assert result["qwentts_VULKAN"] == "not_built"

    def test_cuda_ready_when_cuda_dll_present(self, monkeypatch, tmp_path):
        """When ggml-cuda.dll exists alongside qwen.dll, CUDA is ready."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        (bin_dir / "qwen.dll").touch()
        (bin_dir / "ggml-cuda.dll").touch()
        monkeypatch.setattr("src.config.BIN_DIR", bin_dir)

        from src.core.backend import _detect_backends
        result = _detect_backends()
        assert result["qwentts_CPU"] == "ready"
        assert result["qwentts_CUDA"] == "ready"
        assert result["qwentts_VULKAN"] == "not_built"
