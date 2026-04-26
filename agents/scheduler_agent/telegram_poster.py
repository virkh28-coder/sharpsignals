"""
Telegram poster — pushes a pick to the public SharpSignals channel.

Why direct httpx instead of python-telegram-bot:
  We send one message per pick from a cron job. The full SDK pulls in asyncio
  machinery we don't use. The Bot API is two HTTP calls; that's all we need.

Setup:
  1. @BotFather → /newbot → save token → TELEGRAM_BOT_TOKEN
  2. Create public channel (e.g. @sharpsignals_picks)
  3. Add the bot as an admin of the channel
  4. Set TELEGRAM_CHANNEL_ID to "@sharpsignals_picks" or the numeric -100xxx id
"""

from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Optional

import httpx

log = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


class TelegramPostError(RuntimeError):
    """Raised when the Bot API rejects a message."""


def post(
    message: str,
    photo_path: Optional[Path] = None,
    bot_token: Optional[str] = None,
    channel_id: Optional[str] = None,
    timeout: float = 20.0,
) -> dict:
    """Send a pick to the channel. If photo_path is given, send as photo+caption.

    Returns the Bot API response dict on success.
    Raises TelegramPostError on failure.
    """
    bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
    channel_id = channel_id or os.environ.get("TELEGRAM_CHANNEL_ID")
    if not bot_token or not channel_id:
        raise TelegramPostError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID must be set"
        )

    if photo_path and Path(photo_path).exists():
        return _send_photo(bot_token, channel_id, message, Path(photo_path), timeout)
    return _send_message(bot_token, channel_id, message, timeout)


def _send_message(token: str, chat_id: str, text: str, timeout: float) -> dict:
    url = f"{API_BASE}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    r = httpx.post(url, json=payload, timeout=timeout)
    return _unwrap(r)


def _send_photo(
    token: str, chat_id: str, caption: str, photo: Path, timeout: float
) -> dict:
    # Telegram caption hard limit is 1024 chars; truncate defensively.
    caption = caption if len(caption) <= 1024 else caption[:1021] + "..."
    url = f"{API_BASE}/bot{token}/sendPhoto"
    with open(photo, "rb") as f:
        files = {"photo": (photo.name, f, "image/png")}
        data = {
            "chat_id": chat_id,
            "caption": caption,
            "parse_mode": "Markdown",
        }
        r = httpx.post(url, data=data, files=files, timeout=timeout)
    return _unwrap(r)


def _unwrap(response: httpx.Response) -> dict:
    try:
        body = response.json()
    except Exception as e:
        raise TelegramPostError(f"non-JSON response: {response.text[:200]}") from e
    if not body.get("ok"):
        raise TelegramPostError(f"Bot API error: {body}")
    return body["result"]


def health_check() -> bool:
    """Pings getMe so you can verify the token before going live."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return False
    r = httpx.get(f"{API_BASE}/bot{token}/getMe", timeout=10.0)
    body = r.json()
    if body.get("ok"):
        log.info(f"Telegram bot OK: @{body['result'].get('username')}")
        return True
    log.error(f"Telegram bot failed: {body}")
    return False


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    if not health_check():
        raise SystemExit("Telegram health check failed — verify TELEGRAM_BOT_TOKEN")
    print(post("*SharpSignals* connection test — ignore.\n\n18+ · ConnexOntario 1-866-531-2600"))
