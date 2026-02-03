"""
Uses Torvik efficiency ratings to predict game scores

"""

import pandas as pd

SPAM = False 

# D1 Averages (from Torvik)
D1_AVERAGES = {
    'tempo': 67.6,  
    'def_efficiency': 110.3,  
}

def get_team_data(df: pd.DataFrame, team: str):
    """Get team's data from DataFrame"""
    team_data = df[df['Team'] == team]
    if len(team_data) == 0:
        return None
    return team_data.iloc[0]


def calculate_tempo(torvik_data: pd.DataFrame, home_team: str, away_team: str) -> float:
    """Calculate expected tempo for the game"""
    home_data = get_team_data(torvik_data, home_team)
    away_data = get_team_data(torvik_data, away_team)
    
    tempo = (home_data['AdjT'] * away_data['AdjT']) / D1_AVERAGES['tempo']
    return tempo


def calculate_home_score(torvik_data: pd.DataFrame, home_team: str, away_team: str, neutral_site: bool) -> float:
    """Calculate predicted home team score"""
    home_data = get_team_data(torvik_data, home_team)
    away_data = get_team_data(torvik_data, away_team)
    
    # Get tempo
    tempo = calculate_tempo(torvik_data, home_team, away_team)
    
    # Calculate expected points
    score = (home_data['AdjO'] * away_data['AdjD'] * tempo) / (D1_AVERAGES['def_efficiency'] * 100)
    
    # Add team-specific HCA if not neutral site
    if not neutral_site:
        # Check if HCA column exists, otherwise use default 3.0
        hca = float(home_data['HCA']) if 'HCA' in home_data.index else 3.0
        score += hca
    
    return score


def calculate_away_score(torvik_data: pd.DataFrame, away_team: str, home_team: str) -> float:
    """Calculate predicted away team score"""
    home_data = get_team_data(torvik_data, home_team)
    away_data = get_team_data(torvik_data, away_team)
    
    # Get tempo
    tempo = calculate_tempo(torvik_data, home_team, away_team)
    
    # Calculate expected points (no HCA for away team)
    score = (away_data['AdjO'] * home_data['AdjD'] * tempo) / (D1_AVERAGES['def_efficiency'] * 100)
    
    return score


def predict_games():
    """Generate predictions for all games today"""
    
    print("="*60)
    print("TORVIK GAME PREDICTIONS")
    print("="*60)
    
    # Load data
    try:
        torvik_data = pd.read_csv('torvik_data.csv')
        matchups_df = pd.read_csv('daily_matchups.csv')
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Run fetch_torvik_data.py and fetch_daily_matchups.py first")
        return None
    
    print(f"Processing {len(matchups_df)} games...")
    
    predictions = []
    skipped = []
    
    for _, game in matchups_df.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        neutral_site = game.get('neutral_site', False)
        game_time = game['game_time']
        
        # Check if both teams have data
        home_data = get_team_data(torvik_data, home_team)
        away_data = get_team_data(torvik_data, away_team)
        
        if home_data is None or away_data is None:
            skipped.append({'home': home_team, 'away': away_team})
            if SPAM:
                print(f"⚠ Skipping: {away_team} @ {home_team} (missing data)")
            continue
        
        try:
            # Calculate scores using separate functions
            home_score = calculate_home_score(torvik_data, home_team, away_team, neutral_site)
            away_score = calculate_away_score(torvik_data, away_team, home_team)
            
            prediction = {
                'Home Team': home_team,
                'Away Team': away_team,
                'Home Score': round(home_score, 1),
                'Away Score': round(away_score, 1)
            }
            
            predictions.append(prediction)
            if SPAM:
                print(f"✓ {away_team} @ {home_team}: {away_score:.1f} - {home_score:.1f}")
            
        except Exception as e:
            if SPAM:
                print(f"✗ Error: {home_team} vs {away_team}: {e}")
            skipped.append({'home': home_team, 'away': away_team, 'error': str(e)})
    
    # Create DataFrame
    predictions_df = pd.DataFrame(predictions)
    
    if len(skipped) > 0:
        print(f"⚠ Skipped {len(skipped)} games (missing data)")
    
    # Save to CSV
    output_file = f'torvik_predictions.csv'
    predictions_df.to_csv(output_file, index=False)
    
    print(f"✓ {len(predictions_df)}/{len(matchups_df)} predictions → {output_file}")
    print("="*60)
    
    return predictions_df


if __name__ == "__main__":
    predict_games()