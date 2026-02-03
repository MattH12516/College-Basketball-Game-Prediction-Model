"""
Combine predictions from Kenpom, Torvik, and Haslametrics
Averages scores and rounds to nearest whole number
"""

import pandas as pd


KENPOM_FILE = 'kenpom_predictions.csv'
TORVIK_FILE = 'torvik_predictions.csv'
HASLAM_FILE = 'haslametrics_predictions.csv'
OUTPUT_FILE = 'combined_predictions.csv'

def combine_predictions():
    """Combine predictions from all three models"""
    
    print("="*60)
    print("COMBINING MODEL PREDICTIONS")
    print("="*60)
    
    try:
        # Load all predictions
        kenpom_df = pd.read_csv(KENPOM_FILE)
        torvik_df = pd.read_csv(TORVIK_FILE)
        haslam_df = pd.read_csv(HASLAM_FILE)
        
        print(f"✓ Loaded Kenpom: {len(kenpom_df)} games")
        print(f"✓ Loaded Torvik: {len(torvik_df)} games")
        print(f"✓ Loaded Haslametrics: {len(haslam_df)} games")
        
        # Rename Haslametrics columns to match
        haslam_df = haslam_df.rename(columns={
            'home_team': 'Home Team',
            'away_team': 'Away Team',
            'home_score': 'Home Score',
            'away_score': 'Away Score'
        })
        
        # Merge all three on team names
        # Start with Kenpom as base
        combined_df = kenpom_df.copy()
        combined_df = combined_df.rename(columns={
            'Home Score': 'Kenpom_Home',
            'Away Score': 'Kenpom_Away'
        })
        
        # Merge Torvik
        torvik_df = torvik_df.rename(columns={
            'Home Score': 'Torvik_Home',
            'Away Score': 'Torvik_Away'
        })
        combined_df = combined_df.merge(
            torvik_df[['Home Team', 'Away Team', 'Torvik_Home', 'Torvik_Away']],
            on=['Home Team', 'Away Team'],
            how='left'
        )
        
        # Check for missing Torvik predictions
        missing_torvik = combined_df[combined_df['Torvik_Home'].isna()]
        if len(missing_torvik) > 0:
            print(f"\n⚠ {len(missing_torvik)} games missing from Torvik:")
            for _, game in missing_torvik.iterrows():
                print(f"  - {game['Away Team']} @ {game['Home Team']}")
        
        # Merge Haslametrics
        haslam_df = haslam_df.rename(columns={
            'Home Score': 'Haslam_Home',
            'Away Score': 'Haslam_Away'
        })
        combined_df = combined_df.merge(
            haslam_df[['Home Team', 'Away Team', 'Haslam_Home', 'Haslam_Away']],
            on=['Home Team', 'Away Team'],
            how='left'
        )
        
        # Check for missing Haslametrics predictions
        missing_haslam = combined_df[combined_df['Haslam_Home'].isna()]
        if len(missing_haslam) > 0:
            print(f"\n⚠ {len(missing_haslam)} games missing from Haslametrics:")
            for _, game in missing_haslam.iterrows():
                print(f"  - {game['Away Team']} @ {game['Home Team']}")
        
        # Calculate averages (handling missing values)
        # Home scores
        home_scores = combined_df[['Kenpom_Home', 'Torvik_Home', 'Haslam_Home']]
        combined_df['Home Score'] = home_scores.mean(axis=1, skipna=True)
        
        # Away scores
        away_scores = combined_df[['Kenpom_Away', 'Torvik_Away', 'Haslam_Away']]
        combined_df['Away Score'] = away_scores.mean(axis=1, skipna=True)
        
        # Round to nearest integer
        combined_df['Home Score'] = combined_df['Home Score'].round()
        combined_df['Away Score'] = combined_df['Away Score'].round()
        
        # Keep only final columns
        final_df = combined_df[['Home Team', 'Away Team', 'Home Score', 'Away Score']].copy()
        
        # Save
        final_df.to_csv(OUTPUT_FILE, index=False)
        
        print(f"\n✓ Combined {len(final_df)} games → {OUTPUT_FILE}")
        print("="*60)
        
        # Show sample with all model scores
        print("\nSample (showing all models):")
        sample = combined_df[['Home Team', 'Away Team', 
                             'Kenpom_Home', 'Torvik_Home', 'Haslam_Home', 'Home Score',
                             'Kenpom_Away', 'Torvik_Away', 'Haslam_Away', 'Away Score']].head(3)
        print(sample.to_string(index=False))
        
        return final_df
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Make sure all prediction CSV files exist")
        return None


if __name__ == "__main__":
    combine_predictions()