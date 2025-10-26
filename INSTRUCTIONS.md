# 📋 File Guide & Instructions

This document provides a comprehensive guide to all files in the bet365 scraping project and how to run them.

## � Quick Start - All-in-One Solution

**The fastest way to get everything running:**

```bash
# Start the complete system (API + UI + Live + Pregame)
cd "C:\bet365 demo"
P:/Mamba/Scripts/conda.exe run -p "C:\data\joy" --no-capture-output python dashboard_api.py

# Access the web dashboard at: http://localhost:8000
# API documentation at: http://localhost:8000/docs
```

**What `dashboard_api.py` includes:**
- ✅ **FastAPI Server** - REST API endpoints for all match data
- ✅ **Web Dashboard** - Interactive UI at http://localhost:8000
- ✅ **Live Betting Integration** - Automatically starts live scraping
- ✅ **Pregame Data** - Loads and serves pregame matches
- ✅ **WebSocket Support** - Real-time updates to the dashboard
- ✅ **Combined Data View** - Both live and pregame matches in one interface

*This single command provides the complete betting analytics platform!*

## � Environment Setup

### Prerequisites
```bash
# 1. Ensure conda environment "joy" exists and is activated
P:/Mamba/Scripts/conda.exe info --envs

# 2. Install required packages
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output pip install -r requirements.txt

# 3. Install Playwright browsers (one-time setup)
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output playwright install

# 4. Verify installation
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output python -c "import patchright; print('✅ Setup complete')"
```

### Package Dependencies
The `requirements.txt` file includes all necessary packages:
- **patchright/playwright** - Browser automation
- **fastapi/uvicorn** - Web framework and server
- **beautifulsoup4/lxml** - HTML parsing
- **asyncio/aiofiles** - Async processing
- **websockets** - Real-time communication

## �📁 Project Structure

```
bet365-demo/
├── 🚀 CORE SCRAPERS
│   ├── pregame_new.py              # Main pregame scraper
│   ├── comprehensive_extraction_script.py  # Legacy comprehensive scraper
│   ├── concurrency_live_bet365.py # Live betting scraper
│   └── live_parser_bet365.py      # Live parser utilities
│
├── 🔄 REAL-TIME MONITORING
│   ├── realtime_monitor.py        # Real-time pregame monitor
│   └── dashboard_api.py           # API server for live dashboard
│
├── 🌐 WEB INTERFACE
│   └── index.html                 # Live dashboard web interface
│
├── 📊 DATA FILES
│   ├── bet365_live_current.json   # Current live matches
│   ├── bet365_live_history.json   # Live matches history
│   ├── bet365_live_statistics.json # Live betting statistics
│   └── bet365_statistics.json     # General statistics
│
├── ⚙️ CONFIGURATION
│   └── bet365_selectors_detailed.json # CSS selectors config
│
├── 📁 OUTPUT DIRECTORIES
│   ├── outputs/
│   │   ├── current_pregame_data.json    # Current pregame matches
│   │   ├── debug/                       # Debug information
│   │   ├── html/                        # Saved HTML pages
│   │   └── realtime/                    # Real-time monitoring data
│   │       ├── cycle_statistics.json   # Monitoring statistics
│   │       └── logs/                    # Monitor log files
│   └── __pycache__/                     # Python cache files
│
└── 📖 DOCUMENTATION
    ├── README.md                   # Main project documentation
    ├── INSTRUCTIONS.md            # This file - usage instructions
    ├── ADDING_NEW_SPORTS.md       # Guide for adding new sports
    ├── ARCHITECTURE.md            # System architecture documentation
    └── requirements.txt           # Python package dependencies
```

## 🚀 Core Scrapers

### 1. Pregame Scraper (`pregame_new.py`)
**Purpose**: Scrapes pregame betting data from bet365
**Type**: Standalone scraper for upcoming matches

```bash
# Basic run
python pregame_new.py

# Run with custom options
python pregame_new.py --headless --wait 5000

# Environment setup required
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output python pregame_new.py
```

