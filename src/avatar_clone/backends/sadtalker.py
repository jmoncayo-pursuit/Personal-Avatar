from __future__ import annotations

from pathlib import Path

from ..config import BackendConfig
from ..utils import ensure_dir, find_newest_file, resolve_optional_path, run_command


def run_sadtalker(
    backend: BackendConfig,
    *,
    base_dir: Path,
    audio: Path,
    source_image: Path,
    output_dir: Path,
    enhancer: str | None = None,
) -> Path:
    python_path = resolve_optional_path(backend.python, base_dir=base_dir)
    cwd_path = resolve_optional_path(backend.cwd, base_dir=base_dir)
    if python_path is None or cwd_path is None:
        raise RuntimeError("SadTalker is not fully configured yet.")

    ensure_dir(output_dir)

    extra_args = list(backend.extra_args)
    if enhancer and enhancer != "None":
        extra_args.extend(["--enhancer", enhancer])
    
    # Optimize base resolution to 256 for rapid CPU rendering, relying on GFPGAN face enhancer for high-definition upscaling
    extra_args.extend(["--size", "256", "--expression_scale", "1.3", "--cpu"])

    command = [
        str(python_path),
        "inference.py",
        "--driven_audio",
        str(audio.resolve()),
        "--source_image",
        str(source_image.resolve()),
        "--result_dir",
        str(output_dir.resolve()),
        *extra_args,
    ]
    env = backend.env.copy() if backend.env else {}
    env["OMP_NUM_THREADS"] = "4"
    env["MKL_NUM_THREADS"] = "4"
    run_command(command, cwd=cwd_path, env_overrides=env)

    video = find_newest_file(output_dir, ("*.mp4",))
    if video is None:
        video = find_newest_file(cwd_path / "results", ("*.mp4",))
    if video is None:
        raise RuntimeError("SadTalker did not produce an mp4 file.")
    return video
