# Version Management System

This application includes an automated version management system that tracks the current version and can check for updates.

## Configuration

The version information is stored in `app_config.json` at the root of the project:

```json
{
    "version": "1.0.0.0",
    "last_updated": "2025-07-08T19:07:00",
    "repository_url": "https://github.com/yourusername/your-repo.git",
    "branch": "main"
}
```

### Configuration Options

- **version**: Your current application version (semantic versioning)
- **last_updated**: ISO timestamp of last update
- **repository_url**: GitHub repository URL for checking releases
- **branch**: Git branch (used for future features)

## How It Works

This system uses **GitHub Releases only** for version management:

1. **Your local version** stays exactly as you set it (e.g., `1.0.0.0`)
2. **GitHub releases** are checked for newer versions using semantic versioning
3. **Version comparison** uses the `packaging` library for accurate semantic version comparison
4. **Automatic updates** download and install when a higher version is found

### Creating Releases

To enable version checking, create releases on your GitHub repository:

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag version: `v1.0.0.1` (or `1.0.0.1`)
4. Release title: `Version 1.0.0.1`
5. Publish release

The system will automatically detect when `1.0.0.1` > `1.0.0.0` and offer to update.

## Usage

### Setting the Current Version

To update the current version manually:

1. Edit `app_config.json` and change the `version` field
2. Or use the admin interface after a successful update

### Checking for Updates

The system uses a simple and reliable approach:

1. **GitHub Releases Only**: 
   - Checks your GitHub repository for published releases
   - Compares release version tags with your local version
   - Uses semantic versioning for accurate comparison (1.0.0.1 > 1.0.0.0)

2. **No Commit Tracking**:
   - Does not track individual commits
   - Only responds to official releases you publish
   - Clean and predictable update behavior

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
- **SHA-based Comparison**: Uses commit SHAs for accurate development version tracking
- **Simplified Version Management**: Single version field eliminates confusion
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
