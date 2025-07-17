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

## AI Development Guidelines

### Documentation Reference Requirements
When working on this project, AI assistants must:

1. **Always check AI_Document directory first**:
   - Review `AI_Document/ライブラリ仕様書一覧.md` to understand available library specifications
   - Reference specific library documentation files (e.g., `discord.py仕様書.md`, `twikit仕様書.md`) when working with those libraries
   - Use the Context7 data and code snippets provided in these documents for accurate implementation

2. **Minimize file references by consulting README.md**:
   - Use the project structure section in `README.md` to understand essential files and directories
   - Focus on core files: `main.py`, `src/core/`, `src/cogs/`, `src/config/`, `src/lang/`
   - Avoid referencing deprecated files in `src_old/` directory unless specifically needed
   - Prioritize files mentioned in the README's project structure over other files

3. **Essential files to reference (in order of priority)**:
   - `README.md` - Project overview and structure
   - `AI_Document/ライブラリ仕様書一覧.md` - Library specifications index
   - Specific library documentation in `AI_Document/` as needed
   - Core implementation files in `src/core/` and `src/cogs/`
   - Configuration files: `requirements.txt`, `.env`, `src/config/settings.py`

4. **File reference optimization**:
   - Before examining any file, check if it's mentioned in README.md project structure
   - Use library specifications from AI_Document instead of exploring library source code
   - Focus on files that are actively maintained (avoid `src_old/` unless necessary)

## Automated README Updates

### README Auto-Update System
The project includes an automated system to keep the README.md file synchronized with the actual project structure. This ensures that the documentation always reflects the current state of the codebase.

#### How It Works
- **Script**: `update_readme.py` automatically scans the project directory
- **Target**: Updates the "Project Structure" section in README.md
- **Detection**: Identifies added, removed, or moved files and directories
- **Exclusions**: Automatically excludes `.venv/`, `.git/`, `src_old/`, and other non-essential directories

#### Usage
Run the update script manually:
```bash
python3 update_readme.py
```

#### Integration Recommendations
1. **Before Commits**: Run the script before committing changes that affect project structure
2. **CI/CD Integration**: Add the script to your continuous integration pipeline
3. **Git Hooks**: Consider adding a pre-commit hook to automatically update README
4. **Regular Maintenance**: Run periodically to ensure documentation stays current

#### What Gets Updated
- **File Structure**: Complete directory tree with descriptions
- **New Files**: Automatically detected and added with appropriate descriptions
- **Deleted Files**: Automatically removed from the structure
- **Moved Files**: Reflected in their new locations

#### Customization
The script includes predefined descriptions for key files and directories. To add descriptions for new files:
1. Edit the `get_file_description()` method in `update_readme.py`
2. Add entries to the descriptions dictionary
3. Run the script to apply changes

## Contributing
When contributing to this project, please follow these guidelines:
1. Create a feature branch for your changes
2. Write tests for new functionality
3. Ensure all tests pass before submitting a pull request
4. Follow the existing code style and architecture
5. Document your changes thoroughly
6. **Run `python3 update_readme.py` if you add, remove, or move files**
