import os
import json
import requests
from pathlib import Path

def gen_prizepicks_json(league_id: int = 7, filename: str = "prizepicks_props.json"):
    script_dir = Path(__file__).parent
    file_name = script_dir / filename

    if file_name.exists():
        try:
            os.remove(file_name)
        except OSError as e:
            raise RuntimeError(f"Failed to delete existing props file: {e}") from e

    session = requests.Session()
    session.verify = True

    url = f"https://api.prizepicks.com/projections?league_id={league_id}&per_page=250&single_stat=true"

    headers = {
        "Host": "api.prizepicks.com",
        "Sec-Ch-Ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Sec-Ch-Ua-Mobile": "?1",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36",
        "Sec-Ch-Ua-Platform": '"Android"',
        "Origin": "https://app.prizepicks.com",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://app.prizepicks.com/",
        "Accept-Language": "en-US,en;q=0.9",
        "If-Modified-Since": "Thu, 12 Jan 2023 19:23:47 GMT"
    }

    try:
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"PrizePicks API request failed: {e}") from e

    try:
        with open(file_name, 'w') as f:
            try:
                json_data = response.json()
                json.dump(json_data, f, indent=2)
            except ValueError:
                f.write(response.text)
    except IOError as e:
        raise RuntimeError(f"Failed to write props file: {e}") from e

    print(f"done - file saved at: {file_name}")


def gen_mlb_prizepicks_json():
    gen_prizepicks_json(league_id=2, filename="prizepicks_props_mlb.json")


if __name__ == "__main__":
    gen_prizepicks_json()