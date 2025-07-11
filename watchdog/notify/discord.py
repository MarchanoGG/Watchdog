import os
import requests
from typing import Any, Dict, List, Optional


class DiscordNotifier:
    
    def __init__(self, webhook_url: Optional[str] = None) -> None:
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("Missing Discord webhook URL (set DISCORD_WEBHOOK_URL in .env)")

    def send(
        self,
        content: str = "",
        embeds: Optional[List[Dict[str, Any]]] = None,
        username: str = "WatchDog",
        avatar_url: Optional[str] = None,
    ) -> requests.Response:
        payload: Dict[str, Any] = {
            "username": username,
            "content": content,
        }
        if avatar_url:
            payload["avatar_url"] = avatar_url
        if embeds:
            payload["embeds"] = embeds

        response = requests.post(self.webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        return response
