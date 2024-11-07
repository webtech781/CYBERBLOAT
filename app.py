from flask import Flask, render_template, jsonify, request, send_file, url_for
import subprocess
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import webbrowser
from threading import Timer
from app_titles import APP_TITLES
import socket
import time
from datetime import datetime
import json
import threading
import sys

app = Flask(__name__)

# Replace the current ADB_PATH definition with this more robust version
def get_adb_path():
    try:
        # First try: Check if 'adb' is in system PATH
        if os.name == 'nt':  # Windows
            # Try common Windows installation paths
            possible_paths = [
                'adb',  # If in PATH
                r'C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe',
                r'%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe',
                r'%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe'
            ]
            
            # Expand environment variables
            possible_paths = [os.path.expandvars(path) for path in possible_paths]
            
            # Try each path
            for path in possible_paths:
                try:
                    subprocess.run([path, 'version'], capture_output=True, check=True)
                    return path
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
                    
            # If no paths work, try 'adb' command directly
            subprocess.run(['adb', 'version'], capture_output=True, check=True)
            return 'adb'
            
        else:  # Linux/Mac
            # Check if adb is in PATH
            subprocess.run(['adb', 'version'], capture_output=True, check=True)
            return 'adb'
            
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: ADB not found in system. Please ensure ADB is installed and in your system PATH.")
        return None

# Initialize ADB_PATH
ADB_PATH = get_adb_path()

# Add this check after ADB_PATH initialization
if ADB_PATH is None:
    print("""
    Error: ADB not found in system PATH or common installation locations.
    Please ensure that:
    1. ADB is installed on your system
    2. ADB is added to your system PATH
    3. You can run 'adb version' from terminal/command prompt
    """)
    sys.exit(1)

# At the top of the file, add this global variable after the imports
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True

# Error handlers and undefined route should be at the top
@app.route('/<path:undefined_path>')
def undefined_route(undefined_path):
    if undefined_path.startswith('installed_apps/') or undefined_path.startswith('shell_commands/'):
        return render_template('error.html', 
                             error_message="Device not found or not connected",
                             error_details="Please check your device connection and try again.")
    error_message = f"The path '/{undefined_path}' does not exist."
    error_details = "Please check the URL and try again, or use the navigation menu."
    return render_template('error.html', 
                         error_message=error_message,
                         error_details=error_details), 404

@app.errorhandler(404)
def page_not_found(e):
    error_message = "The page you're looking for doesn't exist."
    error_details = "Please check the URL and try again, or go back to the home page."
    return render_template('error.html', 
                         error_message=error_message,
                         error_details=error_details), 404

@app.errorhandler(500)
def internal_server_error(e):
    error_message = "Something went wrong on our end."
    error_details = "Please try again later or contact support if the problem persists."
    return render_template('error.html', 
                         error_message=error_message,
                         error_details=error_details), 500

@app.errorhandler(Exception)
def handle_exception(e):
    error_message = "An unexpected error occurred."
    error_details = str(e)
    return render_template('error.html', 
                         error_message=error_message,
                         error_details=error_details), 500

# Add available ADB commands
ADB_COMMANDS = {
    'installed_apps': 'shell pm list packages',
    'device_info': 'shell getprop',
    'battery_status': 'shell dumpsys battery',
    'screen_capture': 'shell screencap -p /sdcard/screen.png',
    'reboot': 'reboot',
    'wifi_status': 'shell dumpsys wifi',
    'process_list': 'shell ps',
    'file_manager': 'shell ls'
}

# Add these new functions at the top of app.py after imports
def restart_adb_server():
    try:
        subprocess.run([ADB_PATH, 'kill-server'], check=True)
        time.sleep(2)  # Wait for server to fully stop
        subprocess.run([ADB_PATH, 'start-server'], check=True)
        time.sleep(3)  # Wait for server to fully start
        return True
    except Exception as e:
        print(f"Error restarting ADB server: {e}")
        return False

