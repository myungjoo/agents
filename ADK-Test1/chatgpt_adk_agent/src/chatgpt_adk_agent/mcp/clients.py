"""MCP 클라이언트 레지스트리 구현.

실제 MCP 서버 연결을 우선 시도하되, 파이썬 클라이언트가 설치되지 않은 경우
로컬 파일 시스템 기반의 폴백 검색을 제공합니다.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Iterable, List, Optional

from ..config import MCPServerSettings

try:
    from modelcontextprotocol.client.stdio import StdioClient  # type: ignore
except ImportError:  # pragma: no cover - 선택적 의존성
    StdioClient = None  # type: ignore


class MCPClientRegistry:
    """여러 MCP 서버에 대한 검색 인터페이스."""

    def __init__(self, configs: Iterable[MCPServerSettings]) -> None:
        self._configs = {cfg.name: cfg for cfg in configs}
        self._clients: dict[str, object] = {}

    def search(self, query: str, *, limit: int = 5, server: Optional[str] = None) -> str:
        """주어진 쿼리에 대한 검색 결과를 문자열 형태로 반환한다."""

        configs = (
            [self._configs[server]] if server else self._configs.values()
        )

        outputs: List[str] = []
        for cfg in configs:
            try:
                outputs.extend(self._search_with_config(cfg, query, limit))
            except Exception as exc:  # pragma: no cover - 런타임 경로
                outputs.append(f"[{cfg.name}] 검색 실패: {exc}")

        if not outputs:
            return "검색 결과가 없습니다."

        unique = []
        seen = set()
        for item in outputs:
            if item not in seen:
                unique.append(item)
                seen.add(item)
            if len(unique) == limit:
                break
        return "\n".join(unique)

    # ------------------------------------------------------------------
    # 내부 구현
    # ------------------------------------------------------------------
    def _search_with_config(
        self, cfg: MCPServerSettings, query: str, limit: int
    ) -> List[str]:
        if StdioClient:
            client = self._ensure_client(cfg)
            return self._search_via_mcp(client, query, limit)
        return self._fallback_filesystem_search(cfg, query, limit)

    def _ensure_client(self, cfg: MCPServerSettings):  # pragma: no cover - MCP 설치 시 실행
        client = self._clients.get(cfg.name)
        if client:
            return client

        if cfg.transport != "stdio":
            raise RuntimeError(
                f"현재는 stdio 기반 MCP 서버만 지원합니다: {cfg.transport}"
            )

        if not StdioClient:
            raise RuntimeError("modelcontextprotocol 패키지가 필요합니다.")

        command = [cfg.command, *cfg.args]
        client = StdioClient(command=command)
        self._clients[cfg.name] = client
        return client

    def _search_via_mcp(self, client, query: str, limit: int) -> List[str]:  # pragma: no cover
        """실제 MCP 서버로 검색을 위임한다."""

        response = client.request(
            "search",
            {
                "query": query,
                "limit": limit,
            },
        )
        items = response.get("items", [])
        formatted = []
        for item in items[:limit]:
            location = item.get("location", "(unknown)")
            snippet = item.get("snippet", "")
            formatted.append(f"[{location}] {snippet}")
        return formatted

    def _fallback_filesystem_search(
        self, cfg: MCPServerSettings, query: str, limit: int
    ) -> List[str]:
        """MCP 클라이언트가 없을 때의 폴백 구현."""

        root = self._extract_root(cfg) or Path.cwd()
        matches: List[str] = []

        queue = deque([root])
        while queue and len(matches) < limit:
            current = queue.popleft()
            for path in current.iterdir():
                if path.is_dir():
                    queue.append(path)
                elif query.lower() in path.name.lower():
                    matches.append(f"[{cfg.name}] {path}")
                    if len(matches) >= limit:
                        break

        return matches

    @staticmethod
    def _extract_root(cfg: MCPServerSettings) -> Optional[Path]:
        if "--root" in cfg.args:
            try:
                idx = cfg.args.index("--root")
                return Path(cfg.args[idx + 1]).resolve()
            except (ValueError, IndexError):
                return None
        return None
