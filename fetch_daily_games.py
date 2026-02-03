"""
Fetch daily college basketball matchups from ESPN API
No API key required
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
from team_mapping import get_canonical_name


SPAM = False  

ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"

def fetch_daily_matchups(date=20260204):
    """
    Fetch all college basketball games for a specific date
    
    Args:
        date: Date string in format 'YYYYMMDD' (e.g., '20260117')
              If None, uses today's date
    
    Returns:
        DataFrame with columns: home_team, away_team, game_time, venue, game_status
    """
    
    # Format date for ESPN API
    if date is None:
        date = datetime.now().strftime('%Y%m%d')
    
    try:
        if SPAM:
            print(f"Fetching matchups for {date}...")
        
        params = {
            'dates': date,
            'limit': 500,
            'groups': '50'  # Division I only
        }
        
        response = requests.get(ESPN_SCOREBOARD_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        games = []
        
        # Parse the events (games)
        events = data.get('events', [])
        
        if not events:
            print(f"No games found for {date}")
            return pd.DataFrame()
        
        if SPAM:
            print(f"Found {len(events)} games from ESPN")
        
        # Set up timezone conversion (UTC to Eastern)
        utc = pytz.UTC
        eastern = pytz.timezone('US/Eastern')
        
        for event in events:
            try:
                # Get basic game info
                game_id = event.get('id')
                game_date = event.get('date')
                status = event.get('status', {}).get('type', {}).get('description', 'Unknown')
                
                # Get venue info
                competitions = event.get('competitions', [])
                if not competitions:
                    continue
                
                competition = competitions[0]
                venue = competition.get('venue', {}).get('fullName', 'Unknown')
                neutral_site = competition.get('neutralSite', False)
                
                # Get teams
                competitors = competition.get('competitors', [])
                
                if len(competitors) != 2:
                    continue
                
                # ESPN lists teams as 'home' and 'away'
                home_team = None
                away_team = None
                
                for competitor in competitors:
                    home_away = competitor.get('homeAway')
                    team_name = competitor.get('team', {}).get('displayName')
                    
                    if home_away == 'home':
                        home_team = team_name
                    else:
                        away_team = team_name
                
                if not home_team or not away_team:
                    continue
                
                # Convert UTC time to Eastern time
                game_time_utc = datetime.strptime(game_date, '%Y-%m-%dT%H:%MZ')
                game_time_utc = utc.localize(game_time_utc)
                game_time_eastern = game_time_utc.astimezone(eastern)
                game_time_str = game_time_eastern.strftime('%Y-%m-%d %I:%M %p')
                
                game_info = {
                    'game_id': game_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'game_time': game_time_str,
                    'venue': venue,
                    'neutral_site': neutral_site,
                    'game_status': status
                }
                
                games.append(game_info)
                
            except Exception as e:
                print(f"Error parsing game: {e}")
                continue
        
        if not games:
            print("No valid games found")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(games)
        
        # Normalize team names
        df = normalize_team_names(df)
        
        if SPAM:
            print(f"✓ Fetched {len(df)} games")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching matchups: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def normalize_team_names(df):
    """Normalize ESPN team names to match canonical names"""
    
    unmapped_teams = []
    
    for idx, row in df.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        
        normalized_home = get_canonical_name(home_team)
        normalized_away = get_canonical_name(away_team)
        
        # Check if mapping succeeded
        if normalized_home:
            df.at[idx, 'home_team'] = normalized_home
        else:
            if home_team not in unmapped_teams:
                unmapped_teams.append(home_team)
            df.at[idx, 'home_team'] = home_team
        
        if normalized_away:
            df.at[idx, 'away_team'] = normalized_away
        else:
            if away_team not in unmapped_teams:
                unmapped_teams.append(away_team)
            df.at[idx, 'away_team'] = away_team
    
    # Warn about unmapped teams
    if unmapped_teams:
        print("⚠ Unmapped teams (add to team_mapping.py):")
        for team in sorted(set(unmapped_teams)):
            print(f"  - {team}")
    
    return df


def get_upcoming_games(days_ahead=1):
    """
    Get games for the next N days
    
    Args:
        days_ahead: Number of days ahead to fetch (default 1 = tomorrow)
    
    Returns:
        DataFrame with all games for specified dates
    """
    all_games = []
    
    for i in range(days_ahead):
        target_date = datetime.now() + timedelta(days=i+1)
        date_str = target_date.strftime('%Y%m%d')
        
        print(f"\nFetching games for {target_date.strftime('%A, %B %d, %Y')}...")
        df = fetch_daily_matchups(date_str)
        
        if not df.empty:
            all_games.append(df)
    
    if all_games:
        return pd.concat(all_games, ignore_index=True)
    else:
        return pd.DataFrame()


def main():
    """Fetch and save daily matchups"""
    import sys
    
    print("="*60)
    print("FETCHING DAILY MATCHUPS")
    print("="*60)
    
    # Check if date argument provided
    if len(sys.argv) > 1:
        date_str = sys.argv[1]  # Format: YYYYMMDD
        print(f"Date: {date_str}")
        df = fetch_daily_matchups(date_str)
    else:
        # Default to today
        print("Date: Today")
        df = fetch_daily_matchups()
    
    if df.empty:
        print("No games found")
        return
    
    # Save to CSV
    output_file = 'daily_matchups.csv'
    df.to_csv(output_file, index=False)
    print(f"✓ {len(df)} games → {output_file}")
    print("="*60)


if __name__ == "__main__":
    main()