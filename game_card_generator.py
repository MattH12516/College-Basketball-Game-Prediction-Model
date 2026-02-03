"""
Generate PNG game cards using matplotlib
Creates individual PNGs + index HTML to view all
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import requests
from io import BytesIO
import json
import os
from datetime import datetime


PREDICTIONS_FILE = 'combined_predictions.csv' 
MATCHUPS_FILE = 'daily_matchups.csv'
LOGO_DATA_FILE = 'espn_team_logos.json'
OUTPUT_DIR = 'predictions'
SPAM = False 


def load_logo_data():
    """Load team logo URLs from JSON"""
    try:
        with open(LOGO_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {LOGO_DATA_FILE} not found!")
        print("Run fetch_espn_logos.py first")
        return {}


def get_logo_url(team_name, logo_data):
    """Get logo URL for a team (names are pre-normalized in JSON)"""
    
    # Direct lookup - names are already normalized
    if team_name in logo_data:
        return logo_data[team_name].get('logo_url')
    
    # Fallback: case-insensitive match just in case
    team_lower = team_name.lower()
    for key, value in logo_data.items():
        if key.lower() == team_lower:
            return value.get('logo_url')
    
    return None


def download_logo(url):
    """Download and return logo image, resized to consistent dimensions"""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        
        # Resize to max 150x150 while maintaining aspect ratio
        img.thumbnail((150, 150), Image.Resampling.LANCZOS)
        
        return img
    except:
        return None


def create_game_card(home_team, away_team, home_score, away_score,
                     game_time, venue, neutral_site, logo_data, output_path):
    """
    Create a super compact game card PNG - 2x2 grid layout
    Airtight spacing, black borders, red for winner
    """
    
    # Create figure - MUCH smaller and tighter
    fig, ax = plt.subplots(figsize=(4, 2.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Background
    bg_rect = patches.Rectangle((0, 0), 10, 10, linewidth=0, 
                                 facecolor='white', edgecolor='none')
    ax.add_patch(bg_rect)
    
    # Main border - BLACK
    border = patches.Rectangle((0, 0), 10, 10, linewidth=2,
                               facecolor='none', edgecolor='black')
    ax.add_patch(border)
    
    # Determine winner
    home_winning = home_score > away_score
    
    # === TOP SECTION: Team Logos & Names ===
    # Horizontal divider after logos/names - BLACK
    ax.plot([0, 10], [5.8, 5.8], color='black', linewidth=1.5)
    
    # Vertical divider between teams - BLACK
    ax.plot([5, 5], [5.8, 10], color='black', linewidth=1.5)
    
    # HOME TEAM (LEFT) - Logo and Name
    home_logo_url = get_logo_url(home_team, logo_data)
    if home_logo_url:
        home_logo = download_logo(home_logo_url)
        if home_logo:
            imagebox = OffsetImage(home_logo, zoom=0.23)  # Increased from 0.09
            ab = AnnotationBbox(imagebox, (2.5, 8.3), frameon=False)
            ax.add_artist(ab)
    
    # Home team name - bigger font
    ax.text(2.5, 6.5, home_team, ha='center', va='center', 
            fontsize=10, fontweight='bold', color='#222')  # Increased from 9
    
    # AWAY TEAM (RIGHT) - Logo and Name
    away_logo_url = get_logo_url(away_team, logo_data)
    if away_logo_url:
        away_logo = download_logo(away_logo_url)
        if away_logo:
            imagebox = OffsetImage(away_logo, zoom=0.23)  # Increased from 0.09
            ab = AnnotationBbox(imagebox, (7.5, 8.3), frameon=False)
            ax.add_artist(ab)
    
    # Away team name
    ax.text(7.5, 6.5, away_team, ha='center', va='center',
            fontsize=10, fontweight='bold', color='#222')  # Increased from 9
    
    # === MIDDLE SECTION: Scores ===
    # Horizontal divider after scores - BLACK
    ax.plot([0, 10], [3.2, 3.2], color='black', linewidth=1.5)
    
    # Vertical divider between scores - BLACK
    ax.plot([5, 5], [3.2, 5.8], color='black', linewidth=1.5)
    
    # Home score (left) - RED if winning, BLACK if losing
    home_color = '#d32f2f' if home_winning else '#222'
    ax.text(2.5, 4.5, str(home_score), ha='center', va='center',
            fontsize=28, fontweight='bold', color=home_color)
    
    # Away score (right) - RED if winning, BLACK if losing
    away_color = '#d32f2f' if not home_winning else '#222'
    ax.text(7.5, 4.5, str(away_score), ha='center', va='center',
            fontsize=28, fontweight='bold', color=away_color)
    
    # === BOTTOM SECTION: Game Info ===
    # Time and date - bigger font
    ax.text(5, 2.0, game_time, ha='center', va='center',
            fontsize=12, fontweight='600', color='#222')
    
    # Venue - bigger font
    venue_text = venue
    if neutral_site:
        venue_text += " (N)"
    ax.text(5, 0.8, venue_text, ha='center', va='center',
            fontsize=10, color='#444')
    
    # Save with minimal padding
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                facecolor='white', pad_inches=0.05)
    plt.close()


def generate_index_html(game_files, output_dir):
    """Generate HTML index to view all game cards"""
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CBB Predictions - {datetime.now().strftime('%B %d, %Y')}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }}
            
            .header {{
                text-align: center;
                color: white;
                margin-bottom: 20px;
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 2em;
                margin: 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .header p {{
                font-size: 1em;
                margin: 5px 0;
                opacity: 0.9;
            }}
            
            .games-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 10px;
            }}
            
            .game-card {{
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                transition: transform 0.3s ease;
            }}
            
            .game-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 15px 40px rgba(0,0,0,0.3);
            }}
            
            .game-card img {{
                width: 100%;
                display: block;
            }}
            
            @media (max-width: 768px) {{
                .games-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .header h1 {{
                    font-size: 1.5em;
                }}
            }}
            
            @media (min-width: 769px) and (max-width: 1200px) {{
                .games-grid {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏀 College Basketball Predictions</h1>
            <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
            <p>{len(game_files)} Games</p>
        </div>
        
        <div class="games-grid">
    """
    
    # Add each game card (in chronological order, NOT alphabetical)
    for filename in game_files:
        html += f"""
            <div class="game-card">
                <img src="{filename}" alt="Game prediction">
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    # Save HTML
    html_path = os.path.join(output_dir, 'index.html')
    with open(html_path, 'w') as f:
        f.write(html)
    
    return html_path


def main():
    """Generate all game card visualizations"""
    
    print("="*60)
    print("GENERATING GAME CARD VISUALIZATIONS")
    print("="*60)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load data
    try:
        predictions_df = pd.read_csv(PREDICTIONS_FILE)
        matchups_df = pd.read_csv(MATCHUPS_FILE)
        logo_data = load_logo_data()
        
        if not logo_data:
            print("Warning: No logo data loaded, logos will be missing")
        
        # Merge predictions with matchup details
        merged_df = predictions_df.merge(
            matchups_df[['home_team', 'away_team', 'game_time', 'venue', 'neutral_site']],
            left_on=['Home Team', 'Away Team'],
            right_on=['home_team', 'away_team'],
            how='left'
        )
        
        # Sort by game time (earliest first)
        merged_df['game_time_dt'] = pd.to_datetime(merged_df['game_time'], format='%Y-%m-%d %I:%M %p', errors='coerce')
        merged_df = merged_df.sort_values('game_time_dt')
        
        print(f"\nGenerating {len(merged_df)} game cards (sorted by time)...")
        
        game_files = []
        
        # Generate each game card (already sorted by time)
        for idx, game in merged_df.iterrows():
            # Create filename
            home_safe = game['Home Team'].replace(' ', '_').replace('/', '-')
            away_safe = game['Away Team'].replace(' ', '_').replace('/', '-')
            filename = f"{home_safe}_vs_{away_safe}.png"
            output_path = os.path.join(OUTPUT_DIR, filename)
            
            # Create card
            create_game_card(
                home_team=game['Home Team'],
                away_team=game['Away Team'],
                home_score=game['Home Score'],
                away_score=game['Away Score'],
                game_time=game.get('game_time', 'TBD'),
                venue=game.get('venue', 'TBD'),
                neutral_site=game.get('neutral_site', False),
                logo_data=logo_data,
                output_path=output_path
            )
            
            game_files.append(filename)
        
        # Generate index HTML
        html_path = generate_index_html(game_files, OUTPUT_DIR)
        
        print("="*60)
        print(f"✓ Generated {len(game_files)} game cards")
        print(f"✓ Created index → {html_path}")
        print("="*60)
        print(f"\nOpen {html_path} in your browser to view all games!")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Make sure CSV files exist")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()