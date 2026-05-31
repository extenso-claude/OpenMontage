# Voice Cloning API — Handoff for Hermes (Windows VPS)

OpenMontage's voice cloning runs through three Replicate-hosted models. None
of these run on the VPS — Hermes only needs to make HTTPS calls to
`api.replicate.com`. No GPU, no Docker, no Python ML stack on the VPS.

| Provider | Replicate slug | Capability | Cost | Purpose |
|---|---|---|---|---|
| IndexTTS-2 | `lucataco/indextts-2` | TTS (zero-shot voice clone) | $0.006/run | Read scripts in any voice from a 10-30s reference clip |
| TADA (self-hosted) | `extenso-claude/tada-voice` | TTS (zero-shot voice clone, multilingual) | ~$0.012/run | Alternate TTS with 1:1 token alignment, multilingual |
| RVC v2 | `pseudoram/rvc-v2` | Voice conversion (audio→audio) | ~$0.02/run | Convert TTS output → trained Huxley/Mr. Calder voice |

The typical chain for a sleep documentary narration is:
```
script  →  IndexTTS-2 or TADA  →  base voice WAV  →  RVC v2 + Huxley model  →  final WAV
                                                  →  RVC v2 + Mr. Calder model  →  final WAV
```

## Authentication

All three endpoints use the same Replicate API key:

```
REPLICATE_API_TOKEN=<your_token>
```

Get the token from https://replicate.com/account/api-tokens. The same token
works on all three endpoints (no per-model API keys).

## Calling pattern

All three follow Replicate's standard prediction API:

```http
POST https://api.replicate.com/v1/predictions
Authorization: Bearer $REPLICATE_API_TOKEN
Content-Type: application/json
Prefer: wait=60                # block up to 60s; longer jobs return a poll URL

{
  "version": "<model_version_id>",
  "input": { ... }
}
```

`Prefer: wait=60` returns the completed result inline if the prediction
finishes within 60 s. For longer jobs (chunked long-form, multi-candidate
TADA), the response status will be `processing` and the response includes a
`urls.get` to poll until `status == "succeeded"`.

### Python (3-line minimum)

```python
import requests
TOKEN = os.environ["REPLICATE_API_TOKEN"]

resp = requests.post(
    "https://api.replicate.com/v1/predictions",
    headers={"Authorization": f"Bearer {TOKEN}", "Prefer": "wait=60"},
    json={"version": VERSION, "input": INPUT},
    timeout=120,
)
pred = resp.json()
# Poll if not done synchronously
while pred["status"] in ("starting", "processing"):
    pred = requests.get(pred["urls"]["get"], headers={"Authorization": f"Bearer {TOKEN}"}).json()
audio_url = pred["output"][0] if isinstance(pred["output"], list) else pred["output"]
audio_bytes = requests.get(audio_url, timeout=300).content
```

### PowerShell equivalent

```powershell
$headers = @{ Authorization = "Bearer $env:REPLICATE_API_TOKEN"; Prefer = "wait=60" }
$body = @{ version = $version; input = $input } | ConvertTo-Json -Depth 6
$pred = Invoke-RestMethod -Uri "https://api.replicate.com/v1/predictions" -Method Post -Headers $headers -Body $body -ContentType "application/json"
while ($pred.status -in "starting","processing") { Start-Sleep 3; $pred = Invoke-RestMethod -Uri $pred.urls.get -Headers $headers }
$audioUrl = if ($pred.output -is [array]) { $pred.output[0] } else { $pred.output }
Invoke-WebRequest -Uri $audioUrl -OutFile "out.wav"
```

## Model 1 — IndexTTS-2

- **Slug:** `lucataco/indextts-2`
- **Version (pinned):** `b219b0f22f95fd97cb2c8e3bbea6827a450a7fff05674c996d83171d70b3f685`
- **Hardware:** Nvidia L40S
- **Predict time:** ~7 s
- **Cost:** $0.006 per call

### Required inputs

| Field | Type | Notes |
|---|---|---|
| `text` | string | Script to synthesize |
| `speaker_audio` | URL | 16-48 kHz WAV/MP3 of target voice (Replicate-accessible URL) |

### Key optional inputs (16 total — see Google Doc for full reference)

| Field | Default | Range | Effect |
|---|---|---|---|
| `emotion_text` | – | string | Plain-English emotion direction, e.g. "calm, contemplative" |
| `emotion_vector` | – | "0.1,0.0,0.4,0.0,0.0,0.0,0.5,0.0" | 8-dim weights: happy/angry/sad/fear/disgust/surprised/calm/neutral |
| `emotion_audio` | – | URL | Separate emotion reference clip |
| `temperature` | 0.8 | 0-2 | Higher = more prosody variation |
| `interval_silence_ms` | 200 | 0-2000 | Pause inserted between auto-split segments |
| `max_text_tokens_per_segment` | 120 | 32-300 | Smaller → more auto-splits → more `interval_silence_ms` breaks |
| `repetition_penalty` | 10 | 1-30 | Default of 10 is intentionally high |
| `num_beams` | 3 | 1-8 | Higher = smoother but less expressive |

