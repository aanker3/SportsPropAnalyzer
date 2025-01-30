import requests
import urllib3

urllib3.disable_warnings()

session = requests.Session()
adapter = requests.adapters.HTTPAdapter()

session.mount("https://", adapter)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Connection": "keep-alive",
}

response = session.get(
    "https://api.prizepicks.com/projections?league_id=7&per_page=250&single_stat=true",
    headers=headers,
    verify=False,
)

print(response.status_code, response.text)