def verify_adb_connection():
    try:
        # Check if ADB is responding
        subprocess.run([ADB_PATH, 'devices'], check=True, timeout=5)
        return True
    except Exception:
        # If ADB is not responding, try to restart it
        return restart_adb_server()

# Modify the get_connected_devices function
def get_connected_devices():
    try:
        # First verify ADB connection
        if not verify_adb_connection():
            return []
            
        result = subprocess.check_output([ADB_PATH, 'devices'], universal_newlines=True, timeout=5)
        devices = []
        for line in result.split('\n')[1:]:  # Skip the first line (header)
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2 and parts[1].strip() == 'device':  # Only include fully connected devices
                    device_id = parts[0]
                    devices.append(device_id)
        return devices
    except subprocess.TimeoutExpired:
        print("ADB command timed out")
        restart_adb_server()
        return []
    except subprocess.CalledProcessError as e:
        print(f"Error executing ADB: {e}")
        restart_adb_server()
        return []
    except FileNotFoundError:
        print(f"ADB not found at path: {ADB_PATH}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

@app.route('/execute_command', methods=['POST'])
def execute_command():
    try:
        device_id = request.form.get('device_id')
        command = request.form.get('command')
        
        if command == 'installed_apps':
            # Redirect to installed_apps page
            return jsonify({
                'success': True,
                'redirect': f'/installed_apps/{device_id}'
            })
            
        if command not in ADB_COMMANDS:
            return jsonify({'error': 'Invalid command'}), 400

        full_command = [ADB_PATH, '-s', device_id] + ADB_COMMANDS[command].split()
        result = subprocess.check_output(full_command, universal_newlines=True)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'result': e.output if hasattr(e, 'output') else None
        })

@app.route('/')
def index():
    devices = get_connected_devices()
    if not devices:
        return render_template('loading.html')
    elif len(devices) == 1:
        return render_template('device_selector.html', 
                             devices=devices, 
                             selected_device=devices[0],
                             commands=ADB_COMMANDS)
    else:
        return render_template('device_selector.html', 
                             devices=devices,
                             commands=ADB_COMMANDS)

# Modify the check_devices route
@app.route('/check_devices')
def check_devices():
    try:
        # Verify ADB connection first
        if not verify_adb_connection():
            return jsonify({
                'devices': [],
                'error': 'ADB server not responding. Attempting to restart...'
            })
            
        devices = get_connected_devices()
        return jsonify({
            'devices': devices,
            'error': None if devices else 'No devices connected'
        })
    except Exception as e:
        return jsonify({
            'devices': [],
            'error': f'Error checking devices: {str(e)}'
        })

def get_play_store_icon_url(package_name):
    return f"https://play-lh.googleusercontent.com/apps/icon/{package_name}"

def get_app_info_from_playstore(package_name):
    try:
        url = f"https://play.google.com/store/apps/details?id={package_name}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=2)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('h1', {'itemprop': 'name'})
            if title:
                return {
                    'name': title.text.strip(),
                    'icon_url': f"https://play-lh.googleusercontent.com/apps/icon/{package_name}",
                    'play_store_url': url
                }
    except:
        pass
    return None

# Add this new function to extract app icon from APK
def get_app_icon(device_id, package_name):
    try:
        # Get the APK path
        cmd = [ADB_PATH, '-s', device_id, 'shell', 'pm', 'path', package_name]
        result = subprocess.check_output(cmd, universal_newlines=True)
        apk_path = result.strip().replace('package:', '')
        
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'temp_icons')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Pull the APK
        temp_apk = os.path.join(temp_dir, f'{package_name}.apk')
        pull_cmd = [ADB_PATH, '-s', device_id, 'pull', apk_path, temp_apk]
        subprocess.run(pull_cmd, capture_output=True)
        
        # Extract icon using aapt
        icon_path = os.path.join(temp_dir, f'{package_name}.png')
        aapt_cmd = f'aapt dump badging "{temp_apk}" | findstr "application-icon"'
        icon_info = subprocess.check_output(aapt_cmd, shell=True, universal_newlines=True)
        
        # Clean up
        if os.path.exists(temp_apk):
            os.remove(temp_apk)
            
        return f'/static/temp_icons/{package_name}.png'
    except:
        return None

