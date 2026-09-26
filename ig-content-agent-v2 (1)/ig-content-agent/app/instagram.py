"""Instagram Graph API client (official API only). The HTTP layer is injectable so it can be tested offline."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request


class InstagramError(Exception):
    def __init__(self, message: str, retryable: bool = False, code: str = ""):
        super().__init__(message)
        self.retryable = retryable
        self.code = code


def default_transport(method: str, url: str, params: dict) -> tuple:
    """Returns (status, parsed_json). The access token travels in the body/query, never in a log line."""
    data = None
    if method == "POST":
        data = urllib.parse.urlencode(params).encode("utf-8")
    else:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8") or "{}")
        except ValueError:
            body = {}
        return e.code, body
    except (urllib.error.URLError, TimeoutError, OSError):
        raise InstagramError("Could not reach Instagram. Check the internet connection.", retryable=True)


class GraphClient:
    def __init__(self, settings, transport=None, sleep=time.sleep):
        self.s = settings
        self.transport = transport or default_transport
        self.sleep = sleep
        self.base = f"https://graph.facebook.com/{settings.graph_version}"

    def _call(self, method: str, path: str, params: dict | None = None) -> dict:
        p = dict(params or {})
        p["access_token"] = self.s.ig_access_token
        status, body = self.transport(method, f"{self.base}/{path.lstrip('/')}", p)
        if status >= 400 or "error" in body:
            err = body.get("error", {}) if isinstance(body, dict) else {}
            code = str(err.get("code", status))
            msg = str(err.get("message", "Instagram rejected the request."))[:250]
            if code in ("190", "102") or status == 401:
                raise InstagramError("Instagram no longer accepts the access token. Create a new token and update IG_ACCESS_TOKEN.",
                                     code=code)
            retry = status >= 500 or status == 429 or code in ("4", "17", "32", "613", "2")
            raise InstagramError(f"Instagram said: {msg}", retryable=retry, code=code)
        return body

    def publishing_limit(self) -> dict:
        body = self._call("GET", f"{self.s.ig_user_id}/content_publishing_limit", {"fields": "quota_usage,config"})
        data = (body.get("data") or [{}])[0]
        total = (data.get("config") or {}).get("quota_total", 0)
        used = data.get("quota_usage", 0)
        return {"used": used, "total": total, "remaining": max(0, total - used) if total else None}

    def create_container(self, *, media_type: str, media_url: str = "", caption: str = "",
                         children: list | None = None, carousel_item: bool = False, is_video: bool = False) -> str:
        p: dict = {}
        if media_type == "CAROUSEL":
            p.update(media_type="CAROUSEL", children=",".join(children or []))
        elif carousel_item:
            p["is_carousel_item"] = "true"
            if is_video:
                p.update(media_type="VIDEO", video_url=media_url)
            else:
                p["image_url"] = media_url
        elif media_type == "REEL":
            p.update(media_type="REELS", video_url=media_url)
        elif media_type == "STORY":
            p["media_type"] = "STORIES"
            p["video_url" if is_video else "image_url"] = media_url
        else:
            p["image_url"] = media_url
        if caption and not carousel_item and media_type != "STORY":
            p["caption"] = caption
        body = self._call("POST", f"{self.s.ig_user_id}/media", p)
        cid = str(body.get("id", ""))
        if not cid:
            raise InstagramError("Instagram did not return a container id.")
        return cid

    def wait_until_ready(self, container_id: str, timeout: int = 420, every: int = 5) -> None:
        waited = 0
        while True:
            body = self._call("GET", container_id, {"fields": "status_code,status"})
            status = body.get("status_code", "")
            if status in ("FINISHED", "PUBLISHED"):
                return
            if status in ("ERROR", "EXPIRED"):
                raise InstagramError(f"Instagram could not process the media ({status.lower()}). {str(body.get('status', ''))[:150]}".strip())
            if waited >= timeout:
                raise InstagramError("Instagram took too long to process the media.", retryable=True)
            self.sleep(every)
            waited += every

    def publish(self, container_id: str) -> str:
        body = self._call("POST", f"{self.s.ig_user_id}/media_publish", {"creation_id": container_id})
        mid = str(body.get("id", ""))
        if not mid:
            raise InstagramError("Instagram did not return a media id.")
        return mid

    def permalink(self, media_id: str) -> str:
        try:
            return str(self._call("GET", media_id, {"fields": "permalink"}).get("permalink", ""))
        except InstagramError:
            return ""
