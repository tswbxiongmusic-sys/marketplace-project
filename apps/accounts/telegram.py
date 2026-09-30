"""Minimal Telegram Bot API client for seller order alerts.

Uses the standard library so there is no extra dependency, and polling
(getUpdates) instead of a webhook so no public callback URL has to be set up.
"""
import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

TIMEOUT = 8


def is_configured():
    return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_USERNAME)


def _call(method, **params):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(url, data=data, timeout=TIMEOUT) as response:
        payload = json.load(response)
    if not payload.get("ok"):
        raise RuntimeError(payload.get("description", "Telegram API error"))
    return payload["result"]


def send_message(chat_id, text):
    """Send a message; log (never raise) on failure so orders are unaffected."""
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    try:
        _call("sendMessage", chat_id=chat_id, text=text, disable_web_page_preview="true")
        return True
    except Exception:
        logger.exception("Failed to send Telegram message to chat %s", chat_id)
        return False


def link_url(token):
    return f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={token}"


def sync_links():
    """Read pending "/start <token>" messages and attach each chat to the
    seller who owns that token.  Every pending update is handled (not just the
    caller's) and then acknowledged, so the queue never builds up."""
    from .models import User

    updates = _call("getUpdates", timeout=0)
    linked = []
    for update in updates:
        message = update.get("message") or {}
        text = (message.get("text") or "").strip()
        chat_id = (message.get("chat") or {}).get("id")
        if not chat_id or not text.startswith("/start "):
            continue
        token = text.split(" ", 1)[1].strip()
        user = User.objects.filter(telegram_link_token=token).first() if token else None
        if user is None:
            continue
        user.telegram_chat_id = str(chat_id)
        user.telegram_link_token = ""
        user.save(update_fields=["telegram_chat_id", "telegram_link_token"])
        linked.append(user)
        send_message(chat_id, f"✅ ເຊື່ອມຕໍ່ສຳເລັດ! ຮ້ານ {user.display_name} ຈະໄດ້ຮັບແຈ້ງເຕືອນຄຳສັ່ງຊື້ໃໝ່ຢູ່ນີ້.")
    if updates:
        _call("getUpdates", offset=updates[-1]["update_id"] + 1, timeout=0)
    return linked
