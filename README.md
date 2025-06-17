# CyberBloat - Android Device Manager

<p align="center">
  <img src="static/images/cyberbloat-logo-title.png" alt="CyberBloat Logo"  width="350"/>
</p>

CyberBloat is a web-based Android device management tool that provides a user-friendly interface for ADB (Android Debug Bridge) operations. It allows you to manage your Android device through a local web interface.

## 🚀 Features

### 📱 Device Management
- Real-time device connection monitoring
- Multiple device support
- Automatic device detection

### 📦 App Management
- View installed user apps
- View system apps
- Uninstall applications
- View app details and Play Store links

### 💻 Shell Commands
- Execute custom ADB shell commands
- Quick access to common commands
- Real-time command output

### ℹ️ Device Information
- Battery status
- Device properties
- Network information
- Process list
- Storage information

## 🛠️ Installation

### Prerequisites
- Python 3.6 or higher
- Git
- ADB (Android Debug Bridge) & Fastboot installed on your system

### Installing ADB & Fastboot

#### Windows
```cmd
# Using Windows Package Manager (Winget)
winget install --id Google.PlatformTools
```

Alternatively:
1. Download [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)
2. Extract to a permanent location (e.g., `C:\Program Files\platform-tools`)
3. Add to System Path:
   - Open "Environment Variables" (Search "Environment Variables" in Start menu)
   - Under "System Variables", find and select "Path"
   - Click "Edit" and then "New"
   - Add the platform-tools folder path
   - Click "OK" to save all changes
   - Restart any open terminal windows

#### macOS
```bash
# Using Homebrew
brew install android-platform-tools
```

#### Linux (Debian/Ubuntu)
```bash
sudo apt update
sudo apt install android-tools-adb android-tools-fastboot
```

### Verify ADB Installation
Open terminal/command prompt and run:
```bash
adb version
```
You should see the ADB version information. If you get a "command not found" error, ensure ADB is properly installed and added to your system PATH.

### CyberBloat Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/webtech781/CYBERBLOAT.git
   cd CYBERBLOAT
   ```

2. **Create Virtual Environment**
   ```bash
    # On Windows:
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   venv\Scripts\activate
   ```
   ```
   # On Linux/Mac:
   # Create virtual environment
   python3 -m venv venv
   # Activate virtual environment
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Application**
   ```bash
   python app.py
   ```

5. **Access Web Interface**
   - Open browser and navigate to `http://localhost:5000`
   - Connect Android device via USB
   - Enable USB debugging
   - Accept debugging prompt on device

## 📱 Android Device Setup

1. Enable Developer Options:
   - Go to Settings
   - About Phone
   - Tap Build Number 7 times
   - Developer Options will appear in Settings

2. Enable USB Debugging:
   - Go to Settings
   - Developer Options
   - Enable USB Debugging
   - Connect device to computer
   - Accept USB debugging prompt

## 🔧 Troubleshooting

### Common Issues:
1. **ADB Not Found**
   - Ensure ADB files are in the correct location
   - Check if ADB is in system PATH

2. **Device Not Detected**
   - Enable USB debugging
   - Try different USB cable
   - Accept USB debugging prompt

3. **Dependencies Error**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**CyberVams**
- GitHub: [@webtech781](https://github.com/webtech781)
- Project: [CYBERBLOAT](https://github.com/webtech781/CYBERBLOAT)

## 🙏 Acknowledgments

- Android Debug Bridge (ADB)
- Flask Framework
- Google Play Store API