### Voice references (Drive)

| Character | Drive path | Notes |
|---|---|---|
| Grandpa Huxley | `Inputs/Huxley Voice/ghuxley-short-17s.mp3` | Pre-trimmed short clip |
| Grandpa Huxley | `Inputs/Huxley Voice/huxley_01.wav` ... `huxley_09.wav` | Full clean cuts (~5 min each) |
| Mr. Calder | `Inputs/Midnight Magnate Voice/mr-calder-14s.mp3` | Pre-trimmed short clip |
| Mr. Calder | `Inputs/Midnight Magnate Voice/mr-calder-Intro.mp3` | ~14s intro clip |

The reference clip must be publicly fetchable by Replicate. Upload local
files to Replicate's Files API first (or use a stable HTTP URL).

```python
# Upload a local file → get a URL Replicate can use
with open("ref.mp3", "rb") as f:
    r = requests.post(
        "https://api.replicate.com/v1/files",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files={"content": ("ref.mp3", f, "audio/mpeg")},
    )
ref_url = r.json()["urls"]["get"]
```

## Model 2 — TADA (self-hosted)

- **Slug:** `extenso-claude/tada-voice` (override via `TADA_MODEL_SLUG` env if you rename)
- **Version:** look up via `GET /v1/models/extenso-claude/tada-voice` → `latest_version.id`
- **Hardware:** Nvidia L40S
- **Cold start:** ~1-2 min (downloading 9 GB of Llama weights from container disk)
- **Predict time:** ~5-10 s for ~10 s of speech at `num_acoustic_candidates=1`
- **Cost:** ~$0.012/call at N=1 (per-second L40S billing × predict time)

### Required inputs

| Field | Type | Notes |
|---|---|---|
| `text` | string | Script |
| `prompt_audio` | URL | Reference voice (10-30 s, mono, 16-48 kHz) |
| `prompt_transcript` | string | **Verbatim** transcript of `prompt_audio` (required) |

### Key optional inputs (21 total — see Google Doc for full reference)

| Field | Default | Range | Effect |
|---|---|---|---|
| `language` | `en` | en/ar/ch/de/es/fr/it/ja/pl/pt | Non-English MUST supply transcript |
| `text_temperature` | 0.6 | 0-2 | LM sampling temperature |
| `acoustic_cfg_scale` | 1.6 | 0-5 | Voice-fidelity guidance. 2.0-2.5 = tighter to ref |
| `duration_cfg_scale` | 1.0 | 0-5 | Pacing rigidity. 0.5-0.8 = conversational |
| `noise_temperature` | 0.9 | 0-2 | Run-to-run variation |
| `num_flow_matching_steps` | 10 | 1-50 | Quality vs speed |
| `num_acoustic_candidates` | 1 | 1-8 | Generate N variants, pick best (N× cost) |
| `scorer` | `likelihood` | spkr_verification / likelihood / duration_median | Used when N>1 |
| `speed_up_factor` | – | 1.0-1.5 | Global pacing speedup |
| `seed` | -1 | int | -1 = random; same seed reproduces output |

### Initial UI setup (one-time, not for Hermes)

Before first use, the model must be created on Replicate:
1. Visit https://replicate.com/create
2. Name: `tada-voice`, owner: `extenso-claude`, hardware: L40S, visibility: Private
3. Connect GitHub source: `extenso-claude/tada` (default branch `main`)
4. Add **build secret** `HF_TOKEN` = your HuggingFace token (with Llama 3.2 license accepted)
5. Save → Replicate auto-builds (~10-15 min)

Once built, Hermes just makes API calls to the slug above.

## Model 3 — RVC v2 (voice conversion)

- **Slug:** `pseudoram/rvc-v2`
- **Version (pinned):** `d18e2e0a6a6d3af183cc09622cebba8555ec9a9e66983261fc64c8b1572b7dce`
- **Hardware:** Replicate-managed
- **Predict time:** scales with input audio length; ~10-30 s for typical clips
- **Cost:** ~$0.02 per call

### Required inputs

| Field | Type | Notes |
|---|---|---|
| `input_audio` | URL | Source audio to convert (TTS output, typically) |

### Voice model selection — use CUSTOM

| Field | Required for CUSTOM | Notes |
|---|---|---|
| `rvc_model` | `"CUSTOM"` | Use the trained model, not the bundled Obama/Trump/Sandy/Rogan |
| `custom_rvc_model_download_url` | yes | Public URL to a ZIP containing `.pth` + `.index` |

### Key optional inputs

