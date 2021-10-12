import re

INVITE_RE = re.compile(
    r"(discord([\.,]|dot)gg|"                     # Could be discord.gg/
    r"discord([\.,]|dot)com(\/|slash)invite|"     # or discord.com/invite/
    r"discordapp([\.,]|dot)com(\/|slash)invite|"  # or discordapp.com/invite/
    r"discord([\.,]|dot)me|"                      # or discord.me
    r"discord([\.,]|dot)li|"                      # or discord.li
    r"discord([\.,]|dot)io|"                      # or discord.io.
    r"(\B([\.,]|dot))gg"                          # or .gg/
    r")([\/]|slash)"                              # / or 'slash'
    r"(?P<invite>[a-zA-Z0-9\-]+)",                # the invite code itself
    flags=re.IGNORECASE
)
