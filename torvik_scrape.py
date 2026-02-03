"""
Bart Torvik Data Fetcher
Fetches efficiency data for teams playing today
Requires: daily_matchups.csv (from fetch_daily_matchups.py)
Outputs: torvik_data.csv
"""

import pandas as pd
import requests
from datetime import datetime
from team_mapping import get_canonical_name
import os


SPAM = False  

def fetch_torvik_data_for_today(year=2026):
    """Fetch Torvik efficiency data for teams playing today"""
    
    # Check if daily matchups exists
    if not os.path.exists('daily_matchups.csv'):
        print("ERROR: daily_matchups.csv not found!")
        print("Run fetch_daily_matchups.py first")
        return None
    
    # Get teams playing today
    matchups_df = pd.read_csv('daily_matchups.csv')
    teams_playing = set(matchups_df['home_team'].tolist() + matchups_df['away_team'].tolist())
    
    print("="*60)
    print("FETCHING TORVIK DATA")
    print("="*60)
    
    url = f"https://barttorvik.com/teamslicejson.php?year={year}&json=1"
    
    try:
        if SPAM:
            print(f"Fetching Torvik data for {year} season...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        raw_df = pd.DataFrame(data)
        
        # Extract columns (Column 26 is AdjT)
        df = pd.DataFrame({
            'Team': raw_df[0],
            'AdjO': pd.to_numeric(raw_df[1], errors='coerce'),
            'AdjD': pd.to_numeric(raw_df[2], errors='coerce'),
            'AdjT': pd.to_numeric(raw_df[26], errors='coerce')
        })
        
        df = df.dropna()
        
        if SPAM:
            print(f"✓ Fetched {len(df)} teams from Torvik")
        
        # Normalize team names
        for idx, row in df.iterrows():
            original = row['Team']
            normalized = get_canonical_name(original)
            if normalized and normalized != original:
                df.at[idx, 'Team'] = normalized
        
        # Filter to teams playing today
        teams_found = set(df['Team'].tolist())
        teams_missing = teams_playing - teams_found
        
        if teams_missing:
            print(f"⚠ {len(teams_missing)} teams not found in Torvik:")
            for team in sorted(teams_missing):
                print(f"  - {team}")
        
        df = df[df['Team'].isin(teams_playing)]
        df = df.sort_values('Team').reset_index(drop=True)
        
        # Load and merge HCA data
      
        hca_df = pd.read_csv('kenpomHCA.csv')
        df = df.merge(hca_df, on='Team', how='left')
        df['HCA'] = df['HCA'].fillna(3.0)
       
        
        print(f"✓ {len(df)}/{len(teams_playing)} teams → torvik_data.csv")
        print("="*60)
        
        return df
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def main():
    df = fetch_torvik_data_for_today(year=2026)
    
    if df is None:
        print("\nFailed to fetch Torvik data")
        return
    
    # Save to CSV
    output_file = 'torvik_data.csv'
    df.to_csv(output_file, index=False)


if __name__ == "__main__":
    main()