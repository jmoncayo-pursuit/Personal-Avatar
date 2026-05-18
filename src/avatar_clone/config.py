from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass(slots=True)
class BackendConfig:
    name: str
    kind: str
    python: str
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    extra_args: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AppConfig:
    source_path: Path
    defaults: dict[str, str]
    backends: dict[str, BackendConfig]

    @property
    def base_dir(self) -> Path:
        return self.source_path.parent

    def get_backend(self, name: str) -> BackendConfig:
        try:
            return self.backends[name]
        except KeyError as exc:
            known = ", ".join(sorted(self.backends))
            raise KeyError(f"Unknown backend '{name}'. Known backends: {known}") from exc


def load_config(path: Path) -> AppConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    backends = {
        name: BackendConfig(
            name=name,
            kind=payload["kind"],
            python=payload["python"],
            cwd=payload.get("cwd"),
            env=payload.get("env", {}),
            extra_args=payload.get("extra_args", []),
        )
        for name, payload in data["backends"].items()
    }
    return AppConfig(source_path=path, defaults=data["defaults"], backends=backends)
