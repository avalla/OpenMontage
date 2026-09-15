"""Shared subprocess wrapper around the RunComfy CLI (`@runcomfy/cli`).

RunComfy's Model API lets you invoke any hosted ComfyUI-backed model by
`model_id` without deploying a workflow yourself. The CLI (`runcomfy run`)
wraps submit -> poll -> download in one blocking call, which is what the
image/video tool wrappers in this package use.

Docs: https://docs.runcomfy.com/cli/introduction
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional


class RunComfyCLIError(Exception):
    pass


# RunComfy's Model API proxies many underlying model families under one CLI.
# The right Layer-3 agent skill (prompting/parameter guidance) depends on
# *which model_id is invoked*, not on RunComfy itself. Match model_id
# substrings (case-insensitive) against known underlying model families that
# already have a Layer-3 skill in .agents/skills/. Extend this table as new
# RunComfy-hosted families get a skill of their own.
MODEL_FAMILY_SKILLS: dict[str, list[str]] = {
    "flux": ["flux-best-practices", "bfl-api"],
    "kling": ["ai-video-gen"],
    "seedance": ["seedance-2-0", "ai-video-gen"],
    "ltx": ["ltx2", "ai-video-gen"],
    "veo": ["ai-video-gen"],
    "runway": ["ai-video-gen"],
    "wav2lip": ["faceswap"],
    "sadtalker": ["avatar-video"],
    "ace-step": ["runcomfy-music", "acestep"],
    "music-generation": ["runcomfy-music", "music"],
    "minimax": ["minimax-h3", "ai-video-gen"],
    "gemini-omni": ["ai-video-gen"],
}


# RunComfy's Model API only accepts public HTTPS URLs for media inputs (no
# base64/data: URIs, no upload endpoint). Local files passed in media fields
# (reference_images, images, video, audios, image_url, ...) are uploaded to a
# temporary host first. "auto" uses fal.ai storage when FAL_KEY is set and
# otherwise litterbox (catbox.moe temporary storage: keyless, unlisted public
# link that expires after 72h).
MEDIA_HOSTS = ("auto", "fal", "litterbox")
MEDIA_HOST_SCHEMA = {
    "type": "string",
    "enum": list(MEDIA_HOSTS),
    "default": "auto",
    "description": (
        "Where to upload local file paths found in media fields of `inputs` "
        "(RunComfy only accepts public https URLs). auto = fal.ai storage if FAL_KEY "
        "is set, else litterbox (keyless temporary catbox.moe link, expires in 72h)."
    ),
}
_MEDIA_KEY_RE = re.compile(r"image|video|audio|frame|mask|url|uri|file", re.IGNORECASE)
LITTERBOX_API = "https://litterbox.catbox.moe/resources/internals/api.php"


def _local_file(value: Any) -> Optional[Path]:
    if not isinstance(value, str) or re.match(r"^[a-z][a-z0-9+.-]*://", value, re.IGNORECASE):
        return None
    path = Path(value).expanduser()
    return path if path.is_file() else None


def _upload_fal(path: Path) -> str:
    import requests

    api_key = os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")
    if not api_key:
        raise RunComfyCLIError("media_host='fal' requires FAL_KEY or FAL_AI_API_KEY.")
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    init = requests.post(
        "https://rest.alpha.fal.ai/storage/upload/initiate",
        headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
        json={"content_type": content_type, "file_name": path.name},
        timeout=30,
    )
    init.raise_for_status()
    data = init.json()
    put = requests.put(
        data["upload_url"],
        headers={"Content-Type": content_type},
        data=path.read_bytes(),
        timeout=300,
    )
    put.raise_for_status()
    return data["file_url"]


def _upload_litterbox(path: Path) -> str:
    import requests

    with path.open("rb") as fh:
        resp = requests.post(
            LITTERBOX_API,
            data={"reqtype": "fileupload", "time": "72h"},
            files={"fileToUpload": (path.name, fh)},
            # The default python-requests User-Agent is rejected with 412.
            headers={"User-Agent": "OpenMontage/1.0 (+https://github.com/calesthio/OpenMontage)"},
            timeout=300,
        )
    resp.raise_for_status()
    url = resp.text.strip()
    if not url.startswith("https://"):
        raise RunComfyCLIError(f"litterbox upload of {path} failed: {url[:300]}")
    return url


def upload_media(path: Path, media_host: str = "auto") -> str:
    """Upload a local file and return a public https URL RunComfy can fetch."""
    if media_host not in MEDIA_HOSTS:
        raise RunComfyCLIError(f"media_host must be one of {MEDIA_HOSTS}, got {media_host!r}.")
    if media_host == "auto":
        has_fal = os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")
        media_host = "fal" if has_fal else "litterbox"
    try:
        return _upload_fal(path) if media_host == "fal" else _upload_litterbox(path)
    except RunComfyCLIError:
        raise
    except Exception as e:  # network/HTTP errors from requests
        raise RunComfyCLIError(f"Uploading {path} via {media_host} failed: {e}") from e


def resolve_local_media(
    model_inputs: dict[str, Any], media_host: str = "auto"
) -> tuple[dict[str, Any], dict[str, str]]:
    """Replace local file paths in top-level media fields with uploaded URLs.

    Only keys that look like media fields (image/video/audio/frame/mask/url/
    uri/file) are inspected, as a string or a list of strings. Returns the new
    payload and a {local_path: url} map of what was uploaded.
    """
    uploaded: dict[str, str] = {}

    def resolve(value: Any) -> Any:
        path = _local_file(value)
        if path is None:
            return value
        key = str(path.resolve())
        if key not in uploaded:
            uploaded[key] = upload_media(path, media_host)
        return uploaded[key]

    resolved: dict[str, Any] = {}
    for name, value in model_inputs.items():
        if not _MEDIA_KEY_RE.search(name):
            resolved[name] = value
        elif isinstance(value, list):
            resolved[name] = [resolve(v) for v in value]
        else:
            resolved[name] = resolve(value)
    return resolved, uploaded


def skills_for_model_id(model_id: str) -> list[str]:
    """Best-guess Layer-3 skill(s) to read before crafting inputs for model_id.

    Returns [] when no known family matches — that means either a generic
    prompt is fine, or this table needs a new entry once a skill exists for
    that model family. Always check https://www.runcomfy.com/models for the
    model's own input schema regardless of skill match.
    """
    lowered = model_id.lower()
    skills: list[str] = []
    for family, family_skills in MODEL_FAMILY_SKILLS.items():
        if family in lowered:
            for skill in family_skills:
                if skill not in skills:
                    skills.append(skill)
    return skills


def get_token() -> Optional[str]:
    return os.environ.get("RUNCOMFY_TOKEN")


def cli_available() -> bool:
    """True if either the installed `runcomfy` binary or `npx` exists."""
    return shutil.which("runcomfy") is not None or shutil.which("npx") is not None


def _base_command() -> list[str]:
    runcomfy_bin = shutil.which("runcomfy")
    if runcomfy_bin:
        return [runcomfy_bin]
    npx = shutil.which("npx")
    if not npx:
        raise RunComfyCLIError(
            "Neither 'runcomfy' nor 'npx' found on PATH. Install Node.js >= 18 "
            "(https://nodejs.org/) to run the RunComfy CLI via npx."
        )
    return [npx, "-y", "@runcomfy/cli"]


def _parse_json_output(stdout: str) -> Optional[Any]:
    """Parse the last JSON object in stdout, tolerating progress lines before it."""
    text = stdout.strip()
    if not text:
        return None
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def run_model(
    model_id: str,
    model_inputs: dict[str, Any],
    output_dir: str,
    *,
    timeout_seconds: int = 600,
    media_host: str = "auto",
) -> dict[str, Any]:
    """Run `runcomfy run <model_id> --input <json> --output-dir <dir> --output json`.

    Blocks until the request completes (or times out), downloads outputs into
    output_dir, and returns the parsed `--output json` payload plus the list
    of files actually written.

    Local file paths in media fields are uploaded first (see resolve_local_media).

    Raises RunComfyCLIError on missing token/CLI, failed upload, non-zero exit,
    or timeout.
    """
    token = get_token()
    if not token:
        raise RunComfyCLIError(
            "RUNCOMFY_TOKEN not set. Get a token from https://www.runcomfy.com/profile "
            "(click your avatar -> API tokens) and add RUNCOMFY_TOKEN=... to .env, "
            "or run `runcomfy login` once locally and it will be picked up from "
            "~/.config/runcomfy/token.json."
        )

    model_inputs, uploaded_media = resolve_local_media(model_inputs, media_host)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    before = {p: p.stat().st_mtime for p in out_dir.glob("*") if p.is_file()}

    env = dict(os.environ)
    env["RUNCOMFY_TOKEN"] = token

    # Write the payload to a temp file rather than passing it inline via
    # --input: large payloads (e.g. base64-encoded reference images for
    # image-to-video) blow past the OS arg-list limit (E2BIG) if passed
    # directly on the command line.
    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", prefix="runcomfy_input_", delete=False
    ) as tmp:
        json.dump(model_inputs, tmp)
        input_file_path = tmp.name

    cmd = _base_command() + [
        "run",
        model_id,
        "--input-file",
        input_file_path,
        "--output-dir",
        str(out_dir),
        "--output",
        "json",
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise RunComfyCLIError(
            f"runcomfy CLI timed out after {timeout_seconds}s running model {model_id!r}: "
            f"{(e.stderr or '')[-2000:]}"
        ) from e
    finally:
        try:
            os.unlink(input_file_path)
        except OSError:
            pass

    if proc.returncode != 0:
        raise RunComfyCLIError(
            f"runcomfy CLI exited {proc.returncode} for model {model_id!r}: "
            f"{(proc.stderr or proc.stdout or '').strip()[-2000:]}"
        )

    parsed = _parse_json_output(proc.stdout) or {}
    downloaded = sorted(
        str(p)
        for p in out_dir.glob("*")
        if p.is_file() and before.get(p, 0) != p.stat().st_mtime
    )

    return {
        "response": parsed,
        "downloaded_files": downloaded,
        "raw_stdout": proc.stdout,
        "uploaded_media": uploaded_media,
    }
