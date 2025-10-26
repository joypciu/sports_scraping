# 🏈 Adding New Sports Guide

This guide provides step-by-step instructions for adding new sports to both the **pregame** and **live** scraping systems.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Pregame Sports Integration](#pregame-sports-integration)
3. [Live Sports Integration](#live-sports-integration)
4. [Testing New Sports](#testing-new-sports)
5. [Common Patterns & Examples](#common-patterns--examples)
6. [Troubleshooting](#troubleshooting)

## 🎯 Overview

The bet365 scraping system supports both **pregame** (upcoming matches) and **live** (in-play) betting data. Adding a new sport requires modifications to different files depending on the type of data you want to scrape.

### System Components

```
🏈 NEW SPORT INTEGRATION
├── Pregame System
│   ├── pregame_new.py (main scraper)
│   └── realtime_monitor.py (monitoring)
│
└── Live System
    ├── concurrency_live_bet365.py (live scraper)
    ├── dashboard_api.py (API server)
    └── index.html (web dashboard)
```

## 🔮 Pregame Sports Integration

### Step 1: Analyze the Sport on bet365

Before coding, manually examine the sport on bet365.ca:

1. **Navigate to bet365.ca**
2. **Find the sport tab** (e.g., "Cricket", "Rugby", "Volleyball")
3. **Note the tab name** and any variations
4. **Examine the betting markets** (moneyline, spread, totals, etc.)
5. **Check the HTML structure** using browser dev tools

### Step 2: Update Sport Detection in `pregame_new.py`

**Location**: `pregame_new.py` → `detect_sports_and_tabs()` method

```python
# Add your sport to the sport detection logic
async def detect_sports_and_tabs(self):
    # ... existing code ...
    
    # Add new sport detection
    elif any(keyword in tab_text.lower() for keyword in ['cricket', 'cricket matches']):
        sport_name = 'Cricket'
        self.sport_tabs.append((sport_name, tab_text.strip()))
        logger.info(f"Detected sport tab: {sport_name} -> '{tab_text.strip()}'")
    
    elif any(keyword in tab_text.lower() for keyword in ['rugby', 'rugby union', 'rugby league']):
        sport_name = 'Rugby'
        self.sport_tabs.append((sport_name, tab_text.strip()))
        logger.info(f"Detected sport tab: {sport_name} -> '{tab_text.strip()}'")
```

### Step 3: Create Sport-Specific Extraction Method

**Location**: `pregame_new.py` → Add new method

```python
async def extract_cricket_games(self, sport: str) -> List[Dict[str, Any]]:
    """
    Extract cricket matches with sport-specific logic
    """
    games = []
    
    try:
        # Wait for content to load
        await self.page.wait_for_load_state('networkidle', timeout=10000)
        
        # Find fixtures grid (adjust selector based on inspection)
        fixtures_grid = await self.page.query_selector('div[class*="SportTabContent"], div[class*="PreMatchTabContent"]')
        if not fixtures_grid:
            logger.warning(f"{sport}: No fixtures grid found")
            return games
            
        # Find all fixture elements
        fixtures = await fixtures_grid.query_selector_all('div[class*="FixtureRow"], div[class*="Fixture"]')
        logger.info(f"{sport}: Found {len(fixtures)} potential fixtures")
        
        for i, fixture in enumerate(fixtures):
            try:
                # Extract teams (adjust selectors based on sport)
                teams = await fixture.query_selector_all('div[class*="Team"], span[class*="Team"]')
                if len(teams) < 2:
                    continue
                    
                team1 = (await teams[0].inner_text()).strip()
                team2 = (await teams[1].inner_text()).strip()
                
                # Skip if teams are empty
                if not team1 or not team2:
                    continue
                
                # Extract match time/date
                time_element = await fixture.query_selector('div[class*="Time"], span[class*="Time"]')
                time_text = await time_element.inner_text() if time_element else ""
                
                date_element = await fixture.query_selector('div[class*="Date"], span[class*="Date"]')
                date_text = await date_element.inner_text() if date_element else ""
                
                # Extract odds (cricket-specific markets)
                odds_elements = await fixture.query_selector_all('span[class*="Odds"], div[class*="Price"]')
                odds_values = []
                for odds_el in odds_elements:
                    odds_text = await odds_el.inner_text()
                    if odds_text and odds_text not in ['', '-']:
                        odds_values.append(odds_text.strip())
                
                # Categorize cricket odds
                cricket_odds = self.categorize_cricket_odds(odds_values)
                
                # Create game object
                game = {
                    'sport': sport,
                    'team1': team1,
                    'team2': team2,
                    'date': date_text,
                    'time': time_text,
                    'odds': cricket_odds,
                    'fixture_id': f"{sport}_{i}_{hash(team1 + team2)}",
                    'game_id': self.generate_game_id(team1, team2, date_text, time_text),
                    'confidence_score': 100.0
                }
                
                games.append(game)
                
            except Exception as e:
                logger.warning(f"{sport}: Error processing fixture {i}: {e}")
                continue
                
        logger.info(f"{sport}: Extracted {len(games)} games")
        return games
        
    except Exception as e:
        logger.error(f"{sport}: Extraction failed: {e}")
        return games

def categorize_cricket_odds(self, odds_values: List[str]) -> Dict[str, List[str]]:
    """
    Categorize cricket odds into appropriate markets
    Cricket typically has: Match Winner, Handicap, Total Runs
    """
    categorized = {
        'match_winner': [],  # Team 1 Win, Team 2 Win
        'handicap': [],      # Handicap betting
        'total_runs': [],    # Over/Under total runs
        'other': []          # Other cricket-specific markets
    }
    
    # Cricket odds categorization logic
    for i, odds in enumerate(odds_values):
        if i < 2:  # First two odds typically match winner
            categorized['match_winner'].append(odds)
        elif 'handicap' in odds.lower() or any(x in odds for x in ['+', '-']):
            categorized['handicap'].append(odds)
        elif any(word in odds.lower() for word in ['over', 'under', 'total']):
            categorized['total_runs'].append(odds)
        else:
            categorized['other'].append(odds)
    
    return categorized
```

### Step 4: Add Sport to Main Extraction Loop

**Location**: `pregame_new.py` → `extract_single_sport()` method

```python
async def extract_single_sport(self, sport: str, tab_name: str) -> Dict[str, Any]:
    # ... existing code ...
    
    try:
        # Add your sport to the extraction logic
        if sport.upper() == 'CRICKET':
            games = await self.extract_cricket_games(sport)
        elif sport.upper() == 'RUGBY':
            games = await self.extract_rugby_games(sport)
        # ... existing sports ...
        else:
            # Generic extraction as fallback
            games = await self.extract_generic_sport_games(sport)
    
    # ... rest of method ...
```

### Step 5: Update Real-time Monitor (Optional)

**Location**: `realtime_monitor.py` → Update sport lists

```python
# Add new sport to default sports list
sports_to_monitor = {'NBA', 'NHL', 'NFL', 'MLB', 'NCAAF', 'Tennis', 'UFC', 'CFL', 'PGA', 'Cricket', 'Rugby'}
```

## 🔴 Live Sports Integration

### Step 1: Update Live Scraper Navigation

**Location**: `concurrency_live_bet365.py` → `get_sport_navigation_info()` method

```python
def get_sport_navigation_info(self):
    """Sport-specific navigation patterns for live betting"""
    return {
        # ... existing sports ...
        'Cricket': {
            'tab_selectors': [
                'a[href*="cricket"]',
                'a[class*="Cricket"]',
                'div[data-sport="cricket"]'
            ],
            'content_selectors': [
                'div[class*="CricketContent"]',
                'div[class*="LiveCricket"]'
            ],
            'wait_time': 3000
        },
        'Rugby': {
            'tab_selectors': [
                'a[href*="rugby"]', 
                'a[class*="Rugby"]',
                'div[data-sport="rugby"]'
            ],
            'content_selectors': [
                'div[class*="RugbyContent"]',
                'div[class*="LiveRugby"]'
            ],
            'wait_time': 3000
        }
    }
```

### Step 2: Add Live Match Extraction Logic

**Location**: `concurrency_live_bet365.py` → Add new method

```python
async def extract_live_cricket_matches(self, page) -> List[Dict]:
    """Extract live cricket matches"""
    matches = []
    
    try:
        # Wait for live content
        await page.wait_for_selector('div[class*="LiveEvent"], div[class*="InPlay"]', timeout=10000)
        
        # Find live cricket matches
        live_matches = await page.query_selector_all('div[class*="LiveEvent"], div[class*="InPlayEvent"]')
        
        for match_element in live_matches:
            try:
                # Extract teams
                team_elements = await match_element.query_selector_all('span[class*="Team"], div[class*="Participant"]')
                if len(team_elements) < 2:
                    continue
                
                home_team = await team_elements[0].inner_text()
                away_team = await team_elements[1].inner_text()
                
                # Extract live score (cricket specific)
                score_element = await match_element.query_selector('div[class*="Score"], span[class*="Score"]')
                score_text = await score_element.inner_text() if score_element else "0-0"
                
                # Extract live status (Innings, Over, etc.)
                status_element = await match_element.query_selector('div[class*="Status"], span[class*="InPlay"]')
                status = await status_element.inner_text() if status_element else "Live"
                
                # Extract live odds
                odds_elements = await match_element.query_selector_all('span[class*="Odds"], div[class*="Price"]')
                live_odds = {}
                
                for i, odds_el in enumerate(odds_elements):
                    odds_value = await odds_el.inner_text()
                    if i == 0:
                        live_odds['home'] = odds_value
                    elif i == 1:
                        live_odds['away'] = odds_value
                    # Add more cricket-specific live betting markets
                
                match_data = {
                    'id': f"live_cricket_{hash(home_team + away_team)}",
                    'sport': 'Cricket',
                    'sport_code': 'CRI',
                    'teams': {
                        'home': home_team.strip(),
                        'away': away_team.strip()
                    },
                    'scores': self.parse_cricket_score(score_text),
                    'live_fields': {
                        'is_live': True,
                        'status': status,
                        'time': status  # In cricket, status often shows over/innings
                    },
                    'odds': live_odds,
                    'timestamp': datetime.now().isoformat()
                }
                
                matches.append(match_data)
                
            except Exception as e:
                logger.warning(f"Error extracting cricket match: {e}")
                continue
                
        logger.info(f"Extracted {len(matches)} live cricket matches")
        return matches
        
    except Exception as e:
        logger.error(f"Cricket live extraction failed: {e}")
        return matches

def parse_cricket_score(self, score_text: str) -> Dict[str, str]:
    """Parse cricket score format (e.g., '150/3 (25.0 ov)')"""
    try:
        # Cricket scores are complex, this is a basic parser
        if '/' in score_text:
            parts = score_text.split('/')
            team1_score = parts[0].strip()
            team2_info = parts[1].strip() if len(parts) > 1 else "0"
            
            return {
                'home': team1_score,
                'away': team2_info.split('(')[0].strip()  # Remove over info
            }
        else:
            return {'home': '0', 'away': '0'}
    except:
        return {'home': '0', 'away': '0'}
```

### Step 3: Update Sport List in Live Scraper

**Location**: `concurrency_live_bet365.py` → `get_supported_sports()` method

```python
def get_supported_sports(self):
    """List of supported sports for live betting"""
    return {
        'Soccer': 'SOC',
        'Basketball': 'BAS', 
        'Tennis': 'TEN',
        'American Football': 'NFL',
        'Ice Hockey': 'ICE',
        'Cricket': 'CRI',    # Add new sport
        'Rugby': 'RUG',      # Add new sport
        # ... other sports
    }
```

### Step 4: Update Dashboard API

**Location**: `dashboard_api.py` → Update sport handling in `transform_match_data()`

```python
# The dashboard API should automatically handle new sports if they follow
# the standard data format. No changes needed unless special handling required.
```

### Step 5: Update Web Dashboard (Optional)

**Location**: `index.html` → Add sport-specific styling or icons

```html
<!-- Add cricket/rugby specific icons or styling -->
<style>
.sport-cricket {
    background-color: #1f4e3d;
    color: white;
}

.sport-rugby {
    background-color: #8b0000;
    color: white;
}
</style>
```

## 🧪 Testing New Sports

### Step 1: Test Pregame Scraping

```bash
# Test single sport extraction
cd "C:\Users\User\Desktop\thesis\work related task\bet365\bet365 demo"
P:/Mamba/Scripts/conda.exe run -p "C:\Users\User\Desktop\thesis\data\joy" --no-capture-output python pregame_new.py --headless

# Check output
cat outputs/current_pregame_data.json | grep -A 10 "Cricket"
```

### Step 2: Test Live Scraping

```bash
# Test live scraping with new sport
python concurrency_live_bet365.py --mode extract

# Check live data
cat bet365_live_current.json | grep -A 10 "Cricket"
```

### Step 3: Test Dashboard Integration

```bash
# Start dashboard
python dashboard_api.py

# Test API endpoint
curl http://localhost:8000/api/live-matches | jq '.matches[] | select(.sport=="Cricket")'

# Check web dashboard at http://localhost:8000
```

### Step 4: Validation Checklist

- [ ] **Sport Detection**: Sport tab is found and clicked
- [ ] **Data Extraction**: Teams and odds are extracted correctly
- [ ] **Data Format**: Output follows expected JSON structure
- [ ] **Error Handling**: Graceful failure if sport not available
- [ ] **Integration**: Works with dashboard and real-time monitor
- [ ] **Performance**: No significant slowdown to overall scraping

## 📚 Common Patterns & Examples

### Pattern 1: Soccer/Football-style Sports

```python
# For sports with Home/Draw/Away betting (1X2)
def categorize_soccer_odds(self, odds_values: List[str]) -> Dict[str, List[str]]:
    return {
        'match_result': odds_values[:3] if len(odds_values) >= 3 else odds_values,  # 1X2
        'over_under': [o for o in odds_values if 'over' in o.lower() or 'under' in o.lower()],
        'handicap': [o for o in odds_values if '+' in o or '-' in o],
        'other': []
    }
```

### Pattern 2: American Sports-style

```python
# For sports with Spread/Total/Moneyline
def categorize_american_odds(self, odds_values: List[str]) -> Dict[str, List[str]]:
    return {
        'spread': odds_values[:2] if len(odds_values) >= 2 else [],
        'total': odds_values[2:4] if len(odds_values) >= 4 else [],
        'moneyline': odds_values[4:6] if len(odds_values) >= 6 else [],
        'other': odds_values[6:] if len(odds_values) > 6 else []
    }
```

### Pattern 3: Individual Sports (Tennis, Golf, etc.)

```python
# For head-to-head individual sports
def categorize_individual_odds(self, odds_values: List[str]) -> Dict[str, List[str]]:
    return {
        'winner': odds_values[:2] if len(odds_values) >= 2 else odds_values,
        'handicap': [o for o in odds_values[2:] if '+' in o or '-' in o],
        'totals': [o for o in odds_values[2:] if 'over' in o.lower() or 'under' in o.lower()],
        'specials': []
    }
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue 1: Sport Tab Not Found
```python
# Problem: Tab detection fails
# Solution: Add more tab selector variations
tab_selectors = [
    'a[href*="cricket"]',           # URL-based
    'a[data-sport="cricket"]',      # Data attribute
    'div[class*="Cricket"]',        # Class-based
    'span:contains("Cricket")',     # Text-based
    'li[id*="cricket"]'            # ID-based
]
```

#### Issue 2: No Games Extracted
```python
# Problem: Fixture elements not found
# Solution: Inspect HTML and update selectors
fixtures = await self.page.query_selector_all([
    'div[class*="FixtureRow"]',
    'div[class*="EventRow"]', 
    'div[class*="MatchRow"]',
    'tr[class*="Fixture"]',         # Table rows
    'article[class*="Event"]'       # Article elements
])
```

#### Issue 3: Incorrect Odds Categorization
```python
# Problem: Odds in wrong categories  
# Solution: Debug odds extraction
logger.info(f"Raw odds values: {odds_values}")
for i, odds in enumerate(odds_values):
    logger.info(f"Odds {i}: '{odds}' - Type: {type(odds)}")
```

#### Issue 4: Live Matches Not Found
```python
# Problem: Live content selectors incorrect
# Solution: Use multiple selector strategies
live_selectors = [
    'div[class*="Live"]',
    'div[class*="InPlay"]',
    'div[data-live="true"]',
    'div[class*="Running"]'
]
```

### Debugging Tools

#### Enable Debug Logging
```python
# In your extraction method
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add debug prints
logger.debug(f"Found {len(fixtures)} fixtures")
logger.debug(f"Teams extracted: {team1} vs {team2}")
logger.debug(f"Odds values: {odds_values}")
```

#### Browser Debug Mode
```python
# Run with visible browser for debugging
scraper = EnhancedIntelligentScraper(headless=False, load_wait=10000)
```

#### HTML Inspection
```python
# Save page HTML for inspection
html_content = await self.page.content()
with open(f'debug_{sport}_page.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
```

## 📝 Quick Reference Template

### New Sport Integration Checklist

```python
# 1. ADD SPORT DETECTION
elif any(keyword in tab_text.lower() for keyword in ['YOUR_SPORT', 'variations']):
    sport_name = 'YourSport'
    self.sport_tabs.append((sport_name, tab_text.strip()))

# 2. CREATE EXTRACTION METHOD
async def extract_your_sport_games(self, sport: str) -> List[Dict[str, Any]]:
    # Implementation here
    pass

# 3. ADD TO MAIN EXTRACTION
if sport.upper() == 'YOURSPORT':
    games = await self.extract_your_sport_games(sport)

# 4. ADD ODDS CATEGORIZATION
def categorize_your_sport_odds(self, odds_values: List[str]) -> Dict[str, List[str]]:
    # Sport-specific odds categorization
    return {...}

# 5. TEST THOROUGHLY
# Run scraper, check output, validate data
```

---

**💡 Pro Tips**:
1. **Start with pregame** - it's easier to implement and debug
2. **Use browser dev tools** to inspect bet365's HTML structure
3. **Test with headless=False** first to see what's happening
4. **Add comprehensive logging** for debugging
5. **Follow existing patterns** from similar sports (NBA, NFL, etc.)
6. **Test edge cases** like games with missing data or unusual formats

---

This guide should help you successfully integrate any new sport into the bet365 scraping system. Each sport may have unique challenges, but following these patterns will handle most scenarios.