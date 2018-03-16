# coding=utf-8
import ast
import logging
import re
import time

from discord import Embed, Message
from discord.ext.commands import AutoShardedBot, Context, command, group

from dulwich.repo import Repo

from bot.constants import (BOT_CHANNEL, DEVTEST_CHANNEL, HELP1_CHANNEL,
                           HELP2_CHANNEL, HELP3_CHANNEL, PYTHON_CHANNEL,
                           PYTHON_GUILD, VERIFIED_ROLE)
from bot.decorators import with_role

log = logging.getLogger(__name__)


class Bot:
    """
    Bot information commands
    """

    def __init__(self, bot: AutoShardedBot):
        self.bot = bot

        # Stores allowed channels plus unix timestamp from last call
        self.channel_cooldowns = {HELP1_CHANNEL: 0,
                                  HELP2_CHANNEL: 0,
                                  HELP3_CHANNEL: 0,
                                  PYTHON_CHANNEL: 0,
                                  DEVTEST_CHANNEL: 0,
                                  BOT_CHANNEL: 0
        }  # noqa. E124

    @group(invoke_without_command=True, name="bot", hidden=True)
    @with_role(VERIFIED_ROLE)
    async def bot_group(self, ctx: Context):
        """
        Bot informational commands
        """

        await ctx.invoke(self.bot.get_command("help"), "bot")

    @bot_group.command(aliases=["about"], hidden=True)
    @with_role(VERIFIED_ROLE)
    async def info(self, ctx: Context):
        """
        Get information about the bot
        """

        embed = Embed(
            description="A utility bot designed just for the Python server! Try `bot.help()` for more info.",
            url="https://github.com/discord-python/bot"
        )

        repo = Repo(".")
        sha = repo[repo.head()].sha().hexdigest()

        embed.add_field(name="Total Users", value=str(len(self.bot.get_guild(PYTHON_GUILD).members)))
        embed.add_field(name="Git SHA", value=str(sha)[:7])

        embed.set_author(
            name="Python Bot",
            url="https://github.com/discord-python/bot",
            icon_url="https://raw.githubusercontent.com/discord-python/branding/master/logos/logo_circle.png"
        )

        log.info(f"{ctx.author} called bot.about(). Returning information about the bot.")
        await ctx.send(embed=embed)

    @command(name="info()", aliases=["bot.info", "bot.about", "bot.about()", "info", "bot.info()"])
    @with_role(VERIFIED_ROLE)
    async def info_wrapper(self, ctx: Context):
        """
        Get information about the bot
        """

        await ctx.invoke(self.info)

    def repl_stripping(self, msg: str):
        """
        Strip msg in order to extract Python code out of REPL output.

        Tries to strip out REPL Python code out of msg and returns the stripped msg.
        """
        final = ""
        for line in msg.splitlines(keepends=True):
            if line.startswith(">>>") or line.startswith("..."):
                final += line[4:]
        if len(final):
            return msg
        else:
            return final

    def codeblock_stripping(self, msg: str):
        """
        Strip msg in order to find Python code.

        Tries to strip out Python code out of msg and returns the stripped block or
        None if the block is a valid Python codeblock.
        """
        if msg.count("\n") >= 3:
            # Filtering valid Python codeblocks and exiting if a valid Python codeblock is found
            if re.search("```(python|py)\n((?:.*\n*)+)```", msg, re.IGNORECASE):
                log.trace("Someone wrote a message that was already a "
                          "valid Python syntax highlighted code block. No action taken.")
                return None

            else:
                # Stripping backticks from every line of the message.
                log.trace(f"Stripping backticks from message.\n\n{msg}\n\n")
                content = ""
                for line in msg.splitlines(keepends=True):
                    content += line.strip("`")

                content = content.strip()

                # Remove "Python" or "Py" from top of the message if exists
                log.trace(f"Removing 'py' or 'python' from message.\n\n{content}\n\n")
                if content.lower().startswith("python"):
                    content = content[6:]
                elif content.lower().startswith("py"):
                    content = content[2:]

                # Strip again to remove the whitespace(s) left before the code
                # If the msg looked like "Python <code>" before removing Python
                # And strips REPL code out of the message if there is any
                content = self.repl_stripping(content.strip())
                log.trace(f"Returning message.\n\n{content}\n\n")
                return content

    async def on_message(self, msg: Message):
        if msg.channel.id in self.channel_cooldowns:
            on_cooldown = time.time() - self.channel_cooldowns[msg.channel.id] < 300
            if not on_cooldown or msg.channel.id == DEVTEST_CHANNEL:
                try:
                    howto_embed = ""
                    not_backticks = ["'''", "\"\"\"", "´´´"]
                    python_syntax = any(
                        msg.content[3:9].lower() == "python",
                        msg.content[3:5].lower() == "py"
                    )

                    bad_ticks = msg.content[:3] in not_backticks

                    if bad_ticks and python_syntax:
                        howto = (f"You are using the wrong signs, use ``` instead of"
                                 f" {not_backticks.index(msg.content[:3])}")

                        howto_embed = Embed(description=howto)
                    else:
                        content = self.codeblock_stripping(msg.content)
                        if not content:
                            return

                        # Attempts to parse the message into an AST node.
                        # Invalid Python code will raise a SyntaxError.
                        tree = ast.parse(content)

                        # Multiple lines of single words could be interpreted as expressions.
                        # This check is to avoid all nodes being parsed as expressions.
                        # (e.g. words over multiple lines)
                        if not all(isinstance(node, ast.Expr) for node in tree.body):
                            space_left = 204
                            # Shorten the code.
                            if len(content) >= space_left:
                                current_length = 0
                                for line in content.splitlines(keepends=True):
                                    if current_length+len(line) > space_left:
                                        break
                                    current_length += len(line)
                                content = content[:current_length]+"#..."

                            howto = (f"Hey {msg.author.mention}!\n"
                                     f"I noticed you were trying to paste code into this channel.\n"
                                     "Discord has support for Markdown, which allows you to post code with full syntax"
                                     " highlighting. Please use these whenever you paste code, as this helps improve"
                                     " the legibility and makes it easier for us to help you.\nTo do this, use the"
                                     f"following method:\n\n\`\`\`Python\n{content}\n\`\`\`\n\nThis will result in the"
                                     f" following:\n```Python\n{content}\n```")
                            howto_embed = Embed(description=howto)
                        else:
                            return
                    log.debug(f"{msg.author} posted something that needed to be put inside python code blocks. "
                              "Sending the user some instructions.")
                    await msg.channel.send(embed=howto_embed)
                    self.channel_cooldowns[msg.channel.id] = time.time()
                except SyntaxError:
                    log.trace(f"{msg.author} posted in a help channel, and when we tried to parse it as Python code, "
                              "ast.parse raised a SyntaxError. This probably just means it wasn't Python code. "
                              f"The message that was posted was:\n\n{msg.content}\n\n")
                    pass


def setup(bot):
    bot.add_cog(Bot(bot))
    log.info("Cog loaded: Bot")
