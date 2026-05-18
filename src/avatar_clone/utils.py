from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess
from typing import Iterable


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def looks_unconfigured(value: str | None) -> bool:
    if value is None:
        return False
    return value.startswith("/ABSOLUTE/PATH/TO/")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def resolve_optional_path(raw: str | None, *, base_dir: Path) -> Path | None:
    if raw is None:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def find_newest_file(root: Path, patterns: Iterable[str]) -> Path | None:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(root.rglob(pattern))
    if not matches:
        return None
    return max(matches, key=lambda item: item.stat().st_mtime)


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env_overrides: dict[str, str] | None = None,
) -> None:
    env = os.environ.copy()
    env.pop("PYTHONHASHSEED", None)  # F5-TTS sets this; it can crash other Python runtimes
    if env_overrides:
        env.update(env_overrides)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def run_command_capture(
    command: list[str],
    *,
    cwd: Path | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, check=True)


def check_binary(name: str) -> str | None:
    return shutil.which(name)


def mux_audio(video_path: Path, audio_path: Path, output_path: Path) -> None:
    ensure_parent(output_path)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-shortest",
            str(output_path),
        ]
    )
