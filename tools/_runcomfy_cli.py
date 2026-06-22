"""Shared subprocess wrapper around the RunComfy CLI (`@runcomfy/cli`).

RunComfy's Model API lets you invoke any hosted ComfyUI-backed model by
`model_id` without deploying a workflow yourself. The CLI (`runcomfy run`)
wraps submit -> poll -> download in one blocking call, which is what the
image/video tool wrappers in this package use.

Docs: https://docs.runcomfy.com/cli/introduction
"""

from __future__ import annotations

import json
import os
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
}


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
) -> dict[str, Any]:
    """Run `runcomfy run <model_id> --input <json> --output-dir <dir> --output json`.

    Blocks until the request completes (or times out), downloads outputs into
    output_dir, and returns the parsed `--output json` payload plus the list
    of files actually written.

    Raises RunComfyCLIError on missing token/CLI, non-zero exit, or timeout.
    """
    token = get_token()
    if not token:
        raise RunComfyCLIError(
            "RUNCOMFY_TOKEN not set. Get a token from https://www.runcomfy.com/profile "
            "(click your avatar -> API tokens) and add RUNCOMFY_TOKEN=... to .env, "
            "or run `runcomfy login` once locally and it will be picked up from "
            "~/.config/runcomfy/token.json."
        )

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

    return {"response": parsed, "downloaded_files": downloaded, "raw_stdout": proc.stdout}
