
# RSS-Free Tweet Acquisition Discord Bot
![banner](./img/Twitter.jpg)
English [中文](README_zh.md) [日本語](README_ja.md) 

Until now, there was only a method to acquire tweets using RSS, but we have overcome this by using a Twitter account.
## Table of Contents
- [Features](#features)
- [In Progress](#in-progress)
- [Installation](#installation)
- [Configuration](#configuration)
- [Commands](#commands)

## Features

- Automatic tweet acquisition without cost
- Support for multiple servers and channels
- Automatic conversion to fxtwitter and fxtiktok URLs
- Database-based configuration storage
- Multi-language support (English, Japanese, Chinese)

## In Progress

 - [ ] Support for AliExpress
 - [ ] Fork fxtwitter and customize it independently

## Installation

Here are the installation steps for the project.

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token

### Install Dependencies
Linux or Mac
```bash
python3 -m pip install -r requirements.txt
```
Windows
```bash
pip install -r requirements.txt
```

## Configuration

### 1. Twitter Cookie Setup
1. Install this [Chrome extension](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm).
2. Copy the cookie as shown in the image below.
![image](./img/cookie.png)
3. Save the copied cookie as `cookie.json` in the `data/` directory.

### 2. Environment Variables
Create a `.env` file in the project root with the following configuration:
```dotenv
TOKEN="Your_Discord_Bot_Token"
# Supported languages: ja_JP, en_US, zh_CN
Languages="en_US"
```

### 3. Discord Bot Setup
Please invite your bot with the following permissions:
![discord](./img/Setup_2.png)
![discord](./img/Setup_3.png)

### 4. How to Start
Linux or Mac
```bash
python3 main.py
```
Windows
```bash
python main.py
```

## Commands & Capabilities

### Twitter Feed Management
- **Add Twitter feed to channel**
```
/set_twitter twitter_user_name: <username>
```
![command](img/set_command.png)

- **Remove Twitter feed from channel**
```
/del_twitter user_name: <username>
```
![command](img/del_command.png)

### Settings Management
- **Set cooldown time for Twitter updates**
```
/check-time minutes: <number>
```
![command](img/time_command.png)

- **Toggle Twitter updates on/off**
```
/change-setting-twitter-get mode: <true/false>
```

- **Toggle URL preview conversion on/off**
```
/change-setting-url-preview mode: <true/false>
```
![command](img/command_1.png)

- **Display current settings**
```
/check-settings
```
![command](img/check_command.png)

### Automatic Features
- **Automatic Twitter posting**
![command](img/auto_say.png)

- **Automatic URL conversion** - Converts Twitter/X and TikTok URLs to fxtwitter/fxtiktok for better embeds

## Project Structure
```
twikit_discord_bot/
├── AI_Document/  # AI development documentation
│   ├── discord.py仕様書.md
│   ├── discord.py関数一覧.md
│   ├── twikit仕様書.md
│   ├── twikit関数一覧.md
│   └── ライブラリ仕様書一覧.md
├── data/  # Application data files
│   ├── bot.db  # SQLite database
│   ├── cookie.json  # Twitter authentication cookie
│   └── cookie_edit.json  # Backup cookie file
├── img/  # Image assets
│   ├── auto_say.png
│   ├── check_command.png
│   ├── command_1.png
│   ├── cookie.png
│   ├── del_command.png
│   ├── set_command.png
│   ├── Setup_1.png
│   ├── Setup_2.png
│   ├── Setup_3.png
│   ├── time_command.png
│   └── Twitter.jpg
├── src/  # Source code
│   ├── cogs/  # Discord command modules
│   │   ├── __init__.py
│   │   ├── README.md  # Project documentation
│   │   ├── twitter_commands.py  # Twitter-related slash commands
│   │   └── url_fixer.py  # URL replacement functionality
│   ├── config/  # Configuration management
│   │   ├── __init__.py
│   │   ├── README.md  # Project documentation
│   │   └── settings.py  # Settings and file I/O operations
│   ├── core/  # Core bot functionality
│   │   ├── __init__.py
│   │   ├── bot.py  # Main bot class and event handlers
│   │   ├── database.py  # Database operations
│   │   ├── README.md  # Project documentation
│   │   ├── twitter_analyzer.py  # Tweet analysis functionality
│   │   ├── twitter_client.py  # Twitter API client
│   │   └── twitter_client_manager.py  # Twitter client management
│   ├── lang/  # Language files
│   │   ├── en_US.json  # English translations
│   │   ├── ja_JP.json  # Japanese translations
│   │   ├── README.md  # Project documentation
│   │   └── zh_CN.json  # Chinese translations
│   ├── rss/  # RSS functionality
│   │   ├── __init__.py
│   │   ├── README.md  # Project documentation
│   │   └── rss_generator.py  # RSS feed generation
│   ├── __init__.py
│   └── README.md  # Project documentation
├── .env  # Environment variables
├── get_tweet.json
├── main.py  # Application entry point
├── README.md  # Project documentation
├── README_ja.md
├── README_zh.md
├── requirements.txt  # Python dependencies
├── sample.env
├── test_parent_tweet.py
├── test_twitter_analyzer.py
├── TWITTER_ANALYZER_README.md
├── update_readme.py
└── 使用ライブラリ一覧.md
```
