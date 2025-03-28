import os
import sys
import json
import requests
from pathlib import Path

def gen_prizepicks_json():
    # Get the directory where the script resides
    script_dir = Path(__file__).parent
    file_name = script_dir / "prizepicks_props.json"

    # Delete the existing file if it exists
    if file_name.exists():
        try:
            os.remove(file_name)
        except OSError as e:
            print(f"Failed to delete existing file: {e}")
            sys.exit(1)

    # Set up HTTP session
    session = requests.Session()
    session.verify = True  # SSL verification (False would be equivalent to InsecureSkipVerify=True)

    # NOTE: league_id=8 == NFL FYI
    url = "https://api.prizepicks.com/projections?league_id=7&per_page=250&single_stat=true"

    # Set HTTP headers
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

    # Make HTTP request
    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        sys.exit(1)

    # Write to file
    try:
        with open(file_name, 'w') as f:
            # If the response is JSON, you might want to pretty-print it
            try:
                json_data = response.json()
                json.dump(json_data, f, indent=2)
            except ValueError:
                # If not JSON, write raw content
                f.write(response.text)
    except IOError as e:
        print(f"Failed to write file: {e}")
        sys.exit(1)

    print(f"done - file saved at: {file_name}")

if __name__ == "__main__":
    gen_prizepicks_json()