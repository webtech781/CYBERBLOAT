document.addEventListener('DOMContentLoaded', function() {
    // Restore selected device if exists
    const savedDevice = localStorage.getItem('selectedDevice');
    if (savedDevice) {
        const deviceInput = document.querySelector(`input[value="${savedDevice}"]`);
        if (deviceInput) {
            deviceInput.checked = true;
            handleDeviceSelection(savedDevice);
        }
    }

    // Add command button handlers
    const commandButtons = document.querySelectorAll('.command-button[data-command]');
    commandButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.dataset.command) return;
            
            const selectedDevice = document.querySelector('input[name="device"]:checked');
            if (!selectedDevice) {
                alert('Please select a device first');
                return;
            }
            
            executeCommand(selectedDevice.value, this.dataset.command);
        });
    });

    // Check device status periodically
    checkDeviceStatus();
    setInterval(checkDeviceStatus, 2000);

    // Add loading overlay handler for Installed Apps link
    const installedAppsLink = document.querySelector('a[href*="installed_apps"]');
    if (installedAppsLink) {
        installedAppsLink.addEventListener('click', function(e) {
            e.preventDefault();
            showLoadingOverlay();
            window.location.href = this.href;
        });
    }

    // Handle disabled buttons
    document.querySelectorAll('.command-button.disabled').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (this.classList.contains('disabled')) {
                e.preventDefault();
                alert('Please select a device first');
            }
        });
    });
});

function checkDeviceStatus() {
    fetch('/check_devices')
        .then(response => response.json())
        .then(data => {
            const currentPath = window.location.pathname;
            
            // Only redirect if we're on the loading page or device selector
            if (currentPath === '/' || currentPath === '/loading') {
                if (document.querySelector('.loading-screen')) {
                    // If we're on loading screen and devices are found, reload once
                    if (data.devices.length > 0) {
                        window.location.href = '/';
                    }
                } else {
                    // If we're on device selector and no devices found, go to loading
                    if (data.devices.length === 0) {
                        window.location.href = '/';
                    }
                }
            }
        })
        .catch(error => console.error('Error:', error));
}

function executeCommand(deviceId, command) {
    const formData = new FormData();
    formData.append('device_id', deviceId);
    formData.append('command', command);
    
    const outputArea = document.getElementById('commandOutput');
    outputArea.textContent = 'Executing command...';
    
    fetch('/execute_command', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                outputArea.textContent = data.result || 'Command executed successfully';
            }
        } else {
            outputArea.textContent = `Error: ${data.error}\n${data.result || ''}`;
        }
    })
    .catch(error => {
        outputArea.textContent = `Error executing command: ${error}`;
        console.error('Error:', error);
    });
}

// Add this function
function showLoadingOverlay() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

// Add this function to handle device selection
function handleDeviceSelection(deviceId) {
    // Enable all command buttons and update their hrefs
    document.querySelectorAll('.command-button').forEach(btn => {
        btn.classList.remove('disabled');
        
        // Update hrefs for link buttons
        if (btn.tagName === 'A') {
            if (btn.textContent.trim() === 'Installed Apps') {
                btn.href = `/installed_apps/${deviceId}`;
            } else if (btn.textContent.trim() === 'Shell Commands') {
                btn.href = `/shell_commands/${deviceId}`;
            }
        }
    });

    // Store selected device
    localStorage.setItem('selectedDevice', deviceId);
} 