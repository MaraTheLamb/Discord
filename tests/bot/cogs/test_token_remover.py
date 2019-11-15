import asyncio
import logging
import unittest
from unittest.mock import MagicMock

from discord import Colour

from bot.cogs.token_remover import (
    DELETION_MESSAGE_TEMPLATE,
    TokenRemover,
    setup as setup_cog,
)
from bot.constants import Channels, Colours, Event, Icons
from tests.helpers import AsyncMock, MockBot, MockMessage


class TokenRemoverTests(unittest.TestCase):
    """Tests the `TokenRemover` cog."""

    def setUp(self):
        """Adds the cog, a bot, and a message to the instance for usage in tests."""
        self.bot = MockBot()
        self.bot.get_cog.return_value = MagicMock()
        self.bot.get_cog.return_value.send_log_message = AsyncMock()
        self.cog = TokenRemover(bot=self.bot)

        self.msg = MockMessage(id=555, content='')
        self.msg.author.__str__ = MagicMock()
        self.msg.author.__str__.return_value = 'lemon'
        self.msg.author.bot = False
        self.msg.author.avatar_url_as.return_value = 'picture-lemon.png'
        self.msg.author.id = 42
        self.msg.author.mention = '@lemon'
        self.msg.channel.mention = "#lemonade-stand"

    def test_is_valid_user_id_is_true_for_numeric_content(self):
        """A string decoding to numeric characters is a valid user ID."""
        # MTIz = base64(123)
        self.assertTrue(TokenRemover.is_valid_user_id('MTIz'))

    def test_is_valid_user_id_is_false_for_alphabetic_content(self):
        """A string decoding to alphabetic characters is not a valid user ID."""
        # YWJj = base64(abc)
        self.assertFalse(TokenRemover.is_valid_user_id('YWJj'))

    def test_is_valid_timestamp_is_true_for_valid_timestamps(self):
        """A string decoding to a valid timestamp should be recognized as such."""
        self.assertTrue(TokenRemover.is_valid_timestamp('DN9r_A'))

    def test_is_valid_timestamp_is_false_for_invalid_values(self):
        """A string not decoding to a valid timestamp should not be recognized as such."""
        # MTIz = base64(123)
        self.assertFalse(TokenRemover.is_valid_timestamp('MTIz'))

    def test_mod_log_property(self):
        """The `mod_log` property should ask the bot to return the `ModLog` cog."""
        self.bot.get_cog.return_value = 'lemon'
        self.assertEqual(self.cog.mod_log, self.bot.get_cog.return_value)
        self.bot.get_cog.assert_called_once_with('ModLog')

    def test_ignores_bot_messages(self):
        """When the message event handler is called with a bot message, nothing is done."""
        self.msg.author.bot = True
        coroutine = self.cog.on_message(self.msg)
        self.assertIsNone(asyncio.run(coroutine))

    def test_ignores_messages_without_tokens(self):
        """Messages without anything looking like a token are ignored."""
        for content in ('', 'lemon wins'):
            with self.subTest(content=content):
                self.msg.content = content
                coroutine = self.cog.on_message(self.msg)
                self.assertIsNone(asyncio.run(coroutine))

    def test_ignores_messages_with_invalid_tokens(self):
        """Messages with values that are invalid tokens are ignored."""
        for content in ('foo.bar.baz', 'x.y.'):
            with self.subTest(content=content):
                self.msg.content = content
                coroutine = self.cog.on_message(self.msg)
                self.assertIsNone(asyncio.run(coroutine))

    def test_censors_valid_tokens(self):
        """Valid tokens are censored."""
        cases = (
            # (content, censored_token)
            ('MTIz.DN9R_A.xyz', 'MTIz.DN9R_A.xxx'),
        )

        for content, censored_token in cases:
            with self.subTest(content=content, censored_token=censored_token):
                self.msg.content = content
                coroutine = self.cog.on_message(self.msg)
                with self.assertLogs(logger='bot.cogs.token_remover', level=logging.DEBUG) as cm:
                    self.assertIsNone(asyncio.run(coroutine))  # no return value

                [line] = cm.output
                log_message = (
                    "Censored a seemingly valid token sent by "
                    "lemon (`42`) in #lemonade-stand, "
                    f"token was `{censored_token}`"
                )
                self.assertIn(log_message, line)

                self.msg.delete.assert_called_once_with()
                self.msg.channel.send.assert_called_once_with(
                    DELETION_MESSAGE_TEMPLATE.format(mention='@lemon')
                )
                self.bot.get_cog.assert_called_with('ModLog')
                self.msg.author.avatar_url_as.assert_called_once_with(static_format='png')

                mod_log = self.bot.get_cog.return_value
                mod_log.ignore.assert_called_once_with(Event.message_delete, self.msg.id)
                mod_log.send_log_message.assert_called_once_with(
                    icon_url=Icons.token_removed,
                    colour=Colour(Colours.soft_red),
                    title="Token removed!",
                    text=log_message,
                    thumbnail='picture-lemon.png',
                    channel_id=Channels.mod_alerts
                )


class TokenRemoverSetupTests(unittest.TestCase):
    """Tests setup of the `TokenRemover` cog."""

    def test_setup(self):
        """Setup of the cog should log a message at `INFO` level."""
        bot = MockBot()
        with self.assertLogs(logger='bot.cogs.token_remover', level=logging.INFO) as cm:
            setup_cog(bot)

        [line] = cm.output
        bot.add_cog.assert_called_once()
        self.assertIn("Cog loaded: TokenRemover", line)
