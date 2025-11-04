"""애플리케이션 설정 로더."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import tomllib
from pydantic import AnyHttpUrl, BaseModel, Field, ValidationError


_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = _ROOT / "config" / "settings.toml"


class ChatGPTSettings(BaseModel):
    """ChatGPT(OpenAI) 관련 설정."""

    api_key: str = Field(min_length=1, description="OpenAI API 키")
    model: str = Field(default="gpt-4.1-mini", description="사용할 ChatGPT 모델 ID")


class MCPServerSettings(BaseModel):
    """MCP 서버 연결 설정."""

    name: str = Field(min_length=1)
    transport: str = Field(default="stdio")
    command: str = Field(min_length=1)
    args: List[str] = Field(default_factory=list)


class A2ASettings(BaseModel):
    """A2A(Agent-to-Agent) 상호작용 설정."""

    base_url: AnyHttpUrl
    timeout_seconds: int = Field(default=30, ge=1, le=600)


class Settings(BaseModel):
    """전체 애플리케이션 설정."""

    chatgpt: ChatGPTSettings
    mcp_servers: List[MCPServerSettings] = Field(default_factory=list)
    a2a: Optional[A2ASettings] = None

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        config_path = path or DEFAULT_CONFIG_PATH
        if not config_path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")

        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
        try:
            return cls.model_validate(raw)
        except ValidationError as exc:
            raise ValueError(f"설정 파일이 유효하지 않습니다: {exc}") from exc


def require_api_key(settings: Settings) -> None:
    """필수 입력을 검증한다."""

    if not settings.chatgpt.api_key:
        raise RuntimeError(
            "ChatGPT API 키가 설정되어 있지 않습니다. config/settings.toml 파일을 확인하세요."
        )
