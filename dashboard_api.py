#!/usr/bin/env python3
"""
Real-time API Server for Live Betting Dashboard
Serves data from the concurrent scraper to the React dashboard
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging
import subprocess
import threading

# Import the real-time monitoring system
from realtime_monitor import RealTimeMonitor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

# Background task to monitor file changes and broadcast
async def monitor_data_changes():
    """Monitor data file for changes and broadcast to connected clients"""
    last_modified = None

    while True:
        try:
            if CURRENT_DATA_FILE.exists():
                current_modified = CURRENT_DATA_FILE.stat().st_mtime

                if last_modified is None or current_modified > last_modified:
                    last_modified = current_modified

                    # Load and broadcast new data
                    data = load_current_data()
                    transformed_matches = transform_match_data(data.get('matches', []))

                    await manager.broadcast({
                        'type': 'update',
                        'data': {
                            'timestamp': data.get('timestamp'),
                            'matches': transformed_matches,
                            'summary': data.get('summary', {})
                        }
                    })

                    logger.info(f"Broadcasted update to {len(manager.active_connections)} clients")

            await asyncio.sleep(1)  # Check every second

        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")
            await asyncio.sleep(5)

# Integrated monitoring with realtime_monitor for pregame data
# Live data is still handled by concurrent scraper

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler"""
    # Startup
    live_task = asyncio.create_task(monitor_data_changes())

    # Start concurrent live scraper in a separate thread
    def start_concurrent_scraper():
        try:
            logger.info("Starting concurrent live scraper...")
            python_path = r"C:\Users\User\Desktop\thesis\data\joy\python.exe"
            subprocess.run([python_path, "concurrency_live_bet365.py", "--mode", "monitor", "--interval", "10"])
        except Exception as e:
            logger.error(f"Failed to start concurrent scraper: {e}")

    # Start integrated pregame real-time monitor
    async def start_pregame_realtime_monitor():
        try:
            logger.info("Starting integrated pregame real-time monitor...")
            monitor = RealTimeMonitor(update_interval=1.0)
            await monitor.start_monitoring()
        except Exception as e:
            logger.error(f"Failed to start pregame monitor: {e}")
    
    scraper_thread = threading.Thread(target=start_concurrent_scraper, daemon=True)
    scraper_thread.start()
    
    # Start pregame monitor as async task
    pregame_task = asyncio.create_task(start_pregame_realtime_monitor())
    
    logger.info("API Server started - Live scraper and integrated pregame real-time monitor active")
    
    yield
    
    # Shutdown
    live_task.cancel()
    pregame_task.cancel()
    
    try:
        await live_task
    except asyncio.CancelledError:
        pass
        
    try:
        await pregame_task
    except asyncio.CancelledError:
        pass

# Initialize FastAPI app with lifespan
app = FastAPI(title="Live Betting Dashboard API", version="1.0.0", lifespan=lifespan)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data file paths
CURRENT_DATA_FILE = Path("bet365_live_current.json")
HISTORY_DATA_FILE = Path("bet365_live_history.json")
PREGAME_DATA_FILE = Path("outputs/current_pregame_data.json")  # Real-time pregame data from monitor
PREGAME_HISTORY_FILE = Path("outputs/pregame_history.json")  # Pregame history from monitor
LEGACY_PREGAME_DATA_FILE = Path("ultimate_revised_sport_bet365_data_latest.json")  # Consistent legacy format

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)

manager = ConnectionManager()

# Data cache
data_cache = {
    'matches': [],
    'timestamp': None,
    'summary': {}
}

