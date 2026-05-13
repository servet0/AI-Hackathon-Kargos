"""
Chat (Sohbet) Pydantic şemaları.

AI Agent ile iletişim için request/response modelleri.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Kullanıcı mesajı isteği."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Kullanıcının doğal dilde yazdığı mesaj",
        examples=[
            "SIP-2026-0001 numaralı siparişim ne durumda?",
            "128 numaralı siparişim ne alemde?",
            "Kargom nerede?",
        ],
    )


class ChatResponse(BaseModel):
    """AI Agent yanıtı."""

    response: str = Field(
        description="AI Agent tarafından üretilen doğal dil yanıtı"
    )
    agent_mode: str = Field(
        description="Ajanın çalışma modu: 'llm' veya 'fallback'"
    )