**Features**:
- ✅ Scrapes all major sports (NFL, NBA, NHL, MLB, Tennis, Soccer, etc.)
- ✅ Extracts complete odds (spread, total, moneyline)
- ✅ Handles multiple betting markets
- ✅ Saves to `outputs/current_pregame_data.json`
- ✅ Intelligent sport detection and filtering

**Output**: Creates structured JSON with pregame matches and odds

### 2. Live Betting Scraper (`concurrency_live_bet365.py`)
**Purpose**: Scrapes live/in-play betting data
**Type**: Concurrent scraper for live matches

```bash
# Monitor mode (continuous)
python concurrency_live_bet365.py --mode monitor --interval 10

# Single extraction
python concurrency_live_bet365.py --mode extract

# With environment
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output python concurrency_live_bet365.py --mode monitor --interval 10
```

**Features**:
- ✅ Real-time live match monitoring
- ✅ Concurrent processing of multiple sports
- ✅ Live odds tracking and updates
- ✅ Saves to `bet365_live_current.json`
- ✅ Persistent tab pool for efficiency

**Output**: Updates live betting data continuously

### 3. Comprehensive Scraper (`comprehensive_extraction_script.py`)
**Purpose**: Legacy comprehensive scraper
**Status**: Deprecated - use `pregame_new.py` instead

```bash
# For backward compatibility only
python comprehensive_extraction_script.py
```

**Note**: This is the older version. Use `pregame_new.py` for current projects.

## 🔄 Real-Time Monitoring

### 1. Real-Time Monitor (`realtime_monitor.py`)
**Purpose**: Real-time monitoring of pregame data changes
**Type**: Async monitoring system

```bash
# Start monitoring
python realtime_monitor.py

# With environment
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output python realtime_monitor.py
```

**Features**:
- ✅ Real-time change detection (insert/update/delete)
- ✅ Parallel monitoring of multiple sports
- ✅ History tracking and archival
- ✅ Smart deduplication
- ✅ Cycle statistics and performance metrics

**Output**: 
- Updates `outputs/current_pregame_data.json`
- Creates `outputs/realtime/cycle_statistics.json`
- Logs to `outputs/realtime/logs/`

### 2. Dashboard API (`dashboard_api.py`)
**Purpose**: FastAPI server for web dashboard
**Type**: API server with WebSocket support

```bash
# Start API server
python dashboard_api.py

# With environment
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output python dashboard_api.py
```

**Features**:
- ✅ REST API endpoints for match data
- ✅ WebSocket real-time updates
- ✅ Combines live and pregame data
- ✅ Web dashboard interface
- ✅ CORS enabled for development

**Endpoints**:
- `GET /` - Web dashboard
- `GET /api/live-matches` - All matches (live + pregame)
- `GET /api/sports` - Available sports
- `GET /api/historical-matches` - Historical data
- `WebSocket /ws` - Real-time updates

**Access**: http://localhost:8000

## 🌐 Web Interface

### Dashboard (`index.html`)
**Purpose**: Live web dashboard for viewing betting data
**Type**: Static HTML with JavaScript

**Features**:
- ✅ Real-time match updates
- ✅ Live and pregame data display
- ✅ Sports filtering
- ✅ Odds comparison
- ✅ WebSocket connection for live updates

**Access**: Via dashboard API at http://localhost:8000

## 📊 Data Files

### Live Data Files
- `bet365_live_current.json` - Current live matches
- `bet365_live_history.json` - Historical live matches
- `bet365_live_statistics.json` - Live betting statistics

### Pregame Data Files
- `outputs/current_pregame_data.json` - Current pregame matches
- `outputs/realtime/cycle_statistics.json` - Monitoring statistics

### Configuration Files
- `bet365_selectors_detailed.json` - CSS selectors and patterns

## 🎯 Common Usage Scenarios

### Scenario 1: One-time Pregame Data Extraction
```bash
# Quick pregame scrape
cd "C:\Users\User\Desktop\thesis\work related task\bet365\bet365 demo"
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output python pregame_new.py

# Check results
cat outputs/current_pregame_data.json
```

