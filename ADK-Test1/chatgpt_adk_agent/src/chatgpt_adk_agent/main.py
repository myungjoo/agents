"""커맨드라인 엔트리포인트."""

from __future__ import annotations

import argparse
from pathlib import Path

from .app import ChatGPTAgentApplication
from .config import Settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ChatGPT ADK Agent")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="사용할 설정 파일 경로 (기본값: config/settings.toml)",
    )
    return parser.parse_args()


def cli() -> None:
    args = parse_args()
    settings = Settings.load(args.config)
    app = ChatGPTAgentApplication(settings)
    app.run_cli()


if __name__ == "__main__":
    cli()
