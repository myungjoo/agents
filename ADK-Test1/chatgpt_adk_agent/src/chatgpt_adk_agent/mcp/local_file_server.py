"""로컬 파일 검색을 위한 간단한 MCP 호환 서버 스켈레톤."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List


try:
    from modelcontextprotocol.server.stdio import StdioServer  # type: ignore
except ImportError:  # pragma: no cover - 선택적 의존성
    StdioServer = None  # type: ignore


@dataclass
class SearchResult:
    path: Path
    snippet: str


def _scan(root: Path, query: str, limit: int) -> List[SearchResult]:
    matches: List[SearchResult] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if query.lower() in path.name.lower():
            matches.append(SearchResult(path=path, snippet="파일명 일치"))
        elif path.suffix in {".txt", ".md", ".py", ".json", ".yaml", ".yml"}:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if query.lower() in text.lower():
                idx = text.lower().index(query.lower())
                start = max(0, idx - 40)
                end = min(len(text), idx + len(query) + 40)
                snippet = text[start:end].replace("\n", " ")
                matches.append(SearchResult(path=path, snippet=snippet))
        if len(matches) >= limit:
            break
    return matches


def run_stdio(root: Path, limit: int) -> None:  # pragma: no cover - 런타임 경로
    if not StdioServer:
        raise RuntimeError(
            "modelcontextprotocol 패키지가 설치되어 있어야 stdio 서버를 실행할 수 있습니다."
        )

    server = StdioServer(name="local-files")

    @server.tool("search")
    def search_tool(query: str, limit: int = limit):  # type: ignore[override]
        results = _scan(root, query, limit)
        return {
            "items": [
                {
                    "location": str(item.path),
                    "snippet": item.snippet,
                }
                for item in results
            ]
        }

    server.run()


def run_interactive(root: Path, limit: int) -> None:
    print(f"[INFO] '{root}' 경로에서 로컬 검색을 시작합니다. 종료하려면 Ctrl+C.")
    while True:
        try:
            query = input("검색어> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] 종료합니다.")
            return
        if not query:
            continue
        results = _scan(root, query, limit)
        if not results:
            print("  결과가 없습니다.")
            continue
        for item in results:
            print(f"  - {item.path}: {item.snippet[:120]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="로컬 파일 MCP 서버")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="검색 기준 경로")
    parser.add_argument("--limit", type=int, default=10, help="최대 검색 결과 수")
    parser.add_argument(
        "--mode",
        choices=["stdio", "interactive"],
        default="interactive",
        help="실행 모드",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root: Path = args.root.resolve()
    if not root.exists():
        raise SystemExit(f"루트 경로가 존재하지 않습니다: {root}")

    if args.mode == "stdio":
        run_stdio(root, args.limit)
    else:
        run_interactive(root, args.limit)


if __name__ == "__main__":
    main()
