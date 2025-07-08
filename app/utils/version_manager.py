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
                    "version": "1.0.0",
                    "last_updated": None,
                    "update_available": False,
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
                # Handle different URL formats
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
                    logger.info(f"GitHub API response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        release_data = response.json()
                        remote_version = release_data['tag_name'].lstrip('v')
                        logger.info(f"Found remote version: {remote_version}")
                        
                        current_version = self.get_current_version()
                        logger.info(f"Current version: {current_version}")
                        
                        # Compare versions
                        try:
                            if version.parse(remote_version) > version.parse(current_version):
                                self.config['version'] = remote_version
                                self.config['update_available'] = True
                                self.save_config()
                                return True, f"Update available: {remote_version}"
                            else:
                                self.config['update_available'] = False
                                self.save_config()
                                return False, f"No updates available (latest: {remote_version})"
                        except Exception as ve:
                            logger.error(f"Version comparison error: {ve}")
                            return False, f"Error comparing versions: {str(ve)}"
                    elif response.status_code == 404:
                        # Try checking commits if no releases found
                        return self.check_for_updates_git_api(owner, repo)
                    else:
                        return False, f"GitHub API error: {response.status_code} - {response.text}"
                except requests.exceptions.RequestException as e:
                    logger.error(f"Network error checking GitHub: {e}")
                    return False, f"Network error: {str(e)}"
            else:
                return False, "Not a GitHub repository"
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False, f"Error checking for updates: {str(e)}"
    
    def check_for_updates_git_api(self, owner, repo):
        """Check for updates using GitHub API for commits when no releases exist"""
        try:
            # Get latest commit from the specified branch
            branch = self.config.get('branch', 'main')
            api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
            
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                commit_data = response.json()
                latest_commit_sha = commit_data['sha'][:7]  # Short SHA
                
                current_version = self.get_current_version()
                
                # Extract current commit SHA if version contains one
                current_commit_sha = None
                if '(' in current_version and ')' in current_version:
                    # Format: "2025.07.08.1850 (0f36a88)" - extract the SHA
                    current_commit_sha = current_version.split('(')[1].split(')')[0]
                elif len(current_version) == 7 and all(c in '0123456789abcdef' for c in current_version.lower()):
                    # Version is just a commit SHA
                    current_commit_sha = current_version
                
                # Compare commit SHAs
                if current_commit_sha != latest_commit_sha:
                    # Update available - store just the commit SHA as version
                    self.config['version'] = latest_commit_sha
                    self.config['update_available'] = True
                    self.save_config()
                    return True, f"New commits available: {latest_commit_sha}"
                else:
                    self.config['update_available'] = False
                    self.save_config()
                    return False, "No new commits"
            else:
                return False, f"Could not check commits: {response.status_code}"
        except Exception as e:
            logger.error(f"Error checking git API: {e}")
            return False, f"Error checking commits: {str(e)}"
    
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
        """Get the remote version if available - for backward compatibility"""
        return None  # No longer using remote_version field
    
    def update_version_info(self, new_version=None, mark_updated=True):
        """Update version information after successful update"""
        if new_version:
            self.config['version'] = new_version
        if mark_updated:
            self.config['last_updated'] = datetime.now().isoformat()
            self.config['update_available'] = False
        self.save_config()
