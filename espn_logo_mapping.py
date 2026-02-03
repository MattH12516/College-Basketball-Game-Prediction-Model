"""
Fetch all NCAA Men's Basketball team IDs and logo URLs from ESPN API

"""

import requests
import json
from team_mapping import get_canonical_name

def fetch_all_cbb_teams():
    """Fetch all college basketball teams from ESPN API"""
    
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams"
    
    try:
        response = requests.get(url, params={'limit': 400})
        response.raise_for_status()
        data = response.json()
        
        team_logos = {}
        team_info = {}
        unmapped_teams = []
        
        # Parse the response
        if 'sports' in data and len(data['sports']) > 0:
            leagues = data['sports'][0].get('leagues', [])
            
            for league in leagues:
                teams = league.get('teams', [])
                
                for team_obj in teams:
                    team = team_obj.get('team', {})
                    
                    team_id = team.get('id')
                    team_name = team.get('displayName')
                    team_short = team.get('shortDisplayName')
                    team_abbr = team.get('abbreviation')
                    
                    # Construct logo URL from team ID
                    logo_url = f"https://a.espncdn.com/i/teamlogos/ncaa/500/{team_id}.png" if team_id else None
                    
                    if team_id and team_name:
                        # Normalize team name using canonical mapping
                        canonical_name = get_canonical_name(team_name)
                        
                        if canonical_name:
                            # Use canonical name as key
                            team_logos[canonical_name] = {
                                'id': team_id,
                                'name': canonical_name,
                                'espn_name': team_name,  # Keep original ESPN name
                                'short_name': team_short,
                                'abbreviation': team_abbr,
                                'logo_url': logo_url
                            }
                        else:
                            # No mapping found
                            unmapped_teams.append(team_name)
                            # Still add it with original name
                            team_logos[team_name] = {
                                'id': team_id,
                                'name': team_name,
                                'espn_name': team_name,
                                'short_name': team_short,
                                'abbreviation': team_abbr,
                                'logo_url': logo_url
                            }
                        
                        team_info[team_id] = team_name
        
        print(f"Found {len(team_logos)} teams")
        
        # Report unmapped teams
        if unmapped_teams:
            print(f"\n⚠ {len(unmapped_teams)} teams not mapped (add to team_mapping.py):")
            for team in sorted(unmapped_teams):
                print(f"  - {team}")
        
        # Save to JSON
        with open('espn_team_logos.json', 'w') as f:
            json.dump(team_logos, f, indent=2)
        
        print(f"\n✓ Saved to espn_team_logos.json")
        
        # Show some examples
        print("\nExample teams:")
        for i, (name, info) in enumerate(list(team_logos.items())[:10]):
            espn_name = info.get('espn_name', name)
            if espn_name != name:
                print(f"  {espn_name} → {name}: {info['logo_url']}")
            else:
                print(f"  {name}: {info['logo_url']}")
            if i >= 9:
                break
        
        return team_logos
        
    except Exception as e:
        print(f"Error fetching teams: {e}")
        return None

if __name__ == "__main__":
    teams = fetch_all_cbb_teams()
    
    if teams:
        print(f"\n✓ Successfully fetched {len(teams)} college basketball teams")
        print("Data saved to: espn_team_logos.json")
        print("\nTeam names are now normalized to match your predictions!")