@app.route('/installed_apps/<device_id>')
def installed_apps(device_id):
    try:
        # Check if any device is connected
        devices = get_connected_devices()
        if not devices:
            return render_template('loading.html', 
                                message="Waiting for ADB Devices",
                                details="Please connect your device and ensure ADB is enabled...")
        
        # Check if the specific device is connected
        if device_id not in devices:
            return render_template('loading.html', 
                                message="Device Disconnected",
                                details="Please reconnect your device or select another device...")
        
        user_cmd = [ADB_PATH, '-s', device_id, 'shell', 'pm', 'list', 'packages', '-3']
        system_cmd = [ADB_PATH, '-s', device_id, 'shell', 'pm', 'list', 'packages', '-s']
        
        apps = []
        
        # Process user apps
        try:
            result = subprocess.check_output(user_cmd, universal_newlines=True)
            for line in result.splitlines():
                if line.strip():
                    package = line.replace('package:', '').strip()
                    # Use the APP_TITLES dictionary to get the correct name, fallback to formatted package name
                    app_name = APP_TITLES.get(package, package.split('.')[-1].replace('_', ' ').title())
                    
                    apps.append({
                        'package': package,
                        'name': app_name,
                        'is_system': False,
                        'icon_url': '/static/default_icon.png',  # Use local default icon
                        'play_store_url': f"https://play.google.com/store/apps/details?id={package}"
                    })
        except Exception as e:
            print(f"Error getting user apps: {str(e)}")
            
        # Process system apps
        try:
            result = subprocess.check_output(system_cmd, universal_newlines=True)
            for line in result.splitlines():
                if line.strip():
                    package = line.replace('package:', '').strip()
                    # Use the APP_TITLES dictionary to get the correct name, fallback to formatted package name
                    app_name = APP_TITLES.get(package, package.split('.')[-1].replace('_', ' ').title())
                    
                    apps.append({
                        'package': package,
                        'name': app_name,
                        'is_system': True,
                        'icon_url': '/static/default_icon.png',  # Use local default icon
                        'play_store_url': f"https://play.google.com/store/apps/details?id={package}"
                    })
        except Exception as e:
            print(f"Error getting system apps: {str(e)}")
        
        # Sort apps by name
        apps.sort(key=lambda x: x['name'].lower())
        
        return render_template('installed_apps.html', apps=apps, device_id=device_id)
        
    except Exception as e:
        print(f"Error in installed_apps: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        return render_template('loading.html', 
                             message="Error Loading Apps",
                             details="Please check your device connection and try again...")

