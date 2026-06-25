---
name: comfyui-local
description: Submit a workflow to a local ComfyUI server (the comfyui_local tool) — exporting API-format workflows, parameterizing them with overrides, and debugging node_errors. Use when generating video/images locally on a machine without CUDA (e.g. Apple Silicon Macs), or any machine where the user already runs ComfyUI.
---

# ComfyUI Local

`comfyui_local` (`tools/video/comfyui_local.py`) is a thin HTTP client for a ComfyUI server the
user runs themselves. It does not template, generate, or validate workflows — it submits whatever
graph you give it, polls for completion, and downloads the outputs. All creative/orchestration
decisions (which workflow, which model, what to put in `overrides`) are the agent's job, not the
tool's, per project convention.

**Do not confuse this with `runcomfy_video`/`runcomfy_image`/`runcomfy_music`.** Those are a paid
cloud gateway (RunComfy) that happens to run ComfyUI-backed models on someone else's GPU. This tool
talks to a ComfyUI instance on the user's own machine — free, offline, but requires that machine to
already have the workflow's custom nodes and model checkpoints installed.

## Before calling the tool

1. Confirm the user has ComfyUI running: `get_status()` (or `GET {base_url}/system_stats`) returns
   `AVAILABLE` only if the server answers. If not, walk them through `install_instructions` —
   `git clone https://github.com/comfyanonymous/ComfyUI && cd ComfyUI && pip install -r requirements.txt && python main.py`.
2. **You need an exported API-format workflow JSON.** This tool cannot build one from scratch — the
   user (or a previous step) must have:
   - Built the workflow in the ComfyUI UI (or obtained one from a workflow-sharing site/repo
     matching the custom nodes they have installed), and
   - Enabled **Settings → Dev mode options**, then exported it via the **"Save (API Format)"**
     button (NOT the regular "Save", which exports the UI-format graph — wrong shape, `/prompt`
     will reject it).
3. Ask the user for that JSON file path, or have them paste/describe the workflow if you need to
   help them build one conceptually (you still cannot create the actual ComfyUI graph file without
   them exporting it from the UI).

## Calling the tool

```python
from tools.video.comfyui_local import ComfyUILocal

result = ComfyUILocal().execute({
    "workflow_path": "/path/to/exported_workflow_api.json",
    "overrides": {
        "6.inputs.text": "a neon-lit Shanghai skyline at night, anime style, cel-shaded",
        "3.inputs.seed": 42,
    },
    "output_dir": "projects/my-project/assets/video",
    "timeout_seconds": 1800,
})
```

- `overrides` keys are dotted paths into the workflow dict: `"<node_id>.inputs.<field>"`. Node ids
  and field names are workflow-specific — open the exported JSON (it's just a dict keyed by node id
  string) to find the right node. Common ones:
  - `CLIPTextEncode` nodes — positive/negative prompt text, field is usually `text`.
  - `KSampler` nodes — `seed`, `steps`, `cfg`, `denoise`.
  - `EmptyLatentImage` / `EmptyHunyuanLatentVideo` etc. — `width`, `height`, `length`/`batch_size`.
  - Image/video loader nodes (`LoadImage`, `VHS_LoadVideo`) — `image`/`video` filename, for
    image-to-video workflows. The file must already be reachable by the ComfyUI server (its own
    `input/` folder), not just by the OpenMontage machine — see "Remote ComfyUI" below.
- If you don't know the exact node ids, ask the user to paste the workflow JSON (or the relevant
  node) rather than guessing — a wrong path raises a clear `KeyError`/`TypeError` from `_set_by_path`,
  but it's faster to just look.

## Reading errors

- **`node_errors` in the response, before queuing:** almost always a missing custom node pack or a
  model checkpoint filename that doesn't match what's installed (ComfyUI validates the graph against
  currently-loaded node/model definitions before running). Tell the user exactly which node/field
  it's complaining about — they'll need to install the custom node or fix the model filename
  reference inside the workflow JSON.
- **Timeout waiting for `prompt_id`:** either the job is genuinely slow (video models on modest
  hardware can take many minutes per clip — raise `timeout_seconds`), or it silently errored inside
  ComfyUI without surfacing through `/history` cleanly. Check the ComfyUI server's own terminal
  output, since that's where Python tracebacks from inside node execution land.
- **No outputs downloaded:** the workflow ran but no node produced an `images`/`gifs`/`videos` entry
  in its history output — usually means the workflow is missing a `SaveImage`/`VHSVideoCombine`-style
  terminal node, or that node was disabled/bypassed.

## Remote ComfyUI

If ComfyUI runs on a different machine than wherever this tool executes, set
`COMFYUI_API_URL=http://<host>:8188` (or pass `base_url` per-call). Note this only covers the
`/prompt`, `/history`, `/view` HTTP calls — any input files the workflow references by path (e.g. a
reference image for image-to-video) must already exist on the ComfyUI host's own filesystem; this
tool does not upload local files into ComfyUI's `input/` folder for you. For image-to-video on a
remote/separate ComfyUI host, either pre-place the file there another way, or use a workflow node
that accepts a URL instead of a local path if one is available in the installed node pack.

## Cost and reproducibility

Always `$0` (the user's own hardware). Determinism depends entirely on the workflow's `seed` fields
— fix them via `overrides` for reproducible takes, matching the project convention of recording
seeds for any generation step that needs to be reproducible.
