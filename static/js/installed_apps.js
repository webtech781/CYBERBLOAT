document.addEventListener('DOMContentLoaded', function() {
    const loadingElement = document.getElementById('loadingApps');
    const contentElement = document.getElementById('appsContent');
    
    // Show loading state
    loadingElement.style.display = 'block';
    contentElement.classList.add('hidden');
    
    // Initialize icon loading for all app icons
    document.querySelectorAll('.app-icon-img').forEach(img => {
        loadAppIcon(img, img.dataset.package);
    });

    // Hide loading state after icons are loaded
    Promise.all(Array.from(document.querySelectorAll('.app-icon-img')).map(img => {
        return new Promise((resolve) => {
            if (img.complete) resolve();
            img.onload = resolve;
            img.onerror = resolve;
        });
    })).then(() => {
        loadingElement.style.display = 'none';
        contentElement.classList.remove('hidden');
    });

    const searchInput = document.getElementById('searchApps');
    const clearButton = document.getElementById('clearSearch');

    // Show/hide clear button based on input content
    searchInput.addEventListener('input', function() {
        clearButton.style.display = this.value ? 'flex' : 'none';
        filterApps();
    });

    // Clear search when X is clicked
    clearButton.addEventListener('click', function() {
        searchInput.value = '';
        clearButton.style.display = 'none';
        filterApps();
        searchInput.focus(); // Keep focus on input after clearing
    });

    // Show clear button if search has initial value
    if (searchInput.value) {
        clearButton.style.display = 'flex';
    }

    const tabButtons = document.querySelectorAll('.tab-button');
    
    // Check device connection every second
    setInterval(checkDeviceConnection, 1000);
    
    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            const tabType = button.dataset.tab;
            document.getElementById('userApps').classList.toggle('hidden', tabType !== 'user');
            document.getElementById('systemApps').classList.toggle('hidden', tabType !== 'system');
            
            searchInput.value = '';
            filterApps();
        });
    });

    // Search functionality
    searchInput.addEventListener('input', filterApps);

    // Uninstall functionality
    document.querySelectorAll('.uninstall-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (confirm('Are you sure you want to uninstall this app?')) {
                uninstallApp(this.dataset.device, this.dataset.package);
            }
        });
    });
});

function loadAppIcon(img, packageName) {
    const iconSources = [
        `https://play-lh.googleusercontent.com/apps/icon/${packageName}`,
        `https://lh3.googleusercontent.com/apps/icon/${packageName}`,
        `https://raw.githubusercontent.com/android-app-icons/icons/main/${packageName}.png`,
        '/static/default_app_icon.png'
    ];
    
    function tryNextSource(index) {
        if (index >= iconSources.length) {
            img.src = '/static/default_app_icon.png';
            return;
        }

        const tempImg = new Image();
        tempImg.onload = function() {
            img.src = this.src;
        };
        tempImg.onerror = function() {
            tryNextSource(index + 1);
        };
        tempImg.src = iconSources[index];
    }

    tryNextSource(0);
}

function checkDeviceConnection() {
    fetch('/check_devices')
        .then(response => response.json())
        .then(data => {
            const urlParts = window.location.pathname.split('/');
            const deviceId = urlParts[urlParts.length - 1];
            
            if (!data.devices.includes(deviceId)) {
                window.location.href = '/';
            }
        })
        .catch(error => console.error('Error:', error));
}

function filterApps() {
    const searchTerm = document.getElementById('searchApps').value.toLowerCase();
    const activeTab = document.querySelector('.tab-button.active').dataset.tab;
    const appsList = document.getElementById(activeTab + 'Apps');
    
    appsList.querySelectorAll('.app-item').forEach(app => {
        const packageName = app.dataset.package.toLowerCase();
        const appName = app.querySelector('.app-name').textContent.toLowerCase();
        const matchesSearch = packageName.includes(searchTerm) || appName.includes(searchTerm);
        app.style.display = matchesSearch ? 'flex' : 'none';
    });
}

function uninstallApp(deviceId, packageName) {
    const formData = new FormData();
    formData.append('device_id', deviceId);
    formData.append('package', packageName);

    fetch('/uninstall_app', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const appElement = document.querySelector(`[data-package="${packageName}"]`);
            appElement.remove();
            alert('App uninstalled successfully');
        } else {
            alert('Failed to uninstall app: ' + data.message);
        }
    })
    .catch(error => {
        alert('Error uninstalling app: ' + error);
    });
} 