import os
import requests
from typing import Any, Dict, List, Optional
from watchdog.utils.logger import WatchdogLogger

class DiscordNotifier:
    
    def __init__(self, webhook_url: Optional[str] = None) -> None:
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.logger = WatchdogLogger("logger")
        if not self.webhook_url:
            self.logger.error("Discord webhook URL is not set. Check your environment variables.")
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
        if content and len(content) > 2000:
            self.logger.warning("Content exceeds Discord's 2000 character limit. Cutting content.")
            content = content[:2000]
        if avatar_url:
            payload["avatar_url"] = avatar_url
        if embeds:
            payload["embeds"] = embeds

        response = requests.post(self.webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        
        if response.status_code != 204:
            self.logger.error(f"Failed to send message to Discord: {response.status_code} - {response.text}")
        else:
            self.logger.info("Message successfully sent to Discord.")
            
        return response
