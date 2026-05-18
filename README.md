# Personal Avatar Clone 🎥🎙️

A local-first, privacy-respecting pipeline for generating perfectly lip-synced, high-definition digital clones on Apple Silicon. This repository integrates a non-autoregressive flow-matching voice synthesizer (`F5-TTS`) with an audio-driven talking-head animator (`SadTalker`), optimized for macOS architectures.

---

## Key Features & Architecture

* **100% Offline & Private**: All data processing, audio synthesis, and neural convolutions execute locally on your machine. Absolutely zero data is sent to external clouds or third-party APIs.
* **Stable Attention Windows**: Standard flow-matching voice models loop at long text contexts. This platform integrates a **Sentence-Level Audio Chunking Engine** that splits input texts at sentence boundaries, synthesizes independent vocal segments, and stitches them with a natural 0.25-second silent cadence pause to eliminate all word looping or attention drift.
* **Apple Silicon Optimized Convolutions**: Bound multi-threading constraints (`OMP_NUM_THREADS = 4` / `MKL_NUM_THREADS = 4`) eliminate lock congestion, running face animation restoration at a stable **~25.60 seconds per frame** on macOS CPU.
* **GFPGAN HD Face Restoration**: Integrated Generative Facial Prior GAN upscales facial structures, delivering crisp, high-definition output videos.

---

## Recommended Stack

### Default Core Stack
* **Voice Synthesis**: `F5-TTS` (Flow-Matching Transformer).
* **Talking-Head Animation**: `SadTalker` (with default `gfpgan` HD restoration).

### Target Performance Metrics (Apple Silicon CPU)
* **Voice Cloning Step**: ~30–40 seconds of generation time for a 5-second sentence.
* **Video Animation Step**: ~25.6 seconds per frame (25 FPS).
  * **5-Second Video (125 frames)** ≈ **53 minutes**
  * **12-Second Video (300 frames)** ≈ **2.1 hours**
  * **30-Second Video (750 frames)** ≈ **5.3 hours**

---

## Project Structure

* [docs/setup_mac.md](docs/setup_mac.md): Step-by-step walk-through for setting up isolated backend Python interpreters on macOS.
* [docs/capture_guide.md](docs/capture_guide.md): Photographic and acoustic protocols for pristine reference media.
* [docs/first_recording.md](docs/first_recording.md): Scripting and cadence strategies for training-ready voice cloning.
* [avatar.config.example.json](avatar.config.example.json): Configuration template with relative virtual-environment pointers.

---

## Quick Start

### 1. Initialize the Controller Environment
Clone the repository and install the packaged command-line controller in an isolated virtual environment:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

### 2. Clone Upstream Repositories
Bootstrap the official external repositories into the local `external/` folder:

```bash
avatar-clone bootstrap
```

### 3. Create Backend Virtual Environments
F5-TTS and SadTalker require different Python versions and package indices. Follow the detailed [macOS Virtual Environment Guide](docs/setup_mac.md) to set them up:
* **F5-TTS Environment**: Python `3.11`
* **SadTalker Environment**: Python `3.8`

### 4. Configure Local Paths
Copy the provided config template and edit it to map your local virtual environment Python interpreters:

```bash
cp avatar.config.example.json avatar.config.json
```
Open `avatar.config.json` and verify the `"python"` key paths point to the correct active virtual environments. Note: `avatar.config.json` is strictly gitignored to keep your system directories private.

### 5. Validate System Integrity
Run the diagnostic check to ensure all models, configurations, and backend scripts are fully prepared:

```bash
avatar-clone doctor
```

### 6. Launch the Studio Web UI
Launch the interactive web UI:

```bash
avatar-clone ui
```
Open [http://127.0.0.1:7861](http://127.0.0.1:7861) in your browser. The interface features a premium glassmorphic dark theme and a step-by-step wizard.

---

## Command Line Usage

### A. Prep reference audio
Clean and normalize a raw microphone recording into an optimized, clone-ready WAV file:

```bash
avatar-clone prep-audio \
  --input data/voice_refs/raw_recording.m4a \
  --output data/voice_refs/prepared/voice.wav
```

### B. Generate Voice Only
Generate cloned speech from target text:

```bash
avatar-clone render-voice \
  --text "Hi, this is Jean. I am excited to demonstrate my new digital avatar clone." \
  --ref-audio data/voice_refs/prepared/voice.wav \
  --ref-text "Hey there! My name is Jean." \
  --output data/outputs/cloned_speech.wav
```

### C. Execute End-to-End Pipeline
Go from text directly to high-definition voice and lip-synced talking-head video:

```bash
avatar-clone pipeline \
  --text "Hi, this is Jean. I am excited to demonstrate my new digital avatar clone." \
  --ref-audio data/voice_refs/prepared/voice.wav \
  --ref-text "Hey there! My name is Jean." \
  --source-image data/portraits/uploads/portrait.png \
  --output-dir data/outputs/runs/my_avatar
```

---

## Timbre & Style Cloning Protocols (Crucial for F5-TTS)

To avoid hallucinations, repeating phrases, or context matrix collapse:
1. **Pristine Reference Context**: Use a reference audio file between **3 and 5 seconds** long (ideal: *"Hey there! My name is Jean."*).
2. **Matching Transcript**: Ensure the reference transcript perfectly matches the exact words spoken in the reference recording.
3. **No Background Noise**: Perform recordings in a silent room. Flow-matching transformers will replicate any background hiss, click, or room reverb across the entire synthesized speech timeline.