def load_current_data() -> Dict[str, Any]:
    """Load current match data from both live and pregame JSON files"""
    try:
        all_matches = []
        live_matches = []
        pregame_matches = []

        # Load live data with error handling
        if CURRENT_DATA_FILE.exists():
            try:
                with open(CURRENT_DATA_FILE, 'r', encoding='utf-8') as f:
                    live_data = json.load(f)
                    live_matches = live_data.get('matches', [])
                    logger.info(f"Loaded {len(live_matches)} live matches")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load live data: {e}")
                live_matches = []

        # Load pregame data from realtime_monitor output with error handling
        if PREGAME_DATA_FILE.exists():
            try:
                # Load from real-time pregame data file (realtime_monitor format)
                with open(PREGAME_DATA_FILE, 'r', encoding='utf-8') as f:
                    pregame_data = json.load(f)
                    
                    # Handle different data structures in current_pregame_data.json
                    if 'sports_data' in pregame_data:
                        # New format: sports_data -> sport -> games[]
                        for sport_name, sport_data in pregame_data.get('sports_data', {}).items():
                            if isinstance(sport_data, dict) and 'games' in sport_data:
                                games = sport_data['games']
                            elif isinstance(sport_data, list):
                                games = sport_data
                            else:
                                continue
                                
                            # Convert each game to match format
                            for game in games:
                                pregame_matches.append({
                                    'id': game.get('game_id', f"pregame_{sport_name}_{len(pregame_matches)}"),
                                    'sport': game.get('sport', sport_name),
                                    'player1_team1': game.get('team1', ''),
                                    'player2_team2': game.get('team2', ''),
                                    'date': game.get('date', ''),
                                    'time': game.get('time', ''),
                                    'odds': game.get('odds', {}),
                                    'confidence_score': game.get('confidence_score', 0),
                                    'fixture_id': game.get('fixture_id', ''),
                                    'league': sport_name,  # Use sport name as league
                                    'timestamp': pregame_data.get('extraction_info', {}).get('timestamp', datetime.now().isoformat())
                                })
                    elif 'games' in pregame_data:
                        # Fallback: direct games array
                        pregame_games = pregame_data.get('games', [])
                        
                        # Convert from Game object dict format to match format
                        for game in pregame_games:
                            pregame_matches.append({
                                'id': game.get('fixture_id', f"pregame_{len(pregame_matches)}"),
                                'sport': game.get('sport', 'Unknown'),
                                'player1_team1': game.get('team1', ''),
                                'player2_team2': game.get('team2', ''),
                                'date': game.get('date', ''),
                                'time': game.get('time', ''),
                                'odds': game.get('odds', {}),
                                'confidence_score': game.get('confidence_score', 0),
                                'fixture_id': game.get('fixture_id', ''),
                                'timestamp': pregame_data.get('timestamp', datetime.now().isoformat())
                            })
                    
                    logger.info(f"Loaded {len(pregame_matches)} pregame matches from real-time monitor file")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load real-time pregame data: {e}")
                pregame_matches = []
        else:
            # Fall back to legacy format
            if LEGACY_PREGAME_DATA_FILE.exists():
                with open(LEGACY_PREGAME_DATA_FILE, 'r', encoding='utf-8') as f:
                    pregame_data = json.load(f)
                    # Extract matches from the sports_data structure
                    for sport_data in pregame_data.get('sports_data', {}).values():
                        pregame_matches.extend(sport_data)
                    logger.info(f"Loaded {len(pregame_matches)} pregame matches from legacy file {LEGACY_PREGAME_DATA_FILE}")

        # Combine all matches
        all_matches = live_matches + pregame_matches

        # Create combined data structure
        combined_data = {
            'timestamp': datetime.now().isoformat(),
            'matches': all_matches,
            'summary': {
                'total_matches': len(all_matches),
                'live_matches': len(live_matches),
                'pregame_matches': len(pregame_matches),
                'sports_processed': len(set(m.get('sport', 'Unknown') for m in all_matches))
            }
        }

        return combined_data

    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'matches': [],
            'summary': {
                'total_matches': 0,
                'live_matches': 0,
                'pregame_matches': 0,
                'sports_processed': 0
            }
        }

