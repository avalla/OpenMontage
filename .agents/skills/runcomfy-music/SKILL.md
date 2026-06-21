---
name: runcomfy-music
description: Generate music through RunComfy's Model API gateway (`runcomfy_music` tool) using the model_ids acestep-ai/ace-step-1.5/text-to-audio or elevenlabs/elevenlabs/music-generation. Use when the user wants RunComfy specifically for music, wants to try ACE-Step or ElevenLabs Music through the RunComfy gateway rather than a dedicated integration, or when comparing music model options hosted on RunComfy.
---

# RunComfy Music Generation

`runcomfy_music` (`tools/audio/runcomfy_music.py`) is RunComfy's Model API gateway, scoped to
music. It takes any RunComfy `model_id` plus a free-form `inputs` object matching *that model's*
schema — there's no single typed schema because the underlying model changes per call. This skill
documents the two confirmed music model_ids; for any other music model_id, check
https://www.runcomfy.com/models first.

Requires `RUNCOMFY_TOKEN` in `.env` (or `npx -y @runcomfy/cli login` once locally) and Node.js >= 18.
See `.agents/skills/elevenlabs/SKILL.md` → installation reference, or the RunComfy section of
`docs/PROVIDERS.md`, for token setup details.

## Before calling the tool

Call `RunComfyMusic.required_agent_skills(model_id)` (or the module-level
`skills_for_model_id` in `tools/_runcomfy_cli.py`) before building `inputs`. For both model_ids
below it returns `["runcomfy-music", ...]` plus the underlying model's own Layer-3 skill —
read that one too for deeper prompting technique, since the prompting *style* is identical to
the model's native API even though it's proxied through RunComfy.

## Model 1 — `acestep-ai/ace-step-1.5/text-to-audio`

Open-source ACE-Step 1.5 (MIT license), proxied through RunComfy instead of a dedicated
RunPod deployment. Good when you want ACE-Step without standing up `RUNPOD_ACESTEP_ENDPOINT_ID`.

### Input schema

| Field | Required | Type | Default | Range/Options | Notes |
|---|---|---|---|---|---|
| `tags` | yes | string | — | free text | Comma-separated genre/mood/instrument tags |
| `lyrics` | no | string | — | free text or `[inst]`/`[instrumental]` | Use section markers: `[Verse]`, `[Chorus]`, `[Bridge]` |
| `duration` | no | integer | `60` | `5`–`240` | Seconds |
| `seed` | no | integer | `-1` | `-1`–`2147483647` | `-1` randomizes; fix a seed to reproduce a take |

Output: audio only, 5–240s, stereo, provider-defined sample rate.

### Pricing (published on the model page, as of last check)

$0.0003/second of generated audio — e.g. 60s ≈ $0.018, 240s ≈ $0.072. `runcomfy_music.estimate_cost()`
applies this rate automatically for this exact `model_id`; re-check the model page before relying on
it for a large batch run, since RunComfy can change published rates.

### Example call

```python
from tools.audio.runcomfy_music import RunComfyMusic

result = RunComfyMusic().execute({
    "model_id": "acestep-ai/ace-step-1.5/text-to-audio",
    "inputs": {
        "tags": "upbeat indie rock, driving drums, jangly guitar, studio-polished",
        "duration": 60,
        "seed": 42,
    },
    "output_dir": "projects/my-video/assets/music",
})
```

With vocals:

```python
result = RunComfyMusic().execute({
    "model_id": "acestep-ai/ace-step-1.5/text-to-audio",
    "inputs": {
        "tags": "indie pop jingle, female vocal, warm production",
        "lyrics": "[Verse]\nBuild it better\nShip it faster\n[Chorus - anthemic]\nWE KEEP MOVING FORWARD",
        "duration": 30,
    },
    "output_dir": "projects/my-video/assets/music",
})
```

### Prompting `tags` and `lyrics`

`tags` plays the same role as ACE-Step's native "caption" — see
`.agents/skills/acestep/SKILL.md` for the full prompt-engineering guide (caption layering by
genre/mood/instrument/timbre/era/production/vocal, lyrics structure tags, UPPERCASE for vocal
intensity, parentheses for background vocals, 6-10 syllables per line). Everything in that
skill applies here unchanged — only the field name (`tags` vs. `--prompt`) differs.

