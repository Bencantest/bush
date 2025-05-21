
---

# 🖥️ System Monitor with AI Analysis

This project provides a **Python-based system monitoring tool** (`system_monitor.py`) that leverages the `psutil` library to gather real-time system and process information. It integrates with an **AI monitoring script** (`aimonitor.py`) that uses the **Groq API** to analyze the collected data and provide intelligent advice on system performance, congestion or potential malicious activities.

---

## 🚀 Features

* **Comprehensive System Metrics**: Monitor CPU, memory, disk nd network I/O.
* **Detailed Process Listing**: View all running processes with their PID, name, user, CPU/memory usage and command-line arguments.
* **Process Filtering**: Filter processes by name or command-line arguments.
* **Top CPU Consumers**: Identify processes consuming the most CPU time.
* **Memory Usage Analysis**: Find processes using memory within a specified range (e.g., 40MB to 100MB).
* **Background Monitoring**: Run continuously in the background to periodically collect system data.
* **AI-Powered Insights**: Send system/process data to the Groq AI model for intelligent analysis and actionable advice on system health and security.

---

## 📋 Prerequisites

Ensure the following are installed:

* **Python 3.6+** – [Download here](https://www.python.org/downloads/)
* **pip** – Usually comes with Python
* **Groq API Key** – [Get one from Groq](https://groq.com/) (Required for AI analysis)

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/bush.git
cd bush
```

> 🔁 Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

### 2. Install Dependencies

```bash
pip install psutil requests
```

---

## 🔐 Configuration (Groq API Key)

Set your **Groq API key** as an environment variable.

### Windows (Command Prompt)

```cmd
set GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
```

### Windows (PowerShell)

```powershell
$env:GROQ_API_KEY="YOUR_GROQ_API_KEY_HERE"
```

### Linux/macOS (Bash/Zsh)

```bash
export GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
```

> 📝 *These environment variables are temporary for the session. For a permanent setup, add the export command to `.bashrc`, `.zshrc`, or `.profile`.*

---

## 🛠️ Usage

Navigate to the project directory:

```bash
cd path/to/bush
```

### 🔍 `system_monitor.py`

This script provides command-line options for system and process monitoring.

#### Show Overall System Info

```bash
python system_monitor.py --system
```

#### List All Running Processes

```bash
python system_monitor.py --processes
```

#### Filter by Name (e.g Chrome)

```bash
python system_monitor.py --processes -n chrome
```

#### Filter by Command-Line (e.g Edge renderer)

```bash
python system_monitor.py --processes -c "type=renderer"
```

#### Top N Processes by CPU Time (e.g Top 5)

```bash
python system_monitor.py --top-cpu 5
```

#### Memory Usage in a Range (e.g 40MB to 100MB)

```bash
python system_monitor.py --mem-range 40 100
```

#### Run in Background with AI Analysis

```bash
python system_monitor.py --run-in-background
```

Customize intervals:

```bash
python system_monitor.py --run-in-background --interval 30 --ai-interval 600
```

### 🤖 `aimonitor.py` (Standalone Test Mode)

You can also run `aimonitor.py` directly for testing AI analysis:

```bash
python aimonitor.py
```

---

## 🛑 Terminating the Background Monitor

To stop background monitoring:

1. Focus the terminal where it's running.
2. Press `Ctrl + C` (you may need to press it twice).
3. You’ll see:

   ```
   Background monitoring stopped by user.
   ```

---

## 📁 Project Structure

```
bush/
└── .gitignore            # Git ignored files
├── README.md             # Project documentation
├── system_monitor.py     # System data and process monitoring
├── aimonitor.py          # AI-powered analysis


```

---

## 🤝 Contributing

Feel free to **fork** this repository, open **issues**, or submit **pull requests** if you have suggestions or improvements!

---

## 📄 License

This project is open-source under the **MIT License**.


