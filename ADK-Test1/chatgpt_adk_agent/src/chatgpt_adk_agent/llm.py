"""ChatGPT(OpenAI) 클라이언트 래퍼."""

from __future__ import annotations

from typing import List, Mapping, Optional

from openai import OpenAI


class ChatGPTClient:
    """ChatGPT API와 상호작용하기 위한 단순 래퍼."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(self, prompt: str, *, system: Optional[str] = None) -> str:
        """단일 프롬프트에 대한 ChatGPT 응답을 반환한다."""

        messages: List[Mapping[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        return response.choices[0].message.content or ""
