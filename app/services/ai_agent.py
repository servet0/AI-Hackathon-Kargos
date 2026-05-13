"""
Yapay Zeka Ajanı Servisi.

Müşteri mesajlarını analiz ederek sipariş takip bilgisi sağlar.
Groq API kullanarak doğal dil anlama ve yanıt üretme yapar.

Akış:
  1. Kullanıcı mesajından sipariş numarası/ID çıkarılır (LLM veya regex).
  2. Çıkarılan bilgi ile veritabanında sipariş sorgulanır.
  3. Sipariş bilgisi LLM'e verilerek doğal dilde yanıt üretilir.
  4. Sipariş bulunamazsa veya numara verilmemişse uygun yanıt döndürülür.
"""

import json
import logging
import os
import re
from dataclasses import dataclass

from groq import AsyncGroq
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.crud.orders import OrderCRUD
from app.models.order import Order

load_dotenv()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt Şablonları
# ---------------------------------------------------------------------------

EXTRACT_SYSTEM_PROMPT = """\
Sen bir sipariş takip sistemi için metin analiz asistanısın.
Görevin, kullanıcının mesajından sipariş numarasını veya sipariş ID'sini çıkarmak.

Kurallar:
- Sipariş numarası "SIP-" öneki ile başlayan bir kod olabilir (örn: SIP-2026-0001)
- Sipariş ID'si sadece bir sayı olabilir (örn: 128, 42, 7)
- Kullanıcı "sipariş", "paket", "kargo", "numara" gibi kelimelerle \
birlikte bir sayı verdiyse bu sipariş ID'sidir
- Eğer mesajda hiçbir sipariş bilgisi bulamadıysan null döndür

Yanıtını SADECE aşağıdaki JSON formatında ver, başka bir şey yazma:
{"order_number": "string veya null", "order_id": "number veya null"}\
"""

RESPONSE_SYSTEM_PROMPT = """\
Sen Kargos şirketinin kibar ve yardımsever yapay zeka müşteri temsilcisisin.
Amacın müşterilerle doğal bir şekilde iletişim kurmak ve kargo/sipariş süreçlerinde yardımcı olmak.

Kullanıcının sipariş bilgilerini veritabanından aldık, aşağıda göreceksin.
Bu bilgileri kullanarak kullanıcıya doğal, akıcı ve kibar bir yanıt ver.
Sadece robotik bilgi sunma, müşterinin sohbetine de (varsa) doğal bir karşılık ver.
"""

GENERAL_CHAT_SYSTEM_PROMPT = """\
Sen Kargos şirketinin kibar ve yardımsever yapay zeka müşteri temsilcisisin.
Amacın müşterilerle doğal bir şekilde iletişim kurmak ve kargo/sipariş süreçlerinde yardımcı olmak.

Eğer kullanıcı sana "Merhaba", "Nasılsın", "Kimsin" gibi günlük sohbet kelimeleriyle gelirse,
buna uygun, doğal ve akıcı bir şekilde yanıt ver (Örn: 'Merhaba! Ben Kargos asistanıyım, size kargo takibi konusunda nasıl yardımcı olabilirim?').
Eğer kullanıcı kargosunu soruyorsa ama sipariş numarası vermediyse, kibarca numarasını (Örn: SIP-1234) iste.
"""

ORDER_NOT_FOUND_SYSTEM_PROMPT = """\
Sen Kargos şirketinin kibar ve yardımsever yapay zeka müşteri temsilcisisin.
Amacın müşterilerle doğal bir şekilde iletişim kurmak ve kargo/sipariş süreçlerinde yardımcı olmak.

Kullanıcı bir sipariş numarası veya ID verdi ama sistemde bulamadık.
Kibarca bilgiyi kontrol etmesini iste. Sipariş onay e-postasında doğru numarayı bulabileceğini hatırlat.
"""


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------

@dataclass
class ExtractedOrderInfo:
    """Mesajdan çıkarılan sipariş bilgisi."""

    order_number: str | None = None
    order_id: int | None = None

    @property
    def has_info(self) -> bool:
        """Herhangi bir sipariş tanımlayıcısı bulundu mu?"""
        return self.order_number is not None or self.order_id is not None


# ---------------------------------------------------------------------------
# AI Agent
# ---------------------------------------------------------------------------

