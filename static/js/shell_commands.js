document.addEventListener('DOMContentLoaded', function() {
    // Only run this code on the shell commands page
    if (!document.querySelector('.shell-section')) return;

    const shellInput = document.getElementById('shellCommand');
    const executeBtn = document.getElementById('executeShell');
    const quickCmdBtns = document.querySelectorAll('.quick-cmd-btn');
    
    // Get device ID from URL
    const deviceId = window.location.pathname.split('/').pop();
    
    // Check device connection
    setInterval(() => {
        fetch('/check_devices')
            .then(response => response.json())
            .then(data => {
                if (!data.devices.includes(deviceId)) {
                    window.location.href = '/';
                }
            })
            .catch(error => console.error('Error:', error));
    }, 1000);
    
    // Execute command on button click
    executeBtn.addEventListener('click', () => {
        const command = shellInput.value.trim();
        if (command) {
            executeShellCommand(command);
        }
    });
    
    // Execute command on Enter key
    shellInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const command = shellInput.value.trim();
            if (command) {
                executeShellCommand(command);
            }
        }
    });
    
    // Quick command buttons
    quickCmdBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const cmd = btn.dataset.cmd;
            shellInput.value = cmd;
            executeShellCommand(cmd);
        });
    });
    
    function executeShellCommand(command) {
        const outputArea = document.getElementById('shellOutput');
        outputArea.textContent = 'Executing command...';
        
        const formData = new FormData();
        formData.append('device_id', deviceId);
        formData.append('command', command);
        
        fetch('/execute_shell', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                outputArea.textContent = data.result || 'Command executed successfully';
            } else {
                outputArea.textContent = `Error: ${data.error}\n${data.result || ''}`;
            }
        })
        .catch(error => {
            outputArea.textContent = `Error executing command: ${error}`;
            console.error('Error:', error);
        });
    }
}); 