from flask import Blueprint, render_template, current_app, Response, stream_with_context, request, jsonify
from flask_login import login_required
from app.routes.auth import admin_required
from app.utils.version_manager import VersionManager
import subprocess
import sys
import os
import platform

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/update')
@login_required
@admin_required
def update_page():
    """Render the application update page"""
    version_manager = VersionManager()
    current_version = version_manager.get_current_version()
    update_available = version_manager.is_update_available()
    remote_version = version_manager.get_remote_version()
    
    return render_template('admin/update.html', 
                         current_version=current_version,
                         update_available=update_available,
                         remote_version=remote_version)

@bp.route('/update/check', methods=['POST'])
@login_required
@admin_required
def check_for_updates():
    """Check for available updates"""
    version_manager = VersionManager()
    
    # Try GitHub first (handles both releases and commits)
    has_update, message = version_manager.check_for_updates_github()
    
    # If GitHub check fails completely, fall back to local git
    if "Error" in message and "Network error" not in message:
        has_update, git_message = version_manager.check_for_updates_git()
        if has_update:
            message = git_message
    
    return jsonify({
        'update_available': has_update,
        'message': message,
        'current_version': version_manager.get_current_version(),
        'remote_version': version_manager.get_remote_version()
    })

@bp.route('/update/run', methods=['GET', 'POST'])
@login_required
@admin_required
def run_update():
    """Run the update script and stream the output"""
    
    # Create an ID for this update session to avoid running multiple updates at once
    update_session_id = None
    
    # Store this in the application context for checking if we're already running
    if not hasattr(current_app, 'update_running'):
        current_app.update_running = False
    
    # Handle POST request - this starts the update
    if request.method == 'POST':
        # If update is already running, don't start another one
        if current_app.update_running:
            return jsonify({'error': 'Update already in progress'}), 409
        
        # Mark that we're starting an update
        current_app.update_running = True
        # Return success to indicate the update has been triggered
        return jsonify({'status': 'started'}), 200
    
    # For GET requests, we stream the output
    def generate():
        # Determine which script to run based on OS
        script_path = None
        try:
            if platform.system() == 'Windows':
                script_path = os.path.join(current_app.root_path, '..', 'update.bat')
                yield f"data: Detected Windows OS, using update.bat script\n\n"
            else:
                script_path = os.path.join(current_app.root_path, '..', 'update.sh')
                yield f"data: Detected Unix-like OS, using update.sh script\n\n"
                # Ensure the script is executable on Unix-like systems
                if os.path.exists(script_path):
                    try:
                        os.chmod(script_path, 0o755)
                        yield f"data: Made update.sh executable\n\n"
                    except Exception as e:
                        yield f"data: Warning: Failed to set executable permissions: {e}\n\n"

            # Check if the script exists
            if not script_path or not os.path.exists(script_path):
                yield f"data: Error: Update script not found at {script_path}\n\n"
                yield "event: end\ndata: error\n\n"
                return

            # Send a message about which script is being executed
            yield f"data: Using update script: {script_path}\n\n"

            # Start the process
            if platform.system() == 'Windows':
                yield f"data: Starting Windows update process...\n\n"
                process = subprocess.Popen(
                    script_path,  # Use the path directly for Windows
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    universal_newlines=True,
                    shell=True
                )
            else:
                yield f"data: Starting Unix update process...\n\n"
                process = subprocess.Popen(
                    [script_path],  # Use list format for Unix
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    universal_newlines=True
                )

            # Stream output in real-time
            for line in iter(process.stdout.readline, ''):
                if line.strip():  # Only send non-empty lines
                    line_sanitized = line.replace('\r', '').rstrip('\n')
                    yield f"data: {line_sanitized}\n\n"

            # Wait for the process to complete
            process.stdout.close()
            return_code = process.wait()

            # Log the result
            if return_code == 0:
                yield f"data: Process completed with return code: {return_code}\n\n"
                
                # Update version information after successful update
                try:
                    version_manager = VersionManager()
                    remote_version = version_manager.get_remote_version()
                    if remote_version:
                        # Extract version from remote_version (handle commit format)
                        if '(' in remote_version:  # Format: "2025.07.08.1850 (0f36a88)"
                            new_version = remote_version.split(' ')[0]
                        else:
                            new_version = remote_version
                        version_manager.set_current_version(new_version)
                        yield f"data: Updated version to {new_version}\n\n"
                    else:
                        version_manager.update_version_info(mark_updated=True)
                        yield f"data: Marked update as completed\n\n"
                except Exception as e:
                    yield f"data: Warning: Could not update version info: {str(e)}\n\n"
                
                yield "event: end\ndata: success\n\n"
            else:
                yield f"data: Process failed with return code: {return_code}\n\n"
                yield "event: end\ndata: error\n\n"

        except Exception as e:
            yield f"data: An error occurred: {str(e)}\n\n"
            yield "event: end\ndata: error\n\n"
        finally:
            # Reset the update running flag
            current_app.update_running = False
    
    # Return the streaming response for GET requests
    response = Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )
    # Add headers to prevent caching
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

@bp.route('/update/version', methods=['POST'])
@login_required
@admin_required
def update_version():
    """Update version information after successful update"""
    try:
        data = request.get_json()
        new_version = data.get('version')
        
        version_manager = VersionManager()
        if new_version:
            version_manager.set_current_version(new_version)
        else:
            version_manager.update_version_info(mark_updated=True)
        
        return jsonify({
            'success': True,
            'current_version': version_manager.get_current_version(),
            'message': 'Version updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating version: {str(e)}'
        }), 500
