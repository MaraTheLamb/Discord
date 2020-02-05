import logging
import socket
from typing import Optional

import aiohttp
from discord.ext import commands

from bot import api

log = logging.getLogger('bot')


class Bot(commands.Bot):
    """A subclass of `discord.ext.commands.Bot` with an aiohttp session and an API client."""

    def __init__(self, *args, **kwargs):
        # Use asyncio for DNS resolution instead of threads so threads aren't spammed.
        # Use AF_INET as its socket family to prevent HTTPS related problems both locally
        # and in production.
        self.connector = aiohttp.TCPConnector(
            resolver=aiohttp.AsyncResolver(),
            family=socket.AF_INET,
        )

        super().__init__(*args, connector=self.connector, **kwargs)

        self.http_session: Optional[aiohttp.ClientSession] = None
        self.api_client = api.APIClient(loop=self.loop, connector=self.connector)

        log.addHandler(api.APILoggingHandler(self.api_client))

    def add_cog(self, cog: commands.Cog) -> None:
        """Adds a "cog" to the bot and logs the operation."""
        super().add_cog(cog)
        log.info(f"Cog loaded: {cog.qualified_name}")

    def clear(self) -> None:
        """Clears the internal state of the bot and resets the API client."""
        super().clear()
        self.api_client.recreate()

    async def close(self) -> None:
        """Close the aiohttp session after closing the Discord connection."""
        await super().close()

        await self.http_session.close()
        await self.api_client.close()

    async def start(self, *args, **kwargs) -> None:
        """Open an aiohttp session before logging in and connecting to Discord."""
        self.http_session = aiohttp.ClientSession(connector=self.connector)

        await super().start(*args, **kwargs)
