import colorsys
import logging
import pprint
import textwrap
import typing
from collections import defaultdict
from typing import Any, Mapping, Optional

import discord
from discord import CategoryChannel, Colour, Embed, Member, Role, TextChannel, VoiceChannel, utils
from discord.ext import commands
from discord.ext.commands import Bot, BucketType, Cog, Context, command, group
from discord.utils import escape_markdown

from bot import constants
from bot.decorators import InChannelCheckFailure, in_channel, with_role
from bot.utils.checks import cooldown_with_role_bypass, with_role_check
from bot.utils.time import time_since

log = logging.getLogger(__name__)


class Information(Cog):
    """A cog with commands for generating embeds with server info, such as server stats and user info."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @with_role(*constants.MODERATION_ROLES)
    @command(name="roles")
    async def roles_info(self, ctx: Context) -> None:
        """Returns a list of all roles and their corresponding IDs."""
        # Sort the roles alphabetically and remove the @everyone role
        roles = sorted(ctx.guild.roles, key=lambda role: role.name)
        roles = [role for role in roles if role.name != "@everyone"]

        # Build a string
        role_string = ""
        for role in roles:
            role_string += f"`{role.id}` - {role.mention}\n"

        # Build an embed
        embed = Embed(
            title="Role information",
            colour=Colour.blurple(),
            description=role_string
        )

        embed.set_footer(text=f"Total roles: {len(roles)}")

        await ctx.send(embed=embed)

    @with_role(*constants.MODERATION_ROLES)
    @command(name="role")
    async def role_info(self, ctx: Context, *roles: typing.Union[Role, str]) -> None:
        """
        Return information on a role or list of roles.

        To specify multiple roles just add to the arguments, delimit roles with spaces in them using quotation marks.
        """
        parsed_roles = []

        for role_name in roles:
            if isinstance(role_name, Role):
                # Role conversion has already succeeded
                parsed_roles.append(role_name)
                continue

            role = utils.find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)

            if not role:
                await ctx.send(f":x: Could not convert `{role_name}` to a role")
                continue

            parsed_roles.append(role)

        for role in parsed_roles:
            embed = Embed(
                title=f"{role.name} info",
                colour=role.colour,
            )

            embed.add_field(name="ID", value=role.id, inline=True)

            embed.add_field(name="Colour (RGB)", value=f"#{role.colour.value:0>6x}", inline=True)

            h, s, v = colorsys.rgb_to_hsv(*role.colour.to_rgb())

            embed.add_field(name="Colour (HSV)", value=f"{h:.2f} {s:.2f} {v}", inline=True)

            embed.add_field(name="Member count", value=len(role.members), inline=True)

            embed.add_field(name="Position", value=role.position)

            embed.add_field(name="Permission code", value=role.permissions.value, inline=True)

            await ctx.send(embed=embed)

    @command(name="server", aliases=["server_info", "guild", "guild_info"])
    async def server_info(self, ctx: Context) -> None:
        """Returns an embed full of server information."""
        created = time_since(ctx.guild.created_at, precision="days")
        features = ", ".join(ctx.guild.features)
        region = ctx.guild.region

        # How many of each type of channel?
        roles = len(ctx.guild.roles)
        channels = ctx.guild.channels
        text_channels = 0
        category_channels = 0
        voice_channels = 0
        for channel in channels:
            if type(channel) == TextChannel:
                text_channels += 1
            elif type(channel) == CategoryChannel:
                category_channels += 1
            elif type(channel) == VoiceChannel:
                voice_channels += 1

        # How many of each user status?
        member_count = ctx.guild.member_count
        members = ctx.guild.members
        online = 0
        dnd = 0
        idle = 0
        offline = 0
        for member in members:
            if str(member.status) == "online":
                online += 1
            elif str(member.status) == "offline":
                offline += 1
            elif str(member.status) == "idle":
                idle += 1
            elif str(member.status) == "dnd":
                dnd += 1

        embed = Embed(
            colour=Colour.blurple(),
            description=textwrap.dedent(f"""
                **Server information**
                Created: {created}
                Voice region: {region}
                Features: {features}

                **Counts**
                Members: {member_count:,}
                Roles: {roles}
                Text: {text_channels}
                Voice: {voice_channels}
                Channel categories: {category_channels}

                **Members**
                {constants.Emojis.status_online} {online}
                {constants.Emojis.status_idle} {idle}
                {constants.Emojis.status_dnd} {dnd}
                {constants.Emojis.status_offline} {offline}
            """)
        )

        embed.set_thumbnail(url=ctx.guild.icon_url)

        await ctx.send(embed=embed)

    @command(name="user", aliases=["user_info", "member", "member_info"])
    async def user_info(self, ctx: Context, user: Member = None) -> None:
        """Returns info about a user."""
        if user is None:
            user = ctx.author

        # Do a role check if this is being executed on someone other than the caller
        if user != ctx.author and not with_role_check(ctx, *constants.MODERATION_ROLES):
            await ctx.send("You may not use this command on users other than yourself.")
            return

        # Non-staff may only do this in #bot-commands
        if not with_role_check(ctx, *constants.STAFF_ROLES):
            if not ctx.channel.id == constants.Channels.bot:
                raise InChannelCheckFailure(constants.Channels.bot)

        embed = await self.create_user_embed(ctx, user)

        await ctx.send(embed=embed)

    async def create_user_embed(self, ctx: Context, user: Member) -> Embed:
        """Creates an embed containing information on the `user`."""
        created = time_since(user.created_at, max_units=3)

        # Custom status
        custom_status = ''
        for activity in user.activities:
            if activity.name == 'Custom Status':
                state = escape_markdown(activity.state)
                custom_status = f'Status: {state}\n'

        name = str(user)
        if user.nick:
            name = f"{user.nick} ({name})"

        joined = time_since(user.joined_at, precision="days")
        roles = ", ".join(role.mention for role in user.roles if role.name != "@everyone")

        description = [
            textwrap.dedent(f"""
                **User Information**
                Created: {created}
                Profile: {user.mention}
                ID: {user.id}
                {custom_status}
                **Member Information**
                Joined: {joined}
                Roles: {roles or None}
            """).strip()
        ]

        # Show more verbose output in moderation channels for infractions and nominations
        if ctx.channel.id in constants.MODERATION_CHANNELS:
            description.append(await self.expanded_user_infraction_counts(user))
            description.append(await self.user_nomination_counts(user))
        else:
            description.append(await self.basic_user_infraction_counts(user))

        # Let's build the embed now
        embed = Embed(
            title=name,
            description="\n\n".join(description)
        )

        embed.set_thumbnail(url=user.avatar_url_as(format="png"))
        embed.colour = user.top_role.colour if roles else Colour.blurple()

        return embed

    async def basic_user_infraction_counts(self, member: Member) -> str:
        """Gets the total and active infraction counts for the given `member`."""
        infractions = await self.bot.api_client.get(
            'bot/infractions',
            params={
                'hidden': 'False',
                'user__id': str(member.id)
            }
        )

        total_infractions = len(infractions)
        active_infractions = sum(infraction['active'] for infraction in infractions)

        infraction_output = f"**Infractions**\nTotal: {total_infractions}\nActive: {active_infractions}"

        return infraction_output

    async def expanded_user_infraction_counts(self, member: Member) -> str:
        """
        Gets expanded infraction counts for the given `member`.

        The counts will be split by infraction type and the number of active infractions for each type will indicated
        in the output as well.
        """
        infractions = await self.bot.api_client.get(
            'bot/infractions',
            params={
                'user__id': str(member.id)
            }
        )

        infraction_output = ["**Infractions**"]
        if not infractions:
            infraction_output.append("This user has never received an infraction.")
        else:
            # Count infractions split by `type` and `active` status for this user
            infraction_types = set()
            infraction_counter = defaultdict(int)
            for infraction in infractions:
                infraction_type = infraction["type"]
                infraction_active = 'active' if infraction["active"] else 'inactive'

                infraction_types.add(infraction_type)
                infraction_counter[f"{infraction_active} {infraction_type}"] += 1

            # Format the output of the infraction counts
            for infraction_type in sorted(infraction_types):
                active_count = infraction_counter[f"active {infraction_type}"]
                total_count = active_count + infraction_counter[f"inactive {infraction_type}"]

                line = f"{infraction_type.capitalize()}s: {total_count}"
                if active_count:
                    line += f" ({active_count} active)"

                infraction_output.append(line)

        return "\n".join(infraction_output)

    async def user_nomination_counts(self, member: Member) -> str:
        """Gets the active and historical nomination counts for the given `member`."""
        nominations = await self.bot.api_client.get(
            'bot/nominations',
            params={
                'user__id': str(member.id)
            }
        )

        output = ["**Nominations**"]

        if not nominations:
            output.append("This user has never been nominated.")
        else:
            count = len(nominations)
            is_currently_nominated = any(nomination["active"] for nomination in nominations)
            nomination_noun = "nomination" if count == 1 else "nominations"

            if is_currently_nominated:
                output.append(f"This user is **currently** nominated ({count} {nomination_noun} in total).")
            else:
                output.append(f"This user has {count} historical {nomination_noun}, but is currently not nominated.")

        return "\n".join(output)

    def format_fields(self, mapping: Mapping[str, Any], field_width: Optional[int] = None) -> str:
        """Format a mapping to be readable to a human."""
        # sorting is technically superfluous but nice if you want to look for a specific field
        fields = sorted(mapping.items(), key=lambda item: item[0])

        if field_width is None:
            field_width = len(max(mapping.keys(), key=len))

        out = ''

        for key, val in fields:
            if isinstance(val, dict):
                # if we have dicts inside dicts we want to apply the same treatment to the inner dictionaries
                inner_width = int(field_width * 1.6)
                val = '\n' + self.format_fields(val, field_width=inner_width)

            elif isinstance(val, str):
                # split up text since it might be long
                text = textwrap.fill(val, width=100, replace_whitespace=False)

                # indent it, I guess you could do this with `wrap` and `join` but this is nicer
                val = textwrap.indent(text, ' ' * (field_width + len(': ')))

                # the first line is already indented so we `str.lstrip` it
                val = val.lstrip()

            if key == 'color':
                # makes the base 10 representation of a hex number readable to humans
                val = hex(val)

            out += '{0:>{width}}: {1}\n'.format(key, val, width=field_width)

        # remove trailing whitespace
        return out.rstrip()

    @cooldown_with_role_bypass(2, 60 * 3, BucketType.member, bypass_roles=constants.STAFF_ROLES)
    @group(invoke_without_command=True)
    @in_channel(constants.Channels.bot, bypass_roles=constants.STAFF_ROLES)
    async def raw(self, ctx: Context, *, message: discord.Message, json: bool = False) -> None:
        """Shows information about the raw API response."""
        # I *guess* it could be deleted right as the command is invoked but I felt like it wasn't worth handling
        # doing this extra request is also much easier than trying to convert everything back into a dictionary again
        raw_data = await ctx.bot.http.get_message(message.channel.id, message.id)

        paginator = commands.Paginator()

        def add_content(title: str, content: str) -> None:
            paginator.add_line(f'== {title} ==\n')
            # replace backticks as it breaks out of code blocks. Spaces seemed to be the most reasonable solution.
            # we hope it's not close to 2000
            paginator.add_line(content.replace('```', '`` `'))
            paginator.close_page()

        if message.content:
            add_content('Raw message', message.content)

        transformer = pprint.pformat if json else self.format_fields
        for field_name in ('embeds', 'attachments'):
            data = raw_data[field_name]

            if not data:
                continue

            total = len(data)
            for current, item in enumerate(data, start=1):
                title = f'Raw {field_name} ({current}/{total})'
                add_content(title, transformer(item))

        for page in paginator.pages:
            await ctx.send(page)

    @raw.command()
    async def json(self, ctx: Context, message: discord.Message) -> None:
        """Shows information about the raw API response in a copy-pasteable Python format."""
        await ctx.invoke(self.raw, message=message, json=True)


def setup(bot: Bot) -> None:
    """Information cog load."""
    bot.add_cog(Information(bot))
    log.info("Cog loaded: Information")
