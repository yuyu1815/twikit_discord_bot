# Issue Resolution Summary: 'test-new-structure' Command Not Visible

## Issue Description
The 'test-new-structure' command was not visible in Discord and could not be used, despite being properly defined in the code.

## Root Cause Analysis
After examining the code, I identified that the issue was not with the command implementation itself, but with the Discord command registration process:

1. The command is correctly defined in `src/cogs/twitter_commands.py` with the proper decorators:
   ```python
   @app_commands.command(name='test-new-structure')
   @app_commands.checks.has_permissions(manage_channels=True)
   async def test_new_structure(self, interaction: discord.Interaction):
   ```

2. The database tables that the command queries (`global_twitter_users` and `guild_twitter_feeds`) exist and are properly defined in `src/core/database.py`.

3. The TwitterCommands cog is loaded correctly during the bot's initialization in `src/core/bot.py`.

4. **The missing step**: The command tree was not synced with Discord's API after the command was added to the cog.

## Solution
The solution is to run the bot with the `--update` flag to sync the command tree with Discord's API:

```
python main.py --update
```

This executes the `update_slash_commands` function in `main.py`, which:
1. Creates a bot instance
2. Starts the bot
3. Syncs the command tree with Discord's API
4. Closes the bot

After syncing the command tree, the 'test-new-structure' command will be visible and usable in Discord.

## Why This Works
In Discord's slash command system, there are two parts to adding a new command:

1. **Code Implementation**: Defining the command in your bot's code (which was already done correctly)
2. **API Registration**: Syncing the command tree with Discord's API to make the command visible to users

The second step is necessary whenever new commands are added to the bot. This is a one-time operation that needs to be performed after adding new commands.

The `--update` flag in the bot's `main.py` script is specifically designed for this purpose, making it easy to sync the command tree without modifying the code.

## Verification
After running the bot with the `--update` flag and then starting it normally, the 'test-new-structure' command should be visible in Discord and function as expected, allowing users to test the new database structure.

## Preventive Measures
To prevent similar issues in the future, consider:

1. Adding a note in the development documentation to run `python main.py --update` after adding new commands
2. Implementing an automatic command tree sync during development/testing environments
3. Adding a check at bot startup to verify if all commands are registered, with a warning if they're not