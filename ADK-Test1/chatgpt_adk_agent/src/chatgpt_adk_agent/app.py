"""ChatGPT ADK Agent 애플리케이션 엔트리포인트."""

from __future__ import annotations

import importlib
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .a2a import A2AClient
from .config import Settings, require_api_key
from .llm import ChatGPTClient
from .mcp import MCPClientRegistry


class ChatGPTAgentApplication:
    """ADK 기반 ChatGPT 에이전트 실행기."""

    def __init__(self, settings: Settings) -> None:
        require_api_key(settings)
        self.settings = settings
        self.console = Console()
        self.chatgpt = ChatGPTClient(
            api_key=settings.chatgpt.api_key, model=settings.chatgpt.model
        )
        self.mcp_registry = MCPClientRegistry(settings.mcp_servers)
        self.a2a_client = A2AClient(settings.a2a)
        self._runtime = self._build_adk_runtime()

    # ------------------------------------------------------------------
    # ADK 통합
    # ------------------------------------------------------------------
    def _build_adk_runtime(self):
        """Google ADK 런타임을 구성한다."""

        try:
            adk = importlib.import_module("google_gemini_agents")
            tools_mod = importlib.import_module("google_gemini_agents.tools")
        except ImportError as exc:
            raise ImportError(
                "google-gemini-agents 패키지를 설치해야 ADK 기능을 사용할 수 있습니다."
            ) from exc

        builder_cls = getattr(adk, "AgentBuilder", None)
        runtime_cls = getattr(adk, "AgentRuntime", None)
        function_tool_cls = getattr(tools_mod, "FunctionTool", None)

        if not all([builder_cls, runtime_cls, function_tool_cls]):
            raise RuntimeError(
                "설치된 ADK 버전에서 필요한 클래스(AgentBuilder, AgentRuntime, FunctionTool)를 찾을 수 없습니다."
            )

        builder = builder_cls(
            name="chatgpt-adk-agent",
            instructions=(
                "당신은 ChatGPT를 주 에이전트로 활용하는 조정자입니다. "
                "사용자 질문에 가장 적합한 도구를 사용하고, 필요 시 ChatGPT 응답을 반환하세요."
            ),
            model="gemini-1.5-flash",
        )

        builder.add_tool(
            function_tool_cls(
                name="chatgpt_responder",
                description="ChatGPT API를 호출하여 자연어 응답을 생성합니다.",
                func=self._chatgpt_tool,
            )
        )

        builder.add_tool(
            function_tool_cls(
                name="local_file_search",
                description="MCP 서버를 통해 로컬 파일 시스템에서 정보를 검색합니다.",
                func=self._mcp_search_tool,
            )
        )

        if self.a2a_client.enabled():
            builder.add_tool(
                function_tool_cls(
                    name="call_peer_agent",
                    description="다른 AI 에이전트에 A2A 요청을 전송합니다.",
                    func=self._a2a_tool,
                )
            )

        agent = builder.build()
        return runtime_cls(agent)

    # ------------------------------------------------------------------
    # 도구 구현부
    # ------------------------------------------------------------------
    def _chatgpt_tool(self, prompt: str, system: Optional[str] = None) -> str:
        return self.chatgpt.complete(prompt, system=system)

    def _mcp_search_tool(
        self, query: str, limit: int = 5, server: Optional[str] = None
    ) -> str:
        return self.mcp_registry.search(query=query, limit=limit, server=server)

    def _a2a_tool(self, agent: str, message: str) -> str:
        payload = {"message": message}
        response = self.a2a_client.request(agent, payload)
        return str(response)

    # ------------------------------------------------------------------
    # 실행 루프
    # ------------------------------------------------------------------
    def run_cli(self) -> None:
        self.console.print(
            Panel(
                "ChatGPT ADK Agent CLI\n종료하려면 `exit` 혹은 Ctrl+C를 입력하세요.",
                title="ADK-Test1",
            )
        )

        while True:
            try:
                prompt = Prompt.ask("사용자")
            except (EOFError, KeyboardInterrupt):
                self.console.print("\n[bold yellow]세션을 종료합니다.")
                break

            if prompt.strip().lower() in {"exit", "quit"}:
                self.console.print("[bold yellow]세션을 종료합니다.")
                break

            answer = self.handle_prompt(prompt)
            self.console.print(Panel(answer, title="에이전트"))

    def handle_prompt(self, prompt: str) -> str:
        if self._runtime is None:
            return "ADK 런타임이 초기화되지 않았습니다. 설치를 확인해주세요."

        try:
            result = self._runtime.run(prompt)
        except Exception as exc:  # pragma: no cover - 런타임 경로
            return f"에이전트 실행 중 오류가 발생했습니다: {exc}"

        if isinstance(result, str):
            return result

        # ADK의 반환 객체에 따라 텍스트 추출을 시도한다.
        for attr in ("output", "text", "content", "message"):
            value = getattr(result, attr, None)
            if isinstance(value, str):
                return value
        return str(result)