def transform_match_data(matches: List[Dict]) -> List[Dict]:
    """Transform match data for frontend consumption with improved error handling"""
    transformed = []
    
    if not matches:
        return transformed

    for i, match in enumerate(matches):
        try:
            # Skip invalid match data
            if not match or not isinstance(match, dict):
                logger.warning(f"Skipping invalid match at index {i}: {type(match)}")
                continue
            # Handle different data formats (live vs pregame)
            if 'player1_team1' in match and 'player2_team2' in match:
                # This is pregame data format - transform odds to markets format
                odds = match.get('odds', {})
                markets = []

                # Transform odds to markets format for frontend with proper odds formatting
                if odds:
                    if 'spread' in odds and odds['spread']:
                        # Handle spread odds - ensure they're properly formatted
                        home_odds = odds['spread'][0] if len(odds['spread']) > 0 else 'N/A'
                        away_odds = odds['spread'][1] if len(odds['spread']) > 1 else 'N/A'
                        
                        markets.append({
                            'name': 'Point Spread',
                            'selections': [
                                {'name': 'Home', 'odds': str(home_odds).strip()},
                                {'name': 'Away', 'odds': str(away_odds).strip()}
                            ]
                        })
                        
                    if 'total' in odds and odds['total']:
                        # Handle total odds - ensure they're properly formatted
                        over_odds = odds['total'][0] if len(odds['total']) > 0 else 'N/A'
                        under_odds = odds['total'][1] if len(odds['total']) > 1 else 'N/A'
                        
                        markets.append({
                            'name': 'Total Points',
                            'selections': [
                                {'name': 'Over', 'odds': str(over_odds).strip()},
                                {'name': 'Under', 'odds': str(under_odds).strip()}
                            ]
                        })
                        
                    if 'moneyline' in odds and odds['moneyline']:
                        # Handle moneyline odds - ensure they're properly formatted
                        home_odds = odds['moneyline'][0] if len(odds['moneyline']) > 0 else 'N/A'
                        away_odds = odds['moneyline'][1] if len(odds['moneyline']) > 1 else 'N/A'
                        
                        markets.append({
                            'name': 'Moneyline',
                            'selections': [
                                {'name': 'Home', 'odds': str(home_odds).strip()},
                                {'name': 'Away', 'odds': str(away_odds).strip()}
                            ]
                        })

                # Also create a direct odds object for easier access in UI
                formatted_odds = {}
                if odds:
                    # Format odds for direct display
                    if 'spread' in odds and odds['spread'] and len(odds['spread']) >= 2:
                        formatted_odds['spread'] = [
                            str(odds['spread'][0]).strip(),
                            str(odds['spread'][1]).strip()
                        ]
                    if 'total' in odds and odds['total'] and len(odds['total']) >= 2:
                        formatted_odds['total'] = [
                            str(odds['total'][0]).strip(), 
                            str(odds['total'][1]).strip()
                        ]
                    if 'moneyline' in odds and odds['moneyline'] and len(odds['moneyline']) >= 2:
                        formatted_odds['moneyline'] = [
                            str(odds['moneyline'][0]).strip(),
                            str(odds['moneyline'][1]).strip()
                        ]

                transformed_match = {
                    'id': match.get('id') or match.get('game_id') or f"{match.get('sport', 'UNK')}_{hash(str(match))}",
                    'sport': match.get('sport', 'Unknown'),
                    'sport_code': match.get('sport', ''),
                    'league': match.get('league', match.get('date', '')),
                    'teams': {
                        'home': match.get('player1_team1') or match.get('team1', 'TBD'),
                        'away': match.get('player2_team2') or match.get('team2', 'TBD')
                    },
                    'scores': {
                        'home': '0',  # Pregame matches don't have scores
                        'away': '0'
                    },
                    'live_fields': {
                        'is_live': False,  # Pregame matches are not live
                        'status': 'Scheduled',
                        'time': match.get('time', 'TBD'),
                        'date': match.get('date', '')
                    },
                    'date': match.get('date', ''),  # Add date field directly for UI access
                    'time': match.get('time', 'TBD'),  # Add time field directly for UI access
                    'odds': formatted_odds,  # Use formatted odds for better display
                    'raw_odds': match.get('odds', {}),  # Keep raw odds for reference
                    'markets': markets,  # Now includes transformed markets
                    'timestamp': match.get('timestamp', datetime.now().isoformat())
                }
            else:
                # This is live data format - check both 'odds' and 'markets' fields
                live_odds = match.get('odds', {})
                live_markets = match.get('markets', {})
                
                # Normalize live odds format to match pregame format
                formatted_live_odds = {}
                
                # Try to extract from 'markets' field first (newer live format)
                if live_markets and isinstance(live_markets, dict):
                    # Extract moneyline from markets
                    if 'moneyline' in live_markets and live_markets['moneyline']:
                        moneyline_data = live_markets['moneyline']
                        if isinstance(moneyline_data, dict):
                            home_odds = moneyline_data.get('home', {}).get('odds', 'TBD')
                            away_odds = moneyline_data.get('away', {}).get('odds', 'TBD')
                            formatted_live_odds['moneyline'] = [str(home_odds).strip(), str(away_odds).strip()]
                    
                    # Extract spread from markets
                    if 'spread' in live_markets and live_markets['spread']:
                        spread_data = live_markets['spread']
                        if isinstance(spread_data, dict):
                            home_spread = spread_data.get('home', {})
                            away_spread = spread_data.get('away', {})
                            home_line = home_spread.get('line', '')
                            home_odds = home_spread.get('odds', '')
                            away_line = away_spread.get('line', '')
                            away_odds = away_spread.get('odds', '')
                            
                            if home_line and home_odds:
                                formatted_live_odds['spread'] = [
                                    f"{home_line} {home_odds}".strip(),
                                    f"{away_line} {away_odds}".strip()
                                ]
                    
                    # Extract total from markets
                    if 'total' in live_markets and live_markets['total']:
                        total_data = live_markets['total']
                        if isinstance(total_data, dict):
                            over_data = total_data.get('over', {})
                            under_data = total_data.get('under', {})
                            over_line = over_data.get('line', '')
                            over_odds = over_data.get('odds', '')
                            under_line = under_data.get('line', '')
                            under_odds = under_data.get('odds', '')
                            
                            if over_line and over_odds:
                                formatted_live_odds['total'] = [
                                    f"O {over_line} {over_odds}".strip(),
                                    f"U {under_line} {under_odds}".strip()
                                ]
                
                # Fall back to legacy 'odds' field format if markets is empty
                elif live_odds:
                    # Extract moneyline from various possible formats
                    if 'moneyline' in live_odds and live_odds['moneyline']:
                        if isinstance(live_odds['moneyline'], list) and len(live_odds['moneyline']) >= 2:
                            formatted_live_odds['moneyline'] = [
                                str(live_odds['moneyline'][0]).strip(),
                                str(live_odds['moneyline'][1]).strip()
                            ]
                        elif isinstance(live_odds['moneyline'], dict):
                            formatted_live_odds['moneyline'] = [
                                str(live_odds['moneyline'].get('home', 'TBD')).strip(),
                                str(live_odds['moneyline'].get('away', 'TBD')).strip()
                            ]
                    
                    # Extract spread odds
                    if 'spread' in live_odds and live_odds['spread']:
                        if isinstance(live_odds['spread'], list) and len(live_odds['spread']) >= 2:
                            formatted_live_odds['spread'] = [
                                str(live_odds['spread'][0]).strip(),
                                str(live_odds['spread'][1]).strip()
                            ]
                        elif isinstance(live_odds['spread'], dict):
                            formatted_live_odds['spread'] = [
                                str(live_odds['spread'].get('home', 'TBD')).strip(),
                                str(live_odds['spread'].get('away', 'TBD')).strip()
                            ]
                    
                    # Extract total odds
                    if 'total' in live_odds and live_odds['total']:
                        if isinstance(live_odds['total'], list) and len(live_odds['total']) >= 2:
                            formatted_live_odds['total'] = [
                                str(live_odds['total'][0]).strip(),
                                str(live_odds['total'][1]).strip()
                            ]
                        elif isinstance(live_odds['total'], dict):
                            formatted_live_odds['total'] = [
                                str(live_odds['total'].get('over', 'TBD')).strip(),
                                str(live_odds['total'].get('under', 'TBD')).strip()
                            ]
                
                transformed_match = {
                    'id': match.get('id') or match.get('game_id') or f"{match.get('sport_code', 'UNK')}_{hash(str(match.get('teams', {})))}",
                    'sport': match.get('sport', 'Unknown'),
                    'sport_code': match.get('sport_code', match.get('code', '')),
                    'league': match.get('league', match.get('competition', '')),
                    'teams': {
                        'home': match.get('teams', {}).get('home', 'TBD'),
                        'away': match.get('teams', {}).get('away', 'TBD')
                    },
                    'scores': {
                        'home': str(match.get('scores', {}).get('home', '0')),
                        'away': str(match.get('scores', {}).get('away', '0'))
                    },
                    'live_fields': {
                        'is_live': match.get('live_fields', {}).get('is_live', False),
                        'status': match.get('live_fields', {}).get('status', match.get('status', 'Scheduled')),
                        'time': match.get('live_fields', {}).get('time', match.get('time', '')),
                        'date': match.get('live_fields', {}).get('date', match.get('date', ''))
                    },
                    'date': match.get('date', match.get('live_fields', {}).get('date', '')),  # Add date field directly for UI access
                    'time': match.get('time', match.get('live_fields', {}).get('time', '')),  # Add time field directly for UI access
                    'odds': formatted_live_odds,  # Use normalized odds format
                    'raw_odds': {'odds': live_odds, 'markets': live_markets},  # Keep both original sources for reference
                    'markets': match.get('markets', []),
                    'timestamp': match.get('timestamp', datetime.now().isoformat())
                }

            # Validate transformed match before adding with detailed field checking
            missing_fields = []
            
            # Check ID
            if not transformed_match.get('id'):
                missing_fields.append('id')
            
            # Check teams with fallbacks
            home_team = transformed_match.get('teams', {}).get('home')
            away_team = transformed_match.get('teams', {}).get('away')
            
            if not home_team or home_team == 'TBD':
                # Try alternative team fields
                if 'player1_team1' in match:
                    transformed_match['teams']['home'] = match['player1_team1']
                elif 'team1' in match:
                    transformed_match['teams']['home'] = match['team1']
                else:
                    missing_fields.append('teams.home')
                    
            if not away_team or away_team == 'TBD':
                # Try alternative team fields
                if 'player2_team2' in match:
                    transformed_match['teams']['away'] = match['player2_team2']
                elif 'team2' in match:
                    transformed_match['teams']['away'] = match['team2']
                else:
                    missing_fields.append('teams.away')
            
            if not missing_fields:
                transformed.append(transformed_match)
            else:
                logger.warning(f"Skipping invalid transformed match: missing required fields: {missing_fields}")
                logger.debug(f"Match data was: {match}")
                
        except Exception as e:
            logger.error(f"Error transforming match at index {i}: {e}")
            logger.error(f"Match data: {match}")
            continue

    logger.info(f"Successfully transformed {len(transformed)}/{len(matches)} matches")
    return transformed

