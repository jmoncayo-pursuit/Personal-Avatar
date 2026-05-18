# macOS Environment Setup Guide

This project is built around isolated virtual environments for each specialized machine learning backend. Under macOS, keeping these runtimes isolated ensures package dependency conflicts (e.g., between older PyTorch pins and modern transformers) do not compromise platform stability.

---

## Prerequisites

Before starting, ensure you have the following package managers and utilities installed:
* **uv**: A high-performance Python package installer and virtual environment manager.
* **ffmpeg**: Audio-video compression and decoding utility.
* **git**: Version control.

---

## 1. Upstream Repository Clones

From the repository root, download the official external backend repositories:

```bash
avatar-clone bootstrap
```

This will clone the required projects into:
* `external/F5-TTS`
* `external/SadTalker`

---

## 2. Voice Environment (`F5-TTS`)

F5-TTS requires Python `>=3.10` and works natively with Apple Silicon. We standardize on Python `3.11`:

```bash
uv python install 3.11
uv venv .envs/f5-tts --python 3.11
uv pip install --python .envs/f5-tts/bin/python torch torchaudio
uv pip install --python .envs/f5-tts/bin/python -e external/F5-TTS
```

### Warmup weights download (Optional)
To download and cache the pretrained checkpoints before your first render:

```bash
.envs/f5-tts/bin/python -c "from f5_tts.api import F5TTS; F5TTS(device='cpu')"
```

---

## 3. Video Environment (`SadTalker`)

SadTalker operates stably under Python `3.8`. 

```bash
uv python install 3.8
uv venv .envs/sadtalker --python 3.8
uv pip install --python .envs/sadtalker/bin/python torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
LMDB_FORCE_CFFI=1 uv pip install --python .envs/sadtalker/bin/python -r external/SadTalker/requirements.txt
uv pip install --python .envs/sadtalker/bin/python dlib
```

*Note: `LMDB_FORCE_CFFI=1` is required to avoid building errors during native compilation of the lmdb bindings on Apple Silicon.*

### Downloading Model Weights

Download the required model releases and place them under the `external/SadTalker/` path:

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

---

## 4. Configuring Environment Paths

Copy the example configuration to your active local configuration:

```bash
cp avatar.config.example.json avatar.config.json
```

Open `avatar.config.json` and replace the placeholder executable locations with the paths to your local virtual environments:

* `f5_tts.python` -> `.envs/f5-tts/bin/python`
* `sadtalker.python` -> `.envs/sadtalker/bin/python`
* `sadtalker.cwd` -> `external/SadTalker`

*(You can use absolute paths to your local project directory if needed.)*

---

## 5. Diagnostic Validation

Run the diagnostic utility to verify all dependencies and paths are mapped perfectly:

```bash
avatar-clone doctor
```

Once all checklist status indicators are resolved, launch the studio UI:

```bash
avatar-clone ui
```
Open [http://127.0.0.1:7861](http://127.0.0.1:7861) in your browser.
