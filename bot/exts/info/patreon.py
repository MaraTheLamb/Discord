import datetime
import logging

import discord
from discord.ext import commands, tasks

from bot import constants
from bot.bot import Bot

log = logging.getLogger(__name__)


class Patreon(commands.Cog):
    """Cog that shows patreon supporters."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.current_supporters_monthly.start()

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Send a message when someone receives a patreon role."""
        # Ensure the caches are up to date
        await self.bot.wait_until_guild_available()

        guild = await self.bot.fetch_guild(constants.Guild.id)

        await guild.fetch_channels()
        await guild.fetch_roles()

        patreon_tier_1_role = guild.get_role(constants.Roles.patreon_tier_1)
        patreon_tier_2_role = guild.get_role(constants.Roles.patreon_tier_2)
        patreon_tier_3_role = guild.get_role(constants.Roles.patreon_tier_3)

        sending_channel = discord.utils.get(self.bot.get_all_channels(), id=constants.Channels.meta)

        current_patreon_tier = 0
        new_patreon_tier = 0

        # Both of these go from top to bottom to give the user their highest patreon role if they have multiple

        if patreon_tier_3_role in before.roles:
            current_patreon_tier = 3
        elif patreon_tier_2_role in before.roles:
            current_patreon_tier = 2
        elif patreon_tier_1_role in before.roles:
            current_patreon_tier = 1

        if patreon_tier_3_role in after.roles:
            new_patreon_tier = 3
            colour = patreon_tier_3_role.colour
        elif patreon_tier_2_role in after.roles:
            new_patreon_tier = 2
            colour = patreon_tier_2_role.colour
        elif patreon_tier_1_role in after.roles:
            new_patreon_tier = 1
            colour = patreon_tier_1_role.colour

        if not new_patreon_tier > current_patreon_tier:
            return

        message = (
            f":tada: {after.mention} just became a **tier {new_patreon_tier}** patron!\n"
            f"[Support us on Patreon](https://pydis.com/patreon)"
        )

        await sending_channel.send(
            embed=discord.Embed(
                description=message,
                colour=colour
            )
        )

    async def send_current_supporters(self, channel: discord.TextChannel) -> None:
        """Send the current list of patreon supporters, sorted by tier level."""
        await self.bot.wait_until_guild_available()

        guild = self.bot.get_guild(constants.Guild.id)

        tier_1_patrons = set(guild.get_role(constants.Roles.patreon_tier_1).members)
        tier_2_patrons = set(guild.get_role(constants.Roles.patreon_tier_2).members)
        tier_3_patrons = set(guild.get_role(constants.Roles.patreon_tier_3).members)

        tier_1_patrons = tier_1_patrons - tier_2_patrons - tier_3_patrons
        tier_2_patrons = tier_2_patrons - tier_3_patrons

        tier_1_patrons = {f"{patron.mention} ({patron.name}#{patron.discriminator})" for patron in tier_1_patrons}
        tier_2_patrons = {f"{patron.mention} ({patron.name}#{patron.discriminator})" for patron in tier_2_patrons}
        tier_3_patrons = {f"{patron.mention} ({patron.name}#{patron.discriminator})" for patron in tier_3_patrons}

        embed_list = []

        embed = discord.Embed(
            title="Patreon Supporters",
            description=(
                "Here is a full list of this months Python Discord patrons!\n\nWe use the money from Patreon to offer "
                "excellent prizes for all of our events. Stuff like t-shirts, stickers, microcontrollers that support "
                "CircuitPython, or maybe even a mechanical keyboard.\n\nYou can read more about how Patreon supports "
                "us, or even support us yourself, on our Patreon page [here](https://www.patreon.com/python_discord)!"
            )
        )

        embed_list.append(embed)

        if tier_1_patrons:
            embed = discord.Embed(
                title="Tier 1 patrons",
                description="\n".join(tier_1_patrons),
                colour=guild.get_role(constants.Roles.patreon_tier_1).colour
            )
            embed_list.append(embed)

        if tier_2_patrons:
            embed = discord.Embed(
                title="Tier 2 patrons",
                description="\n".join(tier_2_patrons),
                colour=guild.get_role(constants.Roles.patreon_tier_2).colour
            )
            embed_list.append(embed)

        if tier_3_patrons:
            embed = discord.Embed(
                title="Tier 3 patrons",
                description="\n".join(tier_3_patrons),
                colour=guild.get_role(constants.Roles.patreon_tier_3).colour
            )
            embed_list.append(embed)

        await channel.send(embeds=embed_list)

    @commands.command("patrons")
    async def current_supporters_command(self, ctx: commands.context) -> None:
        """A command to activate self.send_current_supporters()."""
        await self.send_current_supporters(ctx.channel)

    @tasks.loop(time=datetime.time(hour=17))
    async def current_supporters_monthly(self) -> None:
        """A loop running every day to see if it's the first of the month, if so call self.send_current_supporters()."""
        date = datetime.date.today().day

        if date == 1:
            await self.send_current_supporters(
                discord.utils.get(self.bot.get_all_channels(), id=constants.Channels.meta)
            )

    @commands.command("patreon")
    async def patreon_info(self, ctx: commands.context) -> None:
        """A command to send patreon info."""
        await ctx.channel.send(embeds=[discord.Embed(
            title="Patreon",
            description=(
                "We use the money from Patreon to offer excellent prizes for all of our events. Stuff like t-shirts, "
                "stickers, microcontrollers that support CircuitPython, or maybe even a mechanical keyboard.\n\nYou can"
                " read more about how Patreon supports us, or even support us yourself, on our Patreon page "
                "[here](https://www.patreon.com/python_discord)!"
            )
        )])


def setup(bot: Bot) -> None:
    """Load the patreon cog."""
    bot.add_cog(Patreon(bot))