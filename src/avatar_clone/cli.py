from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from .backends import run_f5_tts, run_sadtalker
from .checks import build_doctor_report
from .config import AppConfig, load_config
from .prep import format_audio_prep_report, prepare_reference_audio
from .utils import ensure_dir, timestamp_slug
from .webapp import launch_ui


REPO_URLS = {
    "F5-TTS": "https://github.com/SWivid/F5-TTS.git",
    "SadTalker": "https://github.com/OpenTalker/SadTalker.git",
}


def default_output_dir() -> Path:
    return Path("data/outputs") / "runs" / timestamp_slug()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="avatar-clone",
        description="Local-first controller for free voice and talking-head avatar backends.",
    )
    parser.add_argument(
        "--config",
        default="avatar.config.json",
        help="Path to the controller config file.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check tools, config, and backend paths.")

    bootstrap = subparsers.add_parser("bootstrap", help="Clone official backend repos locally.")
    bootstrap.add_argument("--dest", default="external", help="Where to clone the repos.")

    render_voice = subparsers.add_parser("render-voice", help="Generate cloned speech from text.")
    render_voice.add_argument("--voice-backend", default=None, help="Override the configured default voice backend.")
    render_voice.add_argument("--text", required=True, help="Text to speak.")
    render_voice.add_argument("--ref-audio", required=True, help="Reference speaker audio.")
    render_voice.add_argument("--ref-text", required=True, help="Transcript of the reference speaker audio.")
    render_voice.add_argument("--output", required=True, help="Output wav path.")

    prep_audio = subparsers.add_parser("prep-audio", help="Clean and normalize a raw recording into a clone-ready wav.")
    prep_audio.add_argument("--input", required=True, help="Raw source recording to prepare.")
    prep_audio.add_argument("--output", required=True, help="Prepared wav output path.")
    prep_audio.add_argument(
        "--keep-silence",
        action="store_true",
        help="Skip trimming silence from the start and end of the recording.",
    )
    prep_audio.add_argument(
        "--target-sr",
        type=int,
        default=24000,
        help="Output sample rate for the prepared wav.",
    )
    prep_audio.add_argument(
        "--loudness",
        type=float,
        default=-18.0,
        help="Integrated loudness target in LUFS.",
    )

    ui = subparsers.add_parser("ui", help="Launch a local web UI for prep and rendering.")
    ui.add_argument("--host", default="127.0.0.1", help="Host interface for the local UI.")
    ui.add_argument("--port", type=int, default=7861, help="Port for the local UI.")
    ui.add_argument("--debug", action="store_true", help="Run the UI server in debug mode.")

    render_video = subparsers.add_parser("render-video", help="Generate a talking-head video from audio.")
    render_video.add_argument("--video-backend", default=None, help="Override the configured default video backend.")
    render_video.add_argument("--audio", required=True, help="Input audio path.")
    render_video.add_argument("--source-image", required=True, help="Portrait image path.")
    render_video.add_argument("--output-dir", default=None, help="Where to save render outputs.")

    pipeline = subparsers.add_parser("pipeline", help="Go from text to voice to avatar video.")
    pipeline.add_argument("--voice-backend", default=None, help="Override the configured default voice backend.")
    pipeline.add_argument("--video-backend", default=None, help="Override the configured default video backend.")
    pipeline.add_argument("--text", required=True, help="Text to speak.")
    pipeline.add_argument("--ref-audio", required=True, help="Reference speaker audio.")
    pipeline.add_argument("--ref-text", required=True, help="Transcript of the reference speaker audio.")
    pipeline.add_argument("--source-image", required=True, help="Portrait image path.")
    pipeline.add_argument("--output-dir", default=None, help="Where to save render outputs.")

    for parser_obj in (render_voice, pipeline):
        parser_obj.add_argument("--voice-speed", type=float, default=1.0, help="Speaking speed multiplier (e.g. 0.85).")

    for parser_obj in (render_video, pipeline):
        parser_obj.add_argument("--enhancer", default="gfpgan", choices=["gfpgan", "RestoreFormer", "None"], help="Face enhancer model.")
        parser_obj.add_argument("--animation-region", default="all", choices=["all", "exp", "pose", "lip", "eyes"], help="The region where the animation is performed.")
        parser_obj.add_argument("--driving-multiplier", type=float, default=1.0, help="Scale multiplier for driving motion.")
        parser_obj.add_argument("--no-flag-stitching", action="store_true", help="Disable background stitching.")
        parser_obj.add_argument("--no-flag-pasteback", action="store_true", help="Disable pasting back the animated face.")

    return parser.parse_args(argv)


