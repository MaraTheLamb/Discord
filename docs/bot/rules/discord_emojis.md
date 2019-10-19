# Discord Emojis

> Auto-generated documentation for [bot.rules.discord_emojis](https://github.com/python-discord/bot/blob/master/bot/rules/discord_emojis.py) module.

- [Index](../../README.md#modules) / [Bot](../index.md#bot) / [Rules](index.md#rules) / Discord Emojis
  - [apply](#apply)

## apply

[🔍 find in source code](https://github.com/python-discord/bot/blob/master/bot/rules/discord_emojis.py#L10)

```python
def apply(
    last_message: Message,
    recent_messages: List[discord.message.Message],
    config: Dict[str, int],
) -> Union[Tuple[str, Iterable[discord.member.Member], Iterable[discord.message.Message]], NoneType]
```

Detects total Discord emojis (excluding Unicode emojis) exceeding the limit sent by a single user.
