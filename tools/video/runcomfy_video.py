"""Video generation via the RunComfy CLI (Model API, no deployment_id needed)."""

from __future__ import annotations

import time
from typing import Any

from tools._runcomfy_cli import (
    RunComfyCLIError,
    cli_available,
    get_token,
    run_model,
    skills_for_model_id,
)
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


class RunComfyVideo(BaseTool):
    name = "runcomfy_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "runcomfy"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = ["env:RUNCOMFY_TOKEN"]
    install_instructions = (
        "Get a RunComfy API token from https://www.runcomfy.com/profile "
        "(click your avatar -> API tokens) and set RUNCOMFY_TOKEN in .env. "
        "Alternatively run `npx -y @runcomfy/cli login` once locally.\n"
        "Also requires Node.js >= 18 (https://nodejs.org/) so the CLI can run via npx, "
        "unless `runcomfy` is already installed globally."
    )
    agent_skills = []

    capabilities = ["generate_video", "text_to_video", "image_to_video"]
    supports = {
        "seed": "model-dependent",
        "duration_seconds": "model-dependent",
        "image_to_video": "model-dependent",
    }
    best_for = [
        "running a specific ComfyUI-backed video model hosted on RunComfy by model_id",
        "access to community/specialty video models (AnimateDiff, LTX, etc.) not offered by other providers",
    ]
    not_good_for = [
        "offline generation",
        "models whose input schema you haven't checked on runcomfy.com/models first",
    ]

    input_schema = {
        "type": "object",
        "required": ["model_id", "inputs"],
        "properties": {
            "model_id": {
                "type": "string",
                "description": (
                    "RunComfy model identifier. Find valid ids and their input schema "
                    "at https://www.runcomfy.com/models"
                ),
            },
            "inputs": {
                "type": "object",
                "description": (
                    "Payload matching the chosen model's own input schema "
                    "(commonly includes 'prompt', sometimes 'seed', 'duration', "
                    "or an input image URL/path for image-to-video — check the model page)."
                ),
            },
            "output_dir": {"type": "string", "default": "runcomfy_output"},
            "timeout_seconds": {"type": "integer", "default": 1200},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=1000, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["timeout"])
    idempotency_key_fields = ["model_id", "inputs"]
    side_effects = ["calls the RunComfy API via the runcomfy CLI", "writes output files to output_dir"]
    user_visible_verification = ["Inspect generated clip for relevance, motion quality, and duration"]

    def get_status(self) -> ToolStatus:
        if get_token() and cli_available():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    @staticmethod
    def required_agent_skills(model_id: str) -> list[str]:
        """Layer-3 skill(s) to read before crafting `inputs` for this model_id.

        Call this BEFORE execute() — it costs nothing and tells you which
        prompting/parameter guidance applies to the specific underlying model
        RunComfy will run. Empty list means no matching skill is registered
        yet; still check the model's input schema at runcomfy.com/models.
        """
        return skills_for_model_id(model_id)

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        model_id = inputs["model_id"]
        model_inputs = inputs["inputs"]
        output_dir = inputs.get("output_dir", "runcomfy_output")
        timeout_seconds = inputs.get("timeout_seconds", 1200)

        start = time.time()
        try:
            result = run_model(
                model_id, model_inputs, output_dir, timeout_seconds=timeout_seconds
            )
        except RunComfyCLIError as e:
            return ToolResult(success=False, error=str(e))

        files = result["downloaded_files"]
        if not files:
            return ToolResult(
                success=False,
                error=(
                    f"runcomfy run completed but no files were downloaded to {output_dir!r}. "
                    f"Raw CLI response: {result['response']}"
                ),
            )

        return ToolResult(
            success=True,
            data={
                "provider": "runcomfy",
                "model_id": model_id,
                "output": files[0],
                "response": result["response"],
                "required_agent_skills": skills_for_model_id(model_id),
            },
            artifacts=files,
            duration_seconds=round(time.time() - start, 2),
            model=model_id,
        )
