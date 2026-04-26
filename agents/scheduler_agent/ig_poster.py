"""
Instagram poster — publishes a pick via the Meta Graph API.

IG Graph publishing is a two-step container flow:
  1. POST /{ig-user-id}/media       → returns a creation_id
  2. POST /{ig-user-id}/media_publish with creation_id → posts it

Critical constraints we work around:
  - The image_url MUST be publicly fetchable by Meta — we cannot upload bytes
    directly. We expect the graphic to already be at a public URL, derived from
    GRAPHIC_PUBLIC_BASE_URL + the file name. The user is responsible for
    syncing data/processed/*.png to that location (S3/R2/Pages).
  - Caption hard limit: 2,200 chars. content_agent already targets ≤2,100.
  - Meta processes the container asynchronously. Polling /{creation_id} for
    status_code=FINISHED keeps us safe before we publish.

Setup:
  Long-lived Page access token in META_ACCESS_TOKEN. Permissions required:
    instagram_basic, instagram_content_publish,
    pages_show_list, pages_read_engagement
"""

from __future__ import annotations
import logging
import os
import time
from pathlib import Path
from typing import Optional

import httpx

log = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class IGPostError(RuntimeError):
    """Raised when Meta Graph rejects a step in the publish flow."""


def post(
    caption: str,
    graphic_path: Path,
    *,
    access_token: Optional[str] = None,
    ig_user_id: Optional[str] = None,
    public_base_url: Optional[str] = None,
    timeout: float = 30.0,
    max_status_polls: int = 10,
    poll_interval_s: float = 2.0,
) -> dict:
    """Publish caption + graphic to Instagram. Returns the publish response.

    The graphic must already be reachable at:
      {public_base_url}/{graphic_path.name}
    """
    access_token = access_token or os.environ.get("META_ACCESS_TOKEN")
    ig_user_id = ig_user_id or os.environ.get("IG_BUSINESS_ACCOUNT_ID")
    public_base_url = public_base_url or os.environ.get("GRAPHIC_PUBLIC_BASE_URL")
    if not all([access_token, ig_user_id, public_base_url]):
        raise IGPostError(
            "META_ACCESS_TOKEN, IG_BUSINESS_ACCOUNT_ID, GRAPHIC_PUBLIC_BASE_URL required"
        )
    if len(caption) > 2200:
        raise IGPostError(f"caption too long: {len(caption)} chars (max 2200)")

    image_url = f"{public_base_url.rstrip('/')}/{Path(graphic_path).name}"

    creation_id = _create_container(
        ig_user_id, access_token, image_url, caption, timeout
    )
    _wait_for_container(
        creation_id, access_token, timeout, max_status_polls, poll_interval_s
    )
    return _publish_container(ig_user_id, access_token, creation_id, timeout)


def _create_container(
    ig_user_id: str, token: str, image_url: str, caption: str, timeout: float
) -> str:
    r = httpx.post(
        f"{GRAPH_API_BASE}/{ig_user_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
        timeout=timeout,
    )
    body = _json(r)
    cid = body.get("id")
    if not cid:
        raise IGPostError(f"no creation_id returned: {body}")
    log.info(f"IG container created: {cid}")
    return cid


def _wait_for_container(
    creation_id: str, token: str, timeout: float, max_polls: int, interval: float
) -> None:
    """Poll until status_code=FINISHED. Meta sometimes takes a few seconds."""
    for attempt in range(max_polls):
        r = httpx.get(
            f"{GRAPH_API_BASE}/{creation_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=timeout,
        )
        status = _json(r).get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise IGPostError(f"container processing failed (creation_id={creation_id})")
        log.debug(f"  IG container status={status}, retry {attempt+1}/{max_polls}")
        time.sleep(interval)
    raise IGPostError(f"container never reached FINISHED after {max_polls} polls")


def _publish_container(
    ig_user_id: str, token: str, creation_id: str, timeout: float
) -> dict:
    r = httpx.post(
        f"{GRAPH_API_BASE}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=timeout,
    )
    body = _json(r)
    if "id" not in body:
        raise IGPostError(f"publish failed: {body}")
    log.info(f"IG post published: media_id={body['id']}")
    return body


def _json(response: httpx.Response) -> dict:
    try:
        body = response.json()
    except Exception as e:
        raise IGPostError(f"non-JSON response: {response.text[:200]}") from e
    if "error" in body:
        raise IGPostError(f"Meta error: {body['error']}")
    return body


def health_check() -> bool:
    """Verify the token can read the IG account."""
    token = os.environ.get("META_ACCESS_TOKEN")
    ig_id = os.environ.get("IG_BUSINESS_ACCOUNT_ID")
    if not token or not ig_id:
        return False
    r = httpx.get(
        f"{GRAPH_API_BASE}/{ig_id}",
        params={"fields": "id,username", "access_token": token},
        timeout=10.0,
    )
    body = r.json()
    if "username" in body:
        log.info(f"IG account OK: @{body['username']}")
        return True
    log.error(f"IG health check failed: {body}")
    return False


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    if not health_check():
        raise SystemExit("IG health check failed — verify token + IG_BUSINESS_ACCOUNT_ID")
    print("IG token + account look good. Ready for publishing.")