| Field | Default | Range | Effect |
|---|---|---|---|
| `pitch_change` | 0 | ±semitones | Voice pitch shift (use to match age/register) |
| `index_rate` | 0.5 | 0-1 | How much trained accent vs source. 0.5-0.7 is a good starting range |
| `f0_method` | `rmvpe` | `rmvpe` / `mangio-crepe` | rmvpe = vocal clarity, mangio-crepe = smoother |
| `protect` | 0.33 | 0-0.5 | Preserves breath/consonants from source. 0.5 = disable |
| `rms_mix_rate` | 0.25 | 0-1 | 0 = preserve original loudness, 1 = flat |

### Trained voice models

Both trained RVC models live in a **public** HF model repo:
[`Ryano562/openmontage-voice-models`](https://huggingface.co/Ryano562/openmontage-voice-models).

| Character | URL | Components | Size |
|---|---|---|---|
| Grandpa Huxley | `https://huggingface.co/Ryano562/openmontage-voice-models/resolve/main/huxley.zip` | `huxley.pth` + `huxley.index` | 343 MB |
| Mr. Calder | `https://huggingface.co/Ryano562/openmontage-voice-models/resolve/main/mm.zip` | `mm.pth` + `mm.index` | 244 MB |

Originals are in the Drive shared folder under `Outputs - Runpod/RVC_models/`.
Re-upload via `experiments/voice-clone-eval/host_rvc_models.py` if files change.

Pass the resolve URL directly as `custom_rvc_model_download_url` in the
Replicate input. Replicate downloads the ZIP once per model worker.

## End-to-end example: synthesize → convert

```python
import os, requests

TOKEN = os.environ["REPLICATE_API_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Prefer": "wait=60"}
INDEXTTS_VERSION = "b219b0f22f95fd97cb2c8e3bbea6827a450a7fff05674c996d83171d70b3f685"
RVC_VERSION      = "d18e2e0a6a6d3af183cc09622cebba8555ec9a9e66983261fc64c8b1572b7dce"
HUXLEY_REF       = "https://...your huxley ref.mp3"  # see voice-refs section
HUXLEY_RVC_ZIP   = "https://...your huxley.zip"      # see hosting section

def predict(version, payload):
    r = requests.post("https://api.replicate.com/v1/predictions",
                      headers=HEADERS, json={"version": version, "input": payload},
                      timeout=120).json()
    while r["status"] in ("starting", "processing"):
        r = requests.get(r["urls"]["get"], headers={"Authorization": f"Bearer {TOKEN}"}).json()
    if r["status"] != "succeeded":
        raise RuntimeError(r.get("error"))
    out = r["output"]
    return out[0] if isinstance(out, list) else out

# Step 1 — TTS in any voice (use Huxley ref directly)
tts_url = predict(INDEXTTS_VERSION, {
    "text": "Tonight we drift through a quiet observatory in the highlands.",
    "speaker_audio": HUXLEY_REF,
    "temperature": 0.9,
    "interval_silence_ms": 400,
    "emotion_text": "calm, contemplative late-night narration",
})

# Step 2 — apply Huxley RVC model on top to tighten the voice match
final_url = predict(RVC_VERSION, {
    "input_audio": tts_url,
    "rvc_model": "CUSTOM",
    "custom_rvc_model_download_url": HUXLEY_RVC_ZIP,
    "pitch_change": 0,
    "index_rate": 0.6,
    "f0_method": "rmvpe",
})

audio_bytes = requests.get(final_url, timeout=300).content
open("huxley_output.wav", "wb").write(audio_bytes)
```

## Long-form audio (1 hour scripts)

For scripts beyond a single segment, split client-side and fan out:
- Chunk at paragraph → sentence → comma boundaries to ~80-150 words per chunk
- Submit ~20 predictions concurrently (Replicate's default per-account concurrency)
- Stitch the resulting WAVs with `ffmpeg concat`

For an hour at 150 wpm (~9000 words):
- IndexTTS-2: ~70 calls × $0.006 = **~$0.42**
- TADA: ~70 calls × $0.012 = **~$0.84**
- RVC pass on the result: ~$0.60-1.80 depending on duration

OpenMontage's Python tools (`tools/audio/{indextts2,tada,rvc}_replicate.py`)
already implement this client-side chunking — Hermes can either call those
tools directly (if Python is available on the VPS) or replicate the same
chunking logic in PowerShell/Node.

## Running parameter sweeps

Use `experiments/voice-clone-eval/voice_sweep.py` from a Python environment
(your Mac or wherever the OpenMontage repo lives — not the VPS). Examples are
in `experiments/voice-clone-eval/sweep_examples/`. The runner:

1. Expands a YAML config's parameter grid into a Cartesian product
2. Runs all combos in parallel against Replicate
3. Saves outputs locally + uploads to a Drive folder for review
4. Writes a JSON + CSV manifest with cost / duration / params per run

The result is a Drive folder with N labeled audio files (one per parameter
combination) plus a manifest your assistant can audition through.
