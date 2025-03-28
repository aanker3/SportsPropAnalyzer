import subprocess
import json
import os
from sqlalchemy.orm import Session
from alphabetter.nba_backend.database import get_db
from alphabetter.nba_backend.models import PrizePicksProp, OddsType
from alphabetter.nba_backend.get_props.get_props import load_bets_json, create_props
from alphabetter.nba_backend.common.nba_api_common import get_player_id
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

# Function to call the executable and generate the JSON file
def generate_prize_picks_json():
    """Generate the PrizePicks JSON file by running the appropriate command based on the OS."""
    if os.name == "nt":  # Windows
        # On Windows, run the Go file
        go_file_path = SCRIPT_DIR / "get_props" / "bets.go"
        cmd = ["go", "run", str(go_file_path)]
    else:  # Linux or other OS
        # On Linux, run the compiled binary
        binary_file_path = SCRIPT_DIR / "get_props" / "gen_nba_prizepicks"
        cmd = [str(binary_file_path)]

    # Print the command for debugging purposes
    print(f"Running command: {' '.join(cmd)}")

    # Run the command
    subprocess.run(cmd, check=True)

# Function to store PrizePicks props in the database
def store_prize_picks_props(db: Session, props: list):
    for prop in props:

        #Skip fantasy score for now.  unsupported.
        if prop.stat == "Fantasy Score" or prop.stat == "Dunks":  # Skip unsupported stats
            print(f"Skipping prop for {prop.player_name} with stat 'Fantasy Score'")
            continue
        
        prop_player_id = get_player_id(prop.player_name) 

        new_prop = PrizePicksProp(
            player_name=prop.player_name,
            player_id=prop_player_id,
            stat=prop.stat,
            target=prop.target,
            over_under=prop.over_under,
            odds_type=prop.odds_type.value  # Store enum as string
        )
        db.add(new_prop)

        # If odds_type is "standard", add another entry with over_under set to "under"
        if prop.odds_type == OddsType.STANDARD:
            new_prop_under = PrizePicksProp(
                player_name=prop.player_name,
                player_id=prop_player_id,
                stat=prop.stat,
                target=prop.target,
                over_under="under",
                odds_type=prop.odds_type.value  # Store enum as string
            )
            db.add(new_prop_under)

    db.commit()

def fetch_and_store_prop_data():
    # Generate the JSON file
    generate_prize_picks_json()

    # Load the JSON data
    bet_data = load_bets_json()

    # Create props from the JSON data
    props = create_props(bet_data)

    # Store props in the database
    db: Session = next(get_db())
    store_prize_picks_props(db, props)
    db.close()

    print("Stored PrizePicks props successfully!")

    return props

if __name__ == "__main__":
    fetch_and_store_prop_data()