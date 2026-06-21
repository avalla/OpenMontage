"""Local ComfyUI integration via its HTTP API.

This talks to a ComfyUI instance the user runs themselves (e.g. on a Mac
with Apple Silicon, where the registry's native local video tools —
wan_video, hunyuan_video, cogvideo_video, ltx_video_local — don't work
because tools/video/_shared.py hardcodes `.to("cuda")`). ComfyUI itself
runs fine on Metal/MPS; this tool runs no GPU code in this process at all,
it just submits an API-format workflow graph to an already-running server
and retrieves whatever it produces.

Unlike runcomfy_image/video/music (the cloud gateway under the same-ish
name — easy to confuse with this), nothing here leaves the user's machine
and there is no per-call cost.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

import requests

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)

DEFAULT_BASE_URL = "http://127.0.0.1:8188"


def _base_url(inputs: dict[str, Any]) -> str:
    return (
        inputs.get("base_url")
        or os.environ.get("COMFYUI_API_URL")
        or DEFAULT_BASE_URL
    ).rstrip("/")


def _set_by_path(workflow: dict, path: str, value: Any) -> None:
    """Apply a dotted-path override like '6.inputs.text' onto a workflow dict."""
    parts = path.split(".")
    node: Any = workflow
    for part in parts[:-1]:
        node = node[part]
    node[parts[-1]] = value


class ComfyUILocal(BaseTool):
    name = "comfyui_local"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "comfyui"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = []
    install_instructions = (
        "Install ComfyUI locally — it runs natively on Apple Silicon via "
        "Metal/MPS, no CUDA/NVIDIA GPU needed:\n"
        "  git clone https://github.com/comfyanonymous/ComfyUI\n"
        "  cd ComfyUI && pip install -r requirements.txt\n"
        "  python main.py  # serves the API at http://127.0.0.1:8188\n"
        "Install whatever custom node packs your workflow needs (e.g. "
        "ComfyUI-AnimateDiff-Evolved, ComfyUI-VideoHelperSuite, LTX-Video "
        "nodes, Mochi nodes) via ComfyUI Manager or by cloning into "
        "ComfyUI/custom_nodes/, and download the matching model checkpoints.\n"
        "Set COMFYUI_API_URL in .env if the server isn't at the default "
        "http://127.0.0.1:8188 (e.g. when calling from a different machine "
        "than the one running ComfyUI)."
    )
    agent_skills: list[str] = []  # no Layer-3 skill yet — workflow JSON is supplied by the caller

    capabilities = [
        "generate_video",
        "generate_image",
        "text_to_video",
        "image_to_video",
        "text_to_image",
        "run_arbitrary_workflow",
    ]
    supports = {
        "offline": True,
        "local_gpu": True,
        "apple_silicon": True,
        "requires_custom_workflow": True,
    }
    best_for = [
        "running any model already set up in a local ComfyUI install (AnimateDiff, SVD, LTX-Video, Mochi, etc.)",
        "Apple Silicon Macs, where the registry's CUDA-only local video tools do not work",
        "free, fully offline generation once the workflow and models are in place",
    ]
    not_good_for = [
        "zero-setup use — requires ComfyUI installed, running, and the specific custom nodes/models for your workflow already present",
        "one-shot prompts without an exported API-format workflow JSON",
    ]

    input_schema = {
        "type": "object",
        "properties": {
            "workflow": {
                "type": "object",
                "description": (
                    "Full ComfyUI API-format workflow graph. Export it from the "
                    "ComfyUI UI via the 'Save (API Format)' button — requires "
                    "enabling 'Dev mode options' in ComfyUI settings first. "
                    "Provide this OR workflow_path."
                ),
            },
            "workflow_path": {
                "type": "string",
                "description": "Path to a JSON file containing the API-format workflow.",
            },
            "overrides": {
                "type": "object",
                "description": (
                    "Dotted-path patches applied to the workflow before submission, "
                    "e.g. {'6.inputs.text': 'a neon city at night', '3.inputs.seed': 42}. "
                    "Node ids and field names are workflow-specific — open the "
                    "workflow in the ComfyUI UI (or the exported JSON) to find them."
                ),
            },
            "base_url": {
                "type": "string",
                "description": "Override COMFYUI_API_URL for this call.",
            },
            "output_dir": {"type": "string", "default": "comfyui_output"},
            "timeout_seconds": {"type": "integer", "default": 1200},
            "poll_interval_seconds": {"type": "number", "default": 2.0},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=1000, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=0)
    idempotency_key_fields = ["workflow", "workflow_path", "overrides"]
    side_effects = [
        "submits a job to the local ComfyUI server",
        "writes output files to output_dir",
    ]
    user_visible_verification = ["Inspect generated media for relevance and quality"]

    def get_status(self) -> ToolStatus:
        try:
            base_url = os.environ.get("COMFYUI_API_URL", DEFAULT_BASE_URL).rstrip("/")
            resp = requests.get(f"{base_url}/system_stats", timeout=3)
            return ToolStatus.AVAILABLE if resp.status_code == 200 else ToolStatus.UNAVAILABLE
        except requests.RequestException:
            return ToolStatus.UNAVAILABLE

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start = time.time()
        base_url = _base_url(inputs)

        workflow = inputs.get("workflow")
        if workflow is not None:
            workflow = json.loads(json.dumps(workflow))  # deep copy, don't mutate caller's dict
        else:
            workflow_path = inputs.get("workflow_path")
            if not workflow_path:
                return ToolResult(
                    success=False,
                    error="Provide either 'workflow' (dict) or 'workflow_path' (path to exported API-format JSON).",
                )
            try:
                workflow = json.loads(Path(workflow_path).read_text())
            except Exception as exc:
                return ToolResult(success=False, error=f"Could not read workflow_path {workflow_path!r}: {exc}")

        for path, value in (inputs.get("overrides") or {}).items():
            try:
                _set_by_path(workflow, path, value)
            except (KeyError, TypeError) as exc:
                return ToolResult(
                    success=False,
                    error=f"override path {path!r} did not resolve in the workflow: {exc}",
                )

        client_id = str(uuid.uuid4())
        try:
            resp = requests.post(
                f"{base_url}/prompt",
                json={"prompt": workflow, "client_id": client_id},
                timeout=30,
            )
        except requests.RequestException as exc:
            return ToolResult(
                success=False,
                error=f"Could not reach ComfyUI at {base_url}: {exc}. " + self.install_instructions,
            )

        if resp.status_code != 200:
            return ToolResult(
                success=False,
                error=f"ComfyUI rejected the workflow (HTTP {resp.status_code}): {resp.text[:2000]}",
            )

        payload = resp.json()
        node_errors = payload.get("node_errors") or {}
        if node_errors:
            return ToolResult(
                success=False,
                error=(
                    "ComfyUI reported node errors before queuing (often a missing "
                    f"custom node or model checkpoint): {json.dumps(node_errors)[:2000]}"
                ),
            )
        prompt_id = payload.get("prompt_id")
        if not prompt_id:
            return ToolResult(success=False, error=f"ComfyUI did not return a prompt_id: {payload}")

        timeout_seconds = inputs.get("timeout_seconds", 1200)
        poll_interval = inputs.get("poll_interval_seconds", 2.0)
        deadline = time.time() + timeout_seconds
        history: dict[str, Any] | None = None
        while time.time() < deadline:
            try:
                hist_resp = requests.get(f"{base_url}/history/{prompt_id}", timeout=10)
                hist_resp.raise_for_status()
                data = hist_resp.json()
            except requests.RequestException:
                time.sleep(poll_interval)
                continue
            if prompt_id in data:
                history = data[prompt_id]
                status = history.get("status", {})
                if status.get("completed") or status.get("status_str") == "success":
                    break
                if status.get("status_str") == "error":
                    return ToolResult(
                        success=False,
                        error=f"ComfyUI run failed: {json.dumps(status)[:2000]}",
                    )
            time.sleep(poll_interval)
        else:
            return ToolResult(
                success=False,
                error=f"Timed out after {timeout_seconds}s waiting for ComfyUI prompt_id={prompt_id}.",
            )

        if history is None:
            return ToolResult(
                success=False,
                error=f"No history found for prompt_id={prompt_id} (job may have failed silently).",
            )

        output_dir = Path(inputs.get("output_dir", "comfyui_output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        downloaded: list[str] = []
        for node_output in history.get("outputs", {}).values():
            for media_key in ("images", "gifs", "videos"):
                for item in node_output.get(media_key, []):
                    filename = item.get("filename")
                    if not filename:
                        continue
                    try:
                        view_resp = requests.get(
                            f"{base_url}/view",
                            params={
                                "filename": filename,
                                "subfolder": item.get("subfolder", ""),
                                "type": item.get("type", "output"),
                            },
                            timeout=120,
                        )
                        view_resp.raise_for_status()
                    except requests.RequestException as exc:
                        return ToolResult(
                            success=False,
                            error=f"Failed to download output {filename!r}: {exc}",
                        )
                    dest = output_dir / filename
                    dest.write_bytes(view_resp.content)
                    downloaded.append(str(dest))

        if not downloaded:
            return ToolResult(
                success=False,
                error=(
                    "ComfyUI run completed but no image/gif/video outputs were found "
                    f"in history. Raw outputs: {json.dumps(history.get('outputs', {}))[:2000]}"
                ),
            )

        return ToolResult(
            success=True,
            data={
                "provider": "comfyui",
                "prompt_id": prompt_id,
                "base_url": base_url,
                "outputs": downloaded,
            },
            artifacts=downloaded,
            duration_seconds=round(time.time() - start, 2),
        )
