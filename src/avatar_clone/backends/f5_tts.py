from __future__ import annotations

import json
from pathlib import Path

from ..config import BackendConfig
from ..utils import ensure_parent, resolve_optional_path, run_command


def run_f5_tts(
    backend: BackendConfig,
    *,
    base_dir: Path,
    text: str,
    ref_audio: Path,
    ref_text: str,
    output_file: Path,
    speed: float = 1.0,
) -> Path:
    if not backend.python:
        raise RuntimeError("The f5_tts backend is missing a configured Python interpreter.")

    python_path = resolve_optional_path(backend.python, base_dir=base_dir)
    if python_path is None:
        raise RuntimeError("Could not resolve the configured f5_tts Python path.")

    # Split text into sentences for sentence-by-sentence F5-TTS synthesis to prevent attention-window looping artifacts
    import re
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    if not sentences:
        sentences = [text]

    import random
    import wave

    ensure_parent(output_file)
    temp_files = []
    
    try:
        # Synthesize each sentence chunk independently
        for idx, sentence in enumerate(sentences):
            temp_chunk = output_file.parent / f"{output_file.stem}_chunk_{idx}.wav"
            temp_files.append(temp_chunk)
            
            seed = random.randint(0, 2147483647)
            script = f"""
from f5_tts.api import F5TTS
import json

f5tts = F5TTS()
f5tts.infer(
    ref_file={json.dumps(str(ref_audio.resolve()))},
    ref_text={json.dumps(ref_text)},
    gen_text={json.dumps(sentence)},
    file_wave={json.dumps(str(temp_chunk.resolve()))},
    speed={speed},
    seed={seed},
)
"""
            run_command([str(python_path), "-c", script], env_overrides=backend.env)
            if not temp_chunk.exists():
                raise RuntimeError(f"F5-TTS failed to create chunk {idx} for sentence: '{sentence}'")
        
        # Concatenate the audio chunks with a natural 0.25-second silent pause between sentences
        with wave.open(str(temp_files[0]), 'rb') as f:
            params = f.getparams()
            sample_rate = f.getframerate()
        
        silence_bytes = b"\x00" * int(sample_rate * 0.25 * 2) # 16-bit PCM mono
        
        with wave.open(str(output_file), 'wb') as out:
            out.setparams(params)
            for idx, infile in enumerate(temp_files):
                if idx > 0:
                    out.writeframes(silence_bytes)
                with wave.open(str(infile), 'rb') as f:
                    out.writeframes(f.readframes(f.getnframes()))
                    
    finally:
        # Clean up temporary chunk files safely
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass

    if not output_file.exists():
        raise RuntimeError(f"F5-TTS finished without creating {output_file}")

    return output_file