def load_app_config(path_str: str) -> AppConfig:
    path = Path(path_str).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    return load_config(path)


def clone_repo(url: str, destination: Path) -> None:
    if destination.exists():
        print(f"skip: {destination} already exists")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", url, str(destination)], check=True)
    print(f"cloned: {destination}")


def handle_bootstrap(args: argparse.Namespace) -> int:
    base_dest = Path(args.dest).resolve()
    clone_repo(REPO_URLS["F5-TTS"], base_dest / "F5-TTS")
    clone_repo(REPO_URLS["SadTalker"], base_dest / "SadTalker")
    return 0


def run_voice_from_args(config: AppConfig, args: argparse.Namespace, *, output_path: Path | None = None) -> Path:
    backend_name = args.voice_backend or config.defaults["voice"]
    backend = config.get_backend(backend_name)
    if backend.kind != "voice":
        raise RuntimeError(f"{backend_name} is not a voice backend.")

    target = output_path or Path(args.output).resolve()
    return run_f5_tts(
        backend,
        base_dir=config.base_dir,
        text=args.text,
        ref_audio=Path(args.ref_audio).resolve(),
        ref_text=args.ref_text,
        output_file=target,
        speed=getattr(args, "voice_speed", 1.0),
    )


def run_video_from_args(config: AppConfig, args: argparse.Namespace, *, audio_path: Path | None = None, output_dir: Path | None = None) -> Path:
    backend_name = args.video_backend or config.defaults["video"]
    backend = config.get_backend(backend_name)
    if backend.kind != "video":
        raise RuntimeError(f"{backend_name} is not a video backend.")

    resolved_output_dir = ensure_dir(output_dir or Path(args.output_dir or default_output_dir()).resolve())
    resolved_audio = audio_path or Path(args.audio).resolve()
    source_image = Path(args.source_image).resolve()

    if backend.name == "sadtalker":
        return run_sadtalker(
            backend,
            base_dir=config.base_dir,
            audio=resolved_audio,
            source_image=source_image,
            output_dir=resolved_output_dir,
            enhancer=getattr(args, "enhancer", None),
        )

    raise RuntimeError(f"No runner is implemented for video backend '{backend.name}'.")


def handle_render_voice(args: argparse.Namespace) -> int:
    config = load_app_config(args.config)
    audio_path = run_voice_from_args(config, args)
    print(audio_path)
    return 0


def handle_prep_audio(args: argparse.Namespace) -> int:
    result = prepare_reference_audio(
        Path(args.input).resolve(),
        Path(args.output).resolve(),
        trim_silence=not args.keep_silence,
        target_sample_rate=args.target_sr,
        loudness_lufs=args.loudness,
    )
    print(format_audio_prep_report(result))
    return 0


def handle_ui(args: argparse.Namespace) -> int:
    config = load_app_config(args.config)
    launch_ui(config, host=args.host, port=args.port, debug=args.debug)
    return 0


def handle_render_video(args: argparse.Namespace) -> int:
    config = load_app_config(args.config)
    video_path = run_video_from_args(config, args)
    print(video_path)
    return 0


def handle_pipeline(args: argparse.Namespace) -> int:
    config = load_app_config(args.config)
    output_dir = ensure_dir(Path(args.output_dir or default_output_dir()).resolve())
    audio_path = output_dir / "voice.wav"

    voice_path = run_voice_from_args(config, args, output_path=audio_path)
    video_path = run_video_from_args(config, args, audio_path=voice_path, output_dir=output_dir)

    print(f"voice={voice_path}")
    print(f"video={video_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.command == "doctor":
        config_path = Path(args.config).resolve()
        print(build_doctor_report(config_path))
        return 0

    if args.command == "bootstrap":
        return handle_bootstrap(args)

    if args.command == "render-voice":
        return handle_render_voice(args)

    if args.command == "prep-audio":
        return handle_prep_audio(args)

    if args.command == "ui":
        return handle_ui(args)

    if args.command == "render-video":
        return handle_render_video(args)

    if args.command == "pipeline":
        return handle_pipeline(args)

    raise RuntimeError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