@app.route('/uninstall_app', methods=['POST'])
def uninstall_app():
    try:
        device_id = request.form.get('device_id')
        package = request.form.get('package')
        
        if not device_id or not package:
            return jsonify({
                'success': False,
                'message': 'Missing device_id or package name'
            })

        # First enter shell mode
        shell_process = subprocess.Popen(
            [ADB_PATH, '-s', device_id, 'shell'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Execute the uninstall command in shell with -k flag
        uninstall_command = f'pm uninstall -k --user 0 {package.strip()}\nexit\n'
        output, error = shell_process.communicate(input=uninstall_command)
        
        print(f"Command output: {output}")  # Debug print
        print(f"Command error: {error}")    # Debug print

        # Check for both success message and the specific "not installed" message
        # since the app is actually being uninstalled even with this message
        if ('Success' in output or 'Success' in error or 
            'Failure [not installed for 0]' in output or 
            'Failure [not installed for 0]' in error):
            return jsonify({
                'success': True,
                'message': f'Successfully uninstalled {package}'
            })
        
        # If first attempt fails, try with pm disable
        shell_process = subprocess.Popen(
            [ADB_PATH, '-s', device_id, 'shell'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Try pm disable command
        disable_command = f'pm disable-user --user 0 {package.strip()}\nexit\n'
        output2, error2 = shell_process.communicate(input=disable_command)
        
        if 'Success' in output2 or 'Success' in error2:
            return jsonify({
                'success': True,
                'message': f'Successfully disabled {package}'
            })

        # If both attempts fail, try with pm hide
        shell_process = subprocess.Popen(
            [ADB_PATH, '-s', device_id, 'shell'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Try pm hide command
        hide_command = f'pm hide {package.strip()}\nexit\n'
        output3, error3 = shell_process.communicate(input=hide_command)
        
        if 'Success' in output3 or 'Success' in error3:
            return jsonify({
                'success': True,
                'message': f'Successfully hidden {package}'
            })
            
        return jsonify({
            'success': False,
            'message': f'Failed to uninstall: {error if error else output}'
        })
            
    except subprocess.CalledProcessError as e:
        error_msg = e.output if hasattr(e, 'output') else str(e)
        print(f"Error output: {error_msg}")  # Debug print
        return jsonify({
            'success': False,
            'message': f'Failed to uninstall: {error_msg}'
        })
    except Exception as e:
        print(f"Exception: {str(e)}")  # Debug print
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

# Add this new route for shell commands
@app.route('/shell_commands/<device_id>')
def shell_commands(device_id):
    if device_id not in get_connected_devices():
        return render_template('error.html', 
                             error_message="Device not connected",
                             error_details="Please check your USB connection and ensure USB debugging is enabled.")
    return render_template('shell_commands.html', device_id=device_id)

@app.route('/execute_shell', methods=['POST'])
def execute_shell():
    try:
        device_id = request.form.get('device_id')
        command = request.form.get('command')
        
        # Basic security check to prevent dangerous commands
        dangerous_commands = ['rm -rf', 'mkfs', 'dd', 'format']
        if any(cmd in command.lower() for cmd in dangerous_commands):
            return jsonify({
                'success': False,
                'error': 'Command not allowed for security reasons'
            })
        
        # Handle cd commands separately since they need to be handled differently in ADB shell
        if command.startswith('cd '):
            # For cd commands, we'll execute 'pwd' after to show the current directory
            full_command = [ADB_PATH, '-s', device_id, 'shell', 
                          f"cd {command[3:]} && pwd"]
        else:
            # For other commands, pass them directly to shell
            # Use shell=True for complex commands
            full_command = [ADB_PATH, '-s', device_id, 'shell', command]
        
        try:
            # Use shell=True for Windows to handle commands with pipes and redirections
            if os.name == 'nt':  # Windows
                result = subprocess.check_output(' '.join(full_command), 
                                              shell=True, 
                                              universal_newlines=True,
                                              stderr=subprocess.STDOUT)
            else:  # Linux/Mac
                result = subprocess.check_output(full_command,
                                              universal_newlines=True,
                                              stderr=subprocess.STDOUT)
            
            return jsonify({
                'success': True,
                'result': result.strip()
            })
            
        except subprocess.CalledProcessError as e:
            # Return the error output if the command fails
            return jsonify({
                'success': False,
                'error': str(e),
                'result': e.output if hasattr(e, 'output') else 'Command failed'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'result': 'An unexpected error occurred'
        })

@app.route('/docs')
def documentation():
    return render_template('documentation.html')

# Replace the open_browser function with this version
def open_browser():
    # Wait a bit to ensure server is running
    time.sleep(2)
    try:
        webbrowser.open('http://localhost:5000')
    except Exception as e:
        print(f"Error opening browser: {e}")

# Update the main section at the bottom of app.py
if __name__ == '__main__':
    # Start the browser opener in a separate thread
    if not is_port_in_use(5000):
        Timer(1, open_browser).start()
    # Run the Flask app
    app.run(debug=True, port=5000) 

@app.route('/device/<device_id>/info')
def device_info(device_id):
    try:
        if device_id not in get_connected_devices():
            return render_template('error.html', 
                                error_message="Device not connected",
                                error_details="Please check your connection")
        
        # Get device information
        info = {}
        
        # Get basic device info
        props_cmd = [ADB_PATH, '-s', device_id, 'shell', 'getprop']
        props = subprocess.check_output(props_cmd, universal_newlines=True)
        
        # Parse important properties
        info['model'] = re.search(r'\[ro.product.model\]:\s*\[(.*?)\]', props).group(1)
        info['manufacturer'] = re.search(r'\[ro.product.manufacturer\]:\s*\[(.*?)\]', props).group(1)
        info['android_version'] = re.search(r'\[ro.build.version.release\]:\s*\[(.*?)\]', props).group(1)
        
        # Get battery info
        battery_cmd = [ADB_PATH, '-s', device_id, 'shell', 'dumpsys', 'battery']
        battery = subprocess.check_output(battery_cmd, universal_newlines=True)
        info['battery'] = parse_battery_info(battery)
        
        # Get storage info
        storage_cmd = [ADB_PATH, '-s', device_id, 'shell', 'df']
        storage = subprocess.check_output(storage_cmd, universal_newlines=True)
        info['storage'] = parse_storage_info(storage)
        
        return render_template('device_info.html', device_id=device_id, info=info)
    except Exception as e:
        return render_template('error.html',
                             error_message="Failed to get device info",
                             error_details=str(e))

@app.route('/device/<device_id>/screenshot')
def take_screenshot(device_id):
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'screenshot_{timestamp}.png'
        save_path = os.path.join('static', 'screenshots', filename)
        
        # Ensure screenshots directory exists
        os.makedirs(os.path.join('static', 'screenshots'), exist_ok=True)
        
        # Take screenshot
        subprocess.run([
            ADB_PATH, '-s', device_id, 'shell',
            'screencap', '-p', '/sdcard/screen.png'
        ])
        
        # Pull screenshot
        subprocess.run([
            ADB_PATH, '-s', device_id, 'pull',
            '/sdcard/screen.png', save_path
        ])
        
        # Clean up
        subprocess.run([
            ADB_PATH, '-s', device_id, 'shell',
            'rm', '/sdcard/screen.png'
        ])
        
        return jsonify({
            'success': True,
            'screenshot_url': f'/static/screenshots/{filename}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/device/<device_id>/logcat')
def view_logcat(device_id):
    return render_template('logcat.html', device_id=device_id)

@app.route('/api/logcat/<device_id>')
def get_logcat(device_id):
    try:
        cmd = [ADB_PATH, '-s', device_id, 'logcat', '-d', '-v', 'threadtime']
        output = subprocess.check_output(cmd, universal_newlines=True)
        return jsonify({
            'success': True,
            'logs': output
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def parse_battery_info(battery_dump):
    info = {}
    for line in battery_dump.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    return info

def parse_storage_info(storage_dump):
    info = []
    lines = storage_dump.splitlines()
    for line in lines[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 6:
            info.append({
                'filesystem': parts[0],
                'size': parts[1],
                'used': parts[2],
                'available': parts[3],
                'use_percent': parts[4],
                'mounted': parts[5]
            })
    return info

# Add this route right after your error handlers and before other routes
@app.route('/device/<device_id>/files')
def file_manager(device_id):
    try:
        # Check if device is connected
        devices = get_connected_devices()
        if not devices:
            return render_template('loading.html', 
                                message="Waiting for ADB Devices",
                                details="Please connect your device and ensure ADB is enabled...")
        
        if device_id not in devices:
            return render_template('loading.html', 
                                message="Device Disconnected",
                                details="Please reconnect your device or select another device...")

        # Get current path or use default
        current_path = request.args.get('path', '/storage/emulated/0')
        parent_path = os.path.dirname(current_path)

        # Execute shell command to list files
        shell_process = subprocess.Popen(
            [ADB_PATH, '-s', device_id, 'shell'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # List files command
        ls_command = f'ls -la {current_path}\n'
        result, error = shell_process.communicate(input=ls_command)

        if error and 'No such file or directory' in error:
            current_path = '/storage/emulated/0'
            shell_process = subprocess.Popen(
                [ADB_PATH, '-s', device_id, 'shell'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            ls_command = f'ls -la {current_path}\n'
            result, error = shell_process.communicate(input=ls_command)

        # Parse directory listing
        files = []
        for line in result.splitlines():
            if line.strip() and not line.startswith('total'):
                try:
                    parts = line.split(None, 8)
                    if len(parts) >= 8:
                        permissions = parts[0]
                        size = parts[4]
                        date = f"{parts[5]} {parts[6]} {parts[7]}"
                        name = parts[8] if len(parts) > 8 else ''
                        
                        if name and name not in ['.', '..']:
                            is_dir = permissions.startswith('d')
                            files.append({
                                'name': name,
                                'is_dir': is_dir,
                                'size': size,
                                'modified': date,
                                'path': os.path.join(current_path, name).replace('\\', '/')
                            })
                except Exception as e:
                    print(f"Error parsing line: {line}, Error: {str(e)}")
                    continue

        # Sort files: directories first, then files
        files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))

        return render_template('file_manager.html',
                             device_id=device_id,
                             current_path=current_path,
                             parent_path=parent_path,
                             files=files)

    except Exception as e:
        print(f"Error in file_manager: {str(e)}")  # Debug print
        return render_template('loading.html',
                             message="Error Loading Files",
                             details=f"Error: {str(e)}")

# Add routes for file operations
@app.route('/device/<device_id>/upload', methods=['POST'])
def upload_file(device_id):
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        remote_path = request.form.get('path', '/storage/emulated/0')
        
        # Create temp directory if it doesn't exist
        os.makedirs('temp', exist_ok=True)
        temp_path = os.path.join('temp', file.filename)
        
        # Save file temporarily
        file.save(temp_path)
        
        # Push file to device
        cmd = [ADB_PATH, '-s', device_id, 'push', temp_path, 
               os.path.join(remote_path, file.filename)]
        subprocess.run(cmd, check=True)
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/device/<device_id>/download')
def download_file(device_id):
    try:
        file_path = request.args.get('path')
        if not file_path:
            return jsonify({'success': False, 'error': 'No file path provided'})
        
        # Create temp directory if it doesn't exist
        os.makedirs('temp', exist_ok=True)
        temp_file = os.path.join('temp', os.path.basename(file_path))
        
        # Pull file from device
        cmd = [ADB_PATH, '-s', device_id, 'pull', file_path, temp_file]
        subprocess.run(cmd, check=True)
        
        # Send file to user
        return send_file(temp_file, 
                        as_attachment=True,
                        download_name=os.path.basename(file_path))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/device/<device_id>/create_folder', methods=['POST'])
def create_folder(device_id):
    try:
        path = request.form.get('path')
        folder_name = request.form.get('folder_name')
        
        if not path or not folder_name:
            return jsonify({'success': False, 'error': 'Missing path or folder name'})
        
        full_path = os.path.join(path, folder_name)
        cmd = [ADB_PATH, '-s', device_id, 'shell', 'mkdir', full_path]
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/device/<device_id>/delete', methods=['POST'])
def delete_file(device_id):
    try:
        path = request.form.get('path')
        if not path:
            return jsonify({'success': False, 'error': 'Missing path'})
        
        cmd = [ADB_PATH, '-s', device_id, 'shell', 'rm', '-rf', path]
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/device/<device_id>/rename', methods=['POST'])
def rename_file(device_id):
    try:
        old_path = request.form.get('old_path')
        new_name = request.form.get('new_name')
        
        if not old_path or not new_name:
            return jsonify({'success': False, 'error': 'Missing path or new name'})
        
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        cmd = [ADB_PATH, '-s', device_id, 'shell', 'mv', old_path, new_path]
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/device/<device_id>/share', methods=['POST'])
def share_files(device_id):
    try:
        data = request.get_json()
        files = data.get('files', [])
        
        if not files:
            return jsonify({'success': False, 'error': 'No files selected'})
        
        # Create a temporary directory for the files
        temp_dir = os.path.join('temp', 'shared_files')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Pull all selected files
        for file_path in files:
            cmd = [ADB_PATH, '-s', device_id, 'pull', file_path, temp_dir]
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})