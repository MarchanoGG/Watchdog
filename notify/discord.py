"""
Discord-notificaties voor WatchDog.
"""

import os
import json
import requests
from typing import Any, Dict, List, Optional


class DiscordNotifier:
    """
    Simpele Discord-notifier. Stuurt plain-text of embed-achtige JSON via
    een inkomende webhook.
    """

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("Discord-webhook-URL ontbreekt; zet DISCORD_WEBHOOK_URL in .env")

    def send(
        self,
        content: str = "",
        embeds: Optional[List[Dict[str, Any]]] = None,
        username: str = "WatchDog",
        avatar_url: Optional[str] = None,
    ) -> requests.Response:
        """
        Stuur een bericht naar Discord.

        Parameters
        ----------
        content : str
            Plain-text content (max 2000 tekens). Leeg laten als je alleen embeds stuurt.
        embeds : list
            Optionele embed-objecten (Discord JSON-formaat).
        username : str
            Weergavenaam van de bot.
        avatar_url : str
            Optionele avatar-URL.

        Returns
        -------
        requests.Response
            Antwoord van Discord (200 = OK).
        """
        payload: Dict[str, Any] = {
            "username": username,
            "content": content,
        }
        if avatar_url:
            payload["avatar_url"] = avatar_url
        if embeds:
            payload["embeds"] = embeds

        resp = requests.post(self.webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp
