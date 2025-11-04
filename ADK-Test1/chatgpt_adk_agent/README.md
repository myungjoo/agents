## ChatGPT ADK Agent

이 프로젝트는 Google Agent Development Kit(ADK)를 기반으로 ChatGPT 인스턴스를 구동하고, Model Context Protocol(MCP) 서버를 통해 로컬 파일 검색 기능을 제공하며, Agent-to-Agent(A2A) 호출을 통해 다른 AI 에이전트와 협업할 수 있는 Python 애플리케이션입니다.

> ⚠️ TODO 주석과 `<PLACEHOLDER>` 형태로 표시된 값은 실제 환경에 맞게 반드시 수정하세요.

### 주요 기능
- **ChatGPT 통합**: OpenAI ChatGPT API를 ADK 에이전트 내에서 직접 사용합니다.
- **MCP 연동**: MCP 서버를 통해 로컬 파일 시스템 등 외부 리소스에 접근할 수 있습니다.
- **A2A 상호작용**: HTTP A2A 어댑터를 통해 다른 에이전트에게 작업을 위임하거나 결과를 요청할 수 있습니다.

### 빠른 시작
1. 저장소 루트에서 ADK 프로젝트 디렉터리로 이동합니다.
   ```bash
   cd ADK-Test1/chatgpt_adk_agent
   ```
2. 가상환경을 만들고 의존성을 설치합니다.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -U pip
   pip install -e .
   ```
3. `config/settings.toml` 파일을 열어 TODO 표시가 있는 값을 실제 환경에 맞게 채웁니다.
   ```toml
   [chatgpt]
   # TODO: OpenAI ChatGPT API 키
   api_key = "<YOUR_OPENAI_API_KEY>"
   # TODO: 모델을 변경해야 한다면 수정하세요.
   model = "gpt-4.1-mini"

   [[mcp_servers]]
   # TODO: MCP 서버 설정 확인
   name = "local-files"
   transport = "stdio"
   command = "python"
   args = ["-m", "chatgpt_adk_agent.mcp.local_file_server", "--root", "<PATH_TO_SEARCH>"]

   [a2a]
   # TODO: A2A 엔드포인트 URL을 환경에 맞게 수정하세요.
   base_url = "http://localhost:8080"
   ```
4. CLI로 에이전트를 실행합니다.
   ```bash
   chatgpt-adk-agent
   ```

### MCP 로컬 파일 서버 실행
로컬 파일 검색을 위해 예제 MCP 서버를 제공합니다.
```bash
python -m chatgpt_adk_agent.mcp.local_file_server --root /workspace
```

### 테스트
```bash
pytest
```

### 참고 자료
- [Google Agent Development Kit](https://ai.google.dev/agent) 문서
- [Model Context Protocol](https://github.com/modelcontextprotocol) 사양
- [OpenAI API Reference](https://platform.openai.com/docs)
