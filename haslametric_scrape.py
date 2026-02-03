"""
Haslametrics Prediction Scraper
Scrapes predicted game scores from Haslametrics
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import re
from team_mapping import get_canonical_name


USE_TOMORROW = True  # If True, scrapes tomorrow's games. If False, uses SPECIFIC_DATE below
SPECIFIC_DATE = '2026-02-03'  # Format: 'YYYY-MM-DD' (only used if USE_TOMORROW = False)
SPAM = False  


def scrape_haslametrics_predictions(date_str=None):
    """
    Scrape predicted scores from Haslametrics
    
    Args:
        date_str: Date in format 'YYYY-MM-DD' (e.g., '2026-01-22')
                  If None, uses today's date
    
    Returns:
        DataFrame with columns: home_team, away_team, home_score, away_score
    """
    
    # Format date for dropdown
    if date_str is None:
        date_obj = datetime.now()
    else:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Haslametrics format: "Sunday, December 8, 2025"
    try:
        formatted_date = date_obj.strftime('%A, %B %-d, %Y')
    except:
        formatted_date = date_obj.strftime('%A, %B %#d, %Y')
    
    if SPAM:
        print(f"Fetching Haslametrics predictions for: {formatted_date}")
    
    options = Options()
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    options.add_argument('--disable-gpu')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get('https://haslametrics.com/ratings.php')
        
        wait = WebDriverWait(driver, 10)
        
        # Select date
        date_select_element = wait.until(
            EC.presence_of_element_located((By.ID, "cboUpcomingDates"))
        )
        
        date_dropdown = Select(date_select_element)
        
        try:
            date_dropdown.select_by_visible_text(formatted_date)
            if SPAM:
                print(f"✓ Selected date")
        except Exception as e:
            # Try alternative format
            alt_format = date_obj.strftime('%A, %B %d, %Y')
            date_dropdown.select_by_visible_text(alt_format)
            formatted_date = alt_format
        
        # Wait for games to load
        time.sleep(4)
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        games_data = []
        
        # Find all game cells (IDs like tdUpcoming_N_1 or tdUpcoming_N_2)
        all_cells = soup.find_all('td', id=re.compile(r'tdUpcoming_\d+_[12]'))
        
        # Group by game number
        games_dict = {}
        
        for cell in all_cells:
            cell_id = cell.get('id', '')
            match = re.match(r'tdUpcoming_(\d+)_([12])(_sc)?', cell_id)
            
            if not match:
                continue
            
            game_num = int(match.group(1))
            row_num = int(match.group(2))  # 1 = away, 2 = home
            is_score = match.group(3) == '_sc'
            
            if game_num not in games_dict:
                games_dict[game_num] = {}
            
            if is_score:
                # Score cell
                try:
                    score = float(cell.get_text(strip=True))
                    if row_num == 1:
                        games_dict[game_num]['away_score'] = score
                    else:
                        games_dict[game_num]['home_score'] = score
                except ValueError:
                    pass
            else:
                # Team name cell
                link = cell.find('a', href=re.compile(r'ratings2\.php'))
                if link:
                    team_name = link.get_text(strip=True)
                    if row_num == 1:
                        games_dict[game_num]['away_team'] = team_name
                    else:
                        games_dict[game_num]['home_team'] = team_name
        
        # Convert to list
        for game_num, game_data in sorted(games_dict.items()):
            if all(k in game_data for k in ['away_team', 'home_team', 'away_score', 'home_score']):
                games_data.append({
                    'home_team': game_data['home_team'],
                    'away_team': game_data['away_team'],
                    'home_score': game_data['home_score'],
                    'away_score': game_data['away_score']
                })
        
        if not games_data:
            print("No games found!")
            return None
        
        df = pd.DataFrame(games_data)
        
        # Normalize team names
        df = normalize_team_names(df)
        
        if SPAM:
            print(f"✓ Scraped {len(df)} games")
        
        return df
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        driver.quit()


def normalize_team_names(df):
    """Normalize team names using canonical mapping"""
    
    unmapped_teams = []
    
    for idx, row in df.iterrows():
        # Remove ranking numbers
        away_clean = re.sub(r'\s*\d+$', '', row['away_team']).strip()
        home_clean = re.sub(r'\s*\d+$', '', row['home_team']).strip()
        
        # Map away team
        normalized_away = get_canonical_name(away_clean)
        if normalized_away:
            df.at[idx, 'away_team'] = normalized_away
        else:
            if away_clean not in unmapped_teams:
                unmapped_teams.append(away_clean)
            df.at[idx, 'away_team'] = away_clean
        
        # Map home team
        normalized_home = get_canonical_name(home_clean)
        if normalized_home:
            df.at[idx, 'home_team'] = normalized_home
        else:
            if home_clean not in unmapped_teams:
                unmapped_teams.append(home_clean)
            df.at[idx, 'home_team'] = home_clean
    
    # Warn about unmapped teams
    if unmapped_teams:
        print("⚠ Unmapped teams (add to team_mapping.py):")
        for team in sorted(set(unmapped_teams)):
            print(f"  - {team}")
    
    return df


def main():
    """Run Haslametrics scraper using configuration settings"""
    
    print("="*60)
    print("HASLAMETRICS PREDICTIONS")
    print("="*60)
    
    # Determine which date to use
    if USE_TOMORROW:
        tomorrow = datetime.now() + timedelta(days=1)
        date_str = tomorrow.strftime('%Y-%m-%d')
        if SPAM:
            print(f"Config: USE_TOMORROW = True")
        print(f"Scraping: {date_str}")
    else:
        date_str = SPECIFIC_DATE
        if SPAM:
            print(f"Config: USE_TOMORROW = False")
        print(f"Scraping: {date_str}")
    
    df = scrape_haslametrics_predictions(date_str)
    
    if df is not None:
        # Save to CSV
        output_file = 'haslametrics_predictions.csv'
        df.to_csv(output_file, index=False)
        print(f"✓ {len(df)} predictions → {output_file}")
        print("="*60)
    else:
        print("Failed to scrape predictions")


if __name__ == "__main__":
    main()