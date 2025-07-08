import json
import os
import requests
import subprocess
from datetime import datetime
from packaging import version
import logging

logger = logging.getLogger(__name__)

class VersionManager:
    def __init__(self, config_file='app_config.json'):
        self.config_file = config_file
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), config_file)
        self.config = self.load_config()
    
    def load_config(self):
        """Load the app configuration from JSON file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                # Create default config if it doesn't exist
                default_config = {
                    "version": "1.0.0",
                    "last_updated": None,
                    "update_available": False,
                    "remote_version": None,
                    "repository_url": "",
                    "branch": "main"
                }
                self.save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {
                "version": "1.0.0",
                "last_updated": None,
                "update_available": False,
                "remote_version": None,
                "repository_url": "",
                "branch": "main"
            }
    
    def save_config(self, config=None):
        """Save the app configuration to JSON file"""
        try:
            config_to_save = config if config else self.config
            with open(self.config_path, 'w') as f:
                json.dump(config_to_save, f, indent=4)
            if not config:
                self.config = config_to_save
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get_current_version(self):
        """Get the current application version"""
        return self.config.get('version', '1.0.0')
    
    def set_current_version(self, new_version):
        """Set the current application version"""
        self.config['version'] = new_version
        self.config['last_updated'] = datetime.now().isoformat()
        self.save_config()
    
    def check_for_updates_github(self):
        """Check for updates from GitHub releases"""
        try:
            repo_url = self.config.get('repository_url', '')
            if not repo_url:
                return False, "Repository URL not configured"
            
            # Extract owner and repo from GitHub URL
            if 'github.com' in repo_url:
                parts = repo_url.replace('.git', '').split('/')
                owner = parts[-2]
                repo = parts[-1]
                
                # Get latest release from GitHub API
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    release_data = response.json()
                    remote_version = release_data['tag_name'].lstrip('v')
                    
                    current_version = self.get_current_version()
                    
                    # Compare versions
                    if version.parse(remote_version) > version.parse(current_version):
                        self.config['remote_version'] = remote_version
                        self.config['update_available'] = True
                        self.save_config()
                        return True, f"Update available: {remote_version}"
                    else:
                        self.config['update_available'] = False
                        self.config['remote_version'] = remote_version
                        self.save_config()
                        return False, "No updates available"
                else:
                    return False, f"Failed to check for updates: {response.status_code}"
            else:
                return False, "Not a GitHub repository"
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False, f"Error checking for updates: {str(e)}"
    
    def check_for_updates_git(self):
        """Check for updates using git commands"""
        try:
            # Check if we're in a git repository
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True, cwd=os.path.dirname(self.config_path))
            if result.returncode != 0:
                return False, "Not in a git repository"
            
            # Fetch latest changes
            subprocess.run(['git', 'fetch', 'origin'], 
                          capture_output=True, text=True, cwd=os.path.dirname(self.config_path))
            
            # Check if there are new commits
            branch = self.config.get('branch', 'main')
            result = subprocess.run(['git', 'rev-list', '--count', f'HEAD..origin/{branch}'], 
                                  capture_output=True, text=True, cwd=os.path.dirname(self.config_path))
            
            if result.returncode == 0:
                commit_count = int(result.stdout.strip())
                if commit_count > 0:
                    self.config['update_available'] = True
                    self.save_config()
                    return True, f"{commit_count} new commits available"
                else:
                    self.config['update_available'] = False
                    self.save_config()
                    return False, "No updates available"
            else:
                return False, "Failed to check git status"
        except Exception as e:
            logger.error(f"Error checking git updates: {e}")
            return False, f"Error checking git updates: {str(e)}"
    
    def is_update_available(self):
        """Check if an update is available"""
        return self.config.get('update_available', False)
    
    def get_remote_version(self):
        """Get the remote version if available"""
        return self.config.get('remote_version')
    
    def update_version_info(self, new_version=None, mark_updated=True):
        """Update version information after successful update"""
        if new_version:
            self.config['version'] = new_version
        if mark_updated:
            self.config['last_updated'] = datetime.now().isoformat()
            self.config['update_available'] = False
            self.config['remote_version'] = None
        self.save_config()
