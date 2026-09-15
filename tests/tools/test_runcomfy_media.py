"""Tests for local-media upload in the RunComfy CLI wrapper (no network).

Run: pytest tests/tools/test_runcomfy_media.py -v
"""

from __future__ import annotations

import pytest

from tools import _runcomfy_cli as rc
from tools.video.runcomfy_video import RunComfyVideo


@pytest.fixture
def fake_upload(monkeypatch):
    calls = []

    def upload(path, media_host="auto"):
        calls.append((path.name, media_host))
        return f"https://files.example/{path.name}"

    monkeypatch.setattr(rc, "upload_media", upload)
    return calls


def test_local_paths_in_media_fields_are_uploaded(tmp_path, fake_upload):
    img = tmp_path / "hero.png"
    img.write_bytes(b"png")
    clip = tmp_path / "motion.mp4"
    clip.write_bytes(b"mp4")

    resolved, uploaded = rc.resolve_local_media(
        {
            "prompt": str(img),  # not a media field: left alone
            "reference_images": [str(img), "https://cdn.example/ref.png", str(img)],
            "video": str(clip),
            "duration": 5,
        }
    )

    assert resolved["prompt"] == str(img)
    assert resolved["reference_images"] == [
        "https://files.example/hero.png",
        "https://cdn.example/ref.png",
        "https://files.example/hero.png",
    ]
    assert resolved["video"] == "https://files.example/motion.mp4"
    assert resolved["duration"] == 5
    assert len(uploaded) == 2
    assert fake_upload == [("hero.png", "auto"), ("motion.mp4", "auto")]  # deduped


def test_missing_paths_and_urls_pass_through(fake_upload):
    inputs = {"images": ["/no/such/file.png", "https://x/y.png"], "image_url": "data:image/png;base64,AA"}
    resolved, uploaded = rc.resolve_local_media(inputs)
    assert resolved == inputs
    assert uploaded == {}
    assert fake_upload == []


def test_auto_host_picks_litterbox_without_fal_key(tmp_path, monkeypatch):
    monkeypatch.delenv("FAL_KEY", raising=False)
    monkeypatch.delenv("FAL_AI_API_KEY", raising=False)
    monkeypatch.setattr(rc, "_upload_litterbox", lambda p: "https://litter.catbox.moe/abc.png")
    monkeypatch.setattr(rc, "_upload_fal", lambda p: pytest.fail("fal used without key"))
    f = tmp_path / "a.png"
    f.write_bytes(b"x")
    assert rc.upload_media(f) == "https://litter.catbox.moe/abc.png"


def test_auto_host_prefers_fal_when_key_set(tmp_path, monkeypatch):
    monkeypatch.setenv("FAL_KEY", "k")
    monkeypatch.setattr(rc, "_upload_fal", lambda p: "https://fal.media/a.png")
    f = tmp_path / "a.png"
    f.write_bytes(b"x")
    assert rc.upload_media(f) == "https://fal.media/a.png"


def test_upload_failure_becomes_tool_error(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNCOMFY_TOKEN", "t")

    def boom(p):
        raise ConnectionError("offline")

    monkeypatch.setattr(rc, "_upload_litterbox", boom)
    f = tmp_path / "a.png"
    f.write_bytes(b"x")
    result = RunComfyVideo().execute(
        {
            "model_id": "minimax/minimax-h3-max/reference-to-video",
            "inputs": {"prompt": "p", "reference_images": [str(f)]},
            "media_host": "litterbox",
            "output_dir": str(tmp_path / "out"),
        }
    )
    assert not result.success
    assert "litterbox failed" in result.error


def test_invalid_media_host_rejected(tmp_path):
    f = tmp_path / "a.png"
    f.write_bytes(b"x")
    with pytest.raises(rc.RunComfyCLIError):
        rc.upload_media(f, "s3")


def test_video_tool_declares_reference_to_video():
    assert "reference_to_video" in RunComfyVideo.capabilities
    assert "media_host" in RunComfyVideo.input_schema["properties"]
