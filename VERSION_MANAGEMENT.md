# Version Management System

This application includes an automated version management system that tracks the current version and can check for updates.

## Configuration

The version information is stored in `app_config.json` at the root of the project:

```json
{
    "version": "1.0.0",
    "last_updated": null,
    "update_available": false,
    "remote_version": null,
    "repository_url": "https://github.com/yourusername/your-repo.git",
    "branch": "main"
}
```

### Configuration Options

- **version**: Current application version (semantic versioning recommended)
- **last_updated**: ISO timestamp of last update
- **update_available**: Boolean indicating if an update is available
- **remote_version**: Version available for update
- **repository_url**: GitHub repository URL for checking releases
- **branch**: Git branch to track for updates

## Usage

### Setting the Current Version

To update the current version manually:

1. Edit `app_config.json` and change the `version` field
2. Or use the admin interface after a successful update

### Checking for Updates

The system supports two methods for checking updates:

1. **GitHub Releases** (recommended): 
   - Set `repository_url` to your GitHub repository
   - Create releases with version tags (e.g., `v1.0.1`)
   - The system will compare with GitHub releases

2. **Git Commits**:
   - If not a GitHub repo, checks for new commits on the specified branch
   - Requires the project to be in a Git repository

### Admin Interface

Access the update interface at `/admin/update`:

- View current version information
- Check for available updates
- See update status (up to date / update available)
- Perform updates with real-time console output

### API Endpoints

- `GET /admin/update` - Update page with version info
- `POST /admin/update/check` - Check for updates
- `POST /admin/update/version` - Update version after successful update
- `GET/POST /admin/update/run` - Run update process

## Version Format

Use semantic versioning (semver) format: `MAJOR.MINOR.PATCH`

Examples:
- `1.0.0` - Initial release
- `1.0.1` - Patch update
- `1.1.0` - Minor update with new features
- `2.0.0` - Major update with breaking changes
