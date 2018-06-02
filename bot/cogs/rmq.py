import datetime
import json
import logging
import pprint

import aio_pika
from discord import Colour, Embed
from discord.ext.commands import Bot
from discord.utils import get

from bot.constants import Channels, Guild, RabbitMQ

log = logging.getLogger(__name__)

LEVEL_COLOURS = {
    "debug": Colour.blue(),
    "info": Colour.green(),
    "warning": Colour.gold(),
    "error": Colour.red()
}

DEFAULT_LEVEL_COLOUR = Colour.greyple()
EMBED_PARAMS = (
    "colour", "title", "url", "description", "timestamp"
)


class RMQ:
    """
    RabbitMQ event handling
    """

    rmq = None  # type: aio_pika.Connection
    channel = None  # type: aio_pika.Channel
    queue = None  # type: aio_pika.Queue

    def __init__(self, bot: Bot):
        self.bot = bot

    async def on_ready(self):
        self.rmq = await aio_pika.connect_robust(
            host=RabbitMQ.host, port=RabbitMQ.port, login=RabbitMQ.username, password=RabbitMQ.password
        )

        log.info("Connected to RabbitMQ")

        self.channel = await self.rmq.channel()
        self.queue = await self.channel.declare_queue("bot_events", durable=True)

        log.debug("Channel opened, queue declared")

        async for message in self.queue:
            with message.process():
                await self.handle_message(message, message.body.decode())

    async def handle_message(self, message, data):
        log.debug(f"Message: {message}")
        log.debug(f"Data: {data}")

        try:
            data = json.loads(data)
        except Exception:
            await self.do_mod_log("error", "Unable to parse event", data)
        else:
            event = data["event"]
            event_data = data["data"]

            try:
                func = getattr(self, f"do_{event}")
                await func(**event_data)
            except Exception as e:
                await self.do_mod_log(
                    "error", f"Unable to handle event: {event}",
                    str(e)
                )

    async def do_mod_log(self, level: str, title: str, message: str):
        colour = LEVEL_COLOURS.get(level, DEFAULT_LEVEL_COLOUR)
        embed = Embed(
            title=title, description=f"```\n{message}\n```",
            colour=colour, timestamp=datetime.datetime.now()
        )

        await self.bot.get_channel(Channels.modlog).send(embed=embed)
        log.log(logging._nameToLevel[level.upper()], f"Modlog: {title} | {message}")

    async def do_send_message(self, target: int, message: str):
        channel = self.bot.get_channel(target)

        if channel is None:
            await self.do_mod_log(
                "error", "Failed: Send Message",
                f"Unable to find channel: {target}"
            )
        else:
            await channel.send(message)

            await self.do_mod_log(
                "info", "Succeeded: Send Embed",
                f"Message sent to channel {target}\n\n{message}"
            )

    async def do_send_embed(self, target: int, **embed_params):
        for param in list(embed_params.keys()):  # To keep a full copy
            if param not in EMBED_PARAMS:
                await self.do_mod_log(
                    "warning", "Warning: Send Embed",
                    f"Unknown embed parameter: {param}"
                )
                del embed_params[param]

        channel = self.bot.get_channel(target)

        if channel is None:
            await self.do_mod_log(
                "error", "Failed: Send Embed",
                f"Unable to find channel: {target}"
            )
        else:
            await channel.send(embed=Embed(**embed_params))

            await self.do_mod_log(
                "info", "Succeeded: Send Embed",
                f"Embed sent to channel {target}\n\n{pprint.pformat(embed_params, 4)}"
            )

    async def do_add_role(self, target: int, role_id: int, reason: str):
        guild = self.bot.get_guild(Guild.id)
        member = guild.get_member(target)

        if member is None:
            return await self.do_mod_log(
                "error", "Failed: Add Role",
                f"Unable to find member: {target}"
            )

        role = get(guild.roles, id=int(role_id))

        if role is None:
            return await self.do_mod_log(
                "error", "Failed: Add Role",
                f"Unable to find role: {role_id}"
            )

        try:
            await member.add_roles(role, reason=reason)
        except Exception as e:
            await self.do_mod_log(
                "error", "Failed: Add Role",
                f"Error while adding role {role.name}: {e}"
            )
        else:
            await self.do_mod_log(
                "info", "Succeeded: Add Role",
                f"Role {role.name} added to member {target}"
            )

    async def do_remove_role(self, target: int, role_id: int, reason: str):
        guild = self.bot.get_guild(Guild.id)
        member = guild.get_member(target)

        if member is None:
            return await self.do_mod_log(
                "error", "Failed: Remove Role",
                f"Unable to find member: {target}"
            )

        role = get(guild.roles, id=int(role_id))

        if role is None:
            return await self.do_mod_log(
                "error", "Failed: Remove Role",
                f"Unable to find role: {role_id}"
            )

        try:
            await member.remove_roles(role, reason=reason)
        except Exception as e:
            await self.do_mod_log(
                "error", "Failed: Remove Role",
                f"Error while adding role {role.name}: {e}"
            )
        else:
            await self.do_mod_log(
                "info", "Succeeded: Remove Role",
                f"Role {role.name} removed from member {target}"
            )


def setup(bot):
    bot.add_cog(RMQ(bot))
    log.info("Cog loaded: RMQ")
