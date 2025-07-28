#!/usr/bin/env python3
"""
Main entry point for the twikit_discord_bot application.
This file is responsible for loading environment variables and starting the bot.
"""

import argparse
import asyncio
import os
import subprocess
import sys
from dotenv import load_dotenv

from src.core.bot import run_bot, create_bot

def upgrade_twikit():
    """
    Upgrade the twikit package to the latest version using pip.
    """
    print("Upgrading twikit package to the latest version...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "twikit"])
        print("Successfully upgraded twikit package.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to upgrade twikit package: {e}")
        print("Continuing with the current version...")

async def update_slash_commands(language='en_US'):
    """
    Update slash commands by syncing the command tree.
    This function only syncs commands without fully starting the bot.
    """
    print("Updating slash commands...")
    bot = create_bot(language)
    
    # Check if token is available
    if not bot.token:
        print("Error: No token provided. Set the TOKEN environment variable.")
        return
    
    try:
        # Use lightweight setup for command sync only
        await bot.setup_for_sync()
        
        # Sync the command tree
        await bot.tree.sync()
        print("Successfully synced slash commands.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")
        raise
    finally:
        # Close the bot properly
        try:
            await bot.close()
        except Exception as e:
            print(f"Warning: Error closing bot: {e}")

async def start_bot_safely(language='en_US'):
    """
    Safely start the bot with proper error handling.
    This function ensures that the bot starts correctly and handles any asyncio-related issues.
    """
    try:
        await run_bot(language)
    except Exception as e:
        print(f"Error starting bot: {e}")
        raise

def main():
    """
    Main function that loads environment variables and starts the bot.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Twikit Discord Bot')
    parser.add_argument('--update', action='store_true', help='Update slash commands and exit')
    args = parser.parse_args()
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the language from environment variables or use default
    language = os.getenv('Languages', 'en_US')
    
    try:
        if args.update:
            # Update slash commands and exit
            asyncio.run(update_slash_commands(language))
        else:
            # Upgrade twikit package to the latest version
            upgrade_twikit()
            
            # Run the bot normally with proper error handling
            asyncio.run(start_bot_safely(language))
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


