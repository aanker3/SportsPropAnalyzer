import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

FILE_PATH = "get_props/prizepicks_props.json"


class OddsType(Enum):
    STANDARD = "standard"
    DEMON = "demon"
    GOBLIN = "goblin"

    @staticmethod
    def from_string(value: str) -> "OddsType":
        """Convert a string to an OddsType enum, defaulting to STANDARD."""
        try:
            return OddsType(value.lower())
        except ValueError:
            return OddsType.STANDARD  # Default if an unknown value appears


@dataclass
class Prop:
    player_name: str
    stat: str
    target: float
    over_under: str
    odds_type: OddsType


def load_bets_json(filepath: str = FILE_PATH) -> dict:
    """Read and parse JSON data from the PrizePicks file."""
    with open(filepath, "r", encoding='utf-8') as file:
        return json.load(file)


def extract_players(bet_data: dict) -> Dict[str, dict]:
    """Extract player details into a dictionary mapping player_id -> player_info."""
    return {
        player["id"]: player["attributes"]
        for player in bet_data.get("included", [])
        if player["type"] == "new_player"
    }


def create_props(bet_data: dict) -> List[Prop]:
    """Create Prop objects from bet and player data."""
    players = extract_players(bet_data)
    props = []

    for bet in bet_data.get("data", []):
        attr = bet["attributes"]
        player_id = bet["relationships"]["new_player"]["data"]["id"]
        player = players.get(player_id, {})

        if not player:
            continue  # Skip if player details are missing

        player_name = player.get("name", "Unknown")

        # Skip if the player name contains a '+'
        if "+" in player_name:
            continue

        # Determine Over/Under (Placeholder logic, adjust if needed)
        over_under = "over" if attr["line_score"] > 0 else "under"

        # Convert odds_type string to an enum value
        odds_type = OddsType.from_string(attr.get("odds_type", "standard"))

        props.append(
            Prop(
                player_name=player_name,
                stat=attr["stat_type"],
                target=attr["line_score"],
                over_under=over_under,
                odds_type=odds_type,
            )
        )

    return props


# Example usage:
if __name__ == "__main__":
    bet_data = load_bets_json()
    props = create_props(bet_data)

    for prop in props:
        print(prop)
