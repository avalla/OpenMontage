# OpenMontage Provider Guide

Everything you need to know about every provider in OpenMontage — setup instructions, pricing, free tiers, and what each unlocks.

---

## Quick Start: What Should I Set Up?

**Start free, add paid providers as you need them.** Here's the recommended order:

| Step | Cost | What to set up | What it unlocks |
|------|------|----------------|-----------------|
| 1 | **$0** | Pexels + Pixabay | Stock photos and videos — enough to produce basic videos |
| 2 | **$0** | Google API key | TTS with 700+ voices (1M chars/month free) + $300 new account credit |
| 3 | **$0** | ElevenLabs | Premium TTS + music + SFX (10K chars/month free) |
| 4 | **$0** | Piper (local install) | Fully offline TTS — no API key, no cost, no network |
| 5 | **~$0.03/image** | fal.ai | FLUX images + Kling/Veo/MiniMax video + Recraft — broad single-key image + video coverage |
| 6 | **~$0.04/image** | OpenAI | DALL-E 3 images + OpenAI TTS |
| 7 | **~$0.04/image** | Google Imagen | Imagen 4 images (shares the Google API key) |
| 8 | **$12/month** | Runway | Gen-4 video — highest quality AI video |
| 9 | **pay-as-you-go** | HeyGen | Avatar videos, multi-model video gateway |
| 10 | **pay-as-you-go** | Suno | Full song generation with vocals and lyrics |
| 11 | **$0 + NVIDIA GPU** | Local video gen | WAN 2.1, Hunyuan, CogVideo, LTX — free, offline (CUDA only, not Mac) |
| 12 | **$0 + GPU** | Local Diffusion | Stable Diffusion images — free, offline |
| 13 | **varies by model** | RunComfy | Any ComfyUI-hosted model by `model_id` (FLUX, Kling, LTX, and community models) through one CLI — cloud, pay-per-run, despite the name |
| 14 | **$0 + GPU** | ComfyUI Local | Your own ComfyUI server + workflow — free, offline, works on Apple Silicon Macs |

### Environment Variable Summary

```bash
# .env — add your keys here

# FREE (no cost, ever)
PEXELS_API_KEY=              # Stock photos + videos
PIXABAY_API_KEY=             # Stock photos + videos

# GOOGLE (one key, two tools, generous free tier)
GOOGLE_API_KEY=              # Google TTS + Google Imagen

# VOICE + MUSIC
ELEVENLABS_API_KEY=          # TTS, music, sound effects (10K chars/month free)
OPENAI_API_KEY=              # OpenAI TTS + DALL-E 3 images
XAI_API_KEY=                 # xAI Grok image generation/editing + Grok video generation
DOUBAO_SPEECH_API_KEY=       # Volcengine Doubao Speech TTS (strong Mandarin narration)
DOUBAO_SPEECH_VOICE_TYPE=    # Default Doubao speaker/voice type

# MULTI-MODEL GATEWAY (one key, 6+ tools)
FAL_KEY=                     # FLUX, Recraft, Kling, Veo, MiniMax video
RUNCOMFY_TOKEN=               # Any ComfyUI-hosted model by model_id, via the runcomfy CLI (no deployment needed)

# VIDEO
HEYGEN_API_KEY=              # HeyGen avatar video gateway
RUNWAY_API_KEY=              # Runway Gen-4 video (direct)
SUNO_API_KEY=                # Suno music generation

# LOCAL (no keys needed — just GPU + install)
VIDEO_GEN_LOCAL_ENABLED=     # Set to "true" for local video gen (CUDA/NVIDIA only, not Mac)
VIDEO_GEN_LOCAL_MODEL=       # wan2.1-1.3b, wan2.1-14b, hunyuan-1.5, ltx2-local, cogvideo-5b
COMFYUI_API_URL=             # Optional — local ComfyUI server (Apple Silicon-friendly). Defaults to http://127.0.0.1:8188
```

---

## Cloud Providers

### xAI — Grok Image + Video

> **Best if you want one provider for image edits and reference-conditioned short video.** Grok covers both image generation/editing and video generation under one key.

**Tools unlocked:** `grok_image`, `grok_video`
**Env var:** `XAI_API_KEY`

#### Setup

1. Create an xAI developer account
2. Generate an API key in the xAI developer console
3. Add to `.env`: `XAI_API_KEY=xai-...`

#### What it's best for

- Image editing and style transfer
- Multi-image composites into one generated frame
- Short reference-image videos where a person, garment, or product must carry into motion

#### Pricing

Current xAI docs pricing for the Grok media models:

| Model | Price |
|------|-------|
| `grok-imagine-image` | $0.02 per generated image |
| `grok-imagine-image` input images (edits/composites) | $0.002 per input image |
| `grok-imagine-video` at 480p | $0.05/sec |
| `grok-imagine-video` at 720p | $0.07/sec |
| `grok-imagine-video` input images | $0.002 per input image |

OpenMontage now uses those published rates in the Grok tool estimators.

---

### fal.ai — Multi-Model Gateway

> **Broad single-key coverage.** One API key unlocks image and video providers across multiple models.

**Tools unlocked:** `flux_image`, `recraft_image`, `kling_video`, `veo_video`, `minimax_video`
**Env var:** `FAL_KEY`

#### Setup

