# Personal Avatar Clone

Free, local-first scaffolding for building a voice + video avatar of yourself without reinventing the wheel.

This repo does not train a new foundation model from scratch. Instead, it gives you a stable controller layer that can drive proven open-source backends with separate Python environments on macOS.

## Recommended stack

### Default MVP

- Voice: `F5-TTS`
- Video: `SadTalker`

Why this pairing:

- `F5-TTS` has an official Apple Silicon install path and a Python API we can script cleanly.
- `SadTalker` is audio-driven, so it fits the "type text -> clone voice -> produce talking head video" workflow.

### Upgrade path

- Better motion control: `LivePortrait`
- More permissive voice-cloning option to investigate later: `OpenVoice`

Why `LivePortrait` is not the default:

- It is driven by video or motion templates, not directly by TTS audio.
- It can still be useful once you record a few short driving clips of yourself, but `SadTalker` is the simpler first win.

Why `Wav2Lip` is not the default:

- The official open-source repo still documents `Python 3.6`.
- The authors explicitly limit the open model to research/academic/personal use.
- It is still useful as a specialist lipsync tool, just not the cleanest foundation for your first local build.

## What this repo gives you

- A small CLI controller we own
- Config for separate backend environments
- A bootstrap command to clone official repos locally
- A prep command to clean a raw recording into a clone-ready reference clip
- A pipeline command to go from text -> cloned voice -> talking-head render
- A local web UI for uploading assets and running the pipeline visually
- A capture guide so your first recordings are actually usable

## Project layout

- [`avatar.config.json`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/avatar.config.json)
- [`src/avatar_clone/cli.py`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/src/avatar_clone/cli.py)
- [`docs/capture_guide.md`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/docs/capture_guide.md)
- [`docs/setup_mac.md`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/docs/setup_mac.md)
- [`docs/first_recording.md`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/docs/first_recording.md)

## Quick start

### 1. Create the controller environment

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

### 2. Clone the backend repos

```bash
PYTHONPATH=src python3 -m avatar_clone bootstrap --with-liveportrait
```

That clones the official repos into `external/`.

### 3. Create separate backend envs

Use the versions the upstream projects document.

Suggested macOS split:

- `F5-TTS`: Python `3.11`
- `SadTalker`: Python `3.8`
- `LivePortrait`: Python `3.10`

The controller is intentionally separate from those envs.

There is a concrete setup walkthrough here:

- [`docs/setup_mac.md`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/docs/setup_mac.md)

### 4. Fill in backend paths

Edit [`avatar.config.json`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/avatar.config.json) and replace the placeholder Python paths with the interpreters for each backend env. Also confirm the repo paths under `external/`.

### 5. Check the setup

```bash
PYTHONPATH=src python3 -m avatar_clone doctor
```

### Optional: launch the web UI

```bash
.venv/bin/avatar-clone ui
```

Then open:

- [http://127.0.0.1:7861](http://127.0.0.1:7861)

### 6. Put your assets here

- Voice reference audio: `data/voice_refs/`
- Portrait stills: `data/portraits/`
- Driving clips for `LivePortrait`: `data/driving_videos/`

Read the capture guide first:

- [`docs/capture_guide.md`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/docs/capture_guide.md)
- [`docs/first_recording.md`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/docs/first_recording.md)

### 7. Generate a voice clone sample

If your source is a raw voice memo, prep it first:

```bash
PYTHONPATH=src python3 -m avatar_clone prep-audio \
  --input data/voice_refs/me_raw.m4a \
  --output data/voice_refs/me_ref.wav
```

Then generate the clone sample:

```bash
PYTHONPATH=src python3 -m avatar_clone render-voice \
  --text "This is my first local avatar test." \
  --ref-audio data/voice_refs/me_ref.wav \
  --ref-text "This is the transcript of my reference clip." \
  --output data/outputs/test_voice.wav
```

### 8. Generate a talking-head clip

```bash
PYTHONPATH=src python3 -m avatar_clone pipeline \
  --text "This is my first end to end avatar test." \
  --ref-audio data/voice_refs/me_ref.wav \
  --ref-text "This is the transcript of my reference clip." \
  --source-image data/portraits/me_front.png
```

That uses:

- voice backend: `f5_tts`
- video backend: `sadtalker`

If you want the `LivePortrait` path instead:

```bash
PYTHONPATH=src python3 -m avatar_clone pipeline \
  --text "Testing motion transfer with my cloned voice." \
  --ref-audio data/voice_refs/me_ref.wav \
  --ref-text "This is the transcript of my reference clip." \
  --source-image data/portraits/me_front.png \
  --video-backend liveportrait \
  --driving-video data/driving_videos/me_neutral_driver.mp4
```

## Notes on licenses

- `F5-TTS` code is MIT, but the official pre-trained weights are documented in the repo as `CC-BY-NC`.
- `SadTalker` states its repo license is Apache 2.0 and that the non-commercial restriction was removed.
- `LivePortrait` repo code is MIT, but its published license file notes that bundled `InsightFace` models are for non-commercial research use unless you replace them.

If your goal ever becomes commercial, we should do a stricter license pass before shipping anything public.

## Official upstream sources

- [F5-TTS](https://github.com/SWivid/F5-TTS)
- [F5-TTS inference docs](https://github.com/SWivid/F5-TTS/blob/main/src/f5_tts/infer/README.md)
- [SadTalker](https://github.com/OpenTalker/SadTalker)
- [SadTalker macOS install notes](https://github.com/OpenTalker/SadTalker/blob/main/docs/install.md)
- [LivePortrait](https://github.com/KlingAIResearch/LivePortrait)
- [LivePortrait license](https://github.com/KlingAIResearch/LivePortrait/blob/main/LICENSE)
- [Wav2Lip](https://github.com/Rudrabha/Wav2Lip)
