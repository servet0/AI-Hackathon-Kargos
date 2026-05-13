"""
Chat (Sohbet) API endpoint'i.

Kullanıcıların doğal dille sipariş sorgulama yapabildiği
AI Agent entegrasyonu bu router üzerinden sunulur.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_agent import ai_agent

router = APIRouter(
    prefix="/chat",
    tags=["AI Asistan"],
)


@router.post(
    "/",
    response_model=ChatResponse,
    summary="AI Asistan ile sohbet",
    description=(
        "Kullanıcının doğal dilde yazdığı mesajı AI Agent'a iletir. "
        "Agent, mesajdan sipariş numarasını çıkarır, veritabanında sorgular "
        "ve müşteriye doğal dilde yanıt üretir."
    ),
    responses={
        200: {
            "description": "AI Agent yanıtı",
            "content": {
                "application/json": {
                    "examples": {
                        "siparis_bulundu": {
                            "summary": "Sipariş bulundu",
                            "value": {
                                "response": (
                                    "Merhaba! SIP-2026-0001 numaralı "
                                    "siparişiniz kargoya verilmiştir. "
                                    "Takip No: TR123456789"
                                ),
                                "agent_mode": "llm",
                            },
                        },
                        "numara_yok": {
                            "summary": "Sipariş numarası verilmedi",
                            "value": {
                                "response": (
                                    "Merhaba! Size yardımcı olabilmem "
                                    "için sipariş numaranıza ihtiyacım var."
                                ),
                                "agent_mode": "fallback",
                            },
                        },
                    }
                }
            },
        }
    },
)
async def chat_with_agent(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Kullanıcı mesajını AI Agent ile işle."""
    response_text = await ai_agent.process_message(request.message, db)

    return ChatResponse(
        response=response_text,
        agent_mode="llm" if ai_agent.is_llm_available else "fallback",
    )