1. Go to [fal.ai](https://fal.ai/) and click **Sign up** (GitHub or Google)
2. Navigate to [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)
3. Click **Create Key**, copy it
4. Add to `.env`: `FAL_KEY=your-key-here`

#### Pricing

No subscription — pure pay-as-you-go, no minimum spend.

**Image generation:**

| Model | Price | Per $1 |
|-------|-------|--------|
| FLUX Pro v1.1 | $0.05/image | 20 images |
| FLUX Dev | $0.03/image | 33 images |
| Recraft v3 | ~$0.04/image | 25 images |

**Video generation:**

| Model | Price | Per $1 |
|-------|-------|--------|
| Kling 2.5 Turbo Pro | $0.07/sec | 14 seconds |
| MiniMax | ~$0.05/sec | 20 seconds |
| Veo 3 | $0.40/sec | 2.5 seconds |
| WAN 2.5 | $0.05/sec | 20 seconds |

**Free tier:** None — but $0 to start, you only pay for what you use.

---

### ElevenLabs — Voice, Music, Sound Effects

> **Premium voice quality.** Best TTS for narration-heavy videos. Also generates music and sound effects.

**Tools unlocked:** `elevenlabs_tts`, `music_gen`
**Env var:** `ELEVENLABS_API_KEY`

#### Setup

1. Go to [elevenlabs.io](https://elevenlabs.io) and click **Sign up**
2. Go to **Profile** (bottom-left) > **API Keys**, or visit [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys)
3. Click **Create API Key**, name it, copy it
4. Add to `.env`: `ELEVENLABS_API_KEY=xi_your-key-here`

#### Pricing

| Plan | Price | Characters/month | Key features |
|------|-------|-------------------|--------------|
| **Free** | $0 | 10,000 | 3 custom voices, API access, attribution required |
| Starter | $5/mo | 30,000 | No attribution |
| Creator | $22/mo | 100,000 | Professional voice cloning |
| Pro | $99/mo | 500,000 | 96kbps audio, usage analytics |
| Scale | $330/mo | 2,000,000 | Priority support |

**Free tier:** 10,000 characters/month (roughly 2-3 minutes of narration). API access included. Music generation and sound effects also available on free tier with limited credits.

---

### Doubao Speech — Mandarin TTS

> **Strong Mandarin narration.** Volcengine Doubao Speech is a good choice for Chinese explainer voiceovers and long-form narration that needs subtitle timing metadata.

**Tools unlocked:** `doubao_tts`
**Env vars:** `DOUBAO_SPEECH_API_KEY`, `DOUBAO_SPEECH_VOICE_TYPE`

#### Setup

1. Open the Volcengine Doubao Speech console and enable Speech Synthesis 2.0.
2. Create a new-console API Key.
3. Choose a Speech 2.0 voice type, for example `zh_female_vv_uranus_bigtts`.
4. Add to `.env`:
   ```bash
   DOUBAO_SPEECH_API_KEY=your-api-key
   DOUBAO_SPEECH_VOICE_TYPE=zh_female_vv_uranus_bigtts
   ```

#### API Notes

OpenMontage uses the new-console API key flow:

```text
X-Api-Key: ${DOUBAO_SPEECH_API_KEY}
X-Api-Resource-Id: seed-tts-2.0
```

Do not pass a new-console API Key as `X-Api-App-Id` or `X-Api-Access-Key`. That mismatch can produce `load grant: requested grant not found`.

#### What It Is Best For

- Natural Mandarin narration for Chinese-language explainers
- Async long-form narration via `/api/v3/tts/submit` and `/api/v3/tts/query`
- Character-level timing metadata for subtitle alignment
- Calm educational pacing where the video duration can follow the approved voice rhythm

#### Pacing

Start with `speech_rate: 0` for natural Mandarin delivery. If the approved format needs a tighter runtime, compare short samples at `speech_rate: 25` or `50` before generating the full narration. Do not force Doubao to match another provider's duration unless the user explicitly wants that tradeoff.

#### Pricing

Doubao Speech 2.0 is billed by character package or usage in Volcengine. OpenMontage estimates cost from text length and prefers provider-returned usage metadata when available.

---

### Google — TTS + Imagen (Shared Key)

> **One key, two tools.** Google Cloud TTS has 700+ voices in 50+ languages — the strongest localization option. Imagen 4 generates high-quality images.

**Tools unlocked:** `google_tts`, `google_imagen`
**Env var:** `GOOGLE_API_KEY`

#### Setup

1. Go to [Google AI Studio](https://aistudio.google.com/) and sign in
2. Navigate to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
3. Click **Create API Key**, select a Google Cloud project
4. Copy the key
5. Add to `.env`: `GOOGLE_API_KEY=AIza...`

**For TTS specifically**, you also need to enable the Text-to-Speech API:
1. Visit [console.cloud.google.com/apis/library/texttospeech.googleapis.com](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)
2. Click **Enable**
3. Make sure your API key's restrictions allow the Text-to-Speech API

**For Imagen**, enable the Generative Language API:
1. Visit [console.cloud.google.com/apis/library/generativelanguage.googleapis.com](https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com)
2. Click **Enable**

#### Google TTS Pricing

| Voice Type | Free tier | Paid (per 1M chars) | Notes |
|-----------|-----------|---------------------|-------|
| **Standard** | 1M chars/month | $4.00 | Basic quality, fast |
| **WaveNet** | 1M chars/month | $16.00 | Natural-sounding |
| **Neural2** | 1M chars/month | $16.00 | Best quality |
| **Studio** | — | $24.00 | Professional studio voices |
| **Chirp** | — | $4.00 | Conversational style |

The free tiers apply *independently* — you get 1M Standard AND 1M WaveNet AND 1M Neural2 characters per month free. That's roughly 250+ minutes of narration per month at zero cost.

#### Google Imagen Pricing

| Model | Price per image |
|-------|----------------|
| Imagen 4 Fast | $0.02 |
| Imagen 4 Standard | $0.04 |
| Imagen 4 Ultra | $0.06 |

**Free tier for Imagen:** None. Paid tier only.

**New account bonus:** Google Cloud offers **$300 in free credits** for new accounts (90-day trial), applicable to both TTS and Imagen.

#### Google TTS Voice Types

Google TTS offers 700+ voices across 50+ languages. Voice names follow the pattern `{language}-{type}-{letter}`:

| Type | Example | Quality | Cost |
|------|---------|---------|------|
| **Chirp 3 HD** | `en-US-Chirp3-HD-Orus` | **Best (2024, most natural)** | **Mid — default** |
| Standard | `en-US-Standard-A` | Good | Cheapest |
| WaveNet | `en-US-WaveNet-D` | Very good | Mid |
| Neural2 | `en-US-Neural2-D` | Excellent | Mid |
| Studio | `en-US-Studio-O` | Professional | Highest |
| Journey | `en-US-Journey-D` | Conversational (long-form) | Mid |

**Recommended voices:** `en-US-Chirp3-HD-Orus` (male, rich/cinematic), `en-US-Chirp3-HD-Aoede` (female, warm). These are Google's newest tier — most natural-sounding, uses the v1beta1 endpoint automatically.

**Languages include:** English (US, UK, AU, IN), Spanish, French, German, Italian, Portuguese, Japanese, Korean, Chinese (Mandarin, Cantonese), Arabic, Hindi, Russian, Dutch, Polish, Turkish, Vietnamese, Thai, Indonesian, and 30+ more.

---

### OpenAI — TTS + Image Generation

> **Solid all-rounder.** DALL-E 3 handles complex multi-element compositions well. TTS is fast and affordable.

**Tools unlocked:** `openai_tts`, `openai_image`
**Env var:** `OPENAI_API_KEY`

#### Setup

1. Go to [platform.openai.com/signup](https://platform.openai.com/signup) and create an account
2. Add a payment method at [platform.openai.com/account/billing](https://platform.openai.com/account/billing)
3. Navigate to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
4. Click **Create new secret key**, name it, copy it
5. Add to `.env`: `OPENAI_API_KEY=sk-...`

#### TTS Pricing

| Model | Price per 1M characters |
|-------|------------------------|
| tts-1 | $15.00 |
| tts-1-hd | $30.00 |
| gpt-4o-mini-tts | $12.00 |

#### Image Pricing

| Model | Size | Quality | Price per image |
|-------|------|---------|----------------|
| DALL-E 3 | 1024x1024 | standard | $0.040 |
| DALL-E 3 | 1024x1024 | hd | $0.080 |
| DALL-E 3 | 1024x1792 | standard | $0.080 |
| DALL-E 3 | 1024x1792 | hd | $0.120 |

**Free tier:** None. Requires prepaid billing. Previously offered $5 in free credits for new accounts (discontinued for most signups).

---

### Runway — Gen-3/Gen-4 Video

> **Highest-rated AI video quality.** #1 on Elo rankings. Professional-grade video generation with Gen-3 Alpha Turbo, Gen-4 Turbo, and Gen-4 Aleph models.

**Tools unlocked:** `runway_video`
**Env var:** `RUNWAY_API_KEY`

#### Setup

1. Go to [dev.runwayml.com](https://dev.runwayml.com/) and create a developer account
2. Subscribe to a paid plan (Standard or above — API requires subscription)
3. Generate an API key from the developer portal
4. Add to `.env`: `RUNWAY_API_KEY=key_...`

#### Pricing

| Plan | Price | Credits/month | Video capacity |
|------|-------|---------------|----------------|
| **Free** | $0 | 125 one-time | ~5 seconds Gen-4 |
| Standard | $12/mo | 625 | ~25 seconds Gen-4 |
| Pro | $28/mo | 2,250 | ~90 seconds Gen-4 |
| Unlimited | $76/mo | Unlimited (Explore Mode) | Unlimited Gen-4 Turbo |

**API pricing (approximate):**

| Model | Price per second |
|-------|-----------------|
| Gen-3 Alpha Turbo | ~$0.05 |
| Gen-4 Turbo | ~$0.05 |
| Gen-4 Aleph | ~$0.15 |

**Free tier:** 125 one-time credits (no monthly renewal). Enough for about 5 seconds of Gen-4 video. API access requires a paid subscription.

---

### Higgsfield — Multi-Model Video Orchestrator

> **Multi-model video platform.** Routes to Kling 3.0, Veo 3.1, Sora 2, WAN 2.5, and proprietary Soul Cinema through a single API. Includes Soul ID for character consistency across clips.

**Tools unlocked:** `higgsfield_video`
**Env vars:** `HIGGSFIELD_API_KEY` + `HIGGSFIELD_API_SECRET` (or combined `HIGGSFIELD_KEY=key:secret`)

#### Setup

1. Go to [cloud.higgsfield.ai](https://cloud.higgsfield.ai/) and create an account
2. Subscribe to a plan (Starter or above for API access)
3. Navigate to API Keys section at [cloud.higgsfield.ai/api-keys](https://cloud.higgsfield.ai/api-keys)
4. Generate an API key and secret
5. Add to `.env`:
   ```
   HIGGSFIELD_API_KEY=your-api-key
   HIGGSFIELD_API_SECRET=your-api-secret
   ```

#### Pricing

| Plan | Price | Notes |
|------|-------|-------|
| Free | $0 | Limited credits |
| Starter | $15/mo | Basic allocation |
| Plus | $34/mo | Mid-tier, ~33-56 Kling 3.0 clips |
| Ultra | $84/mo | High volume |

**Per-generation costs (approximate, via credits):**

| Model | Cost per clip |
|-------|--------------|
| Kling 3.0 | ~$0.10 (cheapest) |
| WAN 2.5 | ~$0.10 |
| Soul Cinema | ~$0.15 |
| Veo 3.1 | ~$0.50 |
| Sora 2 | ~$0.50 |

**Free tier:** Limited credits on signup. No monthly renewal on free plan.

---

### RunComfy — ComfyUI Model Gateway

> **Run any ComfyUI-hosted model by `model_id`, no workflow deployment needed.** RunComfy's Model API exposes thousands of community and official ComfyUI-backed models (FLUX, Kling, LTX, AnimateDiff, and more) behind a single CLI. Best when you want a specific community model that no other provider offers, or want to try a model before committing to a dedicated integration.

**Tools unlocked:** `runcomfy_image`, `runcomfy_video`, `runcomfy_music`
**Env var:** `RUNCOMFY_TOKEN`
**Also requires:** Node.js >= 18 (the CLI runs via `npx -y @runcomfy/cli`, or install `@runcomfy/cli` globally)

#### Setup

1. Go to [runcomfy.com](https://www.runcomfy.com) and create an account
2. Get a token from your [profile page](https://www.runcomfy.com/profile) (click your avatar → API tokens)
3. Add to `.env`: `RUNCOMFY_TOKEN=your-token-here`
   - Alternatively, skip the env var and run `npx -y @runcomfy/cli login` once locally — the CLI stores the token at `~/.config/runcomfy/token.json`
4. Browse [runcomfy.com/models](https://www.runcomfy.com/models) to find a `model_id` and its required input fields — every model has its own schema

#### How It Differs From Other Providers

Other providers in this guide (FLUX, Kling, etc.) are single fixed models behind a dedicated tool with a typed `input_schema`. RunComfy is a **gateway** — `runcomfy_image`/`runcomfy_video`/`runcomfy_music` take a `model_id` plus a free-form `inputs` object matching *that model's* schema, which you must look up per model. There's no single typed schema because the underlying model changes per call.

Because the underlying model varies, the right Layer-3 prompting skill also varies. All three tools expose `required_agent_skills(model_id)` — call it before building `inputs` to know which prompting guide applies (e.g. a `model_id` containing `"flux"` maps to the existing `flux-best-practices` / `bfl-api` skills; `"ace-step"` maps to `runcomfy-music` + `acestep`; `"music-generation"` maps to `runcomfy-music` + `music`). An empty result means no matching skill exists yet for that model family; check the model's own page on runcomfy.com/models regardless.

#### Known model_ids

RunComfy hosts thousands of models and the catalog changes constantly, so this is **not**
exhaustive — it's a starting point of model_ids confirmed (by checking the model's own page) at
the time this table was last verified. **The literal `model_id` is the identifier printed on the
model's own page — it does not always match the page's URL slug** (e.g. the Seedance 2.0 Pro page
lives at `runcomfy.com/models/bytedance/seedance-v2/pro` but its documented model_id is
`bytedance/seedance-2.0/pro`). Always confirm on [runcomfy.com/models](https://www.runcomfy.com/models)
before a paid run, especially for any model_id not in this table.

| Category | model_id | Notes / pricing |
|---|---|---|
| Image | `openai/gpt-image-2/text-to-image` | $0.01-$0.66/image by quality+resolution tier |
| Image | `blackforestlabs/flux-2/dev/text-to-image` | Free during promo; normally $0.012/image |
| Video | `google-deepmind/veo-3-1/image-to-video` | $0.20/sec (no audio), $0.40/sec (with audio) |
| Video | `kling/kling-video-o3/4K/image-to-video` | $0.42/sec |
| Video | `bytedance/seedance-2.0/pro` | Cinematic 2K text-to-video with lip-sync |
| Music | `acestep-ai/ace-step-1.5/text-to-audio` | Open-source ACE-Step 1.5, $0.0003/sec of output |
| Music | `elevenlabs/elevenlabs/music-generation` | ElevenLabs Music API via RunComfy, $0.0083/sec of output |

The two music model_ids are documented in detail (full input schema, prompting guidance, example
calls) in `.agents/skills/runcomfy-music/SKILL.md`. `runcomfy_music.estimate_cost()` applies their
published rates automatically; any other model_id returns `0.0` like the image/video gateway tools
(none of the image/video model_ids above have a hardcoded rate yet — only the two music ones do).

#### Pricing

Not published in OpenMontage's provider data for most models — RunComfy bills per model/run via your account balance. Check current rates on the model's page before running at scale; `estimate_cost` returns `0.0` for unrecognized model_ids because no fixed rate exists (see the music model_ids above for the two exceptions where a rate is hardcoded).

#### Free tier

None published. Pay-as-you-go per RunComfy account.

---

### HeyGen — Avatar Video Gateway

> **Multi-model video gateway.** Access VEO, Sora, Runway, Kling, and Seedance through a single API.

**Tools unlocked:** `heygen_video`
**Env var:** `HEYGEN_API_KEY`

#### Setup

1. Go to [app.heygen.com/register](https://app.heygen.com/register) and create an account
2. Navigate to the API section in settings
3. Generate your API key
4. Add API balance (prepaid, separate from web plan credits)
5. Add to `.env`: `HEYGEN_API_KEY=your-key-here`

#### Pricing

| Service | Price |
|---------|-------|
| Avatar video (Engine III) | $0.017/sec |
| Avatar video (Engine IV) | $0.10/sec |
| Prompt to Video | $0.033/sec |
| Video Translation (Speed) | $0.05/sec |
| Video Translation (Precision) | $0.10/sec |

**Web plans:**

| Plan | Price | Notes |
|------|-------|-------|
| Free | $0 | 1 credit (demo) |
| Creator | $24/mo | Limited credits |
| Business | $72/mo | API access, more credits |

**Free tier:** 1 credit on web platform. API is pay-as-you-go with prepaid balance.

---

### Suno — AI Music Generation

> **Full songs with vocals and lyrics.** Any genre, up to 8 minutes. Instrumentals or vocal tracks.

**Tools unlocked:** `suno_music`
**Env var:** `SUNO_API_KEY`

#### Setup

1. Go to [suno.com](https://suno.com) and create a Suno account
2. For API access, go to [sunoapi.org](https://sunoapi.org) and create an account
3. Navigate to the dashboard and copy your API key
4. Add credits (1 credit = $0.005 USD)
5. Add to `.env`: `SUNO_API_KEY=your-key-here`

#### Pricing

**Suno platform:**

| Plan | Price | Credits | Notes |
|------|-------|---------|-------|
| Free | $0 | 50/day | ~10 songs/day, non-commercial only |
| Pro | $10/mo | 2,500/mo | Commercial license |
| Premier | $30/mo | 10,000/mo | Commercial license |

**API (via sunoapi.org):** Pay-as-you-go, 1 credit = $0.005. Each generation produces 2 tracks.

---

### Pexels — Free Stock Media

> **Completely free.** No cost, no attribution required, commercial use allowed.

**Tools unlocked:** `pexels_image`, `pexels_video`
**Env var:** `PEXELS_API_KEY`

#### Setup

1. Go to [pexels.com/join](https://www.pexels.com/join/) and create a free account
2. Navigate to [pexels.com/api](https://www.pexels.com/api/)
3. Click **Your API Key** or request API access
4. Copy your key from the dashboard
5. Add to `.env`: `PEXELS_API_KEY=your-key-here`

#### Pricing

**Completely free.** No paid tiers. No attribution required. Commercial use allowed.

- 200 requests/hour
- 20,000 requests/month
- Photo and video search + download

---

### Pixabay — Free Stock Media

> **Completely free.** 5M+ royalty-free images and videos.

**Tools unlocked:** `pixabay_image`, `pixabay_video`
**Env var:** `PIXABAY_API_KEY`

#### Setup

1. Go to [pixabay.com/accounts/register](https://pixabay.com/accounts/register/) and create a free account
2. Navigate to [pixabay.com/api/docs](https://pixabay.com/api/docs/)
3. Your API key is displayed at the top of the docs page (after login)
4. Copy the key
5. Add to `.env`: `PIXABAY_API_KEY=your-key-here`

#### Pricing

**Completely free.** No paid tiers. No attribution required. Commercial use allowed.

- ~100 requests/minute
- 5,000 requests/hour
- Photo and video search + download
- Standard API limited to 1280px images (full resolution requires editorial API)

---

## Local Providers (Free, No API Key)

These providers run entirely on your machine. No network, no API key, no cost. Some require a GPU.

### Remotion — Programmatic Video Composition

> **React-based video rendering.** Turns still images into animated video with spring physics, animated text cards, stat cards, charts, and transitions. **This is the key fallback when no video generation providers are configured** — the agent generates images and Remotion animates them into professional-looking video.

**Tool:** `video_compose` (with `operation="render"` — auto-routes to Remotion when needed)
**Runtime:** CPU (Node.js required)
**Env var:** None

#### Setup

```bash
# Included in make setup, or install manually:
cd remotion-composer && npm install && cd ..
```

Requires **Node.js 18+** and `npx`. The `remotion-composer/` project is included in the repo.

#### What Remotion Renders

| Component | What it produces |
|-----------|-----------------|
| **TextCard** | Animated title/body text with spring physics entrance |
| **StatCard** | Animated statistics with count-up animations |
| **ProgressBar** | Animated progress indicators |
| **CalloutBox** | Highlighted callout panels with icon animations |
| **ComparisonCard** | Side-by-side comparison layouts |
| **BarChart / LineChart / PieChart** | Animated data visualizations |
| **KPIGrid** | Multi-metric dashboard cards |
| **Image scenes** | Still images with spring-animated motion (replaces Ken Burns) |

#### When Does Remotion Activate?

The `video_compose` tool's `render` operation auto-detects when Remotion is needed:
- Cuts contain still images (`.png`, `.jpg`, etc.)
- Cuts have `type` set to `text_card`, `stat_card`, `chart`, etc.
- Cuts specify `animation` or `transition_in`/`transition_out`

If Remotion is not installed, compositions fall back to FFmpeg Ken Burns pan-and-zoom — functional but less engaging.

**Cost:** Free. Always local.

---

### HyperFrames - HTML/CSS/GSAP Video Composition

> **GSAP-native local rendering.** HyperFrames is the preferred runtime for motion-graphics-heavy HTML compositions and the `character-animation` pipeline's rigged SVG character acting.

**Tool:** `hyperframes_compose` directly, or `video_compose` with `edit_decisions.render_runtime="hyperframes"`
**Runtime:** CPU (Node.js >= 22, FFmpeg, and `npx` required)
**Env var:** None

#### Setup

```bash
node --version
ffmpeg -version
npx --yes hyperframes doctor
```

The CLI is consumed as `npx hyperframes`. Do not use `npx @hyperframes/cli`; that package name is not the OpenMontage runtime path.

#### What HyperFrames Renders

| Use case | What it produces |
|----------|------------------|
| **Kinetic typography** | HTML/CSS text animation driven by GSAP timelines |
| **Product / launch videos** | Structured HTML scenes, registry blocks, and transitions |
| **Website-to-video** | Browser-captured site compositions with HyperFrames validation |
| **Character animation** | SVG character rigs, pose/action timelines, and GSAP acting beats rendered to `renders/final.mp4` |

HyperFrames workspaces live under `projects/<project-name>/hyperframes/`. Final videos still follow the normal OpenMontage convention: `projects/<project-name>/renders/final.mp4`.

**Cost:** Free. Always local.

---

### Piper TTS — Offline Text-to-Speech

> **Completely free, fully offline TTS.** No network required. Good quality for drafts and budget-constrained projects.

**Tool:** `piper_tts`
**Runtime:** CPU (no GPU needed)
**Env var:** None

#### Setup

```bash
# Install via pip
pip install piper-tts

# Or download the binary from GitHub
# https://github.com/rhasspy/piper/releases

# Download a voice model (first run downloads automatically)
piper --download-dir ~/.piper/models --model en_US-lessac-medium
```

**Available voices:** ~30 English voices plus voices for German, French, Spanish, Italian, and other languages. Lower variety than cloud providers but completely free and offline.

**Quality:** Good for drafts, internal videos, and budget projects. For client-facing narration, use ElevenLabs or Google TTS.

---

### Local Video Generation (GPU Required)

> **Free AI video generation.** Requires an NVIDIA GPU with sufficient VRAM.

**Tools:** `wan_video`, `hunyuan_video`, `cogvideo_video`, `ltx_video_local`
**Runtime:** Local GPU (CUDA required)
**Env vars:** `VIDEO_GEN_LOCAL_ENABLED=true`, `VIDEO_GEN_LOCAL_MODEL=<model>`

#### Setup

```bash
# 1. Install the GPU stack
make install-gpu
# Or manually:
pip install diffusers transformers accelerate torch pillow requests

# 2. Enable local generation in .env
VIDEO_GEN_LOCAL_ENABLED=true

# 3. Choose a model based on your GPU VRAM
VIDEO_GEN_LOCAL_MODEL=wan2.1-1.3b      # 6GB+ VRAM (entry-level)
VIDEO_GEN_LOCAL_MODEL=wan2.1-14b       # 24GB+ VRAM (best local quality)
VIDEO_GEN_LOCAL_MODEL=hunyuan-1.5      # 12GB+ VRAM
VIDEO_GEN_LOCAL_MODEL=ltx2-local       # 8GB+ VRAM (fastest)
VIDEO_GEN_LOCAL_MODEL=cogvideo-5b      # 10GB+ VRAM
VIDEO_GEN_LOCAL_MODEL=cogvideo-2b      # 6GB+ VRAM (lightest)
```

#### Model Comparison

| Model | VRAM | Quality | Speed | Best for |
|-------|------|---------|-------|----------|
| **WAN 2.1 (1.3B)** | 6GB | Good | Fast | Entry-level GPU, quick iteration |
| **WAN 2.1 (14B)** | 24GB | Excellent | Slow | Best quality-to-VRAM ratio |
| **Hunyuan 1.5** | 12GB | Very good | Medium | Mid-range GPUs |
| **LTX-2** | 8GB | Good | Fastest | Quick drafts, lowest latency |
| **CogVideo (5B)** | 10GB | Good | Medium | Balanced option |
| **CogVideo (2B)** | 6GB | Fair | Fast | Low-VRAM experimentation |

**All local models support:** Image-to-video, text-to-video, offline generation, seeded reproducibility.

**Apple Silicon / Mac note:** `wan_video`, `hunyuan_video`, `cogvideo_video`, and `ltx_video_local`
load their diffusers pipeline with a hardcoded `.to("cuda")` — they require an NVIDIA GPU and will
not run on a Mac (Apple Silicon or Intel), regardless of RAM. For free/offline generation on a Mac,
use `comfyui_local` below instead.

---

### ComfyUI Local — Bring Your Own Workflow (Apple Silicon-friendly, GPU Required)

> **Free, fully offline generation via a ComfyUI server you run yourself.** Unlike RunComfy
> (below), nothing here is a cloud API — this tool just talks HTTP to a ComfyUI instance on your
> own machine. ComfyUI runs natively on Apple Silicon via Metal/MPS, so this is the practical path
> to local video/image generation on a Mac, where `wan_video`/`hunyuan_video`/`cogvideo_video`/
> `ltx_video_local` (CUDA-only, see above) don't work.

**Tool:** `comfyui_local`
**Runtime:** Local GPU (Metal/MPS on Mac, or CUDA on Linux/Windows — whatever ComfyUI itself supports)
**Env var:** `COMFYUI_API_URL` (optional — defaults to `http://127.0.0.1:8188`)

#### Setup

```bash
# 1. Install ComfyUI (one-time)
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI && pip install -r requirements.txt

# 2. Install whatever custom nodes your workflow needs, e.g.:
#    ComfyUI-AnimateDiff-Evolved, ComfyUI-VideoHelperSuite, LTX-Video nodes, Mochi nodes
#    via ComfyUI Manager, or by cloning into ComfyUI/custom_nodes/.
# Download the matching model checkpoints into ComfyUI/models/.

# 3. Start the server (leave it running)
python main.py        # serves the API at http://127.0.0.1:8188

# 4. In ComfyUI's settings, enable "Dev mode options", then build your
#    workflow in the UI and export it with "Save (API Format)" — that JSON
#    is what comfyui_local submits.
```

If ComfyUI runs on a different machine than OpenMontage, set
`COMFYUI_API_URL=http://<that-machine-ip>:8188` in `.env`.

#### How the tool works

`comfyui_local` is a thin pass-through, by design — it does not template or generate workflows
for you (no orchestration/creative logic in Python, per project convention). Provide:

- `workflow` (dict) or `workflow_path` (path to the exported API-format JSON), and
- `overrides` (optional): dotted-path patches applied before submission, e.g.
  `{"6.inputs.text": "a neon city at night", "3.inputs.seed": 42}` — node ids and field names are
  specific to your workflow; open the exported JSON (or the ComfyUI UI) to find them.

The tool POSTs to `/prompt`, polls `/history/{prompt_id}` until done, and downloads every
image/gif/video output via `/view` into `output_dir`.

#### Limitations

- **Not zero-setup.** You need ComfyUI installed, running, with the specific custom nodes and
  model checkpoints your workflow requires already in place — there's no model catalog or
  templating here, unlike RunComfy's `model_id` gateway.
- **No Layer-3 prompting skill yet** (`agent_skills` is empty) — prompting technique depends
  entirely on whichever model your workflow uses; check that model's own documentation.
- Cost is always `$0` (your own hardware/electricity); `estimate_cost()` returns `0.0`.

---

### Local Diffusion — Offline Image Generation (GPU Required)

> **Free Stable Diffusion image generation.** No API cost, fully offline.

**Tool:** `local_diffusion`
**Runtime:** Local GPU (CUDA required)
**Env var:** None (enable by installing dependencies)

#### Setup

```bash
pip install diffusers transformers accelerate torch
```

First run downloads the model (~4GB). Subsequent runs use the cached model.

**VRAM requirement:** 4GB+ (8GB recommended for 1024x1024 images)

**Supports:** Negative prompts, seeds, custom sizes. Quality is lower than FLUX or DALL-E 3 but completely free and offline.

---

### LTX-2 on Modal — Self-Hosted Cloud GPU

> **Run LTX-2 on Modal's cloud GPUs.** Your own endpoint, your own scale. More consistent than local GPU, cheaper than commercial APIs.

**Tool:** `ltx_video_modal`
**Runtime:** Cloud (self-hosted)
**Env var:** `MODAL_LTX2_ENDPOINT_URL`

#### Setup

1. Create a [Modal](https://modal.com) account
2. Deploy the LTX-2 endpoint (see Modal docs)
3. Set the endpoint URL in `.env`: `MODAL_LTX2_ENDPOINT_URL=https://your-modal-endpoint`

**Modal pricing:** ~$0.99/hour for A100 GPU time. Cost per video depends on generation time.

---

### Other Local Tools (Always Available)

These tools require only FFmpeg or Python packages — no GPU, no API key.

| Tool | Install | What it does |
|------|---------|-------------|
| **FFmpeg tools** (video_compose, video_stitch, video_trimmer, audio_mixer, audio_enhance, color_grade, face_enhance, frame_sampler, scene_detect) | `brew install ffmpeg` / `sudo apt install ffmpeg` / `winget install FFmpeg` | Video editing, audio processing, color grading, analysis |
| **Transcriber** | `pip install faster-whisper` | Speech-to-text with word-level timestamps |
| **Background Remove** | `pip install rembg` (CPU) or `pip install rembg[gpu]` | Remove image/video backgrounds |
| **Upscale** | `pip install realesrgan` (requires PyTorch + CUDA) | Real-ESRGAN image/video upscaling |
| **Face Restore** | `pip install gfpgan` (requires PyTorch) | CodeFormer/GFPGAN face restoration |
| **Code Snippet** | `pip install Pygments Pillow` | Syntax-highlighted code images |
| **Diagram Gen** | `npm install -g @mermaid-js/mermaid-cli` | Mermaid diagram rendering |
| **Math Animate** | `pip install manim` | ManimCE mathematical animations |
| **Subtitle Gen** | No install needed | SRT/VTT subtitle file generation |
| **Video Understand** | `pip install transformers torch` | CLIP/BLIP-2 visual analysis |
| **Talking Head** | Clone [SadTalker](https://github.com/OpenTalker/SadTalker) | Avatar animation from photo + audio |
| **Lip Sync** | Clone [Wav2Lip](https://github.com/Rudrabha/Wav2Lip) | Audio-driven lip synchronization |

---

## Provider-to-Tool Mapping

| Provider | Env Var | Tools Unlocked | Cost |
|----------|---------|---------------|------|
| **Pexels** | `PEXELS_API_KEY` | `pexels_image`, `pexels_video` | Free |
| **Pixabay** | `PIXABAY_API_KEY` | `pixabay_image`, `pixabay_video` | Free |
| **Piper** | — (install only) | `piper_tts` | Free |
| **Google** | `GOOGLE_API_KEY` | `google_tts`, `google_imagen` | Free tier + paid |
| **ElevenLabs** | `ELEVENLABS_API_KEY` | `elevenlabs_tts`, `music_gen` | Free tier + paid |
| **fal.ai** | `FAL_KEY` | `flux_image`, `recraft_image`, `kling_video`, `veo_video`, `minimax_video` | Pay-as-you-go |
| **OpenAI** | `OPENAI_API_KEY` | `openai_tts`, `openai_image` | Paid only |
| **xAI** | `XAI_API_KEY` | `grok_image`, `grok_video` | Paid only |
| **Runway** | `RUNWAY_API_KEY` | `runway_video` | Free trial + paid |
| **Higgsfield** | `HIGGSFIELD_API_KEY` + `HIGGSFIELD_API_SECRET` | `higgsfield_video` | Subscription ($15-84/mo) |
| **HeyGen** | `HEYGEN_API_KEY` | `heygen_video` | Pay-as-you-go |
| **Suno** | `SUNO_API_KEY` | `suno_music` | Pay-as-you-go |
| **RunComfy** | `RUNCOMFY_TOKEN` | `runcomfy_image`, `runcomfy_video`, `runcomfy_music` | Pay-as-you-go (per model) |
| **Local GPU** | `VIDEO_GEN_LOCAL_ENABLED` | `wan_video`, `hunyuan_video`, `cogvideo_video`, `ltx_video_local` | Free (NVIDIA GPU required, not Mac) |
| **ComfyUI Local** | `COMFYUI_API_URL` (optional) | `comfyui_local` | Free (GPU required; Apple Silicon-friendly) |
| **Local Diffusion** | — (install only) | `local_diffusion` | Free (GPU required) |
| **Modal** | `MODAL_LTX2_ENDPOINT_URL` | `ltx_video_modal` | Self-hosted cloud |

---

## Capability Coverage

How many providers cover each capability:

| Capability | Cloud Providers | Local Providers | Free Options |
|-----------|----------------|-----------------|--------------|
| **Image Generation** | FLUX, Grok, Google Imagen, DALL-E 3, Recraft, RunComfy (any model_id) | Local Diffusion | Pexels, Pixabay (stock) |
| **Video Generation** | Grok, Kling, Runway, Veo, Higgsfield, MiniMax, HeyGen, RunComfy (any model_id) | WAN, Hunyuan, CogVideo, LTX (CUDA only), ComfyUI Local (Apple Silicon-friendly) | Pexels, Pixabay (stock) |
| **Text-to-Speech** | ElevenLabs, Google TTS, OpenAI | Piper | Piper, Google free tier, ElevenLabs free tier |
| **Music Generation** | ElevenLabs, Suno, RunComfy (ACE-Step 1.5, ElevenLabs Music) | — | ElevenLabs free tier |
| **Post-Production** | — | FFmpeg (compose, stitch, trim, mix, enhance, grade) | All free |
| **Analysis** | — | WhisperX, Scene Detect, Frame Sampler, CLIP/BLIP-2 | All free |
| **Enhancement** | — | Upscale, BG Remove, Face Enhance, Face Restore | All free |
| **Avatar** | — | SadTalker, Wav2Lip | All free |

---

## FAQ

**Q: What's the absolute minimum I need to produce a video?**
A: FFmpeg + Node.js (both free, local). FFmpeg handles video assembly, audio mixing, and subtitles. With Node.js, Remotion renders still images into animated video — so even without any video generation API, the agent generates images and Remotion turns them into professional-looking video with spring animations, text cards, and transitions. Add Piper TTS for free narration and Pexels/Pixabay for free stock footage.

**Q: I don't have any video generation providers. Can I still make videos?**
A: Yes. The agent generates still images (via any image provider — even free stock from Pexels/Pixabay) and Remotion composes them into animated video with spring physics transitions, text cards, stat cards, and charts. This is the default path for explainer and animation pipelines when no video gen is configured.

**Q: What's one low-friction way to get AI-generated images and video?**
A: fal.ai (`FAL_KEY`) is one pay-as-you-go option with broad single-key coverage. It unlocks FLUX images plus multiple video providers. No subscription — pay only for what you generate.

**Q: I have a GPU. What can I run locally for free?**
A: On an NVIDIA/CUDA machine: set `VIDEO_GEN_LOCAL_ENABLED=true` and install `diffusers`. You get WAN 2.1, Hunyuan, CogVideo, and LTX video generation plus Stable Diffusion image generation — all free, all offline.

**Q: I'm on a Mac (Apple Silicon). Can I generate video locally for free?**
A: Not via `VIDEO_GEN_LOCAL_ENABLED` — those four tools hardcode `.to("cuda")` and don't run on Mac. Instead, install [ComfyUI](https://github.com/comfyanonymous/ComfyUI) yourself (it runs natively on Metal/MPS) and use the `comfyui_local` tool, which talks to your already-running ComfyUI server over HTTP. You'll need to build/export a workflow and install whatever custom nodes + model checkpoints it needs — see the "ComfyUI Local" section above. Don't confuse this with **RunComfy** (`runcomfy_video`), which despite the similar name is a paid cloud gateway, not local.

**Q: Which TTS provider should I use?**
A: For quality → ElevenLabs. For localization (50+ languages) → Google TTS. For budget → Google free tier (1M chars/month). For offline → Piper.

**Q: Do I need all these providers?**
A: No. Start with what you have. The selector pattern auto-routes to whatever's available. Missing a provider? The system falls through to the next one automatically.
