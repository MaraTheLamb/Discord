import logging
import random
import socket
from ssl import CertificateError

import discord
from aiohttp import AsyncResolver, ClientConnectorError, ClientSession, TCPConnector
from discord.ext.commands import BadArgument, Context, Converter
from fuzzywuzzy import fuzz

from bot.constants import DEBUG_MODE, Keys, URLs
from bot.utils import disambiguate


log = logging.getLogger(__name__)


class Snake(Converter):
    snakes = None
    special_cases = None

    async def convert(self, ctx, name):
        await self.build_list()
        name = name.lower()

        if name == 'python':
            return 'Python (programming language)'

        def get_potential(iterable, *, threshold=80):
            nonlocal name
            potential = []

            for item in iterable:
                original, item = item, item.lower()

                if name == item:
                    return [original]

                a, b = fuzz.ratio(name, item), fuzz.partial_ratio(name, item)
                if a >= threshold or b >= threshold:
                    potential.append(original)

            return potential

        # Handle special cases
        if name.lower() in self.special_cases:
            return self.special_cases.get(name.lower(), name.lower())

        names = {snake['name']: snake['scientific'] for snake in self.snakes}
        all_names = names.keys() | names.values()
        timeout = len(all_names) * (3 / 4)

        title_ = 'Found multiple choices. Please choose the correct one.'
        embed = discord.Embed(title=title_, colour=0x59982F)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        name = await disambiguate(ctx, get_potential(all_names), timeout=timeout, embed=embed)
        return names.get(name, name)

    @classmethod
    async def build_list(cls):

        headers = {"X-API-KEY": Keys.site_api}

        # Set up the session
        if DEBUG_MODE:
            http_session = ClientSession(
                connector=TCPConnector(
                    resolver=AsyncResolver(),
                    family=socket.AF_INET,
                    verify_ssl=False,
                )
            )
        else:
            http_session = ClientSession(
                connector=TCPConnector(
                    resolver=AsyncResolver()
                )
            )

        # Get all the snakes
        if cls.snakes is None:
            response = await http_session.get(
                URLs.site_names_api,
                params={"get_all": "true"},
                headers=headers
            )
            cls.snakes = await response.json()

        # Get the special cases
        if cls.special_cases is None:
            response = await http_session.get(
                URLs.site_special_api,
                headers=headers
            )
            special_cases = await response.json()
            cls.special_cases = {snake['name'].lower(): snake for snake in special_cases}

        # Close the session
        http_session.close()

    @classmethod
    async def random(cls):
        """
        This is stupid. We should find a way to
        somehow get the global session into a
        global context, so I can get it from here.
        :return:
        """

        await cls.build_list()
        names = [snake['scientific'] for snake in cls.snakes]
        return random.choice(names)


class ValidPythonIdentifier(Converter):
    """
    A converter that checks whether the given string is a valid Python identifier.

    This is used to have package names
    that correspond to how you would use
    the package in your code, e.g.
    `import package`. Raises `BadArgument`
    if the argument is not a valid Python
    identifier, and simply passes through
    the given argument otherwise.
    """

    @staticmethod
    async def convert(ctx, argument: str):
        if not argument.isidentifier():
            raise BadArgument(f"`{argument}` is not a valid Python identifier")
        return argument


class ValidURL(Converter):
    """
    Represents a valid webpage URL.

    This converter checks whether the given
    URL can be reached and requesting it returns
    a status code of 200. If not, `BadArgument`
    is raised. Otherwise, it simply passes through the given URL.
    """

    @staticmethod
    async def convert(ctx, url: str):
        try:
            async with ctx.bot.http_session.get(url) as resp:
                if resp.status != 200:
                    raise BadArgument(
                        f"HTTP GET on `{url}` returned status `{resp.status_code}`, expected 200"
                    )
        except CertificateError:
            if url.startswith('https'):
                raise BadArgument(
                    f"Got a `CertificateError` for URL `{url}`. Does it support HTTPS?"
                )
            raise BadArgument(f"Got a `CertificateError` for URL `{url}`.")
        except ValueError:
            raise BadArgument(f"`{url}` doesn't look like a valid hostname to me.")
        except ClientConnectorError:
            raise BadArgument(f"Cannot connect to host with URL `{url}`.")
        return url


class InfractionSearchQuery(Converter):
    """
    A converter that checks if the argument is a Discord user, and if not, falls back to a string.
    """

    @staticmethod
    async def convert(ctx, arg):
        try:
            maybe_snowflake = arg.strip("<@!>")
            return await ctx.bot.get_user_info(maybe_snowflake)
        except (discord.NotFound, discord.HTTPException):
            return arg


class Subreddit(Converter):
    """
    Forces a string to begin with "r/" and checks if it's a valid subreddit.
    """

    @staticmethod
    async def convert(ctx, sub: str):
        sub = sub.lower()

        if not sub.startswith("r/"):
            sub = f"r/{sub}"

        resp = await ctx.bot.http_session.get(
            "https://www.reddit.com/subreddits/search.json",
            params={"q": sub}
        )

        json = await resp.json()
        if not json["data"]["children"]:
            raise BadArgument(
                f"The subreddit `{sub}` either doesn't exist, or it has no posts."
            )

        return sub


class TagNameConverter(Converter):
    @staticmethod
    async def convert(ctx: Context, tag_name: str):
        def is_number(value):
            try:
                float(value)
            except ValueError:
                return False
            return True

        tag_name = tag_name.lower().strip()

        # The tag name has at least one invalid character.
        if ascii(tag_name)[1:-1] != tag_name:
            log.warning(f"{ctx.author} tried to put an invalid character in a tag name. "
                        "Rejecting the request.")
            raise BadArgument("Don't be ridiculous, you can't use that character!")

        # The tag name is either empty, or consists of nothing but whitespace.
        elif not tag_name:
            log.warning(f"{ctx.author} tried to create a tag with "
                        "a name consisting only of whitespace. "
                        "Rejecting the request.")
            raise BadArgument("Tag names should not be empty, or filled with whitespace.")

        # The tag name is a number of some kind, we don't allow that.
        elif is_number(tag_name):
            log.warning(f"{ctx.author} tried to create a tag with a digit as its name. "
                        "Rejecting the request.")
            raise BadArgument("Tag names can't be numbers.")

        # The tag name is longer than 127 characters.
        elif len(tag_name) > 127:
            log.warning(f"{ctx.author} tried to request a tag name with over 127 characters. "
                        "Rejecting the request.")
            raise BadArgument("Are you insane? That's way too long!")

        return tag_name


class TagContentConverter(Converter):
    @staticmethod
    async def convert(ctx: Context, tag_content: str):
        tag_content = tag_content.strip()

        # The tag contents should not be empty, or filled with whitespace.
        if not tag_content:
            log.warning(f"{ctx.author} tried to create a tag containing only whitespace. "
                        "Rejecting the request.")
            raise BadArgument("Tag contents should not be empty, or filled with whitespace.")

        return tag_content