class AIAgent:
    """
    Kargos Yapay Zeka Ajanı.

    Müşteri mesajlarını analiz eder, sipariş bilgilerini veritabanından
    çeker ve doğal dilde yanıt üretir.

    Groq API anahtarı ayarlanmamışsa regex + şablon tabanlı fallback
    modunda çalışır (geliştirme/test ortamları için).
    """

    def __init__(self) -> None:
        self._api_key = os.getenv("GROQ_API_KEY")
        self._model_name = os.getenv(
            "GROQ_MODEL", "llama-3.1-8b-instant"
        )
        self._client: AsyncGroq | None = None

        if self._api_key and self._api_key.startswith("gsk_"):
            self._client = AsyncGroq(api_key=self._api_key)
            logger.info("Groq API yapılandırıldı (model: %s)", self._model_name)
        else:
            logger.warning(
                "Geçerli bir GROQ_API_KEY ayarlanmamış. "
                "AI Agent fallback (regex + şablon) modunda çalışacak."
            )

    # -- Public API ---------------------------------------------------------

    @property
    def is_llm_available(self) -> bool:
        """Groq API kullanılabilir mi?"""
        return self._client is not None

    async def process_message(self, message: str, db: Session) -> str:
        """
        Kullanıcı mesajını uçtan uca işle ve yanıt üret.

        Args:
            message: Kullanıcının doğal dil mesajı.
            db: Veritabanı oturumu.

        Returns:
            Müşteriye gönderilecek yanıt metni.
        """
        # 1) Mesajdan sipariş bilgisini çıkar
        extracted = await self._extract_order_info(message)

        # 2) Sipariş bilgisi yoksa genel sohbet veya numara isteme yanıtı üret
        if not extracted.has_info:
            return await self._generate_general_response(message)

        # 3) Veritabanında sipariş ara
        order = self._find_order(db, extracted)

        # 4) Sipariş bulunamadıysa bilgilendir
        if order is None:
            return await self._generate_not_found_response(
                message, extracted
            )

        # 5) Sipariş bilgisiyle doğal yanıt üret
        return await self._generate_order_response(message, order)

    # -- Sipariş Bilgisi Çıkarma -------------------------------------------

    async def _extract_order_info(self, message: str) -> ExtractedOrderInfo:
        """Mesajdan sipariş numarası veya ID çıkar."""
        if self.is_llm_available:
            return await self._extract_with_llm(message)
        return self._extract_with_regex(message)

    async def _extract_with_llm(self, message: str) -> ExtractedOrderInfo:
        """Groq kullanarak sipariş bilgisini çıkar."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                max_tokens=200,
                temperature=0.01,
            )

            raw = response.choices[0].message.content.strip()

            # JSON bloğunu temizle (LLM bazen ```json ... ``` sarar)
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            data = json.loads(raw)

            return ExtractedOrderInfo(
                order_number=data.get("order_number"),
                order_id=(
                    int(data["order_id"])
                    if data.get("order_id") is not None
                    else None
                ),
            )

        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning(
                "LLM çıktısı ayrıştırılamadı, regex fallback: %s", exc
            )
            return self._extract_with_regex(message)

        except Exception as exc:
            logger.error("Groq API hatası (extract): %s", exc)
            return self._extract_with_regex(message)

    @staticmethod
    def _extract_with_regex(message: str) -> ExtractedOrderInfo:
        """Regex ile sipariş bilgisini çıkar (fallback modu)."""
        # SIP-XXXX-XXXX formatını ara
        sip_match = re.search(r"(SIP-[\w-]+)", message, re.IGNORECASE)
        if sip_match:
            return ExtractedOrderInfo(
                order_number=sip_match.group(1).upper()
            )

        # Sayısal ID — sipariş/kargo/paket bağlamında
        id_match = re.search(
            r"(?:sipariş|siparis|kargo|paket|numara|no|takip)"
            r"[\s#:ım]*(\d+)",
            message,
            re.IGNORECASE,
        )
        if id_match:
            return ExtractedOrderInfo(order_id=int(id_match.group(1)))

        # Bağımsız sayı (son çare)
        num_match = re.search(r"\b(\d{1,10})\b", message)
        if num_match:
            return ExtractedOrderInfo(order_id=int(num_match.group(1)))

        return ExtractedOrderInfo()

    # -- Veritabanı Sorgulama -----------------------------------------------

    @staticmethod
    def _find_order(db: Session, extracted: ExtractedOrderInfo) -> Order | None:
        """Veritabanında sipariş ara (önce numara, sonra ID)."""
        if extracted.order_number:
            order = OrderCRUD.get_order_by_number(db, extracted.order_number)
            if order:
                return order

        if extracted.order_id:
            return OrderCRUD.get_order_by_id(db, extracted.order_id)

        return None

    # -- Yanıt Üretme -------------------------------------------------------

    async def _generate_order_response(
        self, message: str, order: Order
    ) -> str:
        """Sipariş bilgisiyle müşteriye doğal yanıt üret."""
        order_context = (
            f"Sipariş No: {order.order_number}\n"
            f"Müşteri: {order.customer_name}\n"
            f"Ürün: {order.product_info}\n"
            f"Kargo Durumu: {order.shipping_status.value}\n"
            f"Takip No: {order.tracking_number or 'Henüz atanmadı'}\n"
            f"Sipariş Tarihi: {order.created_at}"
        )

        if self.is_llm_available:
            return await self._call_llm(
                system=RESPONSE_SYSTEM_PROMPT,
                user_message=(
                    f"Müşteri mesajı: {message}\n\n"
                    f"Veritabanından çekilen sipariş bilgileri:\n"
                    f"{order_context}"
                ),
            )

        return self._template_order_response(order)

    async def _generate_general_response(self, message: str) -> str:
        """Kullanıcı genel bir mesaj attığında veya numara vermediğinde doğal yanıt üret."""
        if self.is_llm_available:
            return await self._call_llm(
                system=GENERAL_CHAT_SYSTEM_PROMPT,
                user_message=f"Müşteri mesajı: {message}",
            )

        return (
            "Merhaba! 👋 Ben Kargos asistanıyım. Size yardımcı olabilmem için sipariş numaranıza "
            "ihtiyacım var. Lütfen sipariş numaranızı (Örn: SIP-2026-0001) paylaşır mısınız?"
        )

    async def _generate_not_found_response(
        self, message: str, extracted: ExtractedOrderInfo
    ) -> str:
        """Sipariş bulunamadığında bilgilendir."""
        identifier = extracted.order_number or str(extracted.order_id)

        if self.is_llm_available:
            return await self._call_llm(
                system=ORDER_NOT_FOUND_SYSTEM_PROMPT,
                user_message=(
                    f"Müşteri mesajı: {message}\n"
                    f"Aranan sipariş: {identifier}\n"
                    f"Sonuç: Sistemde bulunamadı"
                ),
            )

        return (
            f"Üzgünüm, '{identifier}' numaralı siparişi sistemimizde "
            f"bulamadım. 😔 Lütfen sipariş numaranızı kontrol edip "
            f"tekrar dener misiniz? Sipariş onay e-postanızda bu "
            f"bilgiyi bulabilirsiniz."
        )

    # -- LLM Çağrısı --------------------------------------------------------

    async def _call_llm(self, system: str, user_message: str) -> str:
        """Groq API'ye istek gönder ve yanıt al."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=500,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()

        except Exception as exc:
            logger.error("Groq API yanıt üretme hatası: %s", exc)
            return (
                "Şu anda bir teknik sorun yaşıyoruz. "
                "Lütfen birkaç dakika sonra tekrar deneyin. 🙏"
            )

    # -- Fallback Şablonları ------------------------------------------------

    @staticmethod
    def _template_order_response(order: Order) -> str:
        """Şablon tabanlı sipariş yanıtı (LLM olmadan fallback)."""
        status_value = order.shipping_status.value
        tracking = order.tracking_number

        base = (
            f"Merhaba! {order.order_number} numaralı siparişiniz "
            f"hakkında bilgi vereyim:\n\n"
            f"📦 Ürün: {order.product_info}\n"
            f"📋 Durum: {status_value}\n"
        )

        if status_value == "Hazırlanıyor":
            base += (
                "\n⏳ Siparişiniz şu anda hazırlanıyor. "
                "En kısa sürede kargoya verilecektir. "
                "Sabrınız için teşekkür ederiz!"
            )
        elif status_value == "Kargoya Verildi":
            base += f"\n🚚 Takip No: {tracking or 'Henüz atanmadı'}\n"
            if tracking:
                base += (
                    "Kargo firmanızın web sitesinden "
                    "takip numaranızla siparişinizi izleyebilirsiniz."
                )
            else:
                base += "Takip numarası kısa sürede atanacaktır."
        elif status_value == "Gecikmede":
            base += (
                "\n⚠️ Siparişinizde gecikme yaşanmaktadır. "
                "Bu durum için özür dileriz. Ekibimiz sorunu "
                "çözmek için çalışmaktadır. En kısa sürede "
                "sizinle iletişime geçeceğiz."
            )

        return base


# Singleton — uygulama genelinde tek bir agent örneği kullanılır
ai_agent = AIAgent()