Key reminders specific to this gateway call:
- Don't write BPM/key in `tags` as free text — this model_id's schema has no dedicated `bpm`/`key`
  fields the way the RunPod ACE-Step CLI does. If precise tempo matters, say it in `tags` directly
  (e.g. "120 BPM driving rock") since there's no structured parameter for it here.
- `lyrics: "[inst]"` (or omit `lyrics`) for instrumental-only output.

## Model 2 — `elevenlabs/elevenlabs/music-generation`

ElevenLabs' Music API, proxied through RunComfy instead of calling `api.elevenlabs.io` directly
(that direct path is `tools/audio/music_gen.py`, the `music_gen` tool). Use the RunComfy route when
you specifically want it alongside other RunComfy-hosted assets, or to avoid managing
`ELEVENLABS_API_KEY` separately.

### Input schema

| Field | Required | Type | Default | Range/Options | Notes |
|---|---|---|---|---|---|
| `prompt` | yes | string | — | free text | Style description; can include structure markers (verse/chorus) inline |
| `music_length_ms` | no | integer | `40000` | `3000`–`300000` | Milliseconds (3s–5min) |
| `force_instrumental` | no | boolean | `false` | `true`/`false` | Forces instrumental-only, suppresses vocals |
| `output_format` | no | string | `mp3_standard` | platform-dependent | Other formats may be available; check the model page |

Output: audio only, ~3s–5min, 44.1kHz stereo, MP3 or WAV.

### Pricing (published on the model page, as of last check)

$0.0083/second of generated audio — e.g. 30s ≈ $0.249, 60s ≈ $0.498, 300s ≈ $2.49. This is ~28x
the ACE-Step rate above; for non-vocal background beds where ElevenLabs' specific sound isn't
required, ACE-Step is the cheaper default. `runcomfy_music.estimate_cost()` applies this rate
automatically for this exact `model_id`.

### Example call

```python
from tools.audio.runcomfy_music import RunComfyMusic

result = RunComfyMusic().execute({
    "model_id": "elevenlabs/elevenlabs/music-generation",
    "inputs": {
        "prompt": "A chill lo-fi hip hop beat with jazzy piano chords, warm vinyl crackle",
        "music_length_ms": 30000,
        "force_instrumental": True,
    },
    "output_dir": "projects/my-video/assets/music",
})
```

### Prompting

See `.agents/skills/music/SKILL.md` for ElevenLabs Music prompt technique — it applies unchanged
here. Notable content restriction carried over: cannot reference specific artists, bands, or
copyrighted lyrics; the underlying API rejects these regardless of the RunComfy proxy.

## Choosing between the two

| | ACE-Step 1.5 | ElevenLabs Music |
|---|---|---|
| Cost/sec | $0.0003 | $0.0083 (~28x) |
| License | Open-source (MIT) | Proprietary |
| Lyrics control | Section tags + UPPERCASE/parenthesis vocal cues | Inline in `prompt`, less granular |
| Best for | Background beds, jingles, cost-sensitive batches | Polished vocal-forward tracks where ElevenLabs' specific voice/production quality is the point |

Recommend ACE-Step by default for instrumental background music; recommend ElevenLabs Music when
the brief specifically wants ElevenLabs' sound or the user already standardized on ElevenLabs for
other assets in the project.

## Workflow

1. Generate a short sample (15-30s) before committing to the full track duration, especially on
   the pricier ElevenLabs model_id.
2. Confirm mood/instrumentation/duration with the user before generating the full-length track —
   per the Music Plan protocol in `AGENT_GUIDE.md`, music decisions must be surfaced explicitly.
3. Mix background music at 10-20% volume under narration; see `.agents/skills/acestep/SKILL.md` →
   "Combining with Voiceover" for the Remotion pattern.
4. Both model_ids are billed per second of *output* duration regardless of success quality — there
   is no free retry. Don't regenerate at full duration to "try a variation"; iterate on `tags`/
   `prompt` at a short duration first.

## Troubleshooting

- No files downloaded: check the raw CLI response in the tool's error message; RunComfy queues
  generations and a transient timeout doesn't always mean the run failed server-side.
- `RUNCOMFY_TOKEN not set`: see `docs/PROVIDERS.md` → RunComfy section for setup.
- Content rejected (ElevenLabs model_id): rephrase away from artist names or copyrighted lyrics —
  this is the underlying ElevenLabs API restriction, not a RunComfy-specific limit.
