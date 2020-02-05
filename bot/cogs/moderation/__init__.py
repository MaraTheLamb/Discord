from bot.bot import Bot
from .infractions import Infractions
from .management import ModManagement
from .modlog import ModLog
from .superstarify import Superstarify


def setup(bot: Bot) -> None:
    """Load the Infractions, ModManagement, ModLog, and Superstarify cogs."""
    bot.add_cog(Infractions(bot))
    bot.add_cog(ModLog(bot))
    bot.add_cog(ModManagement(bot))
    bot.add_cog(Superstarify(bot))
