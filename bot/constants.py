# coding=utf-8
import os

PYTHON_GUILD = 267624335836053506

BOT_CHANNEL = 267659945086812160
HELP1_CHANNEL = 303906576991780866
HELP2_CHANNEL = 303906556754395136
HELP3_CHANNEL = 303906514266226689
PYTHON_CHANNEL = 267624335836053506
DEVLOG_CHANNEL = 409308876241108992
DEVTEST_CHANNEL = 414574275865870337
VERIFICATION_CHANNEL = 352442727016693763

ADMIN_ROLE = 267628507062992896
MODERATOR_ROLE = 267629731250176001
VERIFIED_ROLE = 352427296948486144
OWNER_ROLE = 267627879762755584
DEVOPS_ROLE = 409416496733880320

CLICKUP_KEY = os.environ.get("CLICKUP_KEY")
CLICKUP_SPACE = 757069
CLICKUP_TEAM = 754996

DEPLOY_URL = os.environ.get("DEPLOY_URL")
STATUS_URL = os.environ.get("STATUS_URL")

DEPLOY_BOT_KEY = os.environ.get("DEPLOY_BOT_KEY")
DEPLOY_SITE_KEY = os.environ.get("DEPLOY_SITE_KEY")

SITE_API_KEY = os.environ.get("BOT_API_KEY")
SITE_API_USER_URL = "https://api.pythondiscord.com/user"

HELP_PREFIX = "bot."

# There are Emoji objects, but they're not usable until the bot is connected,
# so we're using string constants instead
GREEN_CHEVRON = "<:greenchevron:418104310329769993>"
RED_CHEVRON = "<:redchevron:418112778184818698>"
WHITE_CHEVRON = "<:whitechevron:418110396973711363>"
