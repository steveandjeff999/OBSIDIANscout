import json
import os
import requests
from datetime import datetime
from packaging import version
import logging

logger = logging.getLogger(__name__)

class VersionManager:
    def __init__(self, config_file='app_config.json'):
        self.config_file = config_file
        # Always use the root directory for app_config.json
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), config_file)
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
                    "version": "1.0.0.0",
                    "last_updated": None,
                    "repository_url": "",
                    "branch": "main"
                }
                self.save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {
                "version": "1.0.0.0",
                "last_updated": None,
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
        return self.config.get('version', '1.0.0.0')
    
    def set_current_version(self, new_version):
        """Set the current application version"""
        self.config['version'] = new_version
        self.config['last_updated'] = datetime.now().isoformat()
        self.save_config()
    
    def check_for_updates_github(self):
        """Check for updates from GitHub releases only"""
        try:
            repo_url = self.config.get('repository_url', '')
            if not repo_url:
                return False, "Repository URL not configured"
            
            # Extract owner and repo from GitHub URL
            if 'github.com' in repo_url:
                repo_url = repo_url.replace('.git', '')
                if repo_url.endswith('/'):
                    repo_url = repo_url[:-1]
                
                parts = repo_url.split('/')
                if len(parts) >= 2:
                    owner = parts[-2]
                    repo = parts[-1]
                else:
                    return False, "Invalid GitHub URL format"
                
                # Get latest release from GitHub API
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                logger.info(f"Checking for updates at: {api_url}")
                
                try:
                    response = requests.get(api_url, timeout=10)
                    
                    if response.status_code == 200:
                        release_data = response.json()
                        remote_version = release_data['tag_name'].lstrip('v')
                        
                        current_version = self.get_current_version()
                        
                        # Compare versions using semantic versioning
                        try:
                            if version.parse(remote_version) > version.parse(current_version):
                                return True, f"Update available: {remote_version}"
                            else:
                                return False, f"No updates available (latest: {remote_version})"
                        except Exception as ve:
                            logger.error(f"Version comparison error: {ve}")
                            return False, f"Error comparing versions: {str(ve)}"
                    elif response.status_code == 404:
                        return False, "No releases found on GitHub repository"
                    else:
                        return False, f"GitHub API error: {response.status_code}"
                except requests.exceptions.RequestException as e:
                    logger.error(f"Network error checking GitHub: {e}")
                    return False, f"Network error: {str(e)}"
            else:
                return False, "Not a GitHub repository"
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False, f"Error checking for updates: {str(e)}"
    
    def get_latest_release_version(self):
        """Get the latest release version from GitHub"""
        try:
            repo_url = self.config.get('repository_url', '')
            if not repo_url or 'github.com' not in repo_url:
                return None
            
            repo_url = repo_url.replace('.git', '')
            if repo_url.endswith('/'):
                repo_url = repo_url[:-1]
            
            parts = repo_url.split('/')
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1]
                
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    release_data = response.json()
                    return release_data['tag_name'].lstrip('v')
        except Exception as e:
            logger.error(f"Error getting latest release: {e}")
        
        return None
    
    def is_update_available(self):
        """Check if an update is available"""
        has_update, _ = self.check_for_updates_github()
        return has_update
    
    def update_to_latest_version(self):
        """Update the local version to the latest GitHub release version"""
        latest_version = self.get_latest_release_version()
        if latest_version:
            current_version = self.get_current_version()
            try:
                if version.parse(latest_version) > version.parse(current_version):
                    self.set_current_version(latest_version)
                    return True, f"Updated to version {latest_version}"
                else:
                    return False, "Already at latest version"
            except Exception as e:
                return False, f"Error updating version: {str(e)}"
        else:
            return False, "Could not retrieve latest version"
