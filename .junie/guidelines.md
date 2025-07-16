# Twikit Discord Bot - Project Guidelines

## Project Overview
Twikit Discord Bot is a Discord bot that enables automatic tweet acquisition without using RSS feeds. It uses a Twitter account to fetch tweets, supporting multiple servers and channels. The bot provides a seamless way for Discord server administrators to set up automatic tweet feeds from specific Twitter users.

## Key Features
- **Automatic Tweet Acquisition**: Fetches tweets without cost, using Twitter cookies for authentication
- **Multi-server Support**: Works across multiple Discord servers and channels
- **URL Enhancement**: Automatically converts Twitter/X and TikTok URLs to fxtwitter and fxtiktok for better embeds
- **Database Storage**: Uses SQLite to store configuration settings
- **Multi-language Support**: Available in English, Japanese, and Chinese
- **Tweet Analysis**: Analyzes tweets to determine their type (normal, retweet, reply)
- **Thread Retrieval**: For reply tweets, retrieves the entire conversation thread
- **RSS-like Functionality**: Fetches the latest tweets from users similar to an RSS feed

## Project Architecture
The project follows a modular architecture with clear separation of concerns:

### Core Components
1. **Bot Core** (`src/core/bot.py`): Main bot class and event handlers
2. **Twitter Client** (`src/core/twitter_client.py`): Handles Twitter API communication
3. **Twitter Client Manager** (`src/core/twitter_client_manager.py`): Manages both guest and authenticated Twitter clients
4. **Twitter Analyzer** (`src/core/twitter_analyzer.py`): Implements tweet analysis and thread retrieval
5. **Database** (`src/core/database.py`): Handles database operations
6. **Settings** (`src/config/settings.py`): Manages configuration and file I/O

### Discord Commands
1. **Twitter Commands** (`src/cogs/twitter_commands.py`): Implements slash commands for Twitter feed management
2. **URL Fixer** (`src/cogs/url_fixer.py`): Handles automatic URL conversion

### Data Storage
- **Database** (`data/bot.db`): SQLite database for storing settings
- **Cookie Files** (`data/cookie.json`, `data/cookie_edit.json`): Twitter authentication cookies

## Development Guidelines

### Code Style
- Use PEP 8 style guidelines for Python code
- Include type hints to improve code readability and maintainability
- Write docstrings for all classes and methods
- All documentation and comments should be written in both Japanese and English
- All print statements in Python files (except test files) should use language files for text

### Error Handling
- Implement comprehensive error handling for all external API calls
- Use structured error information in analysis results
- Handle rate limits and authentication errors gracefully

### Testing
- Write unit tests for core functionality
- Test different types of tweets and scenarios
- Ensure backward compatibility when making changes

## Future Improvements
Based on the refactoring proposal, the following improvements are planned:

1. **Code Refactoring**:
   - Reduce the size of large files by splitting them into smaller, focused modules
   - Replace global variables with proper class attributes
   - Improve error handling and logging

2. **Feature Enhancements**:
   - Support for AliExpress
   - Fork fxtwitter and customize it independently

3. **Performance Optimization**:
   - Replace synchronous HTTP requests with asynchronous ones
   - Optimize database queries

## Getting Started
For setup instructions, refer to the main README.md file in the project root.

## Contributing
When contributing to this project, please follow these guidelines:
1. Create a feature branch for your changes
2. Write tests for new functionality
3. Ensure all tests pass before submitting a pull request
4. Follow the existing code style and architecture
5. Document your changes thoroughly
