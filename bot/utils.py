# coding=utf-8
import asyncio
from typing import Iterable

from discord import Embed, Member, Reaction
from discord.abc import User
from discord.ext.commands import Context, Paginator

LEFT_EMOJI = "\u2B05"
RIGHT_EMOJI = "\u27A1"
DELETE_EMOJI = "\U0001F5D1"

PAGINATION_EMOJI = [LEFT_EMOJI, RIGHT_EMOJI, DELETE_EMOJI]


class CaseInsensitiveDict(dict):
    """
    We found this class on StackOverflow. Thanks to m000 for writing it!

    https://stackoverflow.com/a/32888599/4022104
    """

    @classmethod
    def _k(cls, key):
        return key.lower() if isinstance(key, str) else key

    def __init__(self, *args, **kwargs):
        super(CaseInsensitiveDict, self).__init__(*args, **kwargs)
        self._convert_keys()

    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(self.__class__._k(key))

    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(self.__class__._k(key), value)

    def __delitem__(self, key):
        return super(CaseInsensitiveDict, self).__delitem__(self.__class__._k(key))

    def __contains__(self, key):
        return super(CaseInsensitiveDict, self).__contains__(self.__class__._k(key))

    def pop(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).pop(self.__class__._k(key), *args, **kwargs)

    def get(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).get(self.__class__._k(key), *args, **kwargs)

    def setdefault(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).setdefault(self.__class__._k(key), *args, **kwargs)

    def update(self, E=None, **F):
        super(CaseInsensitiveDict, self).update(self.__class__(E))
        super(CaseInsensitiveDict, self).update(self.__class__(**F))

    def _convert_keys(self):
        for k in list(self.keys()):
            v = super(CaseInsensitiveDict, self).pop(k)
            self.__setitem__(k, v)


async def paginate(lines: Iterable[str], ctx: Context, embed: Embed,
                   prefix: str = "", suffix: str = "", max_size: int = 500, empty: bool = True,
                   restrict_to_user: User = None):
    """
    Use a paginator and set of reactions to provide pagination over a set of lines. The reactions are used to
    switch page, or to finish with pagination.

    When used, this will send a message using `ctx.send()` and apply a set of reactions to it. These reactions may
    be used to change page, or to remove pagination from the message. Pagination will also be removed automatically
    if no reaction is added for five minutes (300 seconds).

    >>> embed = Embed()
    >>> embed.set_author(name="Some Operation", url=url, icon_url=icon)
    >>> await paginate(
    ...     (line for line in lines),
    ...     ctx, embed
    ... )

    :param lines: The lines to be paginated
    :param ctx: Current context object
    :param embed: A pre-configured embed to be used as a template for each page
    :param prefix: Text to place before each page
    :param suffix: Text to place after each page
    :param max_size: The maximum number of characters on each page
    :param empty: Whether to place an empty line between each given line
    :param restrict_to_user: A user to lock pagination operations to for this message, if supplied
    """

    paginator = Paginator(prefix=prefix, suffix=suffix, max_size=max_size)
    current_page = 0

    for line in lines:
        paginator.add_line(line, empty=empty)

    embed.description = paginator.pages[current_page]
    embed.set_footer(text=f"Page {current_page + 1}/{len(paginator.pages)}")

    message = await ctx.send(embed=embed)

    if len(paginator.pages) <= 1:
        return  # There's only one page

    def event_check(reaction_: Reaction, user_: Member):
        """
        Make sure that this reaction is what we want to operate on
        """

        return (
            reaction_.message.id == message.id and  # Reaction on this specific message
            reaction_.emoji in PAGINATION_EMOJI and  # One of the reactions we handle
            user_.id != ctx.bot.user.id and (  # Not applied by the bot itself
                not restrict_to_user or   # Unrestricted if there's no user to restrict to, or...
                user_.id == restrict_to_user.id  # Only by the restricted user
            )
        )

    for emoji in PAGINATION_EMOJI:
        # Add all the applicable emoji to the message
        await message.add_reaction(emoji)

    while True:
        try:
            reaction, user = await ctx.bot.wait_for("reaction_add", timeout=300, check=event_check)
        except asyncio.TimeoutError:
            break  # We're done, no reactions for the last 5 minutes

        if reaction.emoji == DELETE_EMOJI:
            break

        if reaction.emoji == LEFT_EMOJI:
            await message.remove_reaction(reaction.emoji, user)

            if current_page <= 0:
                continue

            current_page -= 1

            embed.description = paginator.pages[current_page]
            embed.set_footer(text=f"Page {current_page + 1}/{len(paginator.pages)}")
            await message.edit(embed=embed)

        if reaction.emoji == RIGHT_EMOJI:
            await message.remove_reaction(reaction.emoji, user)

            if current_page >= len(paginator.pages) - 1:
                continue

            current_page += 1

            embed.description = paginator.pages[current_page]
            embed.set_footer(text=f"Page {current_page + 1}/{len(paginator.pages)}")
            await message.edit(embed=embed)

    await message.clear_reactions()
