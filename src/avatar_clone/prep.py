from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .utils import check_binary, ensure_parent, run_command, run_command_capture


@dataclass(slots=True)
class AudioPrepResult:
    input_path: Path
    output_path: Path
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None


def _require_media_tools() -> None:
    missing = [tool for tool in ("ffmpeg", "ffprobe") if check_binary(tool) is None]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(f"Missing required media tool(s): {names}")


def _probe_audio(path: Path) -> tuple[float | None, int | None, int | None]:
    completed = run_command_capture(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-print_format",
            "json",
            str(path),
        ]
    )
    payload = json.loads(completed.stdout)
    streams = payload.get("streams", [])
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    format_info = payload.get("format", {})

    duration_raw = format_info.get("duration")
    duration = float(duration_raw) if duration_raw is not None else None

    sample_rate_raw = audio_stream.get("sample_rate")
    sample_rate = int(sample_rate_raw) if sample_rate_raw is not None else None

    channels_raw = audio_stream.get("channels")
    channels = int(channels_raw) if channels_raw is not None else None

    return duration, sample_rate, channels


def prepare_reference_audio(
    input_path: Path,
    output_path: Path,
    *,
    trim_silence: bool = True,
    target_sample_rate: int = 24_000,
    loudness_lufs: float = -18.0,
) -> AudioPrepResult:
    _require_media_tools()
    ensure_parent(output_path)

    filters: list[str] = []
    if trim_silence:
        # Trim only the outer edges. A single silenceremove pass can over-trim
        # natural pauses inside speech, so we trim the front, reverse, trim
        # the new front, then reverse back.
        filters.extend(
            [
                "silenceremove=start_periods=1:start_silence=0.15:start_threshold=-45dB",
                "areverse",
                "silenceremove=start_periods=1:start_silence=0.25:start_threshold=-45dB",
                "areverse",
            ]
        )
    filters.append(f"loudnorm=I={loudness_lufs}:TP=-1.5:LRA=11")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(target_sample_rate),
        "-c:a",
        "pcm_s16le",
    ]
    if filters:
        command.extend(["-af", ",".join(filters)])
    command.append(str(output_path))
    run_command(command)

    duration, sample_rate, channels = _probe_audio(output_path)
    return AudioPrepResult(
        input_path=input_path,
        output_path=output_path,
        duration_seconds=duration,
        sample_rate=sample_rate,
        channels=channels,
    )


def format_audio_prep_report(result: AudioPrepResult) -> str:
    lines = [
        f"input={result.input_path}",
        f"output={result.output_path}",
        f"duration_seconds={result.duration_seconds:.2f}" if result.duration_seconds is not None else "duration_seconds=unknown",
        f"sample_rate={result.sample_rate}" if result.sample_rate is not None else "sample_rate=unknown",
        f"channels={result.channels}" if result.channels is not None else "channels=unknown",
    ]

    if result.duration_seconds is not None:
        if result.duration_seconds < 8:
            lines.append("note=clip is usable but short; aim for 10-20 seconds for a stronger first clone")
        elif result.duration_seconds > 25:
            lines.append("note=clip is longer than needed for the first pass; 10-20 seconds is the sweet spot")
        else:
            lines.append("note=clip length is in the sweet spot for a first-pass clone")

    if result.channels not in (None, 1):
        lines.append("note=reference was converted to mono")

    return "\n".join(lines)
