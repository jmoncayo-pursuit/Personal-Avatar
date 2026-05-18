# First Recording Guide

This guide describes the fastest, most reliable path to capture and prepare a high-fidelity reference audio recording for zero-shot voice cloning.

---

## 1. Acoustic and Recording Setup

* **Silent Environment**: Choose the quietest, soft-furnished room available (e.g., a room with carpets, curtains, and soft furniture to absorb sound reflection).
* **Hardware**: Wired earbuds or a high-quality laptop microphone are fully sufficient. Avoid using bluetooth microphones due to compression artifacts.
* **Cadence**: Speak slightly slower, calmer, and clearer than your average conversational speed.
* **Isolation**: Ensure no background clicks, music, fan hums, or notification sounds are captured.

---

## 2. Scripting Your Reference Clip

For the best results with `F5-TTS`, aim for a clean, single-take recording of approximately **3 to 7 seconds** (containing about 8 to 15 words).

### Proposed Generic Script
> *"Hey there! I am recording my voice to build a digital clone."*

---

## 3. Preparing the Audio for cloning

Save your raw microphone recording to a directory (e.g., `data/voice_refs/raw_take_01.m4a`). 

Run the preparation pipeline to trim silences, convert to mono, and normalize loudness to standard LUFS targets:

```bash
avatar-clone prep-audio \
  --input data/voice_refs/raw_take_01.m4a \
  --output data/voice_refs/prepared/voice.wav
```

This utility performs:
1. **Silence Trimming**: Deletes dead air at the beginning and end of the recording.
2. **Mono Downmixing**: Combines stereo channels to mono.
3. **Loudness Normalization**: Targets standard integrated LUFS for clean transformer input.

---

## 4. Staging the Reference Transcript

Beside your prepared `voice.wav`, stage a matching text file containing the exact transcription of the spoken words:

* File: `data/voice_refs/prepared/voice.txt`
* Content: `Hey there! I am recording my voice to build a digital clone.`

Ensure the text file matches your spoken pronunciation exactly.

---

## 5. Staging Your Portrait Stills

Stage a clean, front-facing neutral portrait image (e.g., `data/portraits/portrait.png`) to serve as the visual baseline for talking-head rendering.
