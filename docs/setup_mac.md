# macOS Setup

This project is designed around separate backend environments.

That is not overengineering. These upstream repos want different Python versions, and trying to force them into one env is how local avatar projects get brittle fast.

## What you need first

- `uv`
- `ffmpeg`
- `git`

You already have `uv`, `ffmpeg`, and `git` on this machine.

## 1. Clone the upstream repos

From the project root:

```bash
.venv/bin/avatar-clone bootstrap --with-liveportrait
```

This creates:

- `external/F5-TTS`
- `external/SadTalker`
- `external/LivePortrait`

## 2. F5-TTS voice environment

Official repo guidance supports Apple Silicon and Python `>=3.10`. We are standardizing on `3.11`.

```bash
uv python install 3.11
uv venv .envs/f5-tts --python 3.11
uv pip install --python .envs/f5-tts/bin/python torch torchaudio
uv pip install --python .envs/f5-tts/bin/python -e external/F5-TTS
```

Optional warmup to cache the official weights before your first real run:

```bash
.envs/f5-tts/bin/python -c "from f5_tts.api import F5TTS; F5TTS(device='cpu')"
```

## 3. SadTalker video environment

The official macOS install notes were tested on an M1 Mac with Python `3.8`.

```bash
uv python install 3.8
uv venv .envs/sadtalker --python 3.8
uv pip install --python .envs/sadtalker/bin/python torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
LMDB_FORCE_CFFI=1 uv pip install --python .envs/sadtalker/bin/python -r external/SadTalker/requirements.txt
uv pip install --python .envs/sadtalker/bin/python dlib
```

Why these pins matter:

- `basicsr` in `SadTalker` expects an older `torchvision` layout.
- letting `uv` choose a newer `torchvision` can break on `functional_tensor`
- `LMDB_FORCE_CFFI=1` avoids an `lmdb` C-extension build failure on this macOS Apple Silicon setup

After that, fetch the checkpoints. The upstream script uses `wget`, which is not installed on this machine by default. If you have `wget`, you can still use:

- `external/SadTalker/scripts/download_models.sh`

Otherwise use the `curl` commands below:

```bash
mkdir -p external/SadTalker/checkpoints external/SadTalker/gfpgan/weights

curl -L --fail -o external/SadTalker/checkpoints/mapping_00109-model.pth.tar https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar
curl -L --fail -o external/SadTalker/checkpoints/mapping_00229-model.pth.tar https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar
curl -L --fail -o external/SadTalker/checkpoints/SadTalker_V0.0.2_256.safetensors https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors
curl -L --fail -o external/SadTalker/checkpoints/SadTalker_V0.0.2_512.safetensors https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors

curl -L --fail -o external/SadTalker/gfpgan/weights/alignment_WFLW_4HG.pth https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth
curl -L --fail -o external/SadTalker/gfpgan/weights/detection_Resnet50_Final.pth https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth
curl -L --fail -o external/SadTalker/gfpgan/weights/GFPGANv1.4.pth https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth
curl -L --fail -o external/SadTalker/gfpgan/weights/parsing_parsenet.pth https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth
```

## 4. LivePortrait environment

The official repo documents macOS Apple Silicon support and recommends Python `3.10`.

```bash
uv python install 3.10
uv venv .envs/liveportrait --python 3.10
uv pip install --python .envs/liveportrait/bin/python --index-strategy unsafe-best-match -r external/LivePortrait/requirements_macOS.txt
```

Then download the weights with the current Hugging Face CLI:

```bash
.envs/liveportrait/bin/hf download KlingTeam/LivePortrait \
  --local-dir external/LivePortrait/pretrained_weights \
  --exclude "*.git*" \
  --exclude "README.md" \
  --exclude "docs/*"
```

## 5. Update the controller config

Edit [`avatar.config.json`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/avatar.config.json) and replace the placeholders with:

- `f5_tts.python` -> `/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/.envs/f5-tts/bin/python`
- `sadtalker.python` -> `/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/.envs/sadtalker/bin/python`
- `sadtalker.cwd` -> `/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/external/SadTalker`
- `liveportrait.python` -> `/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/.envs/liveportrait/bin/python`
- `liveportrait.cwd` -> `/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/external/LivePortrait`

## 6. Sanity check

```bash
.venv/bin/avatar-clone doctor
```

When everything is wired up, the placeholder warnings should disappear.

## Optional: launch the UI

```bash
.venv/bin/avatar-clone ui
```

Open:

- [http://127.0.0.1:7861](http://127.0.0.1:7861)

## 7. First run

Voice only:

```bash
.venv/bin/avatar-clone render-voice \
  --text "This is my first local voice clone." \
  --ref-audio data/voice_refs/me_ref.wav \
  --ref-text "This is the transcript of my reference clip." \
  --output data/outputs/test_voice.wav
```

End to end with SadTalker:

```bash
.venv/bin/avatar-clone pipeline \
  --text "This is my first local avatar test." \
  --ref-audio data/voice_refs/me_ref.wav \
  --ref-text "This is the transcript of my reference clip." \
  --source-image data/portraits/me_front.png
```

## Notes

- `SadTalker` is the first backend to get working because it is directly audio-driven.
- `LivePortrait` is the motion-quality upgrade once you have driving clips.
- If `LivePortrait` runs on Apple Silicon but falls back on unsupported ops, the controller already keeps `PYTORCH_ENABLE_MPS_FALLBACK=1` in config for that backend.
- `SadTalker` can start rendering on this machine, but it is CPU-bound and very slow for full runs. Treat it as a correctness path first, not a speed path.
