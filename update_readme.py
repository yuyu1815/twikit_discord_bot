#!/usr/bin/env python3
"""
README Auto-updater for twikit_discord_bot
This script automatically updates the project structure section in README.md
when files are added, removed, or moved in the project.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set

class ReadmeUpdater:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.readme_path = self.project_root / "README.md"
        
        # Directories and files to exclude from the project structure
        self.exclude_dirs = {
            '.git', '.venv', '__pycache__', '.idea', '.DS_Store', 
            'src_old', '.github', '.junie', 'node_modules'
        }
        
        # File extensions to exclude
        self.exclude_extensions = {'.pyc', '.pyo', '.pyd', '.so', '.egg-info'}
        
        # Files to exclude by name
        self.exclude_files = {'.DS_Store', '.gitignore', 'qodana.yaml'}

    def should_include_path(self, path: Path, relative_path: Path) -> bool:
        """Determine if a path should be included in the project structure."""
        # Skip if any parent directory is in exclude list
        for part in relative_path.parts:
            if part in self.exclude_dirs:
                return False
        
        # Skip files with excluded extensions
        if path.suffix in self.exclude_extensions:
            return False
            
        # Skip specific excluded files
        if path.name in self.exclude_files:
            return False
            
        return True

    def generate_tree_structure(self) -> str:
        """Generate a tree-like structure of the project."""
        structure_lines = ["twikit_discord_bot/"]
        
        def add_directory_contents(dir_path: Path, prefix: str = "", is_last: bool = True):
            """Recursively add directory contents to the structure."""
            try:
                # Get all items in directory
                items = []
                for item in dir_path.iterdir():
                    relative_path = item.relative_to(self.project_root)
                    if self.should_include_path(item, relative_path):
                        items.append(item)
                
                # Sort items: directories first, then files
                items.sort(key=lambda x: (x.is_file(), x.name.lower()))
                
                for i, item in enumerate(items):
                    is_last_item = (i == len(items) - 1)
                    
                    # Determine the tree characters
                    if is_last_item:
                        current_prefix = prefix + "└── "
                        next_prefix = prefix + "    "
                    else:
                        current_prefix = prefix + "├── "
                        next_prefix = prefix + "│   "
                    
                    if item.is_dir():
                        # Add directory with description if it's a key directory
                        dir_description = self.get_directory_description(item.name)
                        if dir_description:
                            structure_lines.append(f"{current_prefix}{item.name}/  {dir_description}")
                        else:
                            structure_lines.append(f"{current_prefix}{item.name}/")
                        
                        # Recursively add subdirectory contents
                        add_directory_contents(item, next_prefix, is_last_item)
                    else:
                        # Add file with description if it's a key file
                        file_description = self.get_file_description(item.name)
                        if file_description:
                            structure_lines.append(f"{current_prefix}{item.name}  {file_description}")
                        else:
                            structure_lines.append(f"{current_prefix}{item.name}")
                            
            except PermissionError:
                # Skip directories we can't read
                pass
        
        # Start from project root
        add_directory_contents(self.project_root)
        
        return "\n".join(structure_lines)

    def get_directory_description(self, dir_name: str) -> str:
        """Get description for key directories."""
        descriptions = {
            "data": "# Application data files",
            "src": "# Source code",
            "cogs": "# Discord command modules", 
            "core": "# Core bot functionality",
            "config": "# Configuration management",
            "lang": "# Language files",
            "rss": "# RSS functionality",
            "img": "# Image assets",
            "AI_Document": "# AI development documentation"
        }
        return descriptions.get(dir_name, "")

    def get_file_description(self, file_name: str) -> str:
        """Get description for key files."""
        descriptions = {
            "main.py": "# Application entry point",
            "requirements.txt": "# Python dependencies",
            ".env": "# Environment variables",
            "README.md": "# Project documentation",
            "bot.py": "# Main bot class and event handlers",
            "database.py": "# Database operations", 
            "twitter_client.py": "# Twitter API client",
            "twitter_client_manager.py": "# Twitter client management",
            "twitter_analyzer.py": "# Tweet analysis functionality",
            "settings.py": "# Settings and file I/O operations",
            "twitter_commands.py": "# Twitter-related slash commands",
            "url_fixer.py": "# URL replacement functionality",
            "rss_generator.py": "# RSS feed generation",
            "cookie.json": "# Twitter authentication cookie",
            "cookie_edit.json": "# Backup cookie file",
            "bot.db": "# SQLite database",
            "en_US.json": "# English translations",
            "ja_JP.json": "# Japanese translations", 
            "zh_CN.json": "# Chinese translations"
        }
        return descriptions.get(file_name, "")

    def update_readme_structure(self) -> bool:
        """Update the project structure section in README.md."""
        if not self.readme_path.exists():
            print(f"README.md not found at {self.readme_path}")
            return False
        
        # Read current README content
        with open(self.readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Generate new project structure
        new_structure = self.generate_tree_structure()
        
        # Find the project structure section and replace it
        # Look for the section that starts with "## Project Structure"
        pattern = r'(## Project Structure\s*\n```\s*\n)(.*?)(\n```)'
        
        def replace_structure(match):
            return f"{match.group(1)}{new_structure}{match.group(3)}"
        
        new_content = re.sub(pattern, replace_structure, content, flags=re.DOTALL)
        
        # Check if any changes were made
        if new_content == content:
            print("No changes needed in README.md")
            return False
        
        # Write updated content back to README
        with open(self.readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("README.md project structure updated successfully!")
        return True

    def check_and_update(self) -> bool:
        """Check if README needs updating and update if necessary."""
        return self.update_readme_structure()

def main():
    """Main function to run the README updater."""
    updater = ReadmeUpdater()
    
    if updater.check_and_update():
        print("README.md has been updated with the current project structure.")
    else:
        print("README.md is already up to date.")

if __name__ == "__main__":
    main()