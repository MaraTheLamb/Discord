import os

# Debug mode
DEBUG_MODE = True if 'local' in os.environ.get("SITE_URL", "local") else False

# Server
PYTHON_GUILD = 267624335836053506

# Channels
BOT_COMMANDS_CHANNEL = 267659945086812160
CHECKPOINT_TEST_CHANNEL = 422077681434099723
DEVLOG_CHANNEL = 409308876241108992
DEVTEST_CHANNEL = 414574275865870337
HELP1_CHANNEL = 303906576991780866
HELP2_CHANNEL = 303906556754395136
HELP3_CHANNEL = 303906514266226689
HELP4_CHANNEL = 439702951246692352
HELPERS_CHANNEL = 385474242440986624
MOD_LOG_CHANNEL = 282638479504965634
PYTHON_CHANNEL = 267624335836053506
VERIFICATION_CHANNEL = 352442727016693763

# Roles
ADMIN_ROLE = 267628507062992896
MODERATOR_ROLE = 267629731250176001
VERIFIED_ROLE = 352427296948486144
OWNER_ROLE = 267627879762755584
DEVOPS_ROLE = 409416496733880320
CONTRIBUTOR_ROLE = 295488872404484098

# Clickup
CLICKUP_KEY = os.environ.get("CLICKUP_KEY")
CLICKUP_SPACE = 757069
CLICKUP_TEAM = 754996

# URLs
DEPLOY_URL = os.environ.get("DEPLOY_URL")
STATUS_URL = os.environ.get("STATUS_URL")
SITE_URL = os.environ.get("SITE_URL", "pythondiscord.local:8080")
SITE_PROTOCOL = 'http' if DEBUG_MODE else 'https'
SITE_API_URL = f"{SITE_PROTOCOL}://api.{SITE_URL}"
GITHUB_URL_BOT = "https://github.com/discord-python/bot"
BOT_AVATAR_URL = "https://raw.githubusercontent.com/discord-python/branding/master/logos/logo_circle/logo_circle.png"
OMDB_URL = "http://www.omdbapi.com/"

# Keys
DEPLOY_BOT_KEY = os.environ.get("DEPLOY_BOT_KEY")
DEPLOY_SITE_KEY = os.environ.get("DEPLOY_SITE_KEY")
SITE_API_KEY = os.environ.get("BOT_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Bot internals
HELP_PREFIX = "bot."
TAG_COOLDOWN = 60  # Per channel, per tag

# There are Emoji objects, but they're not usable until the bot is connected,
# so we're using string constants instead
GREEN_CHEVRON = "<:greenchevron:418104310329769993>"
RED_CHEVRON = "<:redchevron:418112778184818698>"
WHITE_CHEVRON = "<:whitechevron:418110396973711363>"
PAID_ICON = "<:icon_paid:433750296724897798>"
FREEWARE_ICON = "<:icon_freeware:433750375959494657>"
FREE_ICON = "<:icon_free:433750340509368330>"
LINK_ICON = "<:icon_link:433703566830469133>"

# PaperTrail logging
PAPERTRAIL_ADDRESS = os.environ.get("PAPERTRAIL_ADDRESS") or None
PAPERTRAIL_PORT = int(os.environ.get("PAPERTRAIL_PORT") or 0)

# Paths
BOT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BOT_DIR, os.pardir))

# Bot replies
NEGATIVE_REPLIES = [
    "Noooooo!!",
    "Nope.",
    "I'm sorry Dave, I'm afraid I can't do that.",
    "I don't think so.",
    "Not gonna happen.",
    "Out of the question.",
    "Huh? No.",
    "Nah.",
    "Naw.",
    "Not likely.",
    "No way, José.",
    "Not in a million years.",
    "Fat chance.",
    "Certainly not.",
    "NEGATORY."
]

POSITIVE_REPLIES = [
    "Yep.",
    "Absolutely!",
    "Can do!",
    "Affirmative!",
    "Yeah okay.",
    "Sure.",
    "Sure thing!",
    "You're the boss!",
    "Okay.",
    "No problem.",
    "I got you.",
    "Alright.",
    "You got it!",
    "ROGER THAT",
    "Of course!",
    "Aye aye, cap'n!",
    "I'll allow it."
]

ERROR_REPLIES = [
    "Please don't do that.",
    "You have to stop.",
    "Do you mind?",
    "In the future, don't do that.",
    "That was a mistake.",
    "You blew it.",
    "You're bad at computers.",
    "Are you trying to kill me?",
    "Noooooo!!"
]
