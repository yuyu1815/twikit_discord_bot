#!/usr/bin/env python3
"""
Main entry point for the twikit_discord_bot application.
This file is responsible for loading environment variables and starting the bot.
"""

import asyncio
import os
import subprocess
import sys
from dotenv import load_dotenv

from src.core.bot import run_bot

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

def main():
    """
    Main function that loads environment variables and starts the bot.
    """
    # Upgrade twikit package to the latest version
    upgrade_twikit()
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the language from environment variables or use default
    language = os.getenv('Languages', 'en_US')
    
    # Run the bot
    asyncio.run(run_bot(language))

if __name__ == "__main__":
    main()


