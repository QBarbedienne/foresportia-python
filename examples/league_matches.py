from foresportia import ForesportiaClient


client = ForesportiaClient.from_env()
data = client.league_matches("CHN", include="all", days=14, limit=10)
matches = data.get("matches", [])
print(f"CHN matches: {len(matches)}")
for match in matches[:3]:
    print(match.get("home_team"), "vs", match.get("away_team"), "-", match.get("pick"))
