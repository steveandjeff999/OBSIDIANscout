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

The system supports multiple methods for checking updates, automatically falling back if needed:

1. **GitHub Releases** (preferred): 
   - Set `repository_url` to your GitHub repository
   - Create releases with version tags (e.g., `v1.0.1`)
   - The system will compare with GitHub releases using semantic versioning

2. **GitHub Commits** (automatic fallback):
   - If no releases are found, checks for new commits on the specified branch
   - Uses commit timestamps to generate version numbers (YYYY.MM.DD.HHMM format)
   - Includes short commit SHA for identification

3. **Local Git** (final fallback):
   - If GitHub is unavailable, checks for new commits locally
   - Requires the project to be in a Git repository

### Admin Interface

Access the update interface at `/admin/update`:

- View current version information
- Check for available updates automatically
- See update status (up to date / update available)
- Perform updates with real-time console output
- **Automatic version updating** after successful updates

### Automatic Features

- **Single Config File**: All version information stored in one `app_config.json` file
- **Smart Update Detection**: Automatically detects GitHub releases or commits
- **Version Auto-Update**: Updates version number automatically after successful updates
- **Fallback Systems**: Multiple methods ensure update checking works in various environments

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