@app.get("/", response_class=FileResponse)
async def root():
    """Serve the dashboard HTML"""
    html_path = Path("index.html")
    if html_path.exists():
        return FileResponse(html_path)
    else:
        # Return info if HTML not found
        return {
            "message": "Live Betting Dashboard API",
            "version": "1.0.0",
            "note": "Place index.html in the same directory to view the dashboard",
            "endpoints": {
                "matches": "/api/live-matches",
                "websocket": "/ws",
                "health": "/health",
                "docs": "/docs"
            }
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connections": len(manager.active_connections),
        "cached_matches": len(data_cache['matches'])
    }

@app.get("/api/live-matches")
async def get_live_matches():
    """Get current live matches"""
    data = load_current_data()
    
    # Transform matches for frontend
    transformed_matches = transform_match_data(data.get('matches', []))
    
    return {
        'timestamp': data.get('timestamp', datetime.now().isoformat()),
        'matches': transformed_matches,
        'summary': data.get('summary', {
            'total_matches': len(transformed_matches),
            'live_matches': sum(1 for m in transformed_matches if m['live_fields']['is_live']),
            'sports_processed': len(set(m['sport'] for m in transformed_matches))
        })
    }

@app.get("/api/sports")
async def get_available_sports():
    """Get list of available sports"""
    data = load_current_data()
    matches = data.get('matches', [])
    
    sports = {}
    for match in matches:
        sport = match.get('sport', 'Unknown')
        sport_code = match.get('sport_code', match.get('code', ''))
        
        if sport not in sports:
            sports[sport] = {
                'name': sport,
                'code': sport_code,
                'count': 0,
                'live_count': 0
            }
        
        sports[sport]['count'] += 1
        if match.get('live_fields', {}).get('is_live'):
            sports[sport]['live_count'] += 1
    
    return {
        'sports': list(sports.values()),
        'total': len(sports)
    }

