#!/usr/bin/env python3
"""
Main entry point for the twikit_discord_bot application.
This file is responsible for loading environment variables and starting the bot.
"""

import asyncio
import os
from dotenv import load_dotenv

from src.core.bot import run_bot

def main():
    """
    Main function that loads environment variables and starts the bot.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the language from environment variables or use default
    language = os.getenv('Languages', 'en_US')
    
    # Run the bot
    asyncio.run(run_bot(language))

if __name__ == "__main__":
    main()