### Scenario 2: Live Dashboard with Real-time Updates
```bash
# Terminal 1: Start API server
python dashboard_api.py

# Terminal 2: Start real-time monitoring (optional - API starts its own)
python realtime_monitor.py

# Access dashboard at http://localhost:8000
```

### Scenario 3: Continuous Live Betting Monitoring
```bash
# Start live scraper in monitor mode
python concurrency_live_bet365.py --mode monitor --interval 10

# Data updates to bet365_live_current.json continuously
```

### Scenario 4: Development and Testing
```bash
# Test pregame scraper
python pregame_new.py --headless

# Test API endpoints
curl http://localhost:8000/api/live-matches

# Check logs
tail -f outputs/realtime/logs/monitor_*.log
```

## ⚙️ Configuration Options

### Environment Setup
```bash
# Required: Use the joy conda environment
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output python <script>
```

### Common Options

**Pregame Scraper** (`pregame_new.py`):
- `--headless` - Run browser in headless mode
- `--wait <ms>` - Wait time after navigation (default: 10000ms)
- `--scrolls <num>` - Number of scroll attempts (default: 15)

**Live Scraper** (`concurrency_live_bet365.py`):
- `--mode <extract|monitor>` - Single extract or continuous monitoring
- `--interval <seconds>` - Update interval for monitor mode (default: 10)
- `--duration <seconds>` - Duration for monitoring (default: unlimited)

**Real-time Monitor** (`realtime_monitor.py`):
- Built-in configuration in the class initialization
- Modify `update_interval` for monitoring frequency

**Dashboard API** (`dashboard_api.py`):
- Runs on port 8000 by default
- Auto-starts integrated monitoring systems

## 🔧 Troubleshooting

### Common Issues

**1. Browser/WebDriver Issues**
```bash
# Install required browser
pip install playwright
playwright install chromium

# Or use the project's patchright
pip install patchright
patchright install chromium
```

**2. Environment Issues**
```bash
# Verify conda environment
P:/Mamba/Scripts/conda.exe info --envs

# Check Python path
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output python -c "import sys; print(sys.executable)"
```

**3. Permission Issues**
```bash
# Check output directory permissions
ls -la outputs/
mkdir -p outputs/realtime/logs
```

**4. Port Already in Use (Dashboard)**
```bash
# Kill existing process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**5. Missing Dependencies**
```bash
# Install missing packages in joy environment
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output pip install fastapi uvicorn aiofiles
```

## 📈 Performance Tips

### For Better Performance:
1. **Use headless mode** for production: `--headless`
2. **Adjust wait times** based on internet speed: `--wait 5000`
3. **Limit scrolls** for faster extraction: `--scrolls 10`
4. **Monitor system resources** when running multiple scrapers
5. **Use SSD storage** for better I/O performance with logs/data files

### Memory Management:
- Pregame scraper: ~200-400MB RAM
- Live scraper: ~300-500MB RAM  
- Dashboard API: ~150-300MB RAM
- Real-time monitor: ~100-200MB RAM

### Recommended Setup:
- **Development**: Run individually for testing
- **Production**: Use dashboard API (includes integrated monitoring)
- **Data Collection**: Combine pregame + live scrapers with monitoring

## 🔄 Data Flow

```
Pregame Scraper → outputs/current_pregame_data.json
      ↓
Real-time Monitor → cycle_statistics.json + logs/
      ↓
Dashboard API → Combines all data → Web Interface
      ↑
Live Scraper → bet365_live_current.json
```

## 📋 Quick Reference

| Task | Command | Output |
|------|---------|--------|
| **Pregame scrape** | `python pregame_new.py` | `outputs/current_pregame_data.json` |
| **Live monitoring** | `python concurrency_live_bet365.py --mode monitor` | `bet365_live_current.json` |
| **Real-time monitor** | `python realtime_monitor.py` | `outputs/realtime/` |
| **Web dashboard** | `python dashboard_api.py` | http://localhost:8000 |
| **API test** | `curl localhost:8000/api/live-matches` | JSON response |

---

**💡 Pro Tip**: For production use, start with `python dashboard_api.py` as it integrates both live and pregame monitoring with a web interface.