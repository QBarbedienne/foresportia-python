from foresportia import ForesportiaClient


client = ForesportiaClient.from_env()
data = client.picks_today()
matches = data.get("matches", [])
print(f"Today's picks: {len(matches)}")
for match in matches[:3]:
    print(match.get("home_team"), "vs", match.get("away_team"), "-", match.get("pick"))
