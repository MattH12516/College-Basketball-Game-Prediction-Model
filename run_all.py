"""
Master Script - Run Entire CBB Prediction Pipeline
Executes all steps from data fetching to visualization generation
"""

import subprocess
import sys
import shutil
import os




def run_script(script_name, description):
    """Run a Python script and handle errors"""
    print("\n" + "="*60)
    print(f"STEP: {description}")
    print("="*60)
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ ERROR in {script_name}")
        print(f"Script failed with error code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"✗ ERROR: {script_name} not found!")
        return False
    
def clear_predictions_folder():
    """Clear old prediction files before generating new ones"""
    predictions_dir = 'predictions'
    
    print(f"\nClearing old predictions from {predictions_dir}...")
    
    if os.path.exists(predictions_dir):
        shutil.rmtree(predictions_dir)
        print(f"✓ Deleted old predictions folder")
    
    os.makedirs(predictions_dir, exist_ok=True)
    print(f"✓ Created fresh predictions folder")


def main():
    """Run the complete prediction pipeline"""
    
    
    print("COLLEGE BASKETBALL PREDICTION MODEL")
    print("Master Pipeline Execution")
    
    
    steps_completed = 0
    total_steps = 8
    
    # Step 1: Fetch daily matchups from ESPN
    if run_script('fetch_daily_games.py', 'Fetch Daily Matchups (ESPN)'):
        steps_completed += 1
    else:
        print("\n⚠ Pipeline stopped due to error")
        return
    
    # Step 2: Fetch Kenpom data
    if run_script('kenpom_fetch.py', 'Fetch Kenpom Data'):
        steps_completed += 1
    else:
        print("\n⚠ Pipeline stopped due to error")
        return
    
    # Step 3: Generate Kenpom predictions
    if run_script('kenpom_game_output.py', 'Generate Kenpom Predictions'):
        steps_completed += 1
    else:
        print("\n⚠ Pipeline stopped due to error")
        return
    
    # Step 4: Fetch Torvik data
    if run_script('torvik_scrape.py', 'Fetch Torvik Data'):
        steps_completed += 1
    else:
        print("\n⚠ Warning: Torvik data failed, continuing...")
    
    # Step 5: Generate Torvik predictions
    if run_script('torvik_game_output.py', 'Generate Torvik Predictions'):
        steps_completed += 1
    else:
        print("\n⚠ Warning: Torvik predictions failed, continuing...")
    
    # Step 6: Scrape Haslametrics
    if run_script('haslametric_scrape.py', 'Scrape Haslametrics Predictions'):
        steps_completed += 1
    else:
        print("\n⚠ Warning: Haslametrics scraping failed, continuing...")
    
    # Step 7: Combine all predictions
    if run_script('combine_predictions.py', 'Combine Model Predictions'):
        steps_completed += 1
    else:
        print("\n⚠ Pipeline stopped due to error")
        return
    
    # Final Step (8): Generate visualizations
    print("\n" + "="*60)
    print("FINAL STEP: Generate Game Card Visualizations")
    print("="*60)

    clear_predictions_folder()
    
    if run_script('game_card_generator.py', 'Generate Game Cards'):
        steps_completed += 1
    else:
        print("\n⚠ Visualization generation failed")
        return
    
    # Summary
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"Completed {steps_completed}/{total_steps} steps")
    print("\n Results:")
    print("  - Predictions: combined_predictions.csv")
    print("  - Visualizations: predictions/index.html")
    print("\n Next step: Open predictions/index.html in your browser!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()