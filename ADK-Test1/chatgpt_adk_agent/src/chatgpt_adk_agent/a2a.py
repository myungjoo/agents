"""Agent-to-Agent(A2A) 헬퍼."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .config import A2ASettings


class A2AClient:
    """외부 에이전트와의 HTTP 상호작용을 위한 간단한 래퍼."""

    def __init__(self, settings: Optional[A2ASettings]) -> None:
        self._settings = settings
        self._client: Optional[httpx.Client] = None
        if settings:
            self._client = httpx.Client(timeout=settings.timeout_seconds)

    def enabled(self) -> bool:
        return self._client is not None

    def request(self, agent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._client or not self._settings:
            raise RuntimeError("A2A 기능이 비활성화되어 있습니다.")

        endpoint = f"{self._settings.base_url.rstrip('/')}/agents/{agent}/tasks"
        response = self._client.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        if self._client:
            self._client.close()

    def __enter__(self) -> "A2AClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