@app.get("/api/match/{match_id}")
async def get_match_detail(match_id: str):
    """Get detailed information for a specific match"""
    data = load_current_data()
    matches = data.get('matches', [])
    
    for match in matches:
        if str(match.get('id', '')) == match_id:
            return transform_match_data([match])[0]
    
    return {"error": "Match not found"}, 404

@app.get("/api/historical-matches")
async def get_historical_matches():
    """Get recently removed/completed matches from history"""
    try:
        historical_matches = []
        
        # Load pregame history if it exists
        if PREGAME_HISTORY_FILE.exists():
            with open(PREGAME_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                
                # Handle different history formats
                if isinstance(history_data, list):
                    recent_games = history_data[-20:]  # Last 20 entries
                elif isinstance(history_data, dict):
                    if 'removed_games' in history_data:
                        recent_games = history_data['removed_games'][-20:]
                    elif 'games' in history_data:
                        recent_games = history_data['games'][-20:]
                    else:
                        recent_games = []
                else:
                    recent_games = []
                
                # Convert to match format
                for game in recent_games:
                    historical_matches.append({
                        'id': game.get('game_id', f"hist_{len(historical_matches)}"),
                        'sport': game.get('sport', 'Unknown'),
                        'teams': {
                            'home': game.get('team1', 'Unknown'),
                            'away': game.get('team2', 'Unknown')
                        },
                        'time': game.get('time', ''),
                        'date': game.get('date', ''),
                        'status': 'Removed',
                        'removal_time': game.get('removal_time', game.get('timestamp', ''))
                    })
        
        return {
            'historical_matches': historical_matches,
            'count': len(historical_matches),
            'last_update': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error loading historical matches: {e}")
        return {
            'historical_matches': [],
            'count': 0,
            'error': str(e)
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial data
        initial_data = load_current_data()
        await websocket.send_json({
            'type': 'initial',
            'data': {
                'timestamp': initial_data.get('timestamp'),
                'matches': transform_match_data(initial_data.get('matches', [])),
                'summary': initial_data.get('summary', {})
            }
        })
        
        # Keep connection alive and send updates
        while True:
            try:
                # Wait for ping from client or timeout
                await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
            except asyncio.TimeoutError:
                # Send updated data every second
                current_data = load_current_data()
                
                # Only send if data has changed
                if current_data.get('timestamp') != data_cache.get('timestamp'):
                    data_cache['timestamp'] = current_data.get('timestamp')
                    data_cache['matches'] = transform_match_data(current_data.get('matches', []))
                    data_cache['summary'] = current_data.get('summary', {})
                    
                    await websocket.send_json({
                        'type': 'update',
                        'data': {
                            'timestamp': data_cache['timestamp'],
                            'matches': data_cache['matches'],
                            'summary': data_cache['summary']
                        }
                    })
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("LIVE BETTING DASHBOARD API SERVER")
    print("=" * 60)
    print("Server starting on http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws")
    print("API docs: http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )
