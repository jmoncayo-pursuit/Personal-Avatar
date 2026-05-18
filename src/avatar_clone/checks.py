from __future__ import annotations

from pathlib import Path

from .config import load_config
from .utils import check_binary, looks_unconfigured, resolve_optional_path


def build_doctor_report(config_path: Path) -> str:
    lines: list[str] = []

    lines.append("System tools")
    for tool in ("git", "ffmpeg", "uv"):
        resolved = check_binary(tool)
        status = resolved if resolved else "missing"
        lines.append(f"- {tool}: {status}")

    lines.append("")
    lines.append(f"Config: {config_path}")
    if not config_path.exists():
        lines.append("- status: missing")
        return "\n".join(lines)

    config = load_config(config_path)
    lines.append("- status: found")
    lines.append("")
    lines.append("Backends")

    for backend_name in sorted(config.backends):
        backend = config.backends[backend_name]
        lines.append(f"- {backend.name} ({backend.kind})")

        if looks_unconfigured(backend.python):
            lines.append("  python: placeholder")
        else:
            python_path = resolve_optional_path(backend.python, base_dir=config.base_dir)
            assert python_path is not None
            lines.append(f"  python: {'ok' if python_path.exists() else 'missing'} -> {python_path}")

        if backend.cwd is None:
            lines.append("  cwd: not required")
        elif looks_unconfigured(backend.cwd):
            lines.append("  cwd: placeholder")
        else:
            cwd_path = resolve_optional_path(backend.cwd, base_dir=config.base_dir)
            assert cwd_path is not None
            lines.append(f"  cwd: {'ok' if cwd_path.exists() else 'missing'} -> {cwd_path}")

        if backend.env:
            env_keys = ", ".join(sorted(backend.env))
            lines.append(f"  env: {env_keys}")
        else:
            lines.append("  env: none")

    return "\n".join(lines)
