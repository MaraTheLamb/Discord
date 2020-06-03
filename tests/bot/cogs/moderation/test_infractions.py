import textwrap
import unittest
from unittest.mock import AsyncMock, Mock, patch

from bot.cogs.moderation.infractions import Infractions
from tests.helpers import MockBot, MockContext, MockGuild, MockMember, MockRole


class TruncationTests(unittest.IsolatedAsyncioTestCase):
    """Tests for ban and kick command reason truncation."""

    def setUp(self):
        self.bot = MockBot()
        self.cog = Infractions(self.bot)
        self.user = MockMember(id=1234, top_role=MockRole(id=3577, position=10))
        self.target = MockMember(id=1265, top_role=MockRole(id=9876, position=0))
        self.guild = MockGuild(id=4567)
        self.ctx = MockContext(bot=self.bot, author=self.user, guild=self.guild)

    @patch("bot.cogs.moderation.utils.get_active_infraction")
    @patch("bot.cogs.moderation.utils.post_infraction")
    async def test_apply_ban_reason_truncation(self, post_infraction_mock, get_active_mock):
        """Should truncate reason for `ctx.guild.ban`."""
        get_active_mock.return_value = None
        post_infraction_mock.return_value = {"foo": "bar"}

        self.cog.apply_infraction = AsyncMock()
        self.bot.get_cog.return_value = AsyncMock()
        self.cog.mod_log.ignore = Mock()
        self.ctx.guild.ban = Mock()

        await self.cog.apply_ban(self.ctx, self.target, "foo bar" * 3000)
        self.ctx.guild.ban.assert_called_once_with(
            self.target,
            reason=textwrap.shorten("foo bar" * 3000, 512, placeholder="..."),
            delete_message_days=0
        )
        self.cog.apply_infraction.assert_awaited_once_with(
            self.ctx, {"foo": "bar"}, self.target, self.ctx.guild.ban.return_value
        )

    @patch("bot.cogs.moderation.utils.post_infraction")
    async def test_apply_kick_reason_truncation(self, post_infraction_mock):
        """Should truncate reason for `Member.kick`."""
        post_infraction_mock.return_value = {"foo": "bar"}

        self.cog.apply_infraction = AsyncMock()
        self.cog.mod_log.ignore = Mock()
        self.target.kick = Mock()

        await self.cog.apply_kick(self.ctx, self.target, "foo bar" * 3000)
        self.target.kick.assert_called_once_with(reason=textwrap.shorten("foo bar" * 3000, 512, placeholder="..."))
        self.cog.apply_infraction.assert_awaited_once_with(
            self.ctx, {"foo": "bar"}, self.target, self.target.kick.return_value
        )
