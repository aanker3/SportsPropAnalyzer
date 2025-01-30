import json


def Gather_Bets_Json():
    """
    Gather Bet data recieved from PrizePicks
    Turn into JSON
    """
    with open("get_props/prizepicks_props.txt", "r") as file:
        bets = file.readlines()

        bet_data = json.loads(bets[0])

    return bet_data


def Gather_Bets_From_Data(bet_data, Needed_Stat):
    """
    Gather all the bet objects and append to bets_list
    Gather all the players and append to players_list
    """
    bets_list = []
    players_list = []

    i = 0
    while i < (len(bet_data["data"])):

        stat_type = bet_data["data"][i]["attributes"]["stat_type"]

        if stat_type == Needed_Stat:
            stat_type = bet_data["data"][i]["attributes"]["stat_type"]

            bets_list.append(bet_data["data"][i])
        i += 1

    j = 0
    while j < (len(bet_data["included"])):
        if bet_data["included"][j]["type"] == "new_player":
            players_list.append(bet_data["included"][j])
        j += 1

    return bets_list, players_list


def Create_Bet_Dicts(bets_list, players_list):
    """
    Players names were not matched to bets before, so use bets_list
    and players_list to create dictionary for each bet, with the players name
    the team they are playing, the stat line, the stat type, and the players id
    """

    new_bets = []

    i = 0
    while i < len(bets_list):
        id_needed = bets_list[i]["relationships"]["new_player"]["data"]["id"]

        j = 0

        while j < len(players_list):
            current_id = players_list[j]["id"]
            if current_id == id_needed:
                new_bets.append(
                    {
                        "Stat_Score": bets_list[i]["attributes"]["line_score"],
                        "Team_Playing": bets_list[i]["attributes"]["description"],
                        "Stat_Type": bets_list[i]["attributes"]["stat_type"],
                        "Player_ID": players_list[j]["id"],
                        "Player_Name": players_list[j]["attributes"]["name"],
                        "Position": players_list[j]["attributes"]["position"],
                    }
                )
            j += 1
        i += 1

    return new_bets


def Create_Current_Bet_Dicts(Needed_Stat):
    bet_data = Gather_Bets_Json()
    bets_list, players_list = Gather_Bets_From_Data(bet_data, Needed_Stat)
    bet_dicts = Create_Bet_Dicts(bets_list, players_list)

    return bet_dicts


def get_prop_info():
    """
    Fetches player stats and returns them as a nested dictionary with all available stats.

    Returns:
        dict: A dictionary structured as {Player_Name: {Stat_Name: Stat_Value, ...}}.
    """
    # Define the stats you want to retrieve
    needed_stats = [
        "Points",
        "Rebounds",
        "Offensive Rebounds",
        "Assists",
        "Steals",
        "Blocks",
        "Turnovers",
        "3-Point Made",
    ]
    player_stats = {}

    # Loop through each needed stat
    for stat in needed_stats:
        # Fetch data for the specific stat
        bet_dicts = Create_Current_Bet_Dicts(stat)

        # Add data to the player_stats dictionary
        for bet in bet_dicts:
            player_name = bet["Player_Name"]
            # stat_name = bet["Stat_Name"]
            stat_value = bet["Stat_Score"]

            # Initialize player's stats if not already present
            if player_name not in player_stats:
                player_stats[player_name] = {}

            # Add or update the stat for the player
            player_stats[player_name][stat] = stat_value

    # Print the dictionary (optional, for debugging)
    # for name, stats in player_stats.items():
    #     print(f"{name}: {stats}")

    return player_stats


# if __name__ == "__main__":
#     needed_stat = "Points"  # Replace with the stat you're interested in
#     bet_dicts = Create_Current_Bet_Dicts(needed_stat)
#     for bet in bet_dicts:
#         print(bet)
#     stat_score = bet["Stat_Score"]
#     name = bet["Player_Name"]
