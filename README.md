# 🚀 Adaptive Process Booster - Advanced Edition

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive, cross-platform GUI application for real-time process monitoring, priority management, and system resource optimization.

## 📋 Table of Contents

- [Features](#-features)
- [Screenshots](#-screenshots)
- [Installation](#-installation)
- [Usage](#-usage)
- [Requirements](#-requirements)
- [Platform Support](#-platform-support)
- [Features in Detail](#-features-in-detail)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

## ✨ Features

### Core Functionality
- 🔍 **Real-time Process Monitoring** - Monitor all running processes with live CPU and RAM usage
- ⚡ **Priority Management** - Boost or lower process priorities with multiple priority levels
- 🤖 **Auto-Boost** - Automatically boost processes based on configurable thresholds
- 💻 **System Resource Monitoring** - Track CPU, Memory, and Disk usage in real-time
- 📊 **Dynamic Scoring** - Intelligent scoring algorithm (60% CPU + 40% RAM weighted)

### User Interface
- 🎨 **Modern GUI** - Clean, intuitive interface with color-coded indicators
- 🔎 **Advanced Search** - Search processes by name or PID
- 📈 **Multi-column Sorting** - Sort by Score, CPU %, RAM %, PID, or Name
- 🔽 **Smart Filtering** - Filter by High CPU, High RAM, or High Score
- 📜 **Action History** - Complete log of all actions with timestamps

### Data Management
- 💾 **CSV Export** - Export process data to CSV files
- 📝 **Log Export** - Export action history to text files
- 📋 **Process Details** - Comprehensive process information display
- ⚙️ **Settings Management** - Configure auto-boost thresholds and priority levels

### Additional Features
- 🖱️ **Context Menu** - Right-click quick actions
- 🔄 **Real-time Updates** - Automatic refresh every second
- 🎯 **Cross-platform** - Works on Windows and Linux
- 🛡️ **Error Handling** - Graceful handling of access denied and process errors

## 📸 Screenshots

### Process Monitor Tab
- Real-time process list with CPU, RAM, and Score metrics
- Search, sort, and filter capabilities
- Quick action buttons for boosting, viewing details, and terminating processes

### System Resources Tab
- CPU usage with color-coded progress bar
- Memory usage with detailed GB information
- Disk usage monitoring
- Running process count

### History & Logs Tab
- Complete action history with timestamps
- Export functionality for logs

## 🚀 Installation

### Prerequisites
- Python 3.6 or higher
- pip (Python package installer)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/adaptive-process-booster.git
cd adaptive-process-booster
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python adaptive_process_booster.py
```

### For Windows Users
On Windows, you may need to run as Administrator for full functionality:
1. Right-click on Command Prompt or PowerShell
2. Select "Run as Administrator"
3. Navigate to the project directory
4. Run: `python adaptive_process_booster.py`

### For Linux Users
On Linux, you may need root privileges for some operations:
```bash
sudo python3 adaptive_process_booster.py
```

## 💻 Usage

### Basic Operations

1. **View Processes**
   - All running processes are displayed automatically
   - Processes update every second

2. **Search for a Process**
   - Type in the search box to filter by process name or PID

3. **Sort Processes**
   - Click column headers to sort (Score, CPU %, RAM %, PID, Name)
   - Click again to reverse sort order

4. **Filter Processes**
   - Use the filter dropdown to show only:
     - High CPU usage (>50%)
     - High RAM usage (>50%)
     - High Score (>50)

5. **Boost Process Priority**
   - Select a process from the list
   - Click "⚡ Boost Process" button
   - Choose priority level when prompted
   - Process priority will be updated

6. **View Process Details**
   - Select a process
   - Click "ℹ️ View Details" or double-click the process
   - View comprehensive process information

7. **Terminate a Process**
   - Select a process
   - Click "🗑️ Kill Process"
   - Confirm the action
   - ⚠️ **Warning**: This will terminate the process immediately

8. **Configure Auto-Boost**
   - Go to Tools → Settings
   - Enable "Auto-Boost"
   - Set threshold (default: 50.0)
   - Select priority level
   - Click "💾 Save"

9. **Export Data**
   - File → Export to CSV: Export process list
   - History tab → Export Logs: Export action history

### Priority Levels

#### Windows
- **Realtime** - Highest priority (use with caution)
- **High** - High priority
- **Above Normal** - Above normal priority
- **Normal** - Default priority
- **Below Normal** - Below normal priority
- **Low** - Low priority

#### Linux
- **Very High** (-10) - Highest priority
- **High** (-5) - High priority
- **Above Normal** (-2) - Above normal priority
- **Normal** (0) - Default priority
- **Below Normal** (5) - Below normal priority
- **Low** (10) - Low priority

## 📦 Requirements

### Python Packages
- `psutil` - System and process utilities
- `tkinter` - GUI framework (usually included with Python)

### System Requirements
- **OS**: Windows 7+ or Linux
- **RAM**: 100 MB minimum
- **Python**: 3.6 or higher
- **Privileges**: Administrator/root recommended for full functionality

## 🖥️ Platform Support

### Windows
- ✅ Windows 7, 8, 10, 11
- ✅ Full priority management support
- ✅ Administrator privileges recommended

### Linux
- ✅ All major distributions
- ✅ Full priority management support
- ✅ Root privileges may be required for some operations

### macOS
- ⚠️ Not fully tested (should work with minor modifications)

## 🔧 Features in Detail

### Dynamic Scoring Algorithm
The application uses a weighted scoring system to identify resource-intensive processes:
```
Score = (0.6 × CPU Usage) + (0.4 × RAM Usage)
```
This formula prioritizes CPU usage while considering memory consumption.

### Auto-Boost Feature
When enabled, the application automatically boosts processes that exceed the configured threshold:
- Monitors all processes continuously
- Calculates dynamic score for each process
- Automatically boosts processes with score > threshold
- Logs all auto-boost actions

### Thread Safety
- Background monitoring thread runs independently
- GUI updates use thread-safe `root.after()` mechanism
- No blocking of the main GUI thread

### Error Handling
- Graceful handling of terminated processes
- Access denied errors for protected processes
- Zombie process detection
- Disk path fallback mechanisms

## 🛠️ Development

### Project Structure
```
adaptive-process-booster/
├── adaptive_process_booster.py  # Main application file
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── LICENSE                      # License file
└── .gitignore                  # Git ignore rules
```

### Code Statistics
- **Total Lines**: 1,224
- **Functions**: 8 utility functions
- **Classes**: 3 main classes
- **Language**: Python 3

### Key Components
- **Utility Functions**: Process management, priority boosting, scoring
- **GUI Classes**: Main application, process details window, settings window
- **Monitoring Thread**: Background process monitoring
- **Data Structures**: History tracking, process caching

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Areas for Contribution
- 🧪 Unit tests and integration tests
- 📊 Graphical visualizations (charts/graphs)
- ⚙️ Settings persistence to file
- 🌐 Network monitoring features
- 🎨 Dark mode theme
- 📚 Documentation improvements
- 🐛 Bug fixes

## ⚠️ Disclaimer

**Use at your own risk!** 

- Modifying process priorities can affect system stability
- Terminating processes may cause data loss
- Always save your work before terminating applications
- Some system processes are protected and cannot be modified
- Administrator/root privileges are required for full functionality

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

## 🙏 Acknowledgments

- Built with [psutil](https://github.com/giampaolo/psutil) for system and process utilities
- GUI built with [tkinter](https://docs.python.org/3/library/tkinter.html)
- Inspired by the need for better process management tools

## 📊 Project Status

- ✅ Core functionality: 100% Complete
- ✅ User interface: 100% Complete
- ⚠️ Settings persistence: 80% Complete
- ⚠️ Testing: 20% Complete
- ⚠️ Documentation: 85% Complete

**Overall Project Completion: ~85%**

---

⭐ If you find this project useful, please consider giving it a star on GitHub!


