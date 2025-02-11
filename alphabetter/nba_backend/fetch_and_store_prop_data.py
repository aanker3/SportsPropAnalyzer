import subprocess
import json
from sqlalchemy.orm import Session
from alphabetter.nba_backend.database import get_db
from alphabetter.nba_backend.models import PrizePicksProp, OddsType
from get_props.get_props import load_bets_json, create_props

# Function to call the executable and generate the JSON file
def generate_prize_picks_json():
    subprocess.run(["./get_props/gen_nba_prizepicks.exe"], check=True)

# Function to store PrizePicks props in the database
def store_prize_picks_props(db: Session, props: list):
    for prop in props:
        new_prop = PrizePicksProp(
            player_name=prop.player_name,
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
                stat=prop.stat,
                target=prop.target,
                over_under="under",
                odds_type=prop.odds_type.value  # Store enum as string
            )
            db.add(new_prop_under)

    db.commit()

def main():
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

if __name__ == "__main__":
    main()