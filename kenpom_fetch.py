"""
Fetch Kenpom efficiency data for teams playing today
Requires: daily_matchups.csv (from fetch_daily_matchups.py)
Outputs: kenpom_daily_data.csv
"""

import requests
import pandas as pd
from team_mapping import get_canonical_name
import os
from dotenv import load_dotenv

load_dotenv() 

SPAM = False 

# Kenpom API Configuration
API_KEY = os.getenv('KENPOM_API_KEY')
BASE_URL = 'https://kenpom.com/api.php'
CURRENT_SEASON = 2026


def fetch_kenpom_data_for_today():
    """Fetch Kenpom data for teams playing today"""
    
    # Check if daily matchups exists
    if not os.path.exists('daily_matchups.csv'):
        print("ERROR: daily_matchups.csv not found!")
        print("Run fetch_daily_matchups.py first")
        return None
    
    # Get teams playing today
    matchups_df = pd.read_csv('daily_matchups.csv')
    teams_playing = set(matchups_df['home_team'].tolist() + matchups_df['away_team'].tolist())
    
    print("="*60)
    print("FETCHING KENPOM DATA")
    print("="*60)
    
    try:
        # Fetch ratings
        if SPAM:
            print(f"Fetching ratings for {CURRENT_SEASON} season...")
        params = {'endpoint': 'ratings', 'y': CURRENT_SEASON}
        headers = {'Authorization': f'Bearer {API_KEY}'}
        response = requests.get(BASE_URL, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data)
        
        # Select and rename columns
        df = df[['TeamName', 'AdjOE', 'AdjDE', 'AdjTempo', 'SOS']].copy()
        df.columns = ['Team', 'AdjO', 'AdjD', 'AdjT', 'Overall_SOS']
        
        if SPAM:
            print(f"✓ Fetched {len(df)} teams from Kenpom")
        
        # Normalize team names
        for idx, row in df.iterrows():
            original = row['Team']
            normalized = get_canonical_name(original)
            if normalized != original:
                df.at[idx, 'Team'] = normalized
        
        # Filter to only teams playing today
        teams_found = set(df['Team'].tolist())
        teams_missing = teams_playing - teams_found
        
        if teams_missing:
            print(f"⚠ {len(teams_missing)} teams not found in Kenpom:")
            for team in sorted(teams_missing):
                print(f"  - {team}")
        
        df = df[df['Team'].isin(teams_playing)]
        df = df.sort_values('Team').reset_index(drop=True)
        
        # Load and merge HCA data
    
        hca_df = pd.read_csv('kenpomHCA.csv')
        df = df.merge(hca_df, on='Team', how='left')
       
        
        
        print(f"✓ {len(df)}/{len(teams_playing)} teams → kenpom_daily_data.csv")
        print("="*60)
        
        return df
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def main():
    df = fetch_kenpom_data_for_today()
    
    if df is None:
        print("\nFailed to fetch Kenpom data")
        return
    
    # Save to CSV
    output_file = 'kenpom_data.csv'
    df.to_csv(output_file, index=False)


if __name__ == "__main__":
    main()