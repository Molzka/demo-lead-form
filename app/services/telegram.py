import html
import logging

import httpx

from app.core.config import Settings
from app.models.lead import Lead

logger = logging.getLogger(__name__)


def build_telegram_message(lead: Lead) -> str:
    lines = [
        "<b>Новая заявка с сайта</b>",
        "",
        f"Имя: {html.escape(lead.name)}",
        f"Телефон: {html.escape(lead.phone)}",
        f"Услуга: {html.escape(lead.service or '-')}",
        f"Комментарий: {html.escape(lead.comment or '-')}",
        f"Источник: {html.escape(lead.source)}",
    ]

    if lead.utm_source:
        lines.append(f"UTM Source: {html.escape(lead.utm_source)}")
    if lead.utm_campaign:
        lines.append(f"UTM Campaign: {html.escape(lead.utm_campaign)}")

    return "\n".join(lines)


async def send_lead_notification(lead: Lead, settings: Settings) -> None:
    if not settings.telegram_enabled:
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": build_telegram_message(lead),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, dict) or result.get("ok") is not True:
                logger.warning("Telegram rejected notification for lead %s", lead.id)
    except (httpx.HTTPError, ValueError) as exc:
        # Exception messages/tracebacks can contain the bot token or user data.
        logger.warning("Telegram failed for lead %s (%s)", lead.id, type(exc).__name__